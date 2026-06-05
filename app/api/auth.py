from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.models import User, Role
from app.schemas.schemas import Token, UserCreate, UserResponse
from app.repositories.repositories import user_repo, role_repo

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = user_repo.get_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserResponse)
def register_user(
    *, db: Session = Depends(get_db), user_in: UserCreate
):
    user = user_repo.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    
    # Assign default role if none provided
    role_id = user_in.role_id
    if not role_id:
        customer_role = role_repo.get_by_name(db, "Customer")
        if not customer_role:
            # Create Customer role if it doesn't exist
            customer_role = Role(name="Customer")
            db.add(customer_role)
            db.commit()
            db.refresh(customer_role)
        role_id = customer_role.id

    new_user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        role_id=role_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
