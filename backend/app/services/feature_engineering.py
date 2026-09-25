import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime

class FeatureEngineeringService:
    def __init__(self, db: Session):
        self.db = db

    def _get_table_as_df(self, model) -> pd.DataFrame:
        query = self.db.query(model)
        df = pd.read_sql(query.statement, self.db.bind)
        return df

    def calculate_features(self):
        # 1. Fetch raw data from database
        employees = self._get_table_as_df(models.Employee)
        if employees.empty:
            return {"status": "success", "message": "No employees found."}
            
        compensation = self._get_table_as_df(models.Compensation)
        performance = self._get_table_as_df(models.PerformanceReview)
        workload = self._get_table_as_df(models.WorkloadAttendance)
        hr_tickets = self._get_table_as_df(models.HRTicket)
        training = self._get_table_as_df(models.TrainingEngagement)

        # Standardize employee_ids for case-insensitive pandas merges
        employees['employee_id_clean'] = employees['employee_id'].astype(str).str.lower().str.strip()
        for df in [compensation, performance, workload, hr_tickets, training]:
            if not df.empty and 'employee_id' in df.columns:
                df['employee_id_clean'] = df['employee_id'].astype(str).str.lower().str.strip()

        # Base DataFrame with employee backbone
        features_df = employees[['employee_id', 'employee_id_clean', 'hire_date', 'manager_id']].copy()
        current_date = pd.Timestamp(datetime.utcnow().date())
        
        # --- Feature 1: Tenure Years ---
        features_df['hire_date'] = pd.to_datetime(features_df['hire_date'])
        features_df['tenure_years'] = ((current_date - features_df['hire_date']).dt.days / 365.0).clip(lower=0.1)

        # --- Manager Tenure Years (Feature 19) ---
        # Baseline manager tenure approximation
        features_df['manager_tenure_years'] = np.minimum(features_df['tenure_years'], 2.5)

        # --- Feature Group 2: Compensation & Growth ---
        if not compensation.empty:
            compensation['effective_date'] = pd.to_datetime(compensation['effective_date'])
            # Sort by date for proper calculation
            comp_sorted = compensation.sort_values(by=['employee_id_clean', 'effective_date'])
            
            # Latest compensation metrics
            latest_comp = comp_sorted.groupby('employee_id_clean').last().reset_index()
            latest_comp['total_compensation'] = latest_comp['salary'] + latest_comp['bonus'] + latest_comp['stock_options']
            
            # Salary growth rate
            first_comp = comp_sorted.groupby('employee_id_clean').first().reset_index()
            comp_growth = latest_comp[['employee_id_clean', 'salary']].merge(
                first_comp[['employee_id_clean', 'salary']], 
                on='employee_id_clean', 
                suffixes=('_latest', '_first')
            )
            comp_growth['salary_growth_rate'] = np.where(
                comp_growth['salary_first'] > 0,
                (comp_growth['salary_latest'] - comp_growth['salary_first']) / comp_growth['salary_first'],
                0.0
            )
            
            comp_features = latest_comp[['employee_id_clean', 'salary', 'bonus', 'stock_options', 'total_compensation']].merge(
                comp_growth[['employee_id_clean', 'salary_growth_rate']], on='employee_id_clean', how='left'
            )
            features_df = features_df.merge(comp_features, on='employee_id_clean', how='left')
        else:
            features_df['salary'] = 50000.0
            features_df['bonus'] = 0.0
            features_df['stock_options'] = 0.0
            features_df['total_compensation'] = 50000.0
            features_df['salary_growth_rate'] = 0.0

        # --- Feature Group 3: Performance Reviews & Promotions ---
        if not performance.empty:
            performance['review_date'] = pd.to_datetime(performance['review_date'])
            perf_sorted = performance.sort_values(by=['employee_id_clean', 'review_date'])
            
            perf_agg = perf_sorted.groupby('employee_id_clean').agg(
                latest_performance_rating=('rating', 'last'),
                avg_performance_rating=('rating', 'mean'),
                total_promotions=('promotion_given', lambda s: int(s.sum()))
            ).reset_index()
            
            # Years since last promotion
            promoted_records = perf_sorted[perf_sorted['promotion_given'] == True]
            if not promoted_records.empty:
                last_promo = promoted_records.groupby('employee_id_clean')['review_date'].max().reset_index()
                last_promo['years_since_last_promotion'] = (current_date - last_promo['review_date']).dt.days / 365.0
                perf_agg = perf_agg.merge(last_promo[['employee_id_clean', 'years_since_last_promotion']], on='employee_id_clean', how='left')
            else:
                perf_agg['years_since_last_promotion'] = np.nan
                
            features_df = features_df.merge(perf_agg, on='employee_id_clean', how='left')
        else:
            features_df['latest_performance_rating'] = 3.0
            features_df['avg_performance_rating'] = 3.0
            features_df['total_promotions'] = 0
            features_df['years_since_last_promotion'] = features_df['tenure_years']

        # Fill missing years_since_last_promotion with tenure_years
        features_df['years_since_last_promotion'] = features_df['years_since_last_promotion'].fillna(features_df['tenure_years'])
        features_df['total_promotions'] = features_df['total_promotions'].fillna(0)
        features_df['promotion_velocity'] = features_df['total_promotions'] / np.maximum(features_df['tenure_years'], 0.5)
        features_df['rating_trend'] = features_df['latest_performance_rating'] - features_df['avg_performance_rating']

        # --- Feature Group 4: Workload & Attendance ---
        if not workload.empty:
            wl_agg = workload.groupby('employee_id_clean').agg(
                avg_weekly_hours=('weekly_hours', 'mean'),
                avg_overtime_hours=('overtime_hours', 'mean'),
                total_sick_leaves=('sick_leaves_taken', 'sum'),
                avg_remote_days=('remote_days', 'mean')
            ).reset_index()
            
            features_df = features_df.merge(wl_agg, on='employee_id_clean', how='left')
        else:
            features_df['avg_weekly_hours'] = 40.0
            features_df['avg_overtime_hours'] = 0.0
            features_df['total_sick_leaves'] = 0
            features_df['avg_remote_days'] = 2.0

        features_df['avg_weekly_hours'] = features_df['avg_weekly_hours'].fillna(40.0)
        features_df['avg_overtime_hours'] = features_df['avg_overtime_hours'].fillna(0.0)
        features_df['total_sick_leaves'] = features_df['total_sick_leaves'].fillna(0)
        features_df['avg_remote_days'] = features_df['avg_remote_days'].fillna(2.0)

        # Derived workload metrics
        features_df['workload_stress_index'] = features_df['avg_weekly_hours'] + (features_df['avg_overtime_hours'] * 1.5)
        tenure_months = np.maximum(features_df['tenure_years'] * 12.0, 1.0)
        features_df['sick_leave_ratio'] = features_df['total_sick_leaves'] / tenure_months
        features_df['remote_work_ratio'] = (features_df['avg_remote_days'] / 5.0).clip(0.0, 1.0)

        # --- Feature Group 5: HR Tickets & Complaints ---
        if not hr_tickets.empty:
            hr_tickets['issue_date'] = pd.to_datetime(hr_tickets['issue_date'])
            ticket_agg = hr_tickets.groupby('employee_id_clean').agg(
                total_hr_complaints=('ticket_id', 'count'),
                last_complaint_date=('issue_date', 'max'),
                avg_hr_satisfaction=('satisfaction_score', 'mean')
            ).reset_index()
            
            high_sev = hr_tickets[hr_tickets['severity'].str.lower() == 'high'].groupby('employee_id_clean').size().reset_index(name='high_severity_tickets')
            ticket_agg = ticket_agg.merge(high_sev, on='employee_id_clean', how='left')
            
            ticket_agg['days_since_last_complaint'] = (current_date - ticket_agg['last_complaint_date']).dt.days
            features_df = features_df.merge(ticket_agg.drop(columns=['last_complaint_date']), on='employee_id_clean', how='left')
        else:
            features_df['total_hr_complaints'] = 0
            features_df['high_severity_tickets'] = 0
            features_df['days_since_last_complaint'] = 365
            features_df['avg_hr_satisfaction'] = 5.0

        features_df['total_hr_complaints'] = features_df['total_hr_complaints'].fillna(0)
        features_df['high_severity_tickets'] = features_df['high_severity_tickets'].fillna(0)
        features_df['days_since_last_complaint'] = features_df['days_since_last_complaint'].fillna(365)
        features_df['avg_hr_satisfaction'] = features_df['avg_hr_satisfaction'].fillna(5.0)

        # --- Feature Group 6: Training Engagement ---
        if not training.empty:
            tr_completed = training[training['completed'] == True].groupby('employee_id_clean').agg(
                trainings_completed=('event_id', 'count'),
                training_score_avg=('score', 'mean')
            ).reset_index()
            
            tr_total = training.groupby('employee_id_clean')['event_id'].count().reset_index(name='total_trainings')
            tr_agg = tr_total.merge(tr_completed, on='employee_id_clean', how='left')
            features_df = features_df.merge(tr_agg, on='employee_id_clean', how='left')
        else:
            features_df['trainings_completed'] = 0
            features_df['total_trainings'] = 0
            features_df['training_score_avg'] = 75.0

        features_df['trainings_completed'] = features_df['trainings_completed'].fillna(0)
        features_df['total_trainings'] = features_df['total_trainings'].fillna(0)
        features_df['training_score_avg'] = features_df['training_score_avg'].fillna(75.0)

        training_ratio = np.where(
            features_df['total_trainings'] > 0,
            features_df['trainings_completed'] / features_df['total_trainings'],
            1.0
        )

        # Fill any remaining numerical NAs
        features_df = features_df.fillna(0)

        # --- Target Metrics & Composites ---
        # 1. Employee Satisfaction Score (0 - 100)
        # Formula: clip(50 + rating*10 + training_ratio*20 - hr_tickets*8 - high_sev*15 - overtime*0.5, 0, 100)
        sat_raw = (
            50.0 
            + (features_df['latest_performance_rating'] * 10.0)
            + (training_ratio * 20.0)
            - (features_df['total_hr_complaints'] * 8.0)
            - (features_df['high_severity_tickets'] * 15.0)
            - (features_df['avg_overtime_hours'] * 0.5)
        )
        features_df['employee_satisfaction_score'] = np.clip(sat_raw, 0.0, 100.0)

        # 2. Attrition Risk Score (0.0 - 1.0 Flight Risk Heuristic)
        overtime_penalty = np.clip(features_df['avg_overtime_hours'] / 20.0, 0.0, 0.4)
        stagnation_penalty = np.clip(features_df['years_since_last_promotion'] / 5.0, 0.0, 0.3)
        satisfaction_factor = 1.0 - (features_df['employee_satisfaction_score'] / 100.0)
        complaint_penalty = np.clip(features_df['high_severity_tickets'] * 0.15, 0.0, 0.3)

        attr_raw = (overtime_penalty * 0.3) + (stagnation_penalty * 0.2) + (satisfaction_factor * 0.35) + (complaint_penalty * 0.15)
        features_df['attrition_risk_score'] = np.clip(attr_raw, 0.0, 1.0)

        # 3. Estimated Replacement Cost (Standard HR Metric: 50% of annual salary)
        features_df['estimated_replacement_cost'] = features_df['salary'] * 0.5

        # 4. Employee Segment Cohort
        def determine_segment(row):
            if row['attrition_risk_score'] > 0.6 or row['avg_overtime_hours'] > 12:
                return 'Burnout Risk'
            if row['latest_performance_rating'] >= 4.0 and row['employee_satisfaction_score'] >= 70:
                return 'High Performer'
            if row['latest_performance_rating'] <= 2.0:
                return 'Underperforming'
            return 'Core Employee'

        features_df['employee_segment'] = features_df.apply(determine_segment, axis=1)

        # --- Prepare Final Table Schema ---
        keep_cols = [
            'employee_id', 'tenure_years', 'years_since_last_promotion', 'promotion_velocity',
            'manager_tenure_years', 'salary_growth_rate', 'total_compensation',
            'avg_weekly_hours', 'avg_overtime_hours', 'workload_stress_index',
            'sick_leave_ratio', 'remote_work_ratio', 'total_hr_complaints',
            'high_severity_tickets', 'days_since_last_complaint', 'avg_hr_satisfaction',
            'latest_performance_rating', 'avg_performance_rating', 'rating_trend',
            'trainings_completed', 'training_score_avg', 'employee_satisfaction_score',
            'attrition_risk_score', 'estimated_replacement_cost', 'employee_segment'
        ]

        final_df = features_df[keep_cols].copy()

        # Clean NaN/Inf values before SQL insert
        for col in final_df.select_dtypes(include=[np.number]).columns:
            final_df[col] = final_df[col].replace([np.inf, -np.inf], 0).fillna(0)
            if final_df[col].dtype == 'float64':
                final_df[col] = final_df[col].astype(float)
            elif final_df[col].dtype == 'int64':
                final_df[col] = final_df[col].astype(int)

        records = final_df.to_dict(orient='records')

        try:
            self.db.query(models.EmployeeFeature).delete()
            self.db.commit()
            
            self.db.bulk_insert_mappings(models.EmployeeFeature, records)
            self.db.commit()
            return {"status": "success", "features_generated": len(records)}
        except Exception as e:
            self.db.rollback()
            return {"status": "error", "message": str(e)}
