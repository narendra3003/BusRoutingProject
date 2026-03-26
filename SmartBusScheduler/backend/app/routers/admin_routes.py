"""Admin Routes management

Endpoints:
- POST   /admin/routes
- PUT    /admin/routes/{id}
- DELETE /admin/routes/{id}

- POST   /admin/routes/{id}/stops
- PUT    /admin/routes/{id}/stops/{seq}
- DELETE /admin/routes/{id}/stops/{stop_id}
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Route, Stop
from ..utils import get_current_user
from ..schemas import (
    RouteCreate,
    RouteUpdate,
    RouteResponse
)

router = APIRouter()


# =========================
# HELPER
# =========================
def check_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


def format_route(route: Route):
    return {
        "id": route.id,
        "name": route.name,
        "start_stop_id": route.start_stop_id,
        "end_stop_id": route.end_stop_id,
        "distance_km": float(route.distance_km) if route.distance_km else None,
        "is_active": route.is_active,
        "created_at": route.created_at
    }


# =========================
# CREATE ROUTE
# =========================
@router.post("/", response_model=RouteResponse)
def create_route(
    payload: RouteCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    # check route exists
    existing = db.query(Route).filter(Route.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Route already exists")

    # validate stops
    start = db.query(Stop).filter(Stop.id == payload.start_stop_id).first()
    end = db.query(Stop).filter(Stop.id == payload.end_stop_id).first()

    if not start or not end:
        raise HTTPException(status_code=404, detail="Start or End stop not found")

    route = Route(
        id=payload.id,
        name=payload.name,
        start_stop_id=payload.start_stop_id,
        end_stop_id=payload.end_stop_id,
        distance_km=payload.distance_km,
        is_active=True
    )

    db.add(route)
    db.commit()
    db.refresh(route)

    return format_route(route)


# =========================
# GET ALL ROUTES
# =========================
@router.get("/", response_model=list[RouteResponse])
def get_routes(
    is_active: bool | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    query = db.query(Route)

    if is_active is not None:
        query = query.filter(Route.is_active == is_active)

    routes = query.order_by(Route.id).all()

    return [format_route(r) for r in routes]


# =========================
# GET SINGLE ROUTE
# =========================
@router.get("/{route_id}")
def get_route(
    route_id: str,
    include_stops: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    route = db.query(Route).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    result = format_route(route)

    if include_stops:
        from ..models import RouteStop

        stops = db.query(RouteStop).options(
            joinedload(RouteStop.stop)
        ).filter(
            RouteStop.route_id == route_id
        ).order_by(RouteStop.seq).all()

        result["stops"] = [
            {
                "stop_id": s.stop.id,
                "name": s.stop.name,
                "seq": s.seq,
                "dist_from_start": float(s.dist_from_start) if s.dist_from_start else None,
                "time_from_start": s.time_from_start
            }
            for s in stops
        ]

    return result


# =========================
# UPDATE ROUTE
# =========================
@router.put("/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: str,
    payload: RouteUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    route = db.query(Route).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    if payload.name:
        route.name = payload.name

    if payload.start_stop_id:
        route.start_stop_id = payload.start_stop_id

    if payload.end_stop_id:
        route.end_stop_id = payload.end_stop_id

    if payload.distance_km is not None:
        route.distance_km = payload.distance_km

    if payload.is_active is not None:
        route.is_active = payload.is_active

    db.commit()
    db.refresh(route)

    return format_route(route)


# =========================
# DELETE ROUTE (SOFT)
# =========================
@router.delete("/{route_id}")
def delete_route(
    route_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    route = db.query(Route).filter(Route.id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # soft delete
    route.is_active = False
    db.commit()

    return {
        "status": "deleted",
        "route_id": route_id
    }