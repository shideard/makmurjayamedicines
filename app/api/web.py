from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api import deps
from app.repositories.repositories import medicine_repo, category_repo
from app.models.models import Prescription, InventoryBatch, Order, Payment, AuditLog
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid, os, shutil, re
from fastapi import File, UploadFile, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List
from app.models.models import OrderItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def write_audit(db: Session, user_id: str, action: str, entity: str = None, entity_id: str = None, details: str = None, ip: str = None):
    log = AuditLog(user_id=user_id, action=action, entity=entity, entity_id=entity_id, details=details, ip_address=ip)
    db.add(log)
    db.commit()


# ─────────── PUBLIC / SHARED ───────────

@router.get("/", response_class=HTMLResponse)
def read_home(request: Request, current_user = Depends(deps.get_current_user)):
    if current_user and current_user.role:
        role_name = current_user.role.name
        if role_name == "Admin":
            return RedirectResponse(url="/admin/dashboard", status_code=302)
        elif role_name == "Apoteker":
            return RedirectResponse(url="/apoteker/dashboard", status_code=302)
        elif role_name == "Kasir":
            return RedirectResponse(url="/kasir/dashboard", status_code=302)
        elif role_name in ["Pelanggan", "Customer"]:
            return RedirectResponse(url="/pelanggan/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="index.html", context={"user": current_user})


@router.get("/katalog", response_class=HTMLResponse)
def read_catalog(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(deps.get_current_user),
    search: str = "",
    category: str = "",
    sort: str = ""
):
    from app.models.models import Medicine, Category
    query = db.query(Medicine)
    if search:
        query = query.filter(Medicine.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Medicine.category_id == category)
    if sort == "price_asc":
        query = query.order_by(Medicine.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Medicine.price.desc())
    else:
        query = query.order_by(Medicine.name.asc())
    medicines = query.limit(100).all()
    categories = db.query(Category).order_by(Category.name).all()
    medicines_with_stock = []
    for med in medicines:
        total_stock = sum([b.quantity for b in med.batches if b.expiry_date > datetime.utcnow()])
        med_dict = med.__dict__.copy()
        med_dict["stock"] = total_stock
        medicines_with_stock.append(med_dict)
    return templates.TemplateResponse(
        request=request, name="katalog.html",
        context={
            "user": current_user,
            "medicines": medicines_with_stock,
            "categories": categories,
            "search": search,
            "selected_category": category,
            "sort": sort
        }
    )


@router.get("/obat/{slug}", response_class=HTMLResponse)
def read_medicine_detail(slug: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_user)):
    medicine = medicine_repo.get_by_slug(db, slug=slug)
    if not medicine:
        return HTMLResponse(content="Obat tidak ditemukan", status_code=404)
    total_stock = sum([b.quantity for b in medicine.batches if b.expiry_date > datetime.utcnow()])
    medicine_dict = medicine.__dict__.copy()
    medicine_dict["stock"] = total_stock
    return templates.TemplateResponse(request=request, name="detail_obat.html",
        context={"user": current_user, "medicine": medicine_dict})


@router.get("/keranjang", response_class=HTMLResponse)
def read_cart(request: Request, current_user = Depends(deps.get_current_user)):
    return templates.TemplateResponse(request=request, name="keranjang.html", context={"user": current_user})


@router.get("/checkout", response_class=HTMLResponse)
def read_checkout(request: Request, current_user = Depends(deps.get_current_user)):
    return templates.TemplateResponse(request=request, name="checkout.html", context={"user": current_user})


@router.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    csrf_token = str(uuid.uuid4())
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None, "csrf_token": csrf_token})


@router.get("/register", response_class=HTMLResponse)
def read_register(request: Request):
    csrf_token = str(uuid.uuid4())
    request.session["csrf_token"] = csrf_token
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None, "csrf_token": csrf_token})


# ─────────── ADMIN DASHBOARD ───────────

@router.get("/admin/dashboard", response_class=HTMLResponse)
def read_admin_dashboard(request: Request, current_user = Depends(deps.get_current_admin)):
    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={"user": current_user})


# ─────────── ADMIN: MANAJEMEN OBAT ───────────

@router.get("/admin/obat", response_class=HTMLResponse)
def read_admin_obat(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Medicine
    medicines = db.query(Medicine).order_by(Medicine.name).all()
    medicines_with_stock = []
    for med in medicines:
        total_stock = sum([b.quantity for b in med.batches if b.expiry_date > datetime.utcnow()])
        medicines_with_stock.append({"med": med, "stock": total_stock})
    return templates.TemplateResponse(request=request, name="admin_manajemen_obat.html",
        context={"user": current_user, "medicines": medicines_with_stock})


@router.get("/admin/tambah-obat", response_class=HTMLResponse)
def read_tambah_obat(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    categories = category_repo.get_multi(db)
    return templates.TemplateResponse(request=request, name="tambah_obat.html",
        context={"user": current_user, "categories": categories})


@router.post("/admin/tambah-obat")
def process_tambah_obat(
    request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin),
    name: str = Form(...), category_id: str = Form(...), price: float = Form(...),
    description: str = Form(""), composition: str = Form(""), dosage: str = Form(""),
    side_effects: str = Form(""), stock: int = Form(...), expiry_date: str = Form(""),
    file: UploadFile = File(None)
):
    from app.models.models import Medicine, InventoryBatch
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    existing = db.query(Medicine).filter(Medicine.slug == slug).first()
    if existing:
        slug = f"{slug}-{str(uuid.uuid4())[:4]}"
    file_url = None
    if file and file.filename:
        upload_dir = "app/static/uploads/medicines"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = file.filename.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        with open(os.path.join(upload_dir, file_name), "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        file_url = f"/static/uploads/medicines/{file_name}"
    new_med = Medicine(name=name, slug=slug, description=description, composition=composition,
                       dosage=dosage, side_effects=side_effects, price=price, image_url=file_url, category_id=category_id)
    db.add(new_med)
    db.commit()
    db.refresh(new_med)
    if stock > 0:
        try:
            exp_dt = datetime.strptime(expiry_date, "%Y-%m-%d") if expiry_date else datetime.utcnow() + timedelta(days=730)
        except:
            exp_dt = datetime.utcnow() + timedelta(days=730)
        db.add(InventoryBatch(medicine_id=new_med.id,
                              batch_number=f"BATCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                              quantity=stock, expiry_date=exp_dt))
        db.commit()
    write_audit(db, current_user.id, "TAMBAH_OBAT", "Medicine", new_med.id, f"Tambah obat: {name}")
    return RedirectResponse(url="/admin/obat", status_code=302)


@router.get("/admin/edit-obat/{medicine_id}", response_class=HTMLResponse)
def read_edit_obat(medicine_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Medicine
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        return RedirectResponse(url="/admin/obat", status_code=302)
    return templates.TemplateResponse(request=request, name="admin_edit_obat.html",
        context={"user": current_user, "medicine": medicine, "categories": category_repo.get_multi(db)})


@router.post("/admin/edit-obat/{medicine_id}")
def process_edit_obat(
    medicine_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin),
    name: str = Form(...), category_id: str = Form(...), price: float = Form(...),
    description: str = Form(""), composition: str = Form(""), dosage: str = Form(""),
    side_effects: str = Form(""), file: UploadFile = File(None)
):
    from app.models.models import Medicine
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        return RedirectResponse(url="/admin/obat", status_code=302)
    med.name = name
    med.price = price
    med.description = description
    med.composition = composition
    med.dosage = dosage
    med.side_effects = side_effects
    med.category_id = category_id
    if file and file.filename:
        upload_dir = "app/static/uploads/medicines"
        os.makedirs(upload_dir, exist_ok=True)
        file_ext = file.filename.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        with open(os.path.join(upload_dir, file_name), "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        med.image_url = f"/static/uploads/medicines/{file_name}"
    db.commit()
    write_audit(db, current_user.id, "EDIT_OBAT", "Medicine", medicine_id, f"Edit obat: {name}")
    return RedirectResponse(url="/admin/obat", status_code=302)


@router.post("/admin/hapus-obat/{medicine_id}")
def process_hapus_obat(medicine_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Medicine
    db.query(InventoryBatch).filter(InventoryBatch.medicine_id == medicine_id).delete()
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if med:
        write_audit(db, current_user.id, "HAPUS_OBAT", "Medicine", medicine_id, f"Hapus obat: {med.name}")
        db.delete(med)
        db.commit()
    return RedirectResponse(url="/admin/obat", status_code=302)


# ─────────── ADMIN: MANAJEMEN KATEGORI ───────────

@router.get("/admin/kategori", response_class=HTMLResponse)
def read_admin_kategori(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Category
    categories = db.query(Category).order_by(Category.name).all()
    return templates.TemplateResponse(request=request, name="admin_manajemen_kategori.html",
        context={"user": current_user, "categories": categories})


@router.get("/admin/tambah-kategori", response_class=HTMLResponse)
def read_tambah_kategori(request: Request, current_user = Depends(deps.get_current_admin)):
    return templates.TemplateResponse(request=request, name="tambah_kategori.html", context={"user": current_user})


@router.post("/admin/tambah-kategori")
def process_tambah_kategori(
    request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin),
    name: str = Form(...), description: str = Form("")
):
    from app.models.models import Category
    db.add(Category(name=name, description=description))
    db.commit()
    write_audit(db, current_user.id, "TAMBAH_KATEGORI", "Category", details=f"Tambah kategori: {name}")
    return RedirectResponse(url="/admin/kategori", status_code=302)


@router.get("/admin/edit-kategori/{category_id}", response_class=HTMLResponse)
def read_edit_kategori(category_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Category
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        return RedirectResponse(url="/admin/kategori", status_code=302)
    return templates.TemplateResponse(request=request, name="admin_edit_kategori.html",
        context={"user": current_user, "category": cat})


@router.post("/admin/edit-kategori/{category_id}")
def process_edit_kategori(
    category_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin),
    name: str = Form(...), description: str = Form("")
):
    from app.models.models import Category
    cat = db.query(Category).filter(Category.id == category_id).first()
    if cat:
        cat.name = name
        cat.description = description
        db.commit()
        write_audit(db, current_user.id, "EDIT_KATEGORI", "Category", category_id, f"Edit kategori: {name}")
    return RedirectResponse(url="/admin/kategori", status_code=302)


@router.post("/admin/hapus-kategori/{category_id}")
def process_hapus_kategori(category_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    from app.models.models import Category
    cat = db.query(Category).filter(Category.id == category_id).first()
    if cat:
        write_audit(db, current_user.id, "HAPUS_KATEGORI", "Category", category_id, f"Hapus kategori: {cat.name}")
        db.delete(cat)
        db.commit()
    return RedirectResponse(url="/admin/kategori", status_code=302)


# ─────────── ADMIN: AUDIT LOG ───────────

@router.get("/admin/audit-log", response_class=HTMLResponse)
def read_audit_log(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_admin)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200).all()
    return templates.TemplateResponse(request=request, name="admin_audit_log.html",
        context={"user": current_user, "logs": logs})


# ─────────── APOTEKER ───────────

@router.get("/apoteker/dashboard", response_class=HTMLResponse)
def read_apoteker_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    pending_prescriptions = db.query(Prescription).filter(Prescription.status == "PENDING").all()
    three_months = datetime.utcnow() + timedelta(days=90)
    low_stock_count = db.query(InventoryBatch).filter(InventoryBatch.quantity < 10).count()
    expiring_count = db.query(InventoryBatch).filter(
        InventoryBatch.expiry_date <= three_months,
        InventoryBatch.expiry_date > datetime.utcnow()
    ).count()
    return templates.TemplateResponse(request=request, name="apoteker_dashboard.html",
        context={"user": current_user, "pending_prescriptions": pending_prescriptions,
                 "low_stock_count": low_stock_count, "expiring_count": expiring_count})


@router.get("/apoteker/stok-alert", response_class=HTMLResponse)
def read_apoteker_stok_alert(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    three_months = datetime.utcnow() + timedelta(days=90)
    low_stock_batches = db.query(InventoryBatch).filter(InventoryBatch.quantity < 10).all()
    expiring_batches = db.query(InventoryBatch).filter(
        InventoryBatch.expiry_date <= three_months,
        InventoryBatch.expiry_date > datetime.utcnow()
    ).all()
    return templates.TemplateResponse(request=request, name="apoteker_stok.html",
        context={"user": current_user, "low_stock_batches": low_stock_batches,
                 "expiring_batches": expiring_batches, "now": datetime.utcnow()})


@router.post("/api/v1/prescriptions/{id}/verify")
def verify_prescription(id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    rx = db.query(Prescription).filter(Prescription.id == id).first()
    if rx:
        rx.status = "APPROVED"
        rx.verified_by_id = current_user.id
        db.commit()
        write_audit(db, current_user.id, "VERIFIKASI_RESEP", "Prescription", id, f"Disetujui: dr. {rx.doctor_name}")
    return RedirectResponse(url="/apoteker/dashboard", status_code=302)


@router.post("/api/v1/prescriptions/{id}/reject")
def reject_prescription(id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_apoteker)):
    rx = db.query(Prescription).filter(Prescription.id == id).first()
    if rx:
        rx.status = "REJECTED"
        rx.verified_by_id = current_user.id
        db.commit()
        write_audit(db, current_user.id, "TOLAK_RESEP", "Prescription", id, f"Ditolak: dr. {rx.doctor_name}")
    return RedirectResponse(url="/apoteker/dashboard", status_code=302)


# ─────────── KASIR ───────────

@router.get("/kasir/dashboard", response_class=HTMLResponse)
def read_kasir_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_kasir)):
    today = datetime.utcnow().date()
    today_income = db.query(func.sum(Order.grand_total)).filter(
        Order.status == "COMPLETED", func.date(Order.created_at) == today).scalar() or 0.0
    total_transactions = db.query(Order).filter(func.date(Order.created_at) == today).count()
    pending_orders = db.query(Order).filter(Order.status == "PENDING").all()
    ready_orders = db.query(Order).filter(Order.status == "PROCESSING").count()
    return templates.TemplateResponse(request=request, name="kasir_dashboard.html",
        context={"user": current_user, "today_income": today_income,
                 "total_transactions": total_transactions, "pending_orders": pending_orders, "ready_count": ready_orders})


@router.post("/kasir/proses/{order_id}")
def process_order(order_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_kasir)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.status == "PENDING":
        order.status = "COMPLETED"
        if order.payment:
            order.payment.status = "VERIFIED"
            order.payment.verified_by_id = current_user.id
        db.commit()
        write_audit(db, current_user.id, "PROSES_PEMBAYARAN", "Order", order_id, f"Invoice {order.invoice_number} diverifikasi")
    return RedirectResponse(url="/kasir/dashboard", status_code=302)


@router.get("/kasir/pesanan/{order_id}", response_class=HTMLResponse)
def read_kasir_pesanan_detail(order_id: str, request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_kasir)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return RedirectResponse(url="/kasir/dashboard", status_code=302)
    return templates.TemplateResponse(request=request, name="kasir_detail_pesanan.html",
        context={"user": current_user, "order": order})


# ─────────── PELANGGAN ───────────

@router.get("/pelanggan/dashboard", response_class=HTMLResponse)
def read_pelanggan_dashboard(request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_pelanggan)):
    orders = []
    processing_count = 0
    completed_count = 0
    if current_user.customer:
        orders = db.query(Order).filter(Order.customer_id == current_user.customer.id).order_by(Order.created_at.desc()).all()
        processing_count = sum(1 for o in orders if o.status in ["PENDING", "PROCESSING"])
        completed_count = sum(1 for o in orders if o.status in ["COMPLETED", "CANCELLED"])
    return templates.TemplateResponse(request=request, name="pelanggan_dashboard.html",
        context={
            "user": current_user, "orders": orders,
            "processing_count": processing_count, "completed_count": completed_count,
            "prescriptions": db.query(Prescription).filter(
                Prescription.customer_id == current_user.customer.id).order_by(
                Prescription.created_at.desc()).all() if current_user.customer else []
        })


@router.get("/unggah-resep", response_class=HTMLResponse)
def read_unggah_resep(request: Request, current_user = Depends(deps.get_current_pelanggan)):
    return templates.TemplateResponse(request=request, name="unggah_resep.html", context={"user": current_user})


@router.post("/unggah-resep")
def process_unggah_resep(
    request: Request, db: Session = Depends(get_db), current_user = Depends(deps.get_current_pelanggan),
    doctor_name: str = Form(...), notes: str = Form(""), file: UploadFile = File(...)
):
    if not current_user.customer:
        from app.models.models import Customer
        new_customer = Customer(user_id=current_user.id)
        db.add(new_customer)
        db.commit()
        db.refresh(current_user)
    upload_dir = "app/static/uploads/prescriptions"
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = file.filename.split('.')[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    with open(os.path.join(upload_dir, file_name), "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    rx = Prescription(customer_id=current_user.customer.id, doctor_name=doctor_name,
                      file_url=f"/static/uploads/prescriptions/{file_name}", notes=notes, status="PENDING")
    db.add(rx)
    db.commit()
    write_audit(db, current_user.id, "UNGGAH_RESEP", "Prescription", rx.id, f"Resep dr. {doctor_name}")
    return RedirectResponse(url="/pelanggan/dashboard", status_code=302)


# ─────────── CHECKOUT API ───────────

class CheckoutItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int


class CheckoutRequest(BaseModel):
    items: List[CheckoutItem]
    payment_method: str


@router.post("/api/v1/checkout")
def process_checkout(payload: CheckoutRequest, db: Session = Depends(get_db), current_user = Depends(deps.get_current_pelanggan)):
    if not current_user.customer:
        from app.models.models import Customer
        db.add(Customer(user_id=current_user.id))
        db.commit()
        db.refresh(current_user)
    subtotal = sum(item.price * item.quantity for item in payload.items)
    tax = subtotal * 0.11
    grand_total = subtotal + tax
    new_order = Order(
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        customer_id=current_user.customer.id, status="PENDING",
        total=subtotal, tax=tax, grand_total=grand_total
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    for item in payload.items:
        db.add(OrderItem(order_id=new_order.id, medicine_id=item.id, quantity=item.quantity, price=item.price))
        batch = db.query(InventoryBatch).filter(InventoryBatch.medicine_id == item.id, InventoryBatch.quantity > 0).first()
        if batch:
            batch.quantity = max(0, batch.quantity - item.quantity)
    db.commit()
    db.add(Payment(order_id=new_order.id, amount=grand_total, method=payload.payment_method, status="PENDING"))
    db.commit()
    write_audit(db, current_user.id, "CHECKOUT", "Order", new_order.id, f"{new_order.invoice_number} Rp {grand_total:,.0f}")
    return {"status": "success", "order_id": new_order.id}
