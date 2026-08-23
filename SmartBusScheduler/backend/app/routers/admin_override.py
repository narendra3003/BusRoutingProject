"""
Docstring for SmartBusScheduler.backend.app.routers.admin_override

POST /admin/dispatch/override
GET  /admin/dispatch/trips
GET  /admin/dispatch/trip/{trip_id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import (
    Override,
    ScheduleTrip,
    Driver,
    Bus
)
from ..utils import get_current_user
from ..schemas import (
    OverrideCreate,
    OverrideResponse
)

router = APIRouter()


# =========================
# HELPER
# =========================
def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def format_override(o: Override):
    return {
        "id": o.id,
        "trip_id": o.trip_id,
        "old_driver_id": o.old_driver_id,
        "new_driver_id": o.new_driver_id,
        "old_bus_id": o.old_bus_id,
        "new_bus_id": o.new_bus_id,
        "reason": o.reason,
        "created_by": o.created_by,
        "created_at": o.created_at
    }


# =========================
# CREATE OVERRIDE
# =========================
@router.post("/", response_model=OverrideResponse)
def create_override(
    payload: OverrideCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    # 1️⃣ Get trip
    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == payload.trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not payload.new_driver_id and not payload.new_bus_id:
        raise HTTPException(
            status_code=400,
            detail="Provide at least new_driver_id or new_bus_id"
        )

    # 2️⃣ Validate new driver
    if payload.new_driver_id:
        driver = db.query(Driver).filter(
            Driver.user_id == payload.new_driver_id
        ).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")

    # 3️⃣ Validate new bus
    if payload.new_bus_id:
        bus = db.query(Bus).filter(
            Bus.id == payload.new_bus_id
        ).first()
        if not bus:
            raise HTTPException(status_code=404, detail="Bus not found")

    # 4️⃣ Create override record
    override = Override(
        trip_id=trip.id,

        old_driver_id=trip.driver_id,
        new_driver_id=payload.new_driver_id or trip.driver_id,

        old_bus_id=trip.bus_id,
        new_bus_id=payload.new_bus_id or trip.bus_id,

        reason=payload.reason,
        created_by=current_user["user_id"]
    )

    db.add(override)

    # 5️⃣ APPLY CHANGE TO TRIP
    if payload.new_driver_id:
        trip.driver_id = payload.new_driver_id

    if payload.new_bus_id:
        trip.bus_id = payload.new_bus_id

    db.commit()
    db.refresh(override)

    return format_override(override)


# =========================
# GET ALL OVERRIDES
# =========================
@router.get("/", response_model=list[OverrideResponse])
def get_overrides(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    overrides = db.query(Override).order_by(
        Override.created_at.desc()
    ).all()

    return [format_override(o) for o in overrides]


# =========================
# GET OVERRIDE BY ID
# =========================
@router.get("/{override_id}", response_model=OverrideResponse)
def get_override(
    override_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    override = db.query(Override).filter(
        Override.id == override_id
    ).first()

    if not override:
        raise HTTPException(status_code=404, detail="Override not found")

    return format_override(override)


# =========================
# DELETE OVERRIDE (OPTIONAL)
# =========================
@router.delete("/{override_id}")
def delete_override(
    override_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    override = db.query(Override).filter(
        Override.id == override_id
    ).first()

    if not override:
        raise HTTPException(status_code=404, detail="Override not found")

    db.delete(override)
    db.commit()

    return {
        "status": "deleted",
        "override_id": override_id
    }