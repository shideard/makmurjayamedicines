from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.repositories.repositories import medicine_repo, category_repo
from app.models.models import Prescription, InventoryBatch, Order, Payment
from sqlalchemy import func
from datetime import datetime, timedelta
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def read_home(request: Request, current_user = Depends(deps.get_current_user)):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"user": current_user}
    )

@router.get("/katalog", response_class=HTMLResponse)
def read_catalog(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_user)):
    medicines = medicine_repo.get_multi(db, limit=50)
    
    # Normally we would join with inventory to get stock, but for template mock:
    medicines_with_stock = []
    for med in medicines:
        med_dict = med.__dict__
        med_dict["stock"] = 15 # Mocked stock for UI demo
        medicines_with_stock.append(med_dict)

    return templates.TemplateResponse(
        request=request, 
        name="katalog.html", 
        context={
            "user": None,
            "medicines": medicines_with_stock
        }
    )

@router.get("/obat/{slug}", response_class=HTMLResponse)
def read_medicine_detail(slug: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_user)):
    medicine = medicine_repo.get_by_slug(db, slug=slug)
    if not medicine:
        return HTMLResponse(content="Obat tidak ditemukan", status_code=404)
        
    # Mock stock for template
    medicine_dict = medicine.__dict__
    medicine_dict["stock"] = 15
    
    return templates.TemplateResponse(
        request=request, 
        name="detail_obat.html", 
        context={
            "user": current_user,
            "medicine": medicine_dict
        }
    )

@router.get("/keranjang", response_class=HTMLResponse)
def read_cart(request: Request, current_user = Depends(deps.get_current_user)):
    return templates.TemplateResponse(
        request=request, name="keranjang.html", context={"user": current_user}
    )

@router.get("/checkout", response_class=HTMLResponse)
def read_checkout(request: Request, current_user = Depends(deps.get_current_user)):
    return templates.TemplateResponse(
        request=request, name="checkout.html", context={"user": current_user}
    )

import uuid

@router.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    csrf_token = str(uuid.uuid4())
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(
        request=request, name="login.html", context={"user": None, "csrf_token": csrf_token}
    )

@router.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    csrf_token = str(uuid.uuid4())
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(
        request=request, name="register.html", context={"user": None, "csrf_token": csrf_token}
    )

@router.get("/admin/dashboard", response_class=HTMLResponse)
def read_admin_dashboard(request: Request, current_user = Depends(deps.get_current_admin)):
    return templates.TemplateResponse(
        request=request, name="admin_dashboard.html", context={"user": current_user}
    )

@router.get("/apoteker/dashboard", response_class=HTMLResponse)
def read_apoteker_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    pending_prescriptions = db.query(Prescription).filter(Prescription.status == "PENDING").all()
    
    three_months_from_now = datetime.utcnow() + timedelta(days=90)
    low_stock_batches = db.query(InventoryBatch).filter(InventoryBatch.quantity < 10).count()
    expiring_batches = db.query(InventoryBatch).filter(InventoryBatch.expiry_date <= three_months_from_now).count()

    return templates.TemplateResponse(
        request=request, 
        name="apoteker_dashboard.html", 
        context={
            "user": current_user,
            "pending_prescriptions": pending_prescriptions,
            "low_stock_count": low_stock_batches,
            "expiring_count": expiring_batches
        }
    )

@router.get("/kasir/dashboard", response_class=HTMLResponse)
def read_kasir_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_kasir)):
    today = datetime.utcnow().date()
    
    # Calculate today's income
    today_income = db.query(func.sum(Order.grand_total)).filter(
        Order.status == "COMPLETED",
        func.date(Order.created_at) == today
    ).scalar() or 0.0

    total_transactions = db.query(Order).filter(func.date(Order.created_at) == today).count()
    
    pending_orders = db.query(Order).filter(Order.status == "PENDING").all()
    ready_orders = db.query(Order).filter(Order.status == "PROCESSING").count()

    return templates.TemplateResponse(
        request=request, 
        name="kasir_dashboard.html", 
        context={
            "user": current_user,
            "today_income": today_income,
            "total_transactions": total_transactions,
            "pending_orders": pending_orders,
            "ready_count": ready_orders
        }
    )

@router.get("/pelanggan/dashboard", response_class=HTMLResponse)
def read_pelanggan_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_pelanggan)):
    orders = []
    processing_count = 0
    completed_count = 0
    if current_user.customer:
        orders = db.query(Order).filter(Order.customer_id == current_user.customer.id).order_by(Order.created_at.desc()).all()
        processing_count = sum(1 for o in orders if o.status in ["PENDING", "PROCESSING"])
        completed_count = sum(1 for o in orders if o.status in ["COMPLETED", "CANCELLED"])

    return templates.TemplateResponse(
        request=request, 
        name="pelanggan_dashboard.html", 
        context={
            "user": current_user,
            "orders": orders,
            "processing_count": processing_count,
            "completed_count": completed_count,
            "prescriptions": db.query(Prescription).filter(Prescription.customer_id == current_user.customer.id).order_by(Prescription.created_at.desc()).all() if current_user.customer else []
        }
    )

import os
import shutil
from fastapi import File, UploadFile, Form
from fastapi.responses import RedirectResponse

@router.get("/unggah-resep", response_class=HTMLResponse)
def read_unggah_resep(request: Request, current_user = Depends(deps.get_current_pelanggan)):
    return templates.TemplateResponse(
        request=request, name="unggah_resep.html", context={"user": current_user}
    )

@router.post("/unggah-resep")
def process_unggah_resep(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_pelanggan),
    doctor_name: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(...)
):
    if not current_user.customer:
        # Fallback redirect if no customer profile
        return RedirectResponse(url="/pelanggan/dashboard", status_code=302)
        
    upload_dir = "static/uploads/prescriptions"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = file.filename.split('.')[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(upload_dir, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    prescription = Prescription(
        customer_id=current_user.customer.id,
        doctor_name=doctor_name,
        file_url=f"/{file_path.replace(os.sep, '/')}",
        notes=notes,
        status="PENDING"
    )
    db.add(prescription)
    db.commit()
    
    return RedirectResponse(url="/pelanggan/dashboard", status_code=302)

@router.post("/api/v1/prescriptions/{id}/verify")
def verify_prescription(id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if prescription:
        prescription.status = "APPROVED"
        prescription.verified_by_id = current_user.id
        db.commit()
    return RedirectResponse(url="/apoteker/dashboard", status_code=302)
