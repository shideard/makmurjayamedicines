from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.models import (
    User, Role, Customer, Category, Supplier, Medicine,
    InventoryBatch, Order, OrderItem, Payment, Prescription
)

class CRUDUser(CRUDBase[User]):
    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

class CRUDRole(CRUDBase[Role]):
    def get_by_name(self, db: Session, name: str) -> Role | None:
        return db.query(Role).filter(Role.name == name).first()

class CRUDCategory(CRUDBase[Category]):
    def get_by_name(self, db: Session, name: str) -> Category | None:
        return db.query(Category).filter(Category.name == name).first()

class CRUDSupplier(CRUDBase[Supplier]):
    pass

class CRUDMedicine(CRUDBase[Medicine]):
    def get_by_slug(self, db: Session, slug: str) -> Medicine | None:
        return db.query(Medicine).filter(Medicine.slug == slug).first()
        
    def fuzzy_search(self, db: Session, keyword: str) -> list[Medicine]:
        # Simple fuzzy search using LIKE
        return db.query(Medicine).filter(Medicine.name.ilike(f"%{keyword}%")).all()
        
    def get_best_sellers(self, db: Session, limit: int = 5) -> list[Medicine]:
        from sqlalchemy import func
        return db.query(Medicine)\
            .join(OrderItem)\
            .group_by(Medicine.id)\
            .order_by(func.sum(OrderItem.quantity).desc())\
            .limit(limit).all()

from datetime import datetime, timedelta
class CRUDInventoryBatch(CRUDBase[InventoryBatch]):
    def get_expiring_soon(self, db: Session, days: int = 90) -> list[InventoryBatch]:
        threshold = datetime.utcnow() + timedelta(days=days)
        return db.query(InventoryBatch)\
            .filter(InventoryBatch.expiry_date <= threshold, InventoryBatch.quantity > 0)\
            .order_by(InventoryBatch.expiry_date.asc())\
            .all()

class CRUDOrder(CRUDBase[Order]):
    pass

class CRUDOrderItem(CRUDBase[OrderItem]):
    pass

class CRUDPayment(CRUDBase[Payment]):
    pass

class CRUDCustomer(CRUDBase[Customer]):
    def get_by_user_id(self, db: Session, user_id: str) -> Customer | None:
        return db.query(Customer).filter(Customer.user_id == user_id).first()

class CRUDPrescription(CRUDBase[Prescription]):
    pass

user_repo = CRUDUser(User)
role_repo = CRUDRole(Role)
category_repo = CRUDCategory(Category)
supplier_repo = CRUDSupplier(Supplier)
medicine_repo = CRUDMedicine(Medicine)
batch_repo = CRUDInventoryBatch(InventoryBatch)
order_repo = CRUDOrder(Order)
order_item_repo = CRUDOrderItem(OrderItem)
payment_repo = CRUDPayment(Payment)
customer_repo = CRUDCustomer(Customer)
prescription_repo = CRUDPrescription(Prescription)
