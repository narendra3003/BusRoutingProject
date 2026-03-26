"""Admin CRUD for stops

Endpoints:
- POST   /admin/stops
- PUT    /admin/stops/{id}
- DELETE /admin/stops/{id}
- GET    /admin/stops
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import math

from ..database import get_db
from ..models import Stop, StopType
from ..utils import get_current_user
from ..schemas import (
    StopCreate,
    StopUpdate,
    StopResponse
)

router = APIRouter()


# =========================
# HELPER
# =========================
def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def format_stop(s: Stop):
    return {
        "id": s.id,
        "name": s.name,
        "lat": s.lat,
        "lon": s.lon,
        "type": s.type.value,
        "zone": s.zone,
        "is_active": s.is_active
    }


# =========================
# CREATE STOP
# =========================
@router.post("/", response_model=StopResponse)
def create_stop(
    payload: StopCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    stop = Stop(
        name=payload.name,
        lat=payload.lat,
        lon=payload.lon,
        type=StopType(payload.type),
        zone=payload.zone,
        is_active=True
    )

    db.add(stop)
    db.commit()
    db.refresh(stop)

    return format_stop(stop)


# =========================
# GET ALL STOPS
# =========================
@router.get("/", response_model=list[StopResponse])
def get_stops(
    is_active: bool | None = Query(None),
    zone: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    query = db.query(Stop)

    if is_active is not None:
        query = query.filter(Stop.is_active == is_active)

    if zone:
        query = query.filter(Stop.zone == zone)

    stops = query.order_by(Stop.id).all()

    return [format_stop(s) for s in stops]


# =========================
# GET SINGLE STOP
# =========================
@router.get("/{stop_id}", response_model=StopResponse)
def get_stop(
    stop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    stop = db.query(Stop).filter(Stop.id == stop_id).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    return format_stop(stop)


# =========================
# UPDATE STOP
# =========================
@router.put("/{stop_id}", response_model=StopResponse)
def update_stop(
    stop_id: int,
    payload: StopUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    stop = db.query(Stop).filter(Stop.id == stop_id).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    if payload.name:
        stop.name = payload.name

    if payload.lat is not None:
        stop.lat = payload.lat

    if payload.lon is not None:
        stop.lon = payload.lon

    if payload.type:
        stop.type = StopType(payload.type)

    if payload.zone is not None:
        stop.zone = payload.zone

    if payload.is_active is not None:
        stop.is_active = payload.is_active

    db.commit()
    db.refresh(stop)

    return format_stop(stop)


# =========================
# DELETE STOP (SOFT)
# =========================
@router.delete("/{stop_id}")
def delete_stop(
    stop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    stop = db.query(Stop).filter(Stop.id == stop_id).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # soft delete
    stop.is_active = False
    db.commit()

    return {
        "status": "deleted",
        "stop_id": stop_id
    }


# =========================
# NEARBY STOPS (ADMIN TOOL)
# =========================
@router.get("/nearby/search")
def nearby_stops(
    lat: float,
    lon: float,
    radius_km: float = 2.0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Find stops within radius (km)
    """

    check_admin(current_user)

    stops = db.query(Stop).filter(Stop.is_active == True).all()

    def distance(lat1, lon1, lat2, lon2):
        # Haversine formula
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2
        )

        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    result = []

    for s in stops:
        d = distance(lat, lon, s.lat, s.lon)
        if d <= radius_km:
            result.append({
                **format_stop(s),
                "distance_km": round(d, 3)
            })

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "count": len(result),
        "stops": sorted(result, key=lambda x: x["distance_km"])
    }