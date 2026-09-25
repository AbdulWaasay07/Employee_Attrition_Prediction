# Employee Intelligence and Attrition Prediction Platform

A full-stack, data-driven machine learning platform designed to ingest raw, noisy human resources (HR) and workforce data across multiple operational touchpoints and translate it into actionable retention intelligence. The system employs automated data cleaning, scalable feature engineering, and robust machine learning algorithms to identify at-risk employees (burnout and flight risk) and deliver deterministic, prioritized HR retention recommendations.

---

## 1. Problem Statement and Objectives

### Problem Statement
Modern enterprises generate large volumes of fragmented workforce records across disparate systems, including compensation, performance appraisals, workload tracking, attendance, internal support tickets, and professional training. Without a unified workforce data foundation and predictive intelligence, organizations struggle to identify burnout, predict turnover, optimize compensation benchmarks, and prevent costly attrition (which typically costs 50% to 200% of an employee's annual salary).

### Target Users
* **HR Business Partners and People Operations**: Identify burnout risks early and design targeted retention packages.
* **Department Managers**: Monitor team workload stress, overtime spikes, and employee satisfaction trends.
* **HR Data Scientists and Analysts**: Leverage a clean, 24-dimensional feature store to build custom workforce analytics.
* **C-Suite and Executives**: Track headcount, flight risk percentages, compensation equity, and estimated replacement costs.

---

## 2. Key Features

* **Robust Ingestion and Cleaning Engine**: Reads multi-domain CSV files, handles missing values dynamically, applies domain-specific standardizations, and automatically handles extreme salary and workload outliers using Winsorization.
* **Automated HR Feature Engineering**: Flattens 6 relational tables into a 24-column feature store containing tenure metrics, compensation growth rates, performance trends, workload stress indices, HR complaint histories, and training participation.
* **Predictive Machine Learning Pipeline**:
  * **XGBoost Classifier**: Predicts continuous flight risk probabilities (0.0 to 1.0) with high precision, using synthetic boundary sampling to prevent class imbalance collapse.
  * **K-Means Clustering**: Unsupervised segmentation into actionable employee cohorts (High Performers, Burnout / Flight Risk, Underutilized / Stagnant).
* **HR Business Rules Engine**: Deterministically maps machine learning risk probabilities and workplace friction indicators to prioritized, actionable retention plans.
* **Interactive React Dashboard**: Provides an interface for schema mapping and data ingestion, an Executive Overview exploratory data analysis (EDA) view, and a dedicated AI Attrition Engine view with individual employee retention profile cards.

---

## 3. System Architecture and Technology Stack

```text
User (React 18 Frontend)
        │
        ▼ (REST HTTP Requests via Axios / Fetch)
FastAPI Backend Server (backend/app/main.py)
   ├── /api/upload/{dataset_type}   ──> DataCleanerService (data_cleaner.py)
   ├── /api/eda/*                  ──> SQL Aggregations on MySQL tables (routes_eda.py)
   ├── /api/ml/calculate-features  ──> FeatureEngineeringService (feature_engineering.py)
   └── /api/models/*               ──> MLEngineService (ml_engine.py)
        │
        ▼ (SQLAlchemy ORM via PyMySQL)
MySQL Database (attrition_database)
   ├── employees (Primary Hub)
   ├── compensation
   ├── performance_reviews
   ├── workload_attendance
   ├── hr_tickets
   ├── training_engagement
   └── employee_features (24-Feature Store)
```

### Technology Stack
* **Frontend / User Interface**: React 18, Vite, Recharts (data visualization), Lucide-React (icons), Vanilla CSS.
* **Backend Framework**: Python 3.11, FastAPI (asynchronous REST API).
* **Database and ORM**: MySQL 8.0, SQLAlchemy 2.0, PyMySQL.
* **Machine Learning and Data Processing**: Pandas, NumPy, Scikit-Learn (K-Means, StandardScaler), XGBoost, Joblib.

---

## 4. Project Directory Structure

```text
Employee_Attrition_Prediction/
├── backend/                  # FastAPI Backend Application
│   ├── app/
│   │   ├── api/              # REST API route controllers (EDA, ML, Upload, Models)
│   │   ├── core/             # Configuration and database settings (config.py)
│   │   ├── db/               # SQLAlchemy models and session factory (database.py, models.py)
│   │   ├── schemas/          # Pydantic schemas for data validation
│   │   ├── services/         # Core business logic: DataCleaner, FeatureEngine, MLEngine
│   │   └── main.py           # FastAPI application entry point
│   ├── models/               # Serialized machine learning models (.joblib files)
│   └── requirements.txt      # Python backend dependencies
├── frontend/                 # React Frontend Application
│   ├── src/
│   │   ├── App.jsx           # Main application shell and Data Importer view
│   │   ├── Dashboard.jsx     # HR EDA Analytics Dashboard view
│   │   ├── MLDashboard.jsx   # AI Attrition Engine Dashboard view
│   │   └── App.css           # Global application styling
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
├── Mock Data/                # Generated synthetic HR CSV datasets
├── generate_mock_data.py     # Synthetic data generator with realistic HR noise
├── PART1_README.md           # Granular Data Engineering and Architecture documentation
├── MLDD_Part2.md             # Machine Learning Design Document
├── TESTING_GUIDE.md          # Comprehensive End-to-End Testing Manual
└── README.md                 # System overview and master guide
```

---

## 5. Setup and Installation

### Note on Directory Paths
The command locations shown throughout this guide assume the project is installed at `d:\Employee_Attrition_Prediction\`. If you have installed or cloned the project into a different directory or drive (for example, `C:\Projects\Employee_Attrition_Prediction\`), navigate to your specific project root path before running the commands below.

### System Prerequisites
* **Python 3.9+** (Python 3.11 recommended)
* **Node.js 18+** and npm
* **MySQL Server 8.0+** running locally on port 3306

---

### Step 1: Database Setup

Ensure your local MySQL service is running. You can create the database manually using the MySQL CLI or MySQL Workbench:

```sql
CREATE DATABASE IF NOT EXISTS attrition_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

*Note: The platform is configured by default to connect to `mysql+pymysql://root:12345678@localhost:3306/attrition_database`. If your local MySQL credentials differ, update them in `backend/app/core/config.py` or create a `.env` file in the `backend/` directory.*

---

### Step 2: Backend Setup

Open a terminal window and navigate to the `backend/` directory:

* **Command Location**: `d:\Employee_Attrition_Prediction\backend\`
* **Commands to Run**:

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

*On initial startup, FastAPI automatically runs table creation routines. All 7 relational tables and the feature store are initialized in MySQL.*

---

### Step 3: Frontend Setup

Open a second terminal window and navigate to the `frontend/` directory:

* **Command Location**: `d:\Employee_Attrition_Prediction\frontend\`
* **Commands to Run**:

```bash
# Navigate to frontend directory
cd frontend

# Install Node packages
npm install

# Start Vite development server
npm run dev
```

*The user interface will be available at `http://localhost:5173`.*

---

## 6. Comprehensive Usage Guide

Follow the workflow below in sequence to test and operate the entire system.

---

### Stage 1: Generate Synthetic HR Datasets

To test the data cleaning engine and machine learning pipelines, generate synthetic HR datasets containing realistic anomalies (salary typos, negative overtime, missing values, and correlated flight risk patterns).

* **Command Location**: `d:\Employee_Attrition_Prediction\` (Workspace Root)
* **Command to Run**:

```bash
python generate_mock_data.py
```

* **Output**: Creates 6 CSV files in the `Mock Data/` folder:
  1. `Mock Data/mock_employees.csv` (150 employees with demographic and role details)
  2. `Mock Data/mock_compensation.csv` (Salary, bonus, stock options, and effective dates)
  3. `Mock Data/mock_performance.csv` (Appraisals, ratings 1–5, promotion history)
  4. `Mock Data/mock_workload.csv` (Weekly hours, overtime hours, sick leaves, remote days)
  5. `Mock Data/mock_hr_tickets.csv` (Complaints, severity, resolution dates, satisfaction scores)
  6. `Mock Data/mock_training.csv` (Upskilling events, completion flags, assessment scores)

---

### Stage 2: Ingest Datasets via Data Importer

Open your browser to `http://localhost:5173` and stay on the default **Data Importer** view.

#### Mandatory Upload Sequence (Referential Integrity)
Because child tables contain foreign keys pointing to `employees.employee_id`, datasets must be uploaded in the following exact order:

1. **Dataset 1: EMPLOYEES** (Primary Hub — Must be uploaded first)
   * Select dropdown: **EMPLOYEES**
   * Choose file: `Mock Data/mock_employees.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Expected Output*: Success notification confirming 150 rows inserted with ~98% Health Score.
2. **Dataset 2: COMPENSATION**
   * Select dropdown: **COMPENSATION**
   * Choose file: `Mock Data/mock_compensation.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Automated Cleaning*: Strips currency symbols (`$`), parses commas, and Winsorizes extreme salary outliers (>99th percentile).
3. **Dataset 3: PERFORMANCE**
   * Select dropdown: **PERFORMANCE**
   * Choose file: `Mock Data/mock_performance.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Automated Cleaning*: Imputes missing ratings and clamps scores strictly between 1 and 5.
4. **Dataset 4: WORKLOAD**
   * Select dropdown: **WORKLOAD**
   * Choose file: `Mock Data/mock_workload.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Automated Cleaning*: Clamps negative overtime hours to 0.0 and imputes missing weekly hours.
5. **Dataset 5: HR_TICKETS**
   * Select dropdown: **HR_TICKETS**
   * Choose file: `Mock Data/mock_hr_tickets.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Automated Cleaning*: Generates UUIDs for missing primary keys and handles open complaints with null resolution dates.
6. **Dataset 6: TRAINING**
   * Select dropdown: **TRAINING**
   * Choose file: `Mock Data/mock_training.csv`
   * Click **Run Upload & Cleaning Pipeline**
   * *Automated Cleaning*: Standardizes completion flags to boolean values.

*Note: The platform features Smart Upserting. Re-uploading any dataset will safely update existing records without primary key collision errors.*

---

### Stage 3: HR Exploratory Data Analysis (EDA)

Click on the **HR EDA Dashboard** tab in the sidebar navigation.

* **Executive KPI Cards**:
  * **Total Headcount**: Active employee count (150).
  * **Org Attrition Risk Rate**: Percentage of employees currently exhibiting flight risk signals.
  * **Average Org Salary**: Average annual base salary computed across all departments.
  * **Org Satisfaction Score**: Aggregate workforce morale score (0 to 100).
* **Interactive Visualizations**:
  * **Department Flight Risk (Bar Chart)**: Compares attrition risk percentages across Engineering, Sales, Marketing, HR, Finance, Product, and Operations.
  * **Overtime vs. Satisfaction (Composed Chart)**: Highlights departments where overtime spikes correlate with satisfaction drops (Burnout indicator).
  * **Compensation by Department (Bar Chart)**: Compares average departmental compensation packages.
  * **HR Complaint Volume and CSAT (Composed Chart)**: Displays ticket volume versus resolution satisfaction across Low, Medium, and High severity tiers.

---

### Stage 4: AI Attrition Engine and Retention Strategies

Click on the **AI Attrition Engine** tab in the sidebar navigation. Execute the four machine learning control buttons in order:

1. **Step 1: Click "Compile HR Feature Store"**
   * *What it does*: Triggers `FeatureEngineeringService` to query all 6 relational tables, compute 24 derived metrics for each employee, and write them into the `employee_features` table.
   * *Expected Output*: Banner displays `{"status": "success", "features_generated": 150}`.
2. **Step 2: Click "Train Risk Cohorts (K-Means)"**
   * *What it does*: Scales multi-dimensional signals and fits K-Means clustering ($k=3$) to classify employees into risk personas:
     * *High Performers (Low Risk)*: High appraisal ratings and balanced hours.
     * *Burnout / Flight Risk*: High overtime hours and high workload stress.
     * *Underutilized / Stagnant*: Low growth rates and long tenure without promotion.
   * *Expected Output*: Banner displays `Successfully segmented 150 employees into risk cohorts.`
3. **Step 3: Click "Train Attrition Model (XGBoost)"**
   * *What it does*: Trains an `XGBClassifier` over 21 workforce features with boundary sampling for class balance, and saves the trained model to `backend/models/attrition_model.joblib`.
   * *Expected Output*: Banner displays `Employee Attrition Prediction XGBoost model trained and saved successfully.`
4. **Step 4: Click "Generate Attrition Predictions"**
   * *What it does*: Loads the serialized XGBoost model, runs batch inference across all employees, and updates the `attrition_risk_score` column in the database with continuous probabilities (0.0 to 1.0).
   * *Expected Output*: Banner displays `Generated exact ML attrition predictions for 150 employees.`
5. **Step 5: View Individual Retention Profile Cards**
   * Select any employee ID from the dropdown (e.g., `EMP001`, `EMP015`).
   * *Profile Card Details*: Displays Department, Role, Tenure, Base Salary, Estimated Replacement Cost ($), Flight Risk Probability Gauge (%), and Satisfaction Gauge (/100).
   * *Action Plan*: Evaluates deterministic business rules to provide priority-coded retention actions:
     * **CRITICAL**: Immediate Stay Interview, Schedule Salary/Bonus Review, and Retention Grant.
     * **HIGH**: Reallocate Project Workload and Mandate Manager One-on-One Check-in.
     * **MEDIUM**: Enroll in Performance Improvement Plan (PIP) and Skills Training.
     * **NORMAL**: Eligible for Leadership Development and Fast-Track Promotion.

---

## 7. REST API Reference

The backend provides interactive OpenAPI (Swagger) documentation accessible at `http://localhost:8000/docs`.

| HTTP Method | API Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check and platform status |
| `POST` | `/api/upload/{dataset_type}` | Ingest and clean an HR CSV file (`employees`, `compensation`, etc.) |
| `GET` | `/api/eda/kpis` | Executive summary metrics (Headcount, Attrition Rate, Salary, CSAT) |
| `GET` | `/api/eda/department-attrition` | Department-level flight risk statistics |
| `GET` | `/api/eda/overtime-vs-satisfaction` | Department-level overtime and satisfaction correlation data |
| `GET` | `/api/eda/compensation-trends` | Average salary by department |
| `GET` | `/api/eda/hr-ticket-analysis` | Complaint volume and resolution satisfaction grouped by severity |
| `POST` | `/api/ml/calculate-features` | Compile the 24-feature HR feature store |
| `POST` | `/api/models/train-segmentation` | Train and serialize K-Means risk cohort model |
| `POST` | `/api/models/train-attrition` | Train and serialize XGBoost attrition classifier |
| `POST` | `/api/models/predict` | Execute batch flight risk inference for all employees |
| `GET` | `/api/models/employees` | List all employee IDs for selection |
| `GET` | `/api/models/recommendations/{employee_id}` | Fetch individual retention card and prioritized action plan |

---

## 8. Verification and Testing

To execute automated tests or verify full pipeline execution from the terminal, refer to [`TESTING_GUIDE.md`](TESTING_GUIDE.md).

Quick verification command from the terminal:
* **Command Location**: `d:\Employee_Attrition_Prediction\backend\`
* **Command**:

```bash
python -c "from app.main import app; print('Backend App Import Succeeded')"
```
