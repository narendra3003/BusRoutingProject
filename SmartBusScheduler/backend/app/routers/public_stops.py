"""Public stops endpoints

Endpoints:
- GET /stops
- GET /stops/{stop_id}
- GET /stops/nearby?lat=&lon=
- GET /stops/{stop_id}/routes
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Stop, RouteStop, Route
from ..schemas import StopResponse, RouteResponse

router = APIRouter()


@router.get("/", response_model=List[StopResponse])
def list_stops(zone: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Stop)
    if zone:
        q = q.filter(Stop.zone == zone)
    stops = q.order_by(Stop.id).all()
    return [
        StopResponse(
            id=s.id,
            name=s.name,
            lat=s.lat,
            lon=s.lon,
            type=s.type.value if s.type else None,
            zone=s.zone,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in stops
    ]


@router.get("/{stop_id}", response_model=StopResponse)
def get_stop(stop_id: int, db: Session = Depends(get_db)):
    s = db.query(Stop).filter(Stop.id == stop_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Stop not found")
    return StopResponse(
        id=s.id,
        name=s.name,
        lat=s.lat,
        lon=s.lon,
        type=s.type.value if s.type else None,
        zone=s.zone,
        is_active=s.is_active,
        created_at=s.created_at,
    )


@router.get("/nearby", response_model=List[StopResponse])
def nearby_stops(lat: float = Query(...), lon: float = Query(...), radius_km: float = Query(1.0), db: Session = Depends(get_db)):
    # very simple distance approximation using Pythagoras on lat/lon (acceptable for small radii)
    factor = 111  # approx km per degree
    max_delta = radius_km / factor

    stops = (
        db.query(Stop)
        .filter(Stop.lat.between(lat - max_delta, lat + max_delta))
        .filter(Stop.lon.between(lon - max_delta, lon + max_delta))
        .all()
    )

    return [
        StopResponse(
            id=s.id,
            name=s.name,
            lat=s.lat,
            lon=s.lon,
            type=s.type.value if s.type else None,
            zone=s.zone,
            is_active=s.is_active,
            created_at=s.created_at,
        )
        for s in stops
    ]


@router.get("/{stop_id}/routes", response_model=List[RouteResponse])
def stop_routes(stop_id: int, db: Session = Depends(get_db)):
    rs = db.query(RouteStop.route_id).filter(RouteStop.stop_id == stop_id).distinct().all()
    route_ids = [r[0] for r in rs]
    routes = db.query(Route).filter(Route.id.in_(route_ids)).all()

    return [
        RouteResponse(
            id=r.id,
            name=r.name,
            start_stop_id=r.start_stop_id,
            end_stop_id=r.end_stop_id,
            distance_km=r.distance_km,
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in routes
    ]


# Summary:
# - Implemented public stops endpoints with typed responses using `StopResponse` and `RouteResponse`.
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from math import radians, cos, sin, asin, sqrt

from ..database import get_db
from ..models import Stop, RouteStop, Route

router = APIRouter()


# =========================
# HELPER: HAVERSINE DISTANCE
# =========================
def haversine(lat1, lon1, lat2, lon2):
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    r = 6371  # Radius of earth in km
    return c * r


# =========================
# GET ALL STOPS
# =========================
@router.get("/")
def get_stops(db: Session = Depends(get_db)):

    stops = db.query(Stop).filter(Stop.is_active == True).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "lat": s.lat,
            "lon": s.lon,
            "type": s.type.value if s.type else None,
            "zone": s.zone
        }
        for s in stops
    ]


# =========================
# GET STOP BY ID
# =========================
@router.get("/{stop_id}")
def get_stop(stop_id: int, db: Session = Depends(get_db)):

    stop = db.query(Stop).filter(Stop.id == stop_id, Stop.is_active == True).first()

    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    return {
        "id": stop.id,
        "name": stop.name,
        "lat": stop.lat,
        "lon": stop.lon,
        "type": stop.type.value if stop.type else None,
        "zone": stop.zone
    }


# =========================
# GET NEARBY STOPS
# =========================
@router.get("/nearby/")
def get_nearby_stops(
    lat: float = Query(...),
    lon: float = Query(...),
    radius: float = Query(2.0),  # default 2 km
    db: Session = Depends(get_db)
):

    stops = db.query(Stop).filter(Stop.is_active == True).all()

    nearby = []
    for s in stops:
        distance = haversine(lat, lon, s.lat, s.lon)
        if distance <= radius:
            nearby.append({
                "id": s.id,
                "name": s.name,
                "lat": s.lat,
                "lon": s.lon,
                "distance_km": round(distance, 2),
                "type": s.type.value if s.type else None,
                "zone": s.zone
            })

    # sort by nearest
    nearby.sort(key=lambda x: x["distance_km"])

    return {
        "count": len(nearby),
        "stops": nearby
    }


# =========================
# GET ROUTES THROUGH STOP
# =========================
@router.get("/{stop_id}/routes")
def get_routes_for_stop(stop_id: int, db: Session = Depends(get_db)):

    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    route_ids = (
        db.query(RouteStop.route_id)
        .filter(RouteStop.stop_id == stop_id)
        .distinct()
        .all()
    )

    route_ids = [r[0] for r in route_ids]

    routes = db.query(Route).filter(Route.id.in_(route_ids)).all()

    return [
        {
            "id": r.id,
            "name": r.name,
            "distance_km": r.distance_km
        }
        for r in routes
    ]