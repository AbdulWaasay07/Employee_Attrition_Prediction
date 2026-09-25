from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.feature_engineering import FeatureEngineeringService

router = APIRouter(tags=["Machine Learning Pipeline"])

@router.post("/ml/calculate-features")
def trigger_feature_engineering(db: Session = Depends(get_db)):
    """
    Triggers the Pandas-based HR Feature Engineering pipeline.
    Calculates the 24 key HR metrics from raw database tables
    and bulk upserts them into the employee_features table.
    """
    service = FeatureEngineeringService(db)
    
    try:
        result = service.calculate_features()
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("message"))
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
