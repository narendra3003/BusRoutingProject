from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Route, Stop, RouteStop

from ..schemas import (
    RouteStopsBulkCreate,
    RouteStopResponse,
)
from ..utils import get_current_user
from .admin_routes import check_admin

router = APIRouter(
)


# =====================================================
# GET ROUTE STOPS
# =====================================================
# @router.get(
#     "/routes/{route_id}/stops",
#     response_model=list[RouteStopResponse]
# )
# def get_route_stops(
#     route_id: str,
#     db: Session = Depends(get_db),
#     current_user: dict = Depends(get_current_user)
# ):
#     check_admin(current_user)

#     # Validate route
#     route = db.query(Route).filter(Route.id == route_id).first()

#     if not route:
#         raise HTTPException(
#             status_code=404,
#             detail="Route not found"
#         )

#     # Fetch ordered stops
#     route_stops = (
#         db.query(RouteStop, Stop)
#         .join(Stop, Stop.id == RouteStop.stop_id)
#         .filter(RouteStop.route_id == route_id)
#         .order_by(RouteStop.seq.asc())
#         .all()
#     )

#     result = []

#     for rs, stop in route_stops:
#         result.append({
#             "stop_id": stop.id,
#             "seq": rs.seq,
#             "name": stop.name
#         })

#     return result


# =====================================================
# SAVE ROUTE STOPS (BULK REPLACE)
# =====================================================
@router.post("/bulk")
def save_route_stops(
    payload: RouteStopsBulkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    check_admin(current_user)

    # -----------------------------------------
    # Validate route
    # -----------------------------------------
    route = (
        db.query(Route)
        .filter(Route.id == payload.route_id)
        .first()
    )

    if not route:
        raise HTTPException(
            status_code=404,
            detail="Route not found"
        )

    # -----------------------------------------
    # Validate all stops exist
    # -----------------------------------------
    existing_stops = (
        db.query(Stop.id)
        .filter(Stop.id.in_(payload.stops))
        .all()
    )

    existing_stop_ids = {s[0] for s in existing_stops}

    missing = [
        stop_id
        for stop_id in payload.stops
        if stop_id not in existing_stop_ids
    ]

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"Stops not found: {missing}"
        )

    # -----------------------------------------
    # Delete old route stops
    # -----------------------------------------
    (
        db.query(RouteStop)
        .filter(RouteStop.route_id == payload.route_id)
        .delete()
    )

    # -----------------------------------------
    # Insert new ordered stops
    # -----------------------------------------
    route_stop_objects = []

    for index, stop_id in enumerate(payload.stops):
        route_stop_objects.append(
            RouteStop(
                route_id=payload.route_id,
                stop_id=stop_id,
                seq=index + 1
            )
        )

    db.bulk_save_objects(route_stop_objects)

    db.commit()

    return {
        "message": "Route stops saved successfully",
        "route_id": payload.route_id,
        "total_stops": len(payload.stops)
    }