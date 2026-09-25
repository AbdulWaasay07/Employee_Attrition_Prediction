# Master End-to-End Testing Guide
## Employee Intelligence & Attrition Prediction Platform

This guide provides an exhaustive, step-by-step testing manual for the **Employee Intelligence & Attrition Prediction Platform**. It covers every phase from initial database setup to advanced machine learning inference, detailing **what** is tested, **why** it is tested, **how** to test it, **what results to expect**, and **how edge cases are handled**.

---

## Critical Prerequisite: Mandatory CSV Upload Order

Because this platform uses a normalized relational database (MySQL), **referential integrity** dictates the order of dataset uploads.

### Why Order Matters
The `employees` table serves as the central primary hub. Every other table (`compensation`, `performance_reviews`, `workload_attendance`, `hr_tickets`, `training_engagement`) contains a `FOREIGN KEY (employee_id)` referencing `employees(employee_id)`. If you attempt to upload child datasets before uploading employees, foreign key checks will fail.

### Required Upload Sequence:
1. **`mock_employees.csv`** (Primary Hub — **MUST BE UPLOADED FIRST**)
2. **`mock_compensation.csv`** (Financials)
3. **`mock_performance.csv`** (Appraisals)
4. **`mock_workload.csv`** (Workload & Burnout)
5. **`mock_hr_tickets.csv`** (HR Complaints & Friction)
6. **`mock_training.csv`** (Skills & Engagement)

---

## Comprehensive Test Plan Index

* [Phase 0: Environment & Database Setup](#phase-0-environment--database-setup)
* [Phase 1: Synthetic HR Dataset Generation](#phase-1-synthetic-hr-dataset-generation)
* [Phase 2: HR Data Ingestion & Cleaning Engine (Edge Cases Included)](#phase-2-hr-data-ingestion--cleaning-engine)
* [Phase 3: HR Exploratory Data Analysis (EDA Dashboard)](#phase-3-hr-exploratory-data-analysis-eda-dashboard)
* [Phase 4: AI Attrition Engine & Machine Learning Pipeline](#phase-4-ai-attrition-engine--machine-learning-pipeline)
* [Phase 5: REST API & Swagger Manual Verification](#phase-5-rest-api--swagger-manual-verification)

---

## Phase 0: Environment & Database Setup

### Test 0.1: Database Schema Auto-Creation
* **What We Are Testing**: Verifying that `attrition_database` is created in MySQL and tables are initialized automatically upon backend server startup.
* **Why We Test This**: Ensures smooth zero-configuration deployment without needing manual SQL script executions.
* **How to Test**:
  1. Ensure local MySQL Server is running on port `3306`.
  2. Open terminal in `backend/` directory.
  3. Start the FastAPI server:
     ```bash
     uvicorn app.main:app --reload --port 8000
     ```
* **What to Expect**:
  * Terminal displays: `Database tables initialized successfully.`
  * Uvicorn starts running at `http://127.0.0.1:8000`.
  * Open MySQL Workbench/CLI and run `SHOW TABLES IN attrition_database;`. You will see all 8 tables: `employees`, `compensation`, `performance_reviews`, `workload_attendance`, `hr_tickets`, `training_engagement`, `employee_features`, `job_status`.

---

## Phase 1: Synthetic HR Dataset Generation

### Test 1.1: HR Mock Data Generator
* **What We Are Testing**: Verifying that `generate_mock_data.py` produces realistic, noisy HR datasets inside the `Mock Data/` folder.
* **Why We Test This**: We need dirty datasets with realistic workforce noise (missing values, typos, negative overtime, salary outliers, burnout correlations) to stress-test the cleaning engine.
* **How to Test**:
  1. Open terminal in workspace root (`Employee_Attrition_Prediction/`).
  2. Run:
     ```bash
     python generate_mock_data.py
     ```
* **What to Expect**:
  * Output log:
    ```text
    Generating 'Dirty' HR mock data for 150 employees in 'Mock Data' directory...
    Created Mock Data/mock_employees.csv
    Created Mock Data/mock_compensation.csv
    Created Mock Data/mock_performance.csv
    Created Mock Data/mock_workload.csv
    Created Mock Data/mock_hr_tickets.csv
    Created Mock Data/mock_training.csv
    Success! HR 'Dirty' mock datasets created inside 'Mock Data' for 150 employees.
    ```
  * Verify `Mock Data/` directory contains all 6 generated CSV files.

---

## Phase 2: HR Data Ingestion & Cleaning Engine

Access the web application at `http://localhost:5173` and open the **Data Importer** tab.

---

### Test 2.1: Primary Employee Upload (Happy Path)
* **What We Are Testing**: Ingesting the core employee hub dataset.
* **Why We Test This**: Establishes the master employee backbone in MySQL.
* **How to Test**:
  1. Select Dataset Type: **EMPLOYEES**.
  2. Upload `Mock Data/mock_employees.csv`.
  3. Verify required columns (`employee_id`, `name`, `email`, `department`, `job_role`, `hire_date`, `location`, `manager_id`) auto-map.
  4. Click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays: `Success! Inserted 150 rows. Health Score: ~98.33%`.
  * MySQL query `SELECT COUNT(*) FROM employees;` returns `150`.

---

### Test 2.2: Re-Upload Deduplication & Smart Upserting (Edge Case)
* **What We Are Testing**: Uploading the exact same `mock_employees.csv` file a second time.
* **Why We Test This**: Prevents `pymysql.err.IntegrityError (1062 Duplicate entry)` crashes. Ensures re-uploading updates existing records cleanly.
* **How to Test**:
  1. Immediately click **Run Upload & Cleaning Pipeline** again on `mock_employees.csv`.
* **What to Expect**:
  * Status banner displays `Success! Inserted 150 rows` with **0 errors**.
  * Existing employee records are updated in MySQL without duplicate key exceptions.

---

### Test 2.3: Currency Formatting & Salary Winsorization in Compensation (Edge Case)
* **What We Are Testing**: Uploading `mock_compensation.csv` containing formatted currency strings (`$85,000`) and salary typos (`$999,999`).
* **Why We Test This**: Ensures salary values are parsed to float and extreme outliers are capped at the 99th percentile quantile so averages aren't destroyed.
* **How to Test**:
  1. Select Dataset Type: **COMPENSATION**.
  2. Upload `Mock Data/mock_compensation.csv` and click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays `Success! Inserted 220 rows`.
  * MySQL Verification: `SELECT MAX(salary) FROM compensation;` returns a realistic capped maximum (e.g. `~$138,000`) rather than `999999`.

---

### Test 2.4: Rating Clamping & Boolean Coercion in Performance (Edge Case)
* **What We Are Testing**: Uploading `mock_performance.csv` containing missing ratings and string boolean flags (`"True"`, `"yes"`).
* **Why We Test This**: Guarantees appraisal ratings stay strictly within 1–5 and promotion flags are valid booleans.
* **How to Test**:
  1. Select Dataset Type: **PERFORMANCE**.
  2. Upload `Mock Data/mock_performance.csv` and click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays `Success! Inserted ~346 rows`.
  * Missing ratings are imputed with median `3` and clamped between `1` and `5`.

---

### Test 2.5: Negative Overtime Clamping in Workload (Edge Case)
* **What We Are Testing**: Uploading `mock_workload.csv` containing negative overtime hours (`-5`).
* **Why We Test This**: Prevents negative work hours from breaking stress index calculations.
* **How to Test**:
  1. Select Dataset Type: **WORKLOAD**.
  2. Upload `Mock Data/mock_workload.csv` and click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays `Success! Inserted ~685 rows`.
  * MySQL Verification: `SELECT MIN(overtime_hours) FROM workload_attendance;` returns `0.0` (all negative hours reset to 0).

---

### Test 2.6: Auto UUID Generation & NaT Dates in HR Tickets (Edge Case)
* **What We Are Testing**: Uploading `mock_hr_tickets.csv` where `ticket_id` primary key is missing for some rows, and `resolution_date` is unfulfilled (`NaT`).
* **Why We Test This**: Verifies missing PKs are assigned UUIDs and open complaints are handled without SQL date errors.
* **How to Test**:
  1. Select Dataset Type: **HR_TICKETS**.
  2. Upload `Mock Data/mock_hr_tickets.csv` and click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays `Success! Inserted ~295 rows`.
  * Missing primary keys are filled with valid UUID strings. Open tickets have `resolution_date = NULL` and `status = 'Open'`.

---

### Test 2.7: Training Status Standardization (Edge Case)
* **What We Are Testing**: Uploading `mock_training.csv`.
* **Why We Test This**: Ensures training scores and completion statuses are standardized.
* **How to Test**:
  1. Select Dataset Type: **TRAINING**.
  2. Upload `Mock Data/mock_training.csv` and click **Run Upload & Cleaning Pipeline**.
* **What to Expect**:
  * UI displays `Success! Inserted ~303 rows`.

---

## Phase 3: HR Exploratory Data Analysis (EDA Dashboard)

Navigate to the **HR EDA Dashboard** tab in the sidebar.

### Test 3.1: Executive Summary KPIs
* **What We Are Testing**: Aggregation endpoints returning Total Headcount, Org Attrition Rate %, Average Salary, and Org Satisfaction Score.
* **Why We Test This**: Validates real-time SQL queries across `employees`, `compensation`, and `employee_features`.
* **What to Expect**:
  * **Total Headcount**: `150`
  * **Org Attrition Risk Rate**: Displays current flight risk percentage (e.g. `22.5%`)
  * **Average Org Salary**: Formatted dollar value (e.g. `$84,520`)
  * **Org Satisfaction Score**: Average engagement score (e.g. `74.8 / 100`)

---

### Test 3.2: Interactive Analytics Charts
* **What We Are Testing**:
  1. **Department Flight Risk (BarChart)**: Renders risk rate % grouped by department.
  2. **Overtime vs. Satisfaction (ComposedChart)**: Displays weekly overtime bars alongside satisfaction score line graph.
  3. **Average Compensation by Department (BarChart)**: Displays average salary per department.
  4. **HR Complaint Volume & CSAT by Severity (ComposedChart)**: Displays ticket volume vs CSAT rating for Low, Medium, and High severity tickets.
* **What to Expect**: All 4 charts render smoothly with interactive hover tooltips.

---

## Phase 4: AI Attrition Engine & Machine Learning Pipeline

Navigate to the **AI Attrition Engine** tab in the sidebar.

---

### Test 4.1: HR Feature Store Compilation
* **What We Are Testing**: Triggers `FeatureEngineeringService` to compute 24 workforce features.
* **Why We Test This**: Flattens 6 relational tables into `employee_features` matrix.
* **How to Test**: Click **Compile HR Feature Store**.
* **What to Expect**:
  * Status banner displays: `{"status": "success", "features_generated": 150}`.
  * MySQL Verification: `SELECT * FROM employee_features LIMIT 5;` returns 24 engineered features for each employee.

---

### Test 4.2: Risk Cohort K-Means Clustering Training
* **What We Are Testing**: Training K-Means clustering ($k=3$) on `tenure_years`, `avg_overtime_hours`, `salary_growth_rate`, and `latest_performance_rating`.
* **Why We Test This**: Groups employees into personas (*High Performers (Low Risk)*, *Burnout / Flight Risk*, *Underutilized / Stagnant*).
* **How to Test**: Click **Train Risk Cohorts (K-Means)**.
* **What to Expect**:
  * Banner displays: `Successfully segmented 150 employees into risk cohorts.`
  * Model saved to `backend/models/segmentation_kmeans.joblib`.

---

### Test 4.3: XGBoost Attrition Model Training
* **What We Are Testing**: Training XGBoost classifier on 21 workforce features.
* **Why We Test This**: Builds the predictive model for flight risk probability scoring.
* **How to Test**: Click **Train Attrition Model (XGBoost)**.
* **What to Expect**:
  * Banner displays: `Employee Attrition Prediction XGBoost model trained and saved successfully.`
  * Model saved to `backend/models/attrition_model.joblib`.

---

### Test 4.4: Batch Inference Execution
* **What We Are Testing**: Running prediction model on all active employees.
* **Why We Test This**: Overwrites baseline risk heuristics with exact XGBoost probability scores in MySQL.
* **How to Test**: Click **Generate Attrition Predictions**.
* **What to Expect**:
  * Banner displays: `Generated exact ML attrition predictions for 150 employees.`

---

### Test 4.5: Employee Retention Profile & Action Plan
* **What We Are Testing**: Fetching individual HR recommendations for a selected employee.
* **How to Test**: Select an employee profile from the dropdown (e.g. **EMP001**).
* **What to Expect**:
  * **Profile Header**: Department, Job Role, Tenure (Years), Annual Salary ($), and Replacement Cost ($).
  * **Gauges**: Attrition Probability Bar (%) & Satisfaction Score Bar (/100).
  * **HR Action Plan**: Priority-coded badges (**CRITICAL**, **HIGH**, **MEDIUM**, **NORMAL**) with actionable retention strategies.

---

## Phase 5: REST API & Swagger Manual Verification

You can also test all backend endpoints directly via FastAPI Interactive Docs at **`http://localhost:8000/docs`**:

| Method | Endpoint | Description | Expected Output |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Server & Platform status | `{"status": "healthy", "platform": "Employee Attrition Prediction"}` |
| `POST` | `/api/upload/{dataset_type}` | Ingest CSV file | `{"rows_inserted": 150, "dataset_health_score": 98.33}` |
| `GET` | `/api/eda/kpis` | Executive KPIs | `{"total_headcount": 150, "org_attrition_rate": 22.5, ...}` |
| `POST` | `/api/ml/calculate-features` | Run 24 HR feature engine | `{"status": "success", "features_generated": 150}` |
| `POST` | `/api/models/train-segmentation` | Train K-Means cohorts | `{"status": "success", "clusters_found": 3}` |
| `POST` | `/api/models/train-attrition` | Train XGBoost model | `{"status": "success", "message": "...trained successfully"}` |
| `POST` | `/api/models/predict` | Run batch inference | `{"status": "success", "message": "...predictions for 150 employees"}` |
| `GET` | `/api/models/recommendations/{emp_id}` | Fetch HR Action Plan | `{"employee_id": "EMP001", "recommendations": [...]}` |

---

## Verification Summary Checklist
- [x] Database `attrition_database` schema auto-creation verified.
- [x] CSV upload sequence enforced (`employees` hub uploaded first).
- [x] Edge cases handled: currency symbols stripped, negative overtime clamped to 0, salary typos Winsorized, missing PKs assigned UUIDs, duplicate uploads upserted smoothly.
- [x] Executive EDA Dashboard charts & KPIs functional.
- [x] 24 HR Feature Store compiled.
- [x] K-Means risk cohorts & XGBoost attrition models trained.
- [x] Retention Action Plans generated with priority badges.
