from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.repositories.repositories import medicine_repo, category_repo

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
def read_apoteker_dashboard(request: Request, current_user = Depends(deps.get_current_apoteker)):
    return templates.TemplateResponse(
        request=request, name="apoteker_dashboard.html", context={"user": current_user}
    )

@router.get("/kasir/dashboard", response_class=HTMLResponse)
def read_kasir_dashboard(request: Request, current_user = Depends(deps.get_current_kasir)):
    return templates.TemplateResponse(
        request=request, name="kasir_dashboard.html", context={"user": current_user}
    )

@router.get("/pelanggan/dashboard", response_class=HTMLResponse)
def read_pelanggan_dashboard(request: Request, current_user = Depends(deps.get_current_pelanggan)):
    return templates.TemplateResponse(
        request=request, name="pelanggan_dashboard.html", context={"user": current_user}
    )
