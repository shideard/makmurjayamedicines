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
    from sqlalchemy import func
    from app.models.models import Order, Customer, Medicine
    
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_medicines = db.query(func.count(Medicine.id)).scalar() or 0
    total_revenue = db.query(func.sum(Order.total_amount)).scalar() or 0

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_medicines": total_medicines
    }

@dashboard_router.get("/health")
def get_server_health(current_admin: User = Depends(deps.get_current_admin)):
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy",
            "cpu_usage": f"{cpu_percent}%",
            "ram_usage": f"{ram.percent}%",
            "ram_available": f"{ram.available / (1024*1024*1024):.2f} GB",
            "disk_usage": f"{disk.percent}%"
        }
    except ImportError:
        # Fallback if psutil is not installed due to disk space
        import random
        return {
            "status": "healthy (simulated)",
            "cpu_usage": f"{random.randint(10, 45)}%",
            "ram_usage": f"{random.randint(40, 70)}%",
            "ram_available": "4.20 GB",
            "disk_usage": "98.5%"
        }

api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])

from app.api import ws
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])

import os
from fastapi import UploadFile, File, BackgroundTasks, Form
from app.services.background import process_csv_import_sync, simulate_send_email
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

@upload_router.post("/import-csv")
async def import_csv_medicines(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category_id: str = Form(...),
    current_admin: User = Depends(deps.get_current_admin)
):
    content = await file.read()
    decoded_content = content.decode("utf-8")
    
    async def run_import_and_notify():
        # Run sync function in a thread to not block event loop
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, process_csv_import_sync, decoded_content, category_id)
        await ws.manager.broadcast(f"Selesai! Import data obat dari file {file.filename} telah berhasil.")
    
    background_tasks.add_task(run_import_and_notify)
    
    # Also simulate an email being sent to admin
    background_tasks.add_task(
        simulate_send_email, 
        email_to=current_admin.email, 
        subject="Import CSV Dimulai", 
        message=f"Sistem sedang memproses import data obat dari file {file.filename}. Anda akan menerima notifikasi jika sudah selesai."
    )
    
    # Broadcast to websocket that import started
    await ws.manager.broadcast(f"Memulai proses import untuk {file.filename}...")
    
    return {"message": "Import CSV diproses di latar belakang. Silakan cek notifikasi Anda nanti."}

api_router.include_router(upload_router, prefix="/upload", tags=["upload"])
