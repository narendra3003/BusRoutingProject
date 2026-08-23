"""
Docstring for SmartBusScheduler.backend.app.routers.driver_trips

GET /driver/trips/today
GET /driver/trips/date/{date}
GET /driver/trips/{trip_id}
GET /driver/calendar
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import date

from ..database import get_db
from ..models import (
    User,
    ScheduleTrip,
    Route,
    Bus,
    TripLiveStatus,
    TripStatus
)
from ..utils import get_current_user

router = APIRouter()


# =========================
# HELPER
# =========================
def format_trip(trip: ScheduleTrip):
    return {
        "trip_id": trip.id,
        "trip_date": trip.trip_date,
        "start_time": trip.start_time,
        "status": trip.status.value,
        "route": {
            "id": trip.route.id,
            "name": trip.route.name
        } if trip.route else None,
        "bus": {
            "id": trip.bus.id,
            "code": trip.bus.code
        } if trip.bus else None
    }


# =========================
# GET TODAY'S TRIPS
# =========================
@router.get("/today")
def get_today_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    today = date.today()

    trips = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(
        ScheduleTrip.driver_id == current_user["user_id"],
        ScheduleTrip.trip_date == today
    ).order_by(ScheduleTrip.start_time).all()

    return {
        "date": today,
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET ALL TRIPS (FILTERABLE)
# =========================
@router.get("/")
def get_driver_trips(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: TripStatus | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    query = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(ScheduleTrip.driver_id == current_user["user_id"])

    if start_date:
        query = query.filter(ScheduleTrip.trip_date >= start_date)

    if end_date:
        query = query.filter(ScheduleTrip.trip_date <= end_date)

    if status:
        query = query.filter(ScheduleTrip.status == status)

    trips = query.order_by(
        ScheduleTrip.trip_date,
        ScheduleTrip.start_time
    ).all()

    return {
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET SINGLE TRIP DETAILS
# =========================
@router.get("/{trip_id}")
def get_trip_details(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    return format_trip(trip)


# =========================
# UPDATE TRIP STATUS
# =========================
@router.put("/{trip_id}/status")
def update_trip_status(
    trip_id: int,
    status: TripStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    # Optional: enforce flow
    allowed_transitions = {
        "scheduled": ["delayed", "completed"],
        "delayed": ["completed"],
        "completed": []
    }

    if status.value not in allowed_transitions[trip.status.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from {trip.status.value} to {status.value}"
        )

    trip.status = status
    db.commit()

    return {
        "status": "updated",
        "trip_id": trip_id,
        "new_status": status.value
    }


# =========================
# GET LIVE STATUS
# =========================
@router.get("/{trip_id}/live")
def get_live_status(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    live = db.query(TripLiveStatus).filter(
        TripLiveStatus.trip_id == trip_id
    ).first()

    if not live:
        return {"message": "No live data available"}

    return {
        "trip_id": trip_id,
        "delay_minutes": live.delay_minutes,
        "current_stop_id": live.current_stop_id,
        "last_location": {
            "lat": live.last_lat,
            "lon": live.last_lon
        },
        "last_updated": live.last_updated
    }


# =========================
# START TRIP (OPTIONAL)
# =========================
@router.post("/{trip_id}/start")
def start_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    if trip.status != TripStatus.scheduled:
        raise HTTPException(status_code=400, detail="Trip already started or completed")

    trip.status = TripStatus.delayed  # or "in_progress" if you add new enum
    db.commit()

    return {
        "status": "started",
        "trip_id": trip_id
    }