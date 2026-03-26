"""
Docstring for SmartBusScheduler.backend.app.routers.admin_schedule

POST /admin/schedule/generate
GET  /admin/schedule/date/{date}
GET  /admin/schedule/route/{route_id}
PUT  /admin/schedule/{trip_id}
DELETE /admin/schedule/{trip_id}
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import date

from ..database import get_db
from ..models import (
    ScheduleTrip,
    Driver,
    Bus,
    Route,
    DriverLeave,
    LeaveStatus,
    TripStatus
)
from ..utils import get_current_user
from ..schemas import (
    TripCreate,
    BulkTripCreate,
    TripUpdate,
    TripResponse
)

router = APIRouter()


# =========================
# HELPER
# =========================
def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def format_trip(t: ScheduleTrip):
    return {
        "id": t.id,
        "route_id": t.route_id,
        "trip_date": t.trip_date,
        "start_time": t.start_time,
        "bus_id": t.bus_id,
        "driver_id": t.driver_id,
        "status": t.status.value
    }


# =========================
# VALIDATIONS
# =========================
def check_driver_available(db, driver_id, trip_date):
    conflict = db.query(ScheduleTrip).filter(
        ScheduleTrip.driver_id == driver_id,
        ScheduleTrip.trip_date == trip_date
    ).first()

    if conflict:
        raise HTTPException(400, "Driver already assigned for this date")


def check_bus_available(db, bus_id, trip_date):
    conflict = db.query(ScheduleTrip).filter(
        ScheduleTrip.bus_id == bus_id,
        ScheduleTrip.trip_date == trip_date
    ).first()

    if conflict:
        raise HTTPException(400, "Bus already assigned for this date")


def check_driver_leave(db, driver_id, trip_date):
    leave = db.query(DriverLeave).filter(
        DriverLeave.driver_id == driver_id,
        DriverLeave.status == LeaveStatus.granted,
        DriverLeave.start_date <= trip_date,
        DriverLeave.end_date >= trip_date
    ).first()

    if leave:
        raise HTTPException(400, "Driver is on leave")


# =========================
# CREATE TRIP
# =========================
@router.post("/", response_model=TripResponse)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    # validate entities
    if not db.query(Route).filter(Route.id == payload.route_id).first():
        raise HTTPException(404, "Route not found")

    if not db.query(Driver).filter(Driver.user_id == payload.driver_id).first():
        raise HTTPException(404, "Driver not found")

    if not db.query(Bus).filter(Bus.id == payload.bus_id).first():
        raise HTTPException(404, "Bus not found")

    # validations
    check_driver_available(db, payload.driver_id, payload.trip_date)
    check_bus_available(db, payload.bus_id, payload.trip_date)
    check_driver_leave(db, payload.driver_id, payload.trip_date)

    trip = ScheduleTrip(
        route_id=payload.route_id,
        trip_date=payload.trip_date,
        start_time=payload.start_time,
        bus_id=payload.bus_id,
        driver_id=payload.driver_id,
        status=TripStatus.scheduled
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return format_trip(trip)


# =========================
# BULK CREATE
# =========================
@router.post("/bulk")
def bulk_create(
    payload: BulkTripCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    created = []
    errors = []

    for idx, t in enumerate(payload.trips):
        try:
            check_driver_available(db, t.driver_id, t.trip_date)
            check_bus_available(db, t.bus_id, t.trip_date)
            check_driver_leave(db, t.driver_id, t.trip_date)

            trip = ScheduleTrip(**t.dict())
            db.add(trip)
            db.flush()

            created.append(format_trip(trip))

        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    db.commit()

    return {
        "created_count": len(created),
        "error_count": len(errors),
        "created": created,
        "errors": errors
    }


# =========================
# GET SCHEDULE
# =========================
@router.get("/", response_model=list[TripResponse])
def get_schedule(
    trip_date: date | None = Query(None),
    route_id: str | None = Query(None),
    driver_id: int | None = Query(None),
    bus_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    query = db.query(ScheduleTrip)

    if trip_date:
        query = query.filter(ScheduleTrip.trip_date == trip_date)

    if route_id:
        query = query.filter(ScheduleTrip.route_id == route_id)

    if driver_id:
        query = query.filter(ScheduleTrip.driver_id == driver_id)

    if bus_id:
        query = query.filter(ScheduleTrip.bus_id == bus_id)

    trips = query.order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return [format_trip(t) for t in trips]


# =========================
# UPDATE TRIP
# =========================
@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(404, "Trip not found")

    if payload.driver_id:
        check_driver_available(db, payload.driver_id, trip.trip_date)
        check_driver_leave(db, payload.driver_id, trip.trip_date)
        trip.driver_id = payload.driver_id

    if payload.bus_id:
        check_bus_available(db, payload.bus_id, trip.trip_date)
        trip.bus_id = payload.bus_id

    if payload.status:
        trip.status = TripStatus(payload.status)

    db.commit()
    db.refresh(trip)

    return format_trip(trip)


# =========================
# DELETE TRIP
# =========================
@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(404, "Trip not found")

    db.delete(trip)
    db.commit()

    return {
        "status": "deleted",
        "trip_id": trip_id
    }