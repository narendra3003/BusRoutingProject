"""
Docstring for SmartBusScheduler.backend.app.routers.public_routes

GET /schedule/today
GET /schedule/date/{date}
GET /schedule/route/{route_id}
GET /schedule/stop/{stop_id}
GET /schedule/search?from_stop=&to_stop=

"""

from typing import List
from ..schemas import CustRouteResponse
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from .. import models
from ..models import Route, Stop, RouteStop, ScheduleTrip, TripLiveStatus
from ..database import get_db
from collections import defaultdict
# from ..utils import get_current_user

router = APIRouter()

@router.get("/routes/{route_id}")
def get_route(
    route_id: str,
    db: Session = Depends(get_db)
    # current_user: dict = Depends(get_current_user),
):
    route = db.query(models.Route).filter(models.Route.id == route_id).first()

    if not route:
        from typing import List

        from fastapi import APIRouter, Depends, HTTPException
        from sqlalchemy.orm import Session, joinedload

        from .. import models
        from ..models import Route, Stop, RouteStop
        from ..database import get_db
        from ..schemas import RouteResponse, RouteStopResponse, StopResponse


        router = APIRouter(prefix="/routes", tags=["routes"])


        @router.get("/", response_model=List[RouteResponse])
        def get_routes(db: Session = Depends(get_db)):
            routes = (
                db.query(Route)
                .options(joinedload(Route.start_stop), joinedload(Route.end_stop))
                .filter(Route.is_active == True)
                .all()
            )

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


        @router.get("/{route_id}", response_model=RouteResponse)
        def get_route(route_id: str, db: Session = Depends(get_db)):
            route = (
                db.query(Route)
                .options(joinedload(Route.start_stop), joinedload(Route.end_stop))
                .filter(Route.id == route_id, Route.is_active == True)
                .first()
            )

            if not route:
                raise HTTPException(status_code=404, detail="Route not found")

            return RouteResponse(
                id=route.id,
                name=route.name,
                start_stop_id=route.start_stop_id,
                end_stop_id=route.end_stop_id,
                distance_km=route.distance_km,
                is_active=route.is_active,
                created_at=route.created_at,
            )


        @router.get("/{route_id}/stops")
        def get_route_stops(route_id: str, db: Session = Depends(get_db)):
            route = db.query(Route).filter(Route.id == route_id).first()
            if not route:
                raise HTTPException(status_code=404, detail="Route not found")

            route_stops = (
                db.query(RouteStop)
                .options(joinedload(RouteStop.stop))
                .filter(RouteStop.route_id == route_id)
                .order_by(RouteStop.seq)
                .all()
            )

            stops = [
                RouteStopResponse(
                    seq=rs.seq,
                    stop=StopResponse(
                        id=rs.stop.id,
                        name=rs.stop.name,
                        lat=rs.stop.lat,
                        lon=rs.stop.lon,
                        type=rs.stop.type.value if rs.stop.type else None,
                        zone=rs.stop.zone,
                        is_active=rs.stop.is_active,
                        created_at=rs.stop.created_at,
                    ),
                    time_from_start=rs.time_from_start,
                    dist_from_start=rs.dist_from_start,
                )
                for rs in route_stops
            ]

            return {"route_id": route_id, "total_stops": len(stops), "stops": stops}


        @router.get("/by-stop/{stop_id}")
        def get_routes_by_stop(stop_id: int, db: Session = Depends(get_db)):
            stop = db.query(Stop).filter(Stop.id == stop_id).first()
            if not stop:
                raise HTTPException(status_code=404, detail="Stop not found")

            route_ids = (
                db.query(RouteStop.route_id).filter(RouteStop.stop_id == stop_id).distinct().all()
            )
            route_ids = [r[0] for r in route_ids]

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

# routers/routes.py
@router.get("/custRoutes", response_model=List[CustRouteResponse])
def list_routes(db: Session = Depends(get_db)):

    routes = db.query(Route).filter(Route.is_active == True).all()

    response = []

    for r in routes:

        route_stops = (
            db.query(RouteStop, Stop)
            .join(Stop, Stop.id == RouteStop.stop_id)
            .filter(RouteStop.route_id == r.id)
            .order_by(RouteStop.seq)
            .all()
        )

        stops = []
        coords = []
        offsets = []

        for rs, s in route_stops:
            stops.append(s.name)
            coords.append([s.lat, s.lon])
            offsets.append(rs.time_from_start or 0)

        start_stop = stops[0] if stops else None
        end_stop = stops[-1] if stops else None

        trips = db.query(ScheduleTrip).filter(ScheduleTrip.route_id == r.id).all()

        timetable = defaultdict(list)

        for t in trips:
            day = t.trip_date.strftime("%a").lower()

            if day == "sat":
                key = "sat"
            elif day == "sun":
                key = "sun"
            else:
                key = "weekday"

            timetable[key].append(t.start_time.strftime("%H:%M"))

        live = (
            db.query(TripLiveStatus)
            .join(ScheduleTrip, ScheduleTrip.id == TripLiveStatus.trip_id)
            .filter(ScheduleTrip.route_id == r.id)
            .first()
        )

        live_stop = None
        if live and live.current_stop_id:
            stop_obj = db.query(Stop).get(live.current_stop_id)
            if stop_obj:
                live_stop = stop_obj.name

        response.append(
            CustRouteResponse(
                id=r.id,
                name=r.name,
                from_stop=start_stop,
                to_stop=end_stop,
                stops=stops,
                coords=coords,
                stopOffsets=offsets,
                liveStop=live_stop,
                etaFromLive={},
                timetable=timetable
            )
        )

    return response

@router.get("/cust_routes/{route_id}", response_model=CustRouteResponse)
def cust_get_route(route_id: str, db: Session = Depends(get_db)):

    r = db.query(Route).filter(Route.id == route_id).first()
    if not r:
        return None

    route_stops = (
        db.query(RouteStop, Stop)
        .join(Stop, Stop.id == RouteStop.stop_id)
        .filter(RouteStop.route_id == r.id)
        .order_by(RouteStop.seq)
        .all()
    )

    stops = []
    coords = []
    offsets = []

    for rs, s in route_stops:
        stops.append(s.name)
        coords.append([s.lat, s.lon])
        offsets.append(rs.time_from_start or 0)

    start_stop = stops[0] if stops else None
    end_stop = stops[-1] if stops else None

    trips = db.query(ScheduleTrip).filter(ScheduleTrip.route_id == r.id).all()

    timetable = defaultdict(list)

    for t in trips:
        day = t.trip_date.strftime("%a").lower()

        if day == "sat":
            key = "sat"
        elif day == "sun":
            key = "sun"
        else:
            key = "weekday"

        timetable[key].append(t.start_time.strftime("%H:%M"))

    return CustRouteResponse(
        id=r.id,
        name=r.name,
        from_stop=start_stop,
        to_stop=end_stop,
        stops=stops,
        coords=coords,
        stopOffsets=offsets,
        liveStop=None,
        etaFromLive={},
        timetable=timetable
    )


@router.get("/cust-routes-by-stop", response_model=List[CustRouteResponse])
def cust_routes_by_stop(
    stop_id: int,
    db: Session = Depends(get_db)
):

    routes = (
        db.query(Route)
        .join(RouteStop, RouteStop.route_id == Route.id)
        .filter(RouteStop.stop_id == stop_id)
        .filter(Route.is_active == True)
        .distinct()
        .all()
    )

    response = []

    for r in routes:

        route_stops = (
            db.query(RouteStop, Stop)
            .join(Stop, Stop.id == RouteStop.stop_id)
            .filter(RouteStop.route_id == r.id)
            .order_by(RouteStop.seq)
            .all()
        )

        stops = []
        for rs, s in route_stops:
            stops.append(s.name)

        response.append(
            CustRouteResponse(
                id=r.id,
                name=r.name,
                from_stop=stops[0] if stops else None,
                to_stop=stops[-1] if stops else None,
                stops=stops,
                coords=[],
                stopOffsets=[],
                liveStop=None,
                etaFromLive={},
                timetable={}
            )
        )

    return response