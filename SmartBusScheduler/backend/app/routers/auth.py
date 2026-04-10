from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models import User
from ..schemas import SignUpRequest, AuthResponse
from ..utils import hash_password, verify_password, create_access_token, get_current_user
from ..database import get_db

router = APIRouter()

def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

# -----------------
# SIGN UP
# -----------------
@router.post("/signup", response_model=AuthResponse)
def signup(user: SignUpRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        pass_hash=hash_password(user.password),
        role=user.role,
        phone=user.phone if hasattr(user, "phone") else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({
        "user_id": new_user.id,        # ✅ User.id (not user_id)
        "role": new_user.role.value,   # ✅ .value for enum
        "name": new_user.name,
    })

    return AuthResponse(
        status="success",
        message="User created",
        access_token=token,
        token_type="bearer",
        role=new_user.role,
        name=new_user.name,
    )


# -----------------
# LOGIN
# -----------------
@router.post("/login", response_model=AuthResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.pass_hash):  # ✅ pass_hash
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token({
        "user_id": user.id,          # ✅ User.id
        "role": user.role.value,     # ✅ .value for enum
        "name": user.name,
    })

    return AuthResponse(
        status="success",
        message="Login successful",
        access_token=token,
        token_type="bearer",
        role=user.role,
        name=user.name,
    )


@router.get("/protected-route")
def protected(current_user: dict = Depends(get_current_user)):
    return {"message": "You are authenticated", "user": current_user}

@router.get("/users/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user