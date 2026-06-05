from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.repositories import medicine_repo, category_repo

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    return templates.TemplateResponse(
        request=request, name="base.html", context={"user": None}
    )

@router.get("/katalog", response_class=HTMLResponse)
def read_catalog(request: Request, db: Session = Depends(get_db)):
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

@router.get("/keranjang", response_class=HTMLResponse)
def read_cart(request: Request):
    return templates.TemplateResponse(
        request=request, name="keranjang.html", context={"user": None}
    )

@router.get("/checkout", response_class=HTMLResponse)
def read_checkout(request: Request):
    # Pass dummy user for demo purposes if not logged in real implementation
    dummy_user = {"name": "Budi Santoso", "email": "budi@example.com"}
    return templates.TemplateResponse(
        request=request, name="checkout.html", context={"user": dummy_user}
    )

@router.get("/admin/dashboard", response_class=HTMLResponse)
def read_admin_dashboard(request: Request):
    # Normally secured by Depends(get_current_admin)
    dummy_admin = {"name": "Admin Apotek", "role": {"name": "Admin"}}
    return templates.TemplateResponse(
        request=request, name="admin_dashboard.html", context={"user": dummy_admin}
    )
