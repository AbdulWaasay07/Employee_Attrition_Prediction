import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.db import models
from typing import Dict, Any
import math
import uuid

class DataCleanerService:
    def __init__(self, db: Session):
        self.db = db
        
    def _get_expected_columns(self, dataset_type: str) -> list:
        if dataset_type == "employees":
            return ["employee_id", "name", "email", "department", "job_role", "hire_date", "location", "manager_id"]
        elif dataset_type == "compensation":
            return ["comp_id", "employee_id", "salary", "bonus", "stock_options", "effective_date"]
        elif dataset_type == "performance":
            return ["review_id", "employee_id", "review_date", "rating", "promotion_given", "manager_feedback_score"]
        elif dataset_type == "workload":
            return ["workload_id", "employee_id", "log_date", "weekly_hours", "overtime_hours", "sick_leaves_taken", "remote_days"]
        elif dataset_type == "hr_tickets":
            return ["ticket_id", "employee_id", "issue_date", "resolution_date", "category", "severity", "status", "satisfaction_score"]
        elif dataset_type == "training":
            return ["event_id", "employee_id", "training_name", "event_date", "completed", "score"]
        return []

    def process_file_in_chunks(self, file_path: str, dataset_type: str, column_mapping: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Reads a CSV file in chunks to prevent memory exhaustion,
        applies dynamic column mapping, cleaning logic, smart upserting, and inserts into the database.
        """
        chunk_size = 10000
        total_rows = 0
        inserted = 0
        rejected = 0
        errors = []
        imputed_cells = 0

        # Mapping dataset_type to SQLAlchemy models
        model_mapping = {
            "employees": models.Employee,
            "compensation": models.Compensation,
            "performance": models.PerformanceReview,
            "workload": models.WorkloadAttendance,
            "hr_tickets": models.HRTicket,
            "training": models.TrainingEngagement
        }

        if dataset_type not in model_mapping:
            raise ValueError(f"Unknown dataset_type: {dataset_type}")
            
        target_model = model_mapping[dataset_type]
        valid_model_columns = {c.name for c in target_model.__table__.columns}

        # Read CSV in chunks
        try:
            with pd.read_csv(file_path, chunksize=chunk_size) as reader:
                for chunk_index, chunk in enumerate(reader):
                    total_rows += len(chunk)
                    
                    # 1. Standardize column names first
                    chunk.columns = chunk.columns.str.lower().str.strip()
                    
                    # 1.5 Dynamic Column Mapping
                    if column_mapping:
                        clean_mapping = {str(k).lower().strip(): str(v).lower().strip() for k, v in column_mapping.items()}
                        chunk = chunk.rename(columns=clean_mapping)
                        
                    # 2. Domain-specific cleaning
                    if dataset_type == "employees":
                        chunk = self._clean_employees(chunk)
                    elif dataset_type == "compensation":
                        chunk = self._clean_compensation(chunk)
                    elif dataset_type == "performance":
                        chunk = self._clean_performance(chunk)
                    elif dataset_type == "workload":
                        chunk = self._clean_workload(chunk)
                    elif dataset_type == "hr_tickets":
                        chunk = self._clean_hr_tickets(chunk)
                    elif dataset_type == "training":
                        chunk = self._clean_training(chunk)
                    
                    # 3. Advanced Generic Cleaning (Outliers, Imputation, Text Encoding, Duplicates)
                    chunk = self._generic_cleaning(chunk)
                    
                    # Count NaNs for health score before final dict mapping
                    imputed_cells += int(chunk.isnull().sum().sum())
                    
                    # 4. Convert DataFrame to List of Dicts for SQLAlchemy, filtering to target model columns only
                    raw_records = chunk.to_dict(orient="records")
                    records = []
                    for record in raw_records:
                        clean_record = {}
                        for key, value in record.items():
                            if key in valid_model_columns:
                                if pd.isna(value):
                                    clean_record[key] = None
                                elif isinstance(value, pd.Timestamp):
                                    clean_record[key] = value.to_pydatetime()
                                else:
                                    clean_record[key] = value
                        records.append(clean_record)
                    
                    # 5. Smart Deduplication & Bulk Insert
                    pk_cols = [pk.name for pk in target_model.__mapper__.primary_key]
                    if len(pk_cols) == 1:
                        pk_col = pk_cols[0]
                        incoming_pks = [r[pk_col] for r in records if pk_col in r and r[pk_col] is not None]
                        if incoming_pks:
                            try:
                                pk_attr = getattr(target_model, pk_col)
                                self.db.query(target_model).filter(pk_attr.in_(incoming_pks)).delete(synchronize_session=False)
                                self.db.commit()
                            except Exception:
                                self.db.rollback()

                    try:
                        self.db.bulk_insert_mappings(target_model, records)
                        self.db.commit()
                        inserted += len(records)
                    except Exception as e:
                        self.db.rollback()
                        # Fallback to row-by-row session.merge for upserting
                        row_inserted = 0
                        row_rejected = 0
                        for idx, rec in enumerate(records):
                            try:
                                obj = target_model(**rec)
                                self.db.merge(obj)
                                self.db.commit()
                                row_inserted += 1
                            except Exception as row_err:
                                self.db.rollback()
                                row_rejected += 1
                                errors.append({"row_number": chunk_index * chunk_size + idx, "issue": f"Row insert failed: {str(row_err)}"})
                        inserted += row_inserted
                        rejected += row_rejected
                        
        except pd.errors.EmptyDataError:
            pass # Handle empty file

        # Calculate Health Score
        if total_rows > 0:
            total_cells = total_rows * len(chunk.columns)
            imputed_pct = (imputed_cells / total_cells) * 100
            score = (inserted / total_rows) * 100 - (imputed_pct * 0.5)
        else:
            score = 0.0

        return {
            "dataset_type": dataset_type,
            "total_rows_processed": total_rows,
            "rows_inserted": inserted,
            "rows_rejected": rejected,
            "dataset_health_score": round(max(0, min(100, score)), 2),
            "errors": errors[:100]
        }

    def _generic_cleaning(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop exact duplicates
        df = df.drop_duplicates()
        
        # Categorical Encoding (strip whitespace)
        for col in df.select_dtypes(include=['object']).columns:
            mask = df[col].notna()
            df.loc[mask, col] = df.loc[mask, col].astype(str).str.strip()
            
        # Numerical Imputation (Median) & Winsorization (99th percentile capping)
        for col in df.select_dtypes(include=['number']).columns:
            if 'id' in col.lower():
                continue
            median_val = df[col].median()
            if pd.isna(median_val): 
                median_val = 0
            df[col] = df[col].fillna(median_val)
            
            # Winsorization (Cap at 99th percentile)
            upper_limit = df[col].quantile(0.99)
            if not pd.isna(upper_limit) and upper_limit > 0:
                df[col] = df[col].clip(upper=upper_limit)
                
        return df

    def _clean_employees(self, df: pd.DataFrame) -> pd.DataFrame:
        # Case-strip department and job_role
        if 'department' in df.columns:
            df['department'] = df['department'].astype(str).str.strip().str.title().replace({'Nan': 'Unknown', 'None': 'Unknown', '': 'Unknown'})
        if 'job_role' in df.columns:
            df['job_role'] = df['job_role'].astype(str).str.strip().str.title().replace({'Nan': 'Unknown', 'None': 'Unknown', '': 'Unknown'})
        
        # Fill missing location & name
        if 'location' in df.columns:
            df['location'] = df['location'].fillna("Unknown")
        if 'name' in df.columns:
            df['name'] = df['name'].fillna("Unknown")
            
        # Standardize hire_date
        if 'hire_date' in df.columns:
            df['hire_date'] = pd.to_datetime(df['hire_date'], errors='coerce')
            
        subset_drop = [col for col in ['hire_date', 'email'] if col in df.columns]
        if subset_drop:
            df = df.dropna(subset=subset_drop)
            
        return df

    def _clean_compensation(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'comp_id' not in df.columns or df['comp_id'].isnull().all():
            df['comp_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            mask = df['comp_id'].isnull() | (df['comp_id'] == '')
            if mask.any():
                df.loc[mask, 'comp_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]

        # Strip currency symbols ($) and commas, cast salary to float
        for col in ['salary', 'bonus', 'stock_options']:
            if col in df.columns:
                if df[col].dtype == 'O':
                    df[col] = df[col].astype(str).replace(r'[^\d\.-]', '', regex=True).replace('', '0').astype(float)
                else:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    
        # Winsorize salary outliers (>99th percentile)
        if 'salary' in df.columns and len(df) > 0:
            upper_limit = df['salary'].quantile(0.99)
            if not pd.isna(upper_limit) and upper_limit > 0:
                df['salary'] = df['salary'].clip(upper=upper_limit)

        if 'effective_date' in df.columns:
            df['effective_date'] = pd.to_datetime(df['effective_date'], errors='coerce')

        return df

    def _clean_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'review_id' not in df.columns or df['review_id'].isnull().all():
            df['review_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            mask = df['review_id'].isnull() | (df['review_id'] == '')
            if mask.any():
                df.loc[mask, 'review_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]

        # Clamp ratings strictly between 1 and 5
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(3)
            df['rating'] = df['rating'].clip(lower=1, upper=5).astype(int)

        # Coerce promotion_given to boolean
        if 'promotion_given' in df.columns:
            if df['promotion_given'].dtype == 'O':
                df['promotion_given'] = df['promotion_given'].astype(str).str.lower().isin(['true', '1', 'yes', 't'])
            else:
                df['promotion_given'] = df['promotion_given'].fillna(False).astype(bool)

        if 'review_date' in df.columns:
            df['review_date'] = pd.to_datetime(df['review_date'], errors='coerce')

        return df

    def _clean_workload(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'workload_id' not in df.columns or df['workload_id'].isnull().all():
            df['workload_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            mask = df['workload_id'].isnull() | (df['workload_id'] == '')
            if mask.any():
                df.loc[mask, 'workload_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]

        # Fix impossible negative overtime hours (reset <0 to 0)
        if 'overtime_hours' in df.columns:
            df['overtime_hours'] = pd.to_numeric(df['overtime_hours'], errors='coerce').fillna(0)
            df['overtime_hours'] = df['overtime_hours'].clip(lower=0)

        # Impute missing weekly hours with median
        if 'weekly_hours' in df.columns:
            df['weekly_hours'] = pd.to_numeric(df['weekly_hours'], errors='coerce')
            med_hrs = df['weekly_hours'].median()
            if pd.isna(med_hrs): med_hrs = 40.0
            df['weekly_hours'] = df['weekly_hours'].fillna(med_hrs)

        if 'log_date' in df.columns:
            df['log_date'] = pd.to_datetime(df['log_date'], errors='coerce')

        return df

    def _clean_hr_tickets(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'ticket_id' not in df.columns or df['ticket_id'].isnull().all():
            df['ticket_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            mask = df['ticket_id'].isnull() | (df['ticket_id'] == '')
            if mask.any():
                df.loc[mask, 'ticket_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]

        # Handle NaT missing resolution dates
        if 'issue_date' in df.columns:
            df['issue_date'] = pd.to_datetime(df['issue_date'], errors='coerce')
        if 'resolution_date' in df.columns:
            df['resolution_date'] = pd.to_datetime(df['resolution_date'], errors='coerce')

        # Normalize severity strings (Low, Medium, High)
        if 'severity' in df.columns:
            df['severity'] = df['severity'].astype(str).str.strip().str.title()
            df['severity'] = df['severity'].replace({'Nan': 'Medium', 'None': 'Medium', '': 'Medium'})

        return df

    def _clean_training(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'event_id' not in df.columns or df['event_id'].isnull().all():
            df['event_id'] = [str(uuid.uuid4()) for _ in range(len(df))]
        else:
            mask = df['event_id'].isnull() | (df['event_id'] == '')
            if mask.any():
                df.loc[mask, 'event_id'] = [str(uuid.uuid4()) for _ in range(mask.sum())]

        # Coerce completion status to boolean
        if 'completed' in df.columns:
            if df['completed'].dtype == 'O':
                df['completed'] = df['completed'].astype(str).str.lower().isin(['true', '1', 'yes', 't', 'completed'])
            else:
                df['completed'] = df['completed'].fillna(False).astype(bool)

        if 'event_date' in df.columns:
            df['event_date'] = pd.to_datetime(df['event_date'], errors='coerce')

        return df
