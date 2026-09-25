from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_upload
from app.api import routes_eda
from app.api import routes_ml
from app.api import routes_models
from app.db.database import engine
from app.db import models

# Automatically build MySQL database tables if they do not exist
try:
    models.Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")
except Exception as e:
    print(f"Notice: Table creation during startup skipped or failed: {e}")

app = FastAPI(
    title="Employee Intelligence & Attrition Platform API",
    description="Backend API for the Employee Intelligence & Attrition Prediction Platform",
    version="1.0.0"
)

# Allow React Frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Employee Intelligence & Attrition Platform API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "platform": "Employee Attrition Prediction"}

app.include_router(routes_upload.router, prefix="/api")
app.include_router(routes_eda.router, prefix="/api")
app.include_router(routes_ml.router, prefix="/api")
app.include_router(routes_models.router, prefix="/api/models")
