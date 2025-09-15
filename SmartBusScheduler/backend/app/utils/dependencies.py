# utils/deps.py
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .security import decode_token
from ..database import get_db
from ..models import User  # your SQLAlchemy model
from ..schemas import UserInfoResponse  # will show schema below

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Lightweight: decode token claims and return simple user info dict (no DB hit)
def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> UserInfoResponse:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    role = payload.get("role")
    username = payload.get("username")
    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    return UserInfoResponse(user_id=int(user_id), username=username, role=role)


# Stronger option: fetch user from DB (use this if you want to ensure role hasn't changed)
def get_current_user_db(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(User).filter(User.user_id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# Role-hierarchy helper
ROLE_HIERARCHY = {
    "admin": 3,
    "driver": 2,
    "customer": 1
}

def role_allowed(required_role: str):
    """
    Dependency factory: ensures current user role >= required_role in hierarchy.
    Example usage:
        @router.get("/admin-only")
        def admin_only(user: UserInfoResponse = Depends(get_current_user_from_token_from_token), _: None = Depends(role_allowed("admin"))):
            ...
    """
    def _checker(user: UserInfoResponse = Depends(get_current_user_from_token)):
        user_level = ROLE_HIERARCHY.get(user.role, 0)
        req_level = ROLE_HIERARCHY.get(required_role, 0)
        if user_level < req_level:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return True
    return _checker

# create get_token_from_cookie
def get_token_from_cookie(request: Request) -> Optional[str]:
    token = request.cookies.get("token")
    print(f"Token from cookie: {token}")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token