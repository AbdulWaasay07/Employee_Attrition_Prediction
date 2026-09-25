import pandas as pd
import random
import uuid
import os
import numpy as np
from datetime import datetime, timedelta

NUM_EMPLOYEES = 150
OUTPUT_DIR = "Mock Data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"Generating 'Dirty' HR mock data for {NUM_EMPLOYEES} employees in '{OUTPUT_DIR}' directory...")

# Helper to randomly decide if we should introduce noise
def flip_coin(probability=0.05):
    return random.random() < probability

# 1. Employees (Primary Hub)
employees = []
departments = [" Engineering ", "Sales", " Marketing ", "Human Resources", " Finance ", "Product", " Operations "]
job_roles = ["Software Engineer", "Sales Executive", "Marketing Specialist", "HR Generalist", "Financial Analyst", "Product Manager", "Operations Lead"]
locations = ["New York", "San Francisco", "London", "Austin", "Berlin", "Toronto", "Sydney"]

for i in range(1, NUM_EMPLOYEES + 1):
    eid = f"EMP{i:03d}"
    
    # Introduce case/whitespace inconsistency
    if flip_coin(): eid = eid.lower()
    if flip_coin(): eid = f" {eid} "
    
    name = f"Employee {i}" if not flip_coin(0.05) else np.nan  # Missing name
    dept = random.choice(departments)
    role = random.choice(job_roles)
    location = random.choice(locations) if not flip_coin(0.1) else None  # Missing location
    
    # Missing manager_id noise
    manager_id = f"EMP{random.randint(1, 15):03d}" if i > 15 and not flip_coin(0.2) else None

    hire_days_ago = random.randint(180, 2500)
    hire_date = (datetime.now() - timedelta(days=hire_days_ago)).strftime('%Y-%m-%d')
    
    employees.append({
        "employee_id": eid,
        "name": name,
        "email": f"employee{i}@company.com",
        "department": dept,
        "job_role": role,
        "hire_date": hire_date,
        "location": location,
        "manager_id": manager_id
    })

pd.DataFrame(employees).to_csv(os.path.join(OUTPUT_DIR, "mock_employees.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_employees.csv')} (with missing names, missing locations, whitespace departments, and missing manager IDs)")

# 2. Compensation, 3. Performance, 4. Workload, 5. HR Tickets, 6. Training
compensation = []
performance = []
workload = []
hr_tickets = []
training = []

training_names = ["Compliance 101", "Leadership Skills", "Advanced Python", "Security Awareness", "Project Management"]

for emp in employees:
    clean_eid = emp["employee_id"].strip().upper()
    emp_idx = int(clean_eid.replace("EMP", ""))
    
    # Correlation: 30% of employees are burnout/flight risk
    is_burnout = (emp_idx % 3 == 0) or flip_coin(0.15)
    
    # --- 2. Compensation ---
    base_salary = random.randint(55000, 140000) if not is_burnout else random.randint(45000, 85000)
    
    # Inject salary noise
    salary_val = base_salary
    if flip_coin(0.02): salary_val = 999999  # Extreme outlier / typo
    elif flip_coin(0.08): salary_val = f"${base_salary:,}"  # String formatting with $ and commas
    elif flip_coin(0.03): salary_val = np.nan
    
    bonus_val = random.randint(2000, 15000) if not is_burnout else random.randint(0, 2000)
    stock_val = random.randint(0, 10000) if not is_burnout else 0
    
    compensation.append({
        "comp_id": str(uuid.uuid4()),
        "employee_id": clean_eid.lower() if flip_coin() else clean_eid,
        "salary": salary_val,
        "bonus": bonus_val,
        "stock_options": stock_val,
        "effective_date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')
    })
    
    # Add historic compensation record for salary growth rate calculation
    if flip_coin(0.4):
        initial_salary = int(base_salary * random.uniform(0.85, 0.95))
        compensation.append({
            "comp_id": str(uuid.uuid4()),
            "employee_id": clean_eid,
            "salary": initial_salary,
            "bonus": 0,
            "stock_options": 0,
            "effective_date": (datetime.now() - timedelta(days=random.randint(366, 730))).strftime('%Y-%m-%d')
        })

    # --- 3. Performance Reviews ---
    num_reviews = random.randint(1, 4)
    for r in range(num_reviews):
        rating_val = random.randint(1, 2) if is_burnout else random.randint(3, 5)
        if flip_coin(0.08): rating_val = np.nan  # Missing performance rating noise
        
        promo = (not is_burnout) and flip_coin(0.25)
        fb_score = random.randint(1, 3) if is_burnout else random.randint(4, 5)
        
        performance.append({
            "review_id": str(uuid.uuid4()),
            "employee_id": clean_eid,
            "review_date": (datetime.now() - timedelta(days=180 * (r + 1))).strftime('%Y-%m-%d'),
            "rating": rating_val,
            "promotion_given": promo,
            "manager_feedback_score": fb_score
        })

    # --- 4. Workload & Attendance ---
    num_logs = random.randint(3, 6)
    for _ in range(num_logs):
        weekly_hrs = random.randint(48, 65) if is_burnout else random.randint(38, 45)
        if flip_coin(0.05): weekly_hrs = np.nan  # Missing weekly hours
        
        overtime_hrs = random.randint(10, 25) if is_burnout else random.randint(0, 5)
        if flip_coin(0.04): overtime_hrs = -5  # Negative overtime hours noise
        
        sick_leaves = random.randint(3, 10) if is_burnout else random.randint(0, 2)
        remote = random.randint(0, 5)
        
        workload.append({
            "workload_id": str(uuid.uuid4()),
            "employee_id": clean_eid.lower() if flip_coin() else clean_eid,
            "log_date": (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
            "weekly_hours": weekly_hrs,
            "overtime_hours": overtime_hrs,
            "sick_leaves_taken": sick_leaves,
            "remote_days": remote
        })

    # --- 5. HR Tickets ---
    num_tickets = random.randint(2, 6) if is_burnout else random.randint(0, 1)
    for _ in range(num_tickets):
        ticket_id = str(uuid.uuid4()) if not flip_coin(0.25) else np.nan  # Missing PK noise
        
        sev = "High" if is_burnout else random.choice(["Low", "Medium"])
        if flip_coin(): sev = sev.lower()
        if flip_coin(): sev = f" {sev} "
        
        cat = random.choice(["Compensation", "Culture", "Workload"])
        sat = random.randint(1, 2) if is_burnout else random.randint(4, 5)
        
        issue_d = datetime.now() - timedelta(days=random.randint(1, 180))
        res_d = issue_d + timedelta(days=random.randint(1, 10)) if not flip_coin(0.2) else np.nan  # Missing resolution date
        
        hr_tickets.append({
            "ticket_id": ticket_id,
            "employee_id": f" {clean_eid} " if flip_coin() else clean_eid,
            "issue_date": issue_d.strftime('%Y-%m-%d'),
            "resolution_date": res_d.strftime('%Y-%m-%d') if isinstance(res_d, datetime) else res_d,
            "category": cat,
            "severity": sev,
            "status": "Resolved" if not pd.isna(res_d) else "Open",
            "satisfaction_score": sat
        })

    # --- 6. Training Engagement ---
    for t_name in random.sample(training_names, random.randint(1, 3)):
        completed_val = random.choice([True, False]) if is_burnout else True
        if flip_coin(0.1): completed_val = "True" if completed_val else "False"
        
        score_val = random.randint(50, 75) if is_burnout else random.randint(80, 100)
        
        training.append({
            "event_id": str(uuid.uuid4()),
            "employee_id": clean_eid,
            "training_name": t_name,
            "event_date": (datetime.now() - timedelta(days=random.randint(10, 180))).strftime('%Y-%m-%d'),
            "completed": completed_val,
            "score": score_val
        })

# Export to CSVs in Mock Data folder
pd.DataFrame(compensation).to_csv(os.path.join(OUTPUT_DIR, "mock_compensation.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_compensation.csv')} (with salary typos like $999,999, string formatting, missing values)")

pd.DataFrame(performance).to_csv(os.path.join(OUTPUT_DIR, "mock_performance.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_performance.csv')} (with missing ratings)")

pd.DataFrame(workload).to_csv(os.path.join(OUTPUT_DIR, "mock_workload.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_workload.csv')} (with negative overtime hours, missing weekly hours)")

pd.DataFrame(hr_tickets).to_csv(os.path.join(OUTPUT_DIR, "mock_hr_tickets.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_hr_tickets.csv')} (with missing PKs, whitespace in severity, missing resolution dates)")

pd.DataFrame(training).to_csv(os.path.join(OUTPUT_DIR, "mock_training.csv"), index=False)
print(f"Created {os.path.join(OUTPUT_DIR, 'mock_training.csv')} (with mixed type boolean completion flags)")

print(f"\nSuccess! HR 'Dirty' mock datasets created inside '{OUTPUT_DIR}' for 150 employees.")
