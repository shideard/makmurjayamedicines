from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenPayload
from app.repositories.repositories import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = user_repo.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role or current_user.role.name != "Admin":
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_apoteker(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.role or current_user.role.name not in ["Admin", "Apoteker"]:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user
