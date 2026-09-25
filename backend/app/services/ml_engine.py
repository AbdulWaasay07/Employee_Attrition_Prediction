import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.db.database import engine
from app.db.models import EmployeeFeature, Employee
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import joblib
import os

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

class MLEngineService:
    @staticmethod
    def train_segmentation_model(db: Session):
        """
        Trains K-Means clustering on employee features and assigns personas:
        - High Performers (Low Risk)
        - Burnout / Flight Risk
        - Underutilized / Stagnant
        """
        df = pd.read_sql("SELECT * FROM employee_features", engine)
        if len(df) < 3:
            return {"status": "error", "message": "Need at least 3 employees to train segmentation."}

        # Features used: tenure_years, avg_overtime_hours, salary_growth_rate, latest_performance_rating
        features = ["tenure_years", "avg_overtime_hours", "salary_growth_rate", "latest_performance_rating"]
        for f in features:
            if f not in df.columns:
                df[f] = 0.0
            else:
                df[f] = df[f].fillna(0.0)

        X = df[features].copy()

        # Scale data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Train K-Means (k=3)
        kmeans = KMeans(n_clusters=min(3, len(X)), random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(X_scaled)

        # Persona mapping based on cluster centroids
        centroids = kmeans.cluster_centers_
        
        # Centroid column indexes: 0: tenure_years, 1: avg_overtime_hours, 2: salary_growth_rate, 3: latest_performance_rating
        high_perf_cluster = np.argmax(centroids[:, 3])  # Highest rating
        burnout_cluster = np.argmax(centroids[:, 1])    # Highest overtime hours
        
        remaining = [c for c in range(min(3, len(X))) if c not in [high_perf_cluster, burnout_cluster]]
        stagnant_cluster = remaining[0] if remaining else burnout_cluster

        def map_persona(cluster_id):
            if cluster_id == high_perf_cluster and high_perf_cluster != burnout_cluster:
                return "High Performers (Low Risk)"
            elif cluster_id == burnout_cluster:
                return "Burnout / Flight Risk"
            else:
                return "Underutilized / Stagnant"

        df['predicted_segment'] = df['cluster'].apply(map_persona)

        # Save model and scaler
        joblib.dump(scaler, os.path.join(MODELS_DIR, "segmentation_scaler.joblib"))
        joblib.dump(kmeans, os.path.join(MODELS_DIR, "segmentation_kmeans.joblib"))

        # Update DB
        updated_count = 0
        for index, row in df.iterrows():
            emp_feature = db.query(EmployeeFeature).filter(EmployeeFeature.employee_id == row['employee_id']).first()
            if emp_feature:
                emp_feature.employee_segment = row['predicted_segment']
                updated_count += 1
        db.commit()

        return {
            "status": "success", 
            "message": f"Successfully segmented {updated_count} employees into risk cohorts.", 
            "clusters_found": len(np.unique(df['cluster']))
        }

    @staticmethod
    def train_attrition_model(db: Session):
        """
        Trains an XGBoost model to predict employee attrition risk.
        Synthesizes binary target 'is_attrition_risk' and applies boundary sampling if needed.
        """
        df = pd.read_sql("SELECT * FROM employee_features", engine)
        if len(df) == 0:
            return {"status": "error", "message": "No employee features found. Compile feature store first."}

        # Define attrition risk target dynamically
        threshold = df['attrition_risk_score'].median() if 'attrition_risk_score' in df.columns else 0.5
        if threshold == 0 or pd.isna(threshold): 
            threshold = 0.4
        
        df['is_attrition_risk'] = (df['attrition_risk_score'] >= threshold).astype(int)

        # Handle class imbalance / single class edge cases with synthetic boundary sampling
        if df['is_attrition_risk'].nunique() < 2:
            dummy_high = df.iloc[0:1].copy()
            dummy_high['avg_overtime_hours'] = 25.0
            dummy_high['attrition_risk_score'] = 0.95
            dummy_high['is_attrition_risk'] = 1
            
            dummy_low = df.iloc[0:1].copy()
            dummy_low['avg_overtime_hours'] = 0.0
            dummy_low['attrition_risk_score'] = 0.05
            dummy_low['is_attrition_risk'] = 0
            
            df = pd.concat([df, dummy_high, dummy_low], ignore_index=True)

        features = [
            "tenure_years", "years_since_last_promotion", "promotion_velocity",
            "manager_tenure_years", "salary_growth_rate", "total_compensation",
            "avg_weekly_hours", "avg_overtime_hours", "workload_stress_index",
            "sick_leave_ratio", "remote_work_ratio", "total_hr_complaints",
            "high_severity_tickets", "days_since_last_complaint", "avg_hr_satisfaction",
            "latest_performance_rating", "avg_performance_rating", "rating_trend",
            "trainings_completed", "training_score_avg", "employee_satisfaction_score"
        ]

        # Ensure all columns exist
        for col in features:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        X = df[features]
        y = df['is_attrition_risk']

        # Train XGBoost Classifier
        model = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=3, 
            learning_rate=0.1, 
            eval_metric='logloss',
            random_state=42
        )
        model.fit(X, y)

        # Save models
        joblib.dump(model, os.path.join(MODELS_DIR, "attrition_model.joblib"))
        joblib.dump(features, os.path.join(MODELS_DIR, "attrition_features.joblib"))

        # For backward compatibility, also save churn_xgboost.joblib if needed
        joblib.dump(model, os.path.join(MODELS_DIR, "churn_xgboost.joblib"))
        joblib.dump(features, os.path.join(MODELS_DIR, "churn_features.joblib"))

        return {"status": "success", "message": "Employee Attrition Prediction XGBoost model trained and saved successfully."}

    @staticmethod
    def generate_predictions(db: Session):
        """
        Loads trained XGBoost model and batch updates employee_features table with exact probabilities.
        """
        model_path = os.path.join(MODELS_DIR, "attrition_model.joblib")
        features_path = os.path.join(MODELS_DIR, "attrition_features.joblib")

        # Fallback to churn naming if attrition_model doesn't exist yet
        if not os.path.exists(model_path):
            model_path = os.path.join(MODELS_DIR, "churn_xgboost.joblib")
            features_path = os.path.join(MODELS_DIR, "churn_features.joblib")

        if not os.path.exists(model_path) or not os.path.exists(features_path):
            return {"status": "error", "message": "Models not found. Train attrition model first."}

        model = joblib.load(model_path)
        feature_cols = joblib.load(features_path)

        df = pd.read_sql("SELECT * FROM employee_features", engine)
        if len(df) == 0:
             return {"status": "error", "message": "No employees found for prediction."}
             
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0.0
            else:
                df[col] = df[col].fillna(0.0)

        X = df[feature_cols]

        # Predict probabilities (class 1: high attrition risk)
        probabilities = model.predict_proba(X)[:, 1]

        # Update Database
        updated = 0
        for i, row in df.iterrows():
            emp_feature = db.query(EmployeeFeature).filter(EmployeeFeature.employee_id == row['employee_id']).first()
            if emp_feature:
                emp_feature.attrition_risk_score = float(probabilities[i])
                updated += 1
        
        db.commit()
        return {"status": "success", "message": f"Generated exact ML attrition predictions for {updated} employees."}

    @staticmethod
    def get_hr_recommendations(employee_id: str, db: Session):
        """
        HR Business Rules Engine.
        Translates ML attrition probabilities and feature signals into prioritized HR retention strategies.
        """
        feature = db.query(EmployeeFeature).filter(EmployeeFeature.employee_id == employee_id).first()
        if not feature:
            return {"status": "error", "message": "Employee not found."}

        # Fetch demographic details from Employee model
        emp = db.query(Employee).filter(Employee.employee_id == employee_id).first()
        dept = emp.department if emp else "Unknown"
        job_role = emp.job_role if emp else "Unknown"

        actions = []
        
        # Rule 1 (CRITICAL): High Attrition Risk + High Performance Rating
        if feature.attrition_risk_score > 0.6 and (feature.latest_performance_rating or 0) >= 4.0:
            actions.append({
                "priority": "CRITICAL", 
                "action": "Immediate Stay Interview, Schedule Salary/Bonus Review & Retention Grant. High performer is at high flight risk!"
            })
        
        # Rule 2 (HIGH): High Overtime Hours + Low Satisfaction Score
        if (feature.avg_overtime_hours or 0) > 10 or (feature.employee_satisfaction_score or 100) < 60:
            actions.append({
                "priority": "HIGH", 
                "action": "Reallocate Project Workload & Mandate Manager One-on-One Check-in to alleviate burnout."
            })

        # Rule 3 (MEDIUM): Low Performance Rating + Low Engagement
        if (feature.latest_performance_rating or 3) <= 2.0 or (feature.trainings_completed or 0) == 0:
            actions.append({
                "priority": "MEDIUM", 
                "action": "Enroll in Performance Improvement Plan (PIP) & Skills Training to boost engagement and delivery."
            })

        # Rule 4 (NORMAL): Low Attrition Risk + High Performance
        if feature.attrition_risk_score < 0.3 and (feature.latest_performance_rating or 0) >= 4.0:
            actions.append({
                "priority": "NORMAL", 
                "action": "Eligible for Leadership Development & Fast-Track Promotion. Maintain growth trajectory."
            })
            
        if not actions:
            actions.append({
                "priority": "NORMAL", 
                "action": "Maintain standard employee engagement and regular 1-on-1 check-ins."
            })

        return {
            "employee_id": employee_id,
            "department": dept,
            "job_role": job_role,
            "tenure_years": round(feature.tenure_years or 0.0, 1),
            "salary": round(feature.total_compensation or 0.0, 2),
            "segment": feature.employee_segment or "Core Employee",
            "satisfaction_score": round(feature.employee_satisfaction_score or 0.0, 1),
            "attrition_risk_percentage": round((feature.attrition_risk_score or 0.0) * 100, 2),
            "replacement_cost": round(feature.estimated_replacement_cost or 0.0, 2),
            "recommendations": actions
        }
