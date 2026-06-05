from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenPayload
from app.repositories.repositories import user_repo

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_user(
    request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User | None:
    # Try token from header first
    if not token:
        # Fallback to cookie
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

    if not token:
        return None # Anonymous user for web pages

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except JWTError:
        return None

    user = user_repo.get(db, id=token_data.sub)
    return user

def require_current_user(current_user: User | None = Depends(get_current_user)) -> User:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return current_user

def get_current_admin(current_user: User = Depends(require_current_user)) -> User:
    if not current_user.role or current_user.role.name != "Admin":
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_apoteker(current_user: User = Depends(require_current_user)) -> User:
    if not current_user.role or current_user.role.name not in ["Admin", "Apoteker"]:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_kasir(current_user: User = Depends(require_current_user)) -> User:
    if not current_user.role or current_user.role.name not in ["Admin", "Kasir"]:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_pelanggan(current_user: User = Depends(require_current_user)) -> User:
    # Pelanggan can be just require_current_user, but we enforce it if needed.
    return current_user
