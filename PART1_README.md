# Employee Intelligence & Attrition Platform: Comprehensive Part 1 Documentation

This document provides an exhaustive, granular breakdown of **Part 1** of the Employee Intelligence and Attrition Platform. It covers the complete journey of workforce data from raw CSV uploads to mathematically engineered Machine Learning features.

Our goal in Part 1 is to solve the classic data engineering problem: *taking messy, disconnected, human-generated HR data and transforming it into a pristine, unified numerical matrix that an Artificial Intelligence can interpret.*

---

## Table of Contents

1. [Project Vision & Business Scope](#1-project-vision--business-scope)
2. [System Architecture & Database Design](#2-system-architecture--database-design)
3. [Data Ingestion & The Cleaning Engine](#3-data-ingestion--the-cleaning-engine)
4. [Exploratory Data Analysis (EDA) Engine](#4-exploratory-data-analysis-eda-engine)
5. [Feature Engineering Pipeline (The 24 HR Features)](#5-feature-engineering-pipeline-the-24-hr-features)

---

## 1. Project Vision & Business Scope

### The Problem
Modern enterprises generate vast amounts of fragmented workforce data across disparate HR systems (compensation, performance reviews, workload, attendance, HR tickets, training). Without a unified workforce data foundation and intelligent analytics, organizations struggle to accurately identify burnout risks, predict employee flight risk, optimize compensation structures, and prevent costly turnover.

### Target Users
- **HR Business Partners & People Operations**: Identifying burnout risk and designing retention packages.
- **Department Managers**: Understanding workload stress, overtime spikes, and team satisfaction.
- **HR Data Scientists & Analysts**: Leveraging engineered workforce features for custom predictive models.
- **C-Suite & Executives**: Tracking headcount, organizational attrition risk rates, average salary, and replacement costs.

---

## 2. System Architecture & Database Design

The platform relies on a normalized relational database (MySQL) accessed via **SQLAlchemy** (an Object-Relational Mapper) in our FastAPI backend. The schema is divided into 6 core HR tables and 1 derived feature store:

```text
User (React 18 Frontend)
        │
        ▼ (REST HTTP Requests)
FastAPI Backend Server (`backend/app/main.py`)
   ├── /api/upload/{dataset_type}   ──> DataCleanerService (`data_cleaner.py`)
   ├── /api/eda/*                  ──> SQL Aggregations on MySQL tables (`routes_eda.py`)
   ├── /api/ml/calculate-features  ──> FeatureEngineeringService (`feature_engineering.py`)
   └── /api/models/*               ──> MLEngineService (`ml_engine.py`)
        │
        ▼ (SQLAlchemy ORM)
MySQL Database (`attrition_database`)
   ├── employees (The Primary Hub)
   ├── compensation (Financial Records)
   ├── performance_reviews (Appraisals)
   ├── workload_attendance (Hours & Remote Days)
   ├── hr_tickets (Friction & Complaints)
   ├── training_engagement (Skills & Growth)
   └── employee_features (24-Feature ML Matrix)
```

### The 6 Raw HR Tables

1. **`employees` (The Hub):** The central table. Every other table links back to this via `employee_id` (Foreign Key). Contains demographic and role data (`name`, `email`, `department`, `job_role`, `hire_date`, `location`, `manager_id`).
2. **`compensation` (Financials):** Logs `salary`, `bonus`, `stock_options`, and `effective_date`.
3. **`performance_reviews` (Appraisals):** Tracks historic performance ratings (`rating` on a 1–5 scale), `promotion_given` (boolean), and `manager_feedback_score`.
4. **`workload_attendance` (Workload & Burnout):** Logs `weekly_hours`, `overtime_hours`, `sick_leaves_taken`, and `remote_days`.
5. **`hr_tickets` (Friction & Culture):** Tracks employee complaints (`issue_date`, `resolution_date`, `category`, `severity`, `status`, `satisfaction_score`).
6. **`training_engagement` (Skills & Growth):** Tracks training courses (`training_name`, `event_date`, `completed`, `score`).

### The Derived Table

* **`employee_features` (The AI Input):** A strictly numerical table containing 1 row per employee and exactly 24 computed metrics. This is the ultimate output of Part 1.

---

## 3. Data Ingestion & The Cleaning Engine

Real-world HR CSV data uploaded by companies is inherently dirty. It contains blank values, string-casing inconsistencies, missing primary keys, negative overtime hours, and salary typographical errors.

When an HR admin uploads a CSV in the React frontend, it hits our **FastAPI upload routes**. It is immediately processed by the `DataCleanerService` (powered by Pandas).

### Cleaning Principles Applied:

* **Chunked Ingestion**: Reads CSV uploads in chunks of 10,000 rows to prevent memory overflow (`pd.read_csv(..., chunksize=10000)`).
* **ID Generation & Constraint Satisfaction**: If primary keys are missing (e.g. `comp_id`, `ticket_id`, `event_id`), the cleaner automatically generates UUIDs.
* **Intelligent Imputation**: Fills numerical missing values with medians and missing text fields (e.g. `location`, `department`) with `"Unknown"`.
* **Outlier Winsorization**: Caps salary outliers (>99th percentile) to prevent typos ($999,999) from destroying company average compensation statistics.
* **Negative Value Correction**: Resets negative overtime hours (<0) to 0.
* **Schema Hardening**: Columns are stripped of whitespace and dates are parsed with `pd.to_datetime(errors='coerce')`.
* **Smart Upserting**: Handles duplicate re-uploads smoothly by updating existing employee records without raising primary key collision exceptions.
* **Dataset Health Score**: Calculates dataset hygiene percentage:
  $$\text{Health Score} = \frac{\text{Inserted Rows}}{\text{Total Rows}} \times 100 - (\text{Imputed Cell } \% \times 0.5)$$

---

## 4. Exploratory Data Analysis (EDA) Engine

Once data is clean, HR leaders need immediate visual analytics. We built an interactive React Dashboard (`Dashboard.jsx`) powered by `recharts`:

1. **`/api/eda/kpis` (Executive Summary)**: Returns Total Headcount, Org Attrition Risk Rate %, Average Salary, and Org Satisfaction Score.
2. **`/api/eda/department-attrition` (Flight Risk by Dept)**: Renders a BarChart showing flight risk percentage per department.
3. **`/api/eda/overtime-vs-satisfaction` (Burnout Analytics)**: Renders a ComposedChart comparing average weekly overtime hours against satisfaction scores.
4. **`/api/eda/compensation-trends` (Pay Structure)**: Renders average salary per department.
5. **`/api/eda/hr-ticket-analysis` (Culture & Friction)**: Analyzes complaint volume and CSAT grouped by severity (Low, Medium, High).

---

## 5. Feature Engineering Pipeline (The 24 HR Features)

The `FeatureEngineeringService` takes raw logs across 6 tables and mathematically flattens them into a single 24-column vector per employee.

### The 24 Engineered HR Features:

1. **`tenure_years`**: Years employed: $\frac{\text{Current Date} - \text{hire\_date}}{365.0}$.
2. **`years_since_last_promotion`**: Years since last `promotion_given == True` (or `tenure_years` if never promoted).
3. **`salary_growth_rate`**: Percentage growth between initial and current salary: $\frac{\text{salary}_{\text{latest}} - \text{salary}_{\text{first}}}{\text{salary}_{\text{first}}}$.
4. **`total_compensation`**: $\text{salary} + \text{bonus} + \text{stock\_options}$.
5. **`avg_weekly_hours`**: Mean weekly hours worked from `workload_attendance`.
6. **`avg_overtime_hours`**: Mean weekly overtime hours (Primary burnout indicator).
7. **`workload_stress_index`**: $\text{avg\_weekly\_hours} + (\text{avg\_overtime\_hours} \times 1.5)$.
8. **`sick_leave_ratio`**: $\frac{\text{Total sick leaves taken}}{\text{tenure\_months}}$.
9. **`remote_work_ratio`**: Remote days / total working days ratio.
10. **`total_hr_complaints`**: Count of HR tickets opened.
11. **`high_severity_tickets`**: Count of tickets where $\text{severity} == \text{'High'}$.
12. **`days_since_last_complaint`**: $\text{Current Date} - \max(\text{issue\_date})$.
13. **`avg_hr_satisfaction`**: Mean satisfaction score on HR tickets.
14. **`latest_performance_rating`**: Most recent performance appraisal (1–5 scale).
15. **`avg_performance_rating`**: Historic mean rating across all reviews.
16. **`rating_trend`**: $\text{latest\_performance\_rating} - \text{avg\_performance\_rating}$.
17. **`trainings_completed`**: Count of completed training events.
18. **`training_score_avg`**: Mean test score across all completed training courses.
19. **`manager_tenure_years`**: Estimated time spent under current manager.
20. **`promotion_velocity`**: $\frac{\text{total\_promotions}}{\text{tenure\_years}}$.
21. **`employee_satisfaction_score` (0–100)**: Derived engagement score:
   $$\text{Satisfaction} = \text{clip}(50 + \text{rating} \times 10 + \text{training\_ratio} \times 20 - \text{complaints} \times 8 - \text{high\_sev} \times 15 - \text{overtime} \times 0.5, 0, 100)$$
22. **`attrition_risk_score` (0.0–1.0)**: Initial baseline flight risk heuristic combining overtime stress, promotion stagnation, satisfaction deficit, and severe complaints.
23. **`estimated_replacement_cost`**: $\text{salary} \times 0.5$ (Standard HR industry benchmark for turnover cost).
24. **`employee_segment`**: Persona label (*High Performer*, *Burnout Risk*, *Underperforming*, *Core Employee*).
