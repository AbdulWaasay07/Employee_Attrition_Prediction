# Machine Learning Design Document (MLDD)
## Part 2: Machine Learning & HR Analytics Engine
**Project:** Employee Intelligence & Attrition Prediction Platform

---

## 1. Employee Risk Cohort Segmentation (K-Means)

### Purpose & Business Problem
Segmentation transforms a monolithic employee workforce into actionable cohorts. By understanding distinct risk personas (e.g., "High Performers (Low Risk)", "Burnout / Flight Risk", "Underutilized / Stagnant"), HR managers and department leads can tailor retention grants, balance project workloads, and prevent costly turnover.

### Inputs & Workflow
* **Input Features**: `tenure_years`, `avg_overtime_hours`, `salary_growth_rate`, `latest_performance_rating`.
* **Workflow**:
  ```text
  Raw Features Matrix ──> StandardScaler ──> K-Means Clustering (k=3) ──> Centroid Profiling ──> Assign Personas ──> Update Database (`employee_segment`)
  ```
* **Persona Mapping Logic**:
  * **High Performers (Low Risk)**: Cluster with highest performance rating and normal working hours.
  * **Burnout / Flight Risk**: Cluster with highest overtime hours and high workload stress.
  * **Underutilized / Stagnant**: Cluster with low growth rate and stagnant tenure.
* **Model Serialization**: Saved to `backend/models/segmentation_scaler.joblib` and `backend/models/segmentation_kmeans.joblib`.

---

## 2. Employee Attrition Prediction Model (XGBoost Classifier)

### Business Objective & Formulation
Predict the probability ($0.0 \rightarrow 1.0$) that an employee will leave the organization within the next 6 to 12 months. This is formulated as a **Binary Classification** problem ($1 = \text{High Flight Risk}$, $0 = \text{Retained}$).

### Algorithms & Hyperparameters
* **Model**: `xgboost.XGBClassifier`
* **Configuration**:
  * `n_estimators = 100`
  * `max_depth = 3`
  * `learning_rate = 0.1`
  * `eval_metric = 'logloss'`
  * `random_state = 42`
* **Features Used (21 Dimensions)**:
  `tenure_years`, `years_since_last_promotion`, `promotion_velocity`, `manager_tenure_years`, `salary_growth_rate`, `total_compensation`, `avg_weekly_hours`, `avg_overtime_hours`, `workload_stress_index`, `sick_leave_ratio`, `remote_work_ratio`, `total_hr_complaints`, `high_severity_tickets`, `days_since_last_complaint`, `avg_hr_satisfaction`, `latest_performance_rating`, `avg_performance_rating`, `rating_trend`, `trainings_completed`, `training_score_avg`, `employee_satisfaction_score`.

### Handling Class Imbalance & Boundary Sampling
To prevent single-class collapse during edge-case training runs, the pipeline dynamically determines the median attrition threshold and injects synthetic boundary controls to guarantee stable probability calibration.

### Model Persistence & Serving
* **Artifacts**: Saved to `backend/models/attrition_model.joblib` and `backend/models/attrition_features.joblib`.
* **Inference**: During batch prediction (`POST /api/models/predict`), FastAPI loads the serialized model into memory and executes matrix inference across all employees, updating `attrition_risk_score` in MySQL in milliseconds.

---

## 3. HR Rules-Based Recommendation Engine

### Translating ML to Actionable Retention Plans
The ML model outputs raw continuous probabilities. The HR Rules Engine uses decision rules to map flight risk and friction metrics to actionable retention strategies.

| Attrition Risk Score | Performance Rating | Overtime / Friction | **Priority** | **Recommended Action Plan** |
| :--- | :--- | :--- | :--- | :--- |
| High (>0.6) | High ($\ge$4.0) | Any | **CRITICAL** | **Immediate Stay Interview, Schedule Salary/Bonus Review & Retention Grant.** |
| High (>0.6) or Any | Any | High (>10 hrs OT) / Low Sat (<60) | **HIGH** | **Reallocate Project Workload & Mandate Manager One-on-One Check-in.** |
| Low (<0.3) | Low ($\le$2.0) | Low | **MEDIUM** | **Enroll in Performance Improvement Plan (PIP) & Skills Training.** |
| Low (<0.3) | High ($\ge$4.0) | Low | **NORMAL** | **Eligible for Leadership Development & Fast-Track Promotion.** |
| Default | Any | Normal | **NORMAL** | **Maintain standard employee engagement and regular 1-on-1 check-ins.** |
