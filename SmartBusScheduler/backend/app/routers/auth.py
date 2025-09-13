from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..models import User
from ..schemas import SignUpRequest, LoginRequest, AuthResponse
from ..utils import hash_password, verify_password, create_access_token
from ..database import get_db  # your SQLAlchemy session dependency

router = APIRouter()

# -----------------
# SIGN UP
# -----------------
@router.post("/signup", response_model=AuthResponse)
def signup(user: SignUpRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token
    token = create_access_token({"user_id": new_user.user_id, "role": new_user.role})

    return AuthResponse(status="success", message="User created", access_token=token)


# -----------------
# LOGIN
# -----------------
@router.post("/login", response_model=AuthResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # check user
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # include role + user_id in token
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}
