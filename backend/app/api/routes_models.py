from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import EmployeeFeature, Employee
from app.services.ml_engine import MLEngineService

router = APIRouter()

@router.get("/employees")
def get_all_employees(db: Session = Depends(get_db)):
    """
    Returns a list of all employee IDs available for ML predictions.
    """
    try:
        employees = db.query(EmployeeFeature.employee_id).all()
        if not employees:
            employees = db.query(Employee.employee_id).all()
        return {"employees": [e[0] for e in employees], "customers": [e[0] for e in employees]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers")
def get_all_customers_alias(db: Session = Depends(get_db)):
    """
    Alias endpoint for backward compatibility.
    """
    return get_all_employees(db)

@router.post("/train-segmentation")
def train_segmentation(db: Session = Depends(get_db)):
    """
    Trains the K-Means clustering model on employee features and assigns risk personas.
    """
    try:
        result = MLEngineService.train_segmentation_model(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-attrition")
def train_attrition_model(db: Session = Depends(get_db)):
    """
    Trains the XGBoost Employee Attrition Prediction model.
    """
    try:
        result = MLEngineService.train_attrition_model(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/train-churn")
def train_churn_model_alias(db: Session = Depends(get_db)):
    """
    Alias endpoint for backward compatibility.
    """
    return train_attrition_model(db)

@router.post("/predict")
def generate_predictions(db: Session = Depends(get_db)):
    """
    Loads saved models and updates all employees with their exact ML attrition probabilities.
    """
    try:
        result = MLEngineService.generate_predictions(db)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/{employee_id}")
def get_recommendations(employee_id: str, db: Session = Depends(get_db)):
    """
    Returns Business Rules Engine HR recommendations for a specific employee.
    """
    try:
        result = MLEngineService.get_hr_recommendations(employee_id.lower().strip(), db)
        if result.get("status") == "error":
            # Try original casing if lower didn't hit
            result = MLEngineService.get_hr_recommendations(employee_id.strip(), db)
            if result.get("status") == "error":
                raise HTTPException(status_code=404, detail=result.get("message"))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
