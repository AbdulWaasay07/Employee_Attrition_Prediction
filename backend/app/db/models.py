from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, ForeignKey, Index, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=True)
    job_role = Column(String(100), nullable=True)
    hire_date = Column(Date, nullable=False)
    location = Column(String(100), nullable=True)
    manager_id = Column(String(50), nullable=True)

    # Relationships
    compensation = relationship("Compensation", back_populates="employee")
    performance_reviews = relationship("PerformanceReview", back_populates="employee")
    workload = relationship("WorkloadAttendance", back_populates="employee")
    hr_tickets = relationship("HRTicket", back_populates="employee")
    training = relationship("TrainingEngagement", back_populates="employee")
    features = relationship("EmployeeFeature", back_populates="employee", uselist=False)

class Compensation(Base):
    __tablename__ = "compensation"

    comp_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    salary = Column(Float, nullable=False)
    bonus = Column(Float, default=0.0)
    stock_options = Column(Float, default=0.0)
    effective_date = Column(Date, nullable=False)

    # Relationships
    employee = relationship("Employee", back_populates="compensation")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    review_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    review_date = Column(Date, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 scale
    promotion_given = Column(Boolean, default=False)
    manager_feedback_score = Column(Float, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="performance_reviews")

class WorkloadAttendance(Base):
    __tablename__ = "workload_attendance"

    workload_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    log_date = Column(Date, nullable=False)
    weekly_hours = Column(Float, default=40.0)
    overtime_hours = Column(Float, default=0.0)
    sick_leaves_taken = Column(Integer, default=0)
    remote_days = Column(Integer, default=0)

    # Relationships
    employee = relationship("Employee", back_populates="workload")

class HRTicket(Base):
    __tablename__ = "hr_tickets"

    ticket_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    issue_date = Column(DateTime, nullable=False)
    resolution_date = Column(DateTime, nullable=True)
    category = Column(String(100), nullable=True)   # Compensation, Culture, Workload
    severity = Column(String(50), nullable=True)    # Low, Medium, High
    status = Column(String(50), nullable=False, default="Open")
    satisfaction_score = Column(Integer, nullable=True) # 1-5 scale

    # Relationships
    employee = relationship("Employee", back_populates="hr_tickets")

class TrainingEngagement(Base):
    __tablename__ = "training_engagement"

    event_id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), ForeignKey("employees.employee_id"), nullable=False, index=True)
    training_name = Column(String(150), nullable=False)
    event_date = Column(Date, nullable=False)
    completed = Column(Boolean, default=False)
    score = Column(Float, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="training")

class EmployeeFeature(Base):
    __tablename__ = "employee_features"

    employee_id = Column(String(50), ForeignKey("employees.employee_id"), primary_key=True, index=True)
    
    # 1. Tenure & Career Growth
    tenure_years = Column(Float, nullable=True)
    years_since_last_promotion = Column(Float, nullable=True)
    promotion_velocity = Column(Float, nullable=True)
    manager_tenure_years = Column(Float, nullable=True)

    # 2. Compensation & Value
    salary_growth_rate = Column(Float, nullable=True)
    total_compensation = Column(Float, nullable=True)
    
    # 3. Workload & Burnout
    avg_weekly_hours = Column(Float, nullable=True)
    avg_overtime_hours = Column(Float, nullable=True)
    workload_stress_index = Column(Float, nullable=True)
    sick_leave_ratio = Column(Float, nullable=True)
    remote_work_ratio = Column(Float, nullable=True)
    
    # 4. HR Friction & Complaints
    total_hr_complaints = Column(Integer, nullable=True)
    high_severity_tickets = Column(Integer, nullable=True)
    days_since_last_complaint = Column(Integer, nullable=True)
    avg_hr_satisfaction = Column(Float, nullable=True)
    
    # 5. Performance & Engagement
    latest_performance_rating = Column(Float, nullable=True)
    avg_performance_rating = Column(Float, nullable=True)
    rating_trend = Column(Float, nullable=True)
    trainings_completed = Column(Integer, nullable=True)
    training_score_avg = Column(Float, nullable=True)
    
    # 6. Target Scores & Segment
    employee_satisfaction_score = Column(Float, nullable=True)  # 0 - 100
    attrition_risk_score = Column(Float, nullable=True)         # 0.0 - 1.0
    estimated_replacement_cost = Column(Float, nullable=True)   # $
    employee_segment = Column(String(50), nullable=True)        # High Performer, Burnout Risk, etc.

    # Relationships
    employee = relationship("Employee", back_populates="features")

class JobStatus(Base):
    __tablename__ = "job_status"
    
    job_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_type = Column(String(50))
    filename = Column(String(255))
    status = Column(String(50)) # e.g. "Processing", "Completed", "Failed"
    total_rows_processed = Column(Integer, default=0)
    rows_inserted = Column(Integer, default=0)
    rows_rejected = Column(Integer, default=0)
    dataset_health_score = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
