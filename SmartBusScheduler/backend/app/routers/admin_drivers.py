"""Admin drivers management

Endpoints:
- POST /admin/drivers
- GET  /admin/drivers
- GET  /admin/drivers/{id}
- PUT  /admin/drivers/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import User, Driver, UserRole, DriverStatus
from ..utils import get_current_user, hash_password
from ..schemas import (
    DriverCreate,
    DriverUpdate,
    DriverResponse
)

router = APIRouter()


# =========================
# HELPER
# =========================
def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def format_driver(user: User, driver: Driver):
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "license_no": driver.license_no,
        "experience_years": driver.experience_years,
        "joining_date": driver.joining_date,
        "status": driver.status.value
    }


# =========================
# CREATE DRIVER
# =========================
@router.post("/", response_model=DriverResponse)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    # check email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # check license
    existing_license = db.query(Driver).filter(
        Driver.license_no == payload.license_no
    ).first()
    if existing_license:
        raise HTTPException(status_code=400, detail="License already exists")

    # create user
    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        pass_hash=hash_password(payload.password or "password123"),
        role=UserRole.driver
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # create driver
    driver = Driver(
        user_id=user.id,
        license_no=payload.license_no,
        experience_years=payload.experience_years,
        joining_date=payload.joining_date,
        status=DriverStatus.active
    )
    db.add(driver)
    db.commit()

    return format_driver(user, driver)


# =========================
# GET ALL DRIVERS
# =========================
@router.get("/", response_model=list[DriverResponse])
def get_drivers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    drivers = db.query(Driver).options(
        joinedload(Driver.user)
    ).all()

    return [
        format_driver(d.user, d)
        for d in drivers
    ]


# =========================
# GET DRIVER BY ID
# =========================
@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    driver = db.query(Driver).options(
        joinedload(Driver.user)
    ).filter(Driver.user_id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    return format_driver(driver.user, driver)


# =========================
# UPDATE DRIVER
# =========================
@router.put("/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    payload: DriverUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    driver = db.query(Driver).options(
        joinedload(Driver.user)
    ).filter(Driver.user_id == driver_id).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    user = driver.user

    if payload.name:
        user.name = payload.name

    if payload.phone:
        user.phone = payload.phone

    if payload.experience_years is not None:
        driver.experience_years = payload.experience_years

    if payload.status:
        driver.status = DriverStatus(payload.status)

    db.commit()
    db.refresh(driver)

    return format_driver(user, driver)


# =========================
# DELETE DRIVER (SOFT)
# =========================
@router.delete("/{driver_id}")
def delete_driver(
    driver_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    driver = db.query(Driver).filter(
        Driver.user_id == driver_id
    ).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    # soft delete → deactivate
    driver.status = DriverStatus.inactive
    db.commit()

    return {
        "status": "deleted",
        "driver_id": driver_id
    }