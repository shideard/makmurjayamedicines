from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.models import (
    User, Role, Customer, Category, Supplier, Medicine,
    InventoryBatch, Order, OrderItem, Payment
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

class CRUDInventoryBatch(CRUDBase[InventoryBatch]):
    pass

class CRUDOrder(CRUDBase[Order]):
    pass

class CRUDOrderItem(CRUDBase[OrderItem]):
    pass

class CRUDPayment(CRUDBase[Payment]):
    pass

class CRUDCustomer(CRUDBase[Customer]):
    def get_by_user_id(self, db: Session, user_id: str) -> Customer | None:
        return db.query(Customer).filter(Customer.user_id == user_id).first()

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
