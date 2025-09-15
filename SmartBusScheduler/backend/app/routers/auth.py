# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta

from ..database import get_db
from ..models import User
from ..schemas import SignUpRequest, LoginRequest, AuthResponse, UserInfoResponse
from ..utils.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from ..utils.dependencies import get_token_from_cookie

router = APIRouter()

# Cookie settings
ACCESS_COOKIE_NAME = "token"
REFRESH_COOKIE_NAME = "refresh_token"
ACCESS_EXPIRE_MINUTES = 15
REFRESH_EXPIRE_MINUTES = 60*24*7  # 7 days

# -----------------
# SIGNUP
# -----------------
@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            print(f"Error 400: Email already registered")
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password), role=payload.role)
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token(subject=str(user.user_id), extra_claims={"role": user.role, "username": user.name}, expires_delta=timedelta(minutes=ACCESS_EXPIRE_MINUTES))
        refresh_token = create_refresh_token(subject=str(user.user_id), expires_delta=timedelta(minutes=REFRESH_EXPIRE_MINUTES))

        resp = Response()
        resp.set_cookie(ACCESS_COOKIE_NAME, access_token, httponly=True, secure=False, samesite="lax", max_age=ACCESS_EXPIRE_MINUTES*60)
        resp.set_cookie(REFRESH_COOKIE_NAME, refresh_token, httponly=True, secure=False, samesite="lax", max_age=REFRESH_EXPIRE_MINUTES*60)
        resp.status_code = status.HTTP_201_CREATED
        resp.media_type = "application/json"
        resp.body = b''

        return {"status": "success", "message": "User created", "user_id": user.user_id, "username": user.name, "role": user.role}
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        print(f"Error 500: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------
# LOGIN
# -----------------
@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.password_hash):
            print(f"Error 401: Invalid credentials")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(subject=str(user.user_id), extra_claims={"role": user.role, "username": user.name}, expires_delta=timedelta(minutes=ACCESS_EXPIRE_MINUTES))
        refresh_token = create_refresh_token(subject=str(user.user_id), expires_delta=timedelta(minutes=REFRESH_EXPIRE_MINUTES))
        response = JSONResponse(content={"msg": "Login successful"})
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=ACCESS_EXPIRE_MINUTES * 60,
            domain="localhost"   # 👈 important
        )
        print(f"Set refresh token cookie: {response.cookies.get(ACCESS_COOKIE_NAME)}")
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            httponly=True,
            samesite="lax",
            max_age=REFRESH_EXPIRE_MINUTES * 60,
        )
        return {"status": "success", "message": "Login successful", "user_id": user.user_id, "username": user.name, "role": user.role}
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        print(f"Error 500: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------
# CHECKME (get current user info from token)
# -----------------
@router.get("/me", response_model=UserInfoResponse)
def me(token: str = Depends(get_token_from_cookie)):
    try:
        payload = decode_token(token)
        if not payload:
            print(f"Error 401: Invalid or expired token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        return UserInfoResponse(user_id=int(payload["sub"]), username=payload.get("username"), role=payload.get("role"))
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        print(f"Error 500: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------
# REFRESH (use refresh cookie to issue new access token)
# -----------------
@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
        if not refresh_token:
            print(f"Error 401: No refresh token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            print(f"Error 401: Invalid refresh token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == int(user_id)).first()
        if not user:
            print(f"Error 404: User not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        access_token = create_access_token(subject=str(user.user_id), extra_claims={"role": user.role, "username": user.name})
        response.set_cookie(ACCESS_COOKIE_NAME, access_token, httponly=True, secure=False, samesite="lax", max_age=ACCESS_EXPIRE_MINUTES*60)
        return {"status": "success", "message": "Token refreshed", "user_id": user.user_id, "username": user.name, "role": user.role}
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
        raise
    except Exception as e:
        print(f"Error 500: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# -----------------
# LOGOUT (clear cookies)
# -----------------
@router.post("/logout", response_model=AuthResponse)
def logout(response: Response):
    try:
        response.delete_cookie(ACCESS_COOKIE_NAME)
        response.delete_cookie(REFRESH_COOKIE_NAME)
        return {"status": "success", "message": "Logged out"}
    except Exception as e:
        print(f"Error 500: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
