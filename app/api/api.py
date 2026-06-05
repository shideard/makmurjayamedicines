from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import auth, deps
from app.core.database import get_db
from app.models.models import User
from app.repositories.repositories import medicine_repo
from app.schemas.schemas import MedicineResponse

api_router = APIRouter()

# Auth router
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Medicines
medicines_router = APIRouter()

@medicines_router.get("/", response_model=list[MedicineResponse])
def read_medicines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    medicines = medicine_repo.get_multi(db, skip=skip, limit=limit)
    return medicines

api_router.include_router(medicines_router, prefix="/medicines", tags=["medicines"])

# Dashboard (Admin Only Example)
dashboard_router = APIRouter()

@dashboard_router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(deps.get_current_admin)
):
    # Ini hanya dapat diakses oleh Admin
    return {
        "total_revenue": 125000000,
        "total_orders": 342,
        "total_customers": 128
    }

api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

import os
from fastapi import UploadFile, File
upload_router = APIRouter()

@upload_router.post("/")
def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.require_current_user)
):
    upload_dir = "app/static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
        
    return {"filename": file.filename, "url": f"/static/uploads/{file.filename}"}

api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
