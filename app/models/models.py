import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role_id = Column(String, ForeignKey("roles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")
    customer = relationship("Customer", back_populates="user", uselist=False)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    
    user = relationship("User", back_populates="customer")
    orders = relationship("Order", back_populates="customer")

class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    medicines = relationship("Medicine", back_populates="category")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    medicines = relationship("Medicine", back_populates="supplier")

class Medicine(Base):
    __tablename__ = "medicines"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True) # New field for image upload
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=True)
    
    category = relationship("Category", back_populates="medicines")
    supplier = relationship("Supplier", back_populates="medicines")
    batches = relationship("InventoryBatch", back_populates="medicine")
    order_items = relationship("OrderItem", back_populates="medicine")

class InventoryBatch(Base):
    __tablename__ = "inventory_batches"
    id = Column(String, primary_key=True, default=generate_uuid)
    medicine_id = Column(String, ForeignKey("medicines.id"), nullable=False)
    batch_number = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    medicine = relationship("Medicine", back_populates="batches")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    invoice_number = Column(String, unique=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, CANCELLED
    total = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    grand_total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payment = relationship("Payment", back_populates="order", uselist=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    medicine_id = Column(String, ForeignKey("medicines.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")
    medicine = relationship("Medicine", back_populates="order_items")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("orders.id"), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, nullable=False) # BANK_TRANSFER, E_WALLET, CASH
    status = Column(String, default="PENDING") # PENDING, VERIFIED, FAILED
    receipt_url = Column(String, nullable=True) # New field for payment proof upload
    verified_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="payment")
    verifier = relationship("User")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False) # e.g., "LOGIN", "CREATE_MEDICINE"
    entity = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class Prescription(Base):
    __tablename__ = "prescriptions"
    id = Column(String, primary_key=True, default=generate_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    doctor_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False) # Uploaded prescription image/pdf
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED
    notes = Column(Text, nullable=True)
    verified_by_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer")
    verifier = relationship("User")
