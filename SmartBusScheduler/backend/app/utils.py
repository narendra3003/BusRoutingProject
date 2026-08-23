from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, OAuth2PasswordBearer, HTTPBearer
from jose import jwt, JWTError
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Secret key for JWT (use env variable in production)
SECRET_KEY = os.getenv("JWT_SECRET", "SecretKey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = HTTPBearer()  # Using HTTPBearer for token extraction from Authorization header

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify JWT & extract payload
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing credentials",
    )

    if credentials.scheme != "Bearer":
        raise credentials_exception

    token = credentials.credentials  # 🔥 actual JWT string

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        role = payload.get("role")
        name = payload.get("name")

        if user_id is None:
            raise credentials_exception

        return {
            "user_id": int(user_id),
            "role": role,
            "name": name
        }

    except JWTError:
        raise credentials_exception
