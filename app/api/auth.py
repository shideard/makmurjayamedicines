from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.models.models import User, Role, AuditLog
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
    
    # Audit log
    audit_log = AuditLog(user_id=user.id, action="LOGIN_API", ip_address="API")
    db.add(audit_log)
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

from fastapi import Response, Form, Request
from fastapi.responses import RedirectResponse

@router.post("/login-web")
def login_web(
    request: Request,
    response: Response,
    db: Session = Depends(get_db), 
    email: str = Form(...), 
    password: str = Form(...),
    csrf_token: str = Form(...)
):
    # Validate CSRF
    session_csrf = request.session.get("csrf_token")
    if not session_csrf or session_csrf != csrf_token:
        raise HTTPException(status_code=400, detail="Invalid CSRF token")

    user = user_repo.get_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        # In a real app we'd redirect back with an error flash message
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # Audit log
    audit_log = AuditLog(user_id=user.id, action="LOGIN_WEB")
    db.add(audit_log)
    db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.id, expires_delta=access_token_expires)
    
    # Redirect to home or dashboard based on role
    redirect_url = "/admin/dashboard" if user.role and user.role.name == "Admin" else "/"
    redirect_response = RedirectResponse(url=redirect_url, status_code=302)
    redirect_response.set_cookie(
        key="access_token", 
        value=f"Bearer {token}", 
        httponly=True, 
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    return redirect_response

@router.get("/logout")
def logout_web(db: Session = Depends(get_db)):
    redirect_response = RedirectResponse(url="/", status_code=302)
    redirect_response.delete_cookie("access_token")
    return redirect_response

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
