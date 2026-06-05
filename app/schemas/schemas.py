from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# User
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Minimal 8 karakter, ada huruf besar, huruf kecil, dan angka.")
    role_id: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(char.isupper() for char in v):
            raise ValueError('Password harus memiliki minimal satu huruf besar')
        if not any(char.islower() for char in v):
            raise ValueError('Password harus memiliki minimal satu huruf kecil')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password harus memiliki minimal satu angka')
        return v

class UserResponse(UserBase):
    id: str
    role_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Medicine
class MedicineBase(BaseModel):
    name: str
    slug: str
    price: float
    description: Optional[str] = None
    category_id: str
    supplier_id: Optional[str] = None

class MedicineCreate(MedicineBase):
    pass

class MedicineResponse(MedicineBase):
    id: str
    class Config:
        from_attributes = True

# Checkout / Order
class CartItem(BaseModel):
    id: str # medicine_id
    quantity: int
    name: Optional[str] = None

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    payment_method: str # BANK_TRANSFER, E_WALLET, CASH
