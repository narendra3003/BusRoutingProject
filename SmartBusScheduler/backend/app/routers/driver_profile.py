"""
Docstring for SmartBusScheduler.backend.app.routers.driver_profile

GET /driver/profile
PUT /driver/profile
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Driver
from ..utils import get_current_user

router = APIRouter()


# =========================
# HELPER
# =========================
def format_profile(user: User, driver: Driver):
    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": driver.user.email,
        "phone": driver.user.phone,
        "role": user["role"],
        "driver_details": {
            "license_no": driver.license_no,
            "experience_years": driver.experience_years,
            "joining_date": driver.joining_date,
            "status": driver.status.value
        } if driver else None
    }

# =========================
# GET PROFILE
# =========================
@router.get("/")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Driver gets own profile
    Admin can also hit this but gets their own user (not driver unless exists)
    """

    driver = db.query(Driver).filter(
        Driver.user_id == current_user["user_id"]
    ).first()

    if current_user["role"] == "driver" and not driver:
        raise HTTPException(status_code=404, detail="Driver profile not found")

    return format_profile(current_user, driver)


# =========================
# UPDATE PROFILE
# =========================
@router.put("/")
def update_profile(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Driver can update:
    - name
    - phone
    """

    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    name = payload.get("name")
    phone = payload.get("phone")

    if name:
        current_user["name"] = name

    if phone:
        current_user["phone"] = phone

    db.commit()
    db.refresh(current_user)

    driver = db.query(Driver).filter(
        Driver.user_id == current_user["user_id"]
    ).first()

    return {
        "status": "updated",
        "profile": format_profile(current_user, driver)
    }


# =========================
# GET DRIVER PROFILE BY ID (ADMIN)
# =========================
@router.get("/{driver_id}")
def get_driver_by_id(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin can view any driver profile
    """

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admin allowed")

    user = db.query(User).filter(User.id == driver_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    driver = db.query(Driver).filter(
        Driver.user_id == driver_id
    ).first()

    return format_profile(user, driver)