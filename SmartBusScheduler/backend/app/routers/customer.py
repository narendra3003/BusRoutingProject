from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import ScheduleResponse, RouteStopsResponse, StopBase, RouteMapResponse, StopTimeBase
from ..utils import get_current_user
from datetime import date, datetime, timedelta

router = APIRouter()

# 1. Get schedules for route or stop (today)
@router.get("/schedules/{route_id}", response_model=ScheduleResponse)
def get_schedule(route_id: int, stop_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ("customer", "admin", "uploader", "driver"):
        raise HTTPException(status_code=403, detail="Access denied")

    today = date.today()
    now_time = datetime.utcnow().time()

    # All trips for route today
    trips = db.query(models.Trip).filter(
        models.Trip.route_id == route_id,
        models.Trip.date == today
    ).all()

    previous, upcoming = [], []

    for trip in trips:
        # find stop time for provided stop
        st = next((st for st in trip.stop_times if st.stop_id == stop_id), None)
        if not st:
            continue

        # apply admin overrides for today
        adj_arr = st.arrival_time
        adj_dep = st.departure_time
        for ov in trip.overrides:
            if ov.effective_date == today:
                delta = timedelta(minutes=ov.delta_minutes)
                if adj_arr:
                    adj_arr = (datetime.combine(today, adj_arr) + delta).time()
                if adj_dep:
                    adj_dep = (datetime.combine(today, adj_dep) + delta).time()

        stop = db.query(models.Stop).filter(models.Stop.stop_id == stop_id).first()
        stop_name = stop.stop_name if stop else f"Stop {stop_id}"

        item = StopTimeBase(
            trip_id=trip.trip_id,
            stop_id=stop_id,
            stop_name=stop_name,
            arrival_time=adj_arr,
            departure_time=adj_dep
        )
        # categorize by time
        if adj_dep and adj_dep <= now_time:
            previous.append(item)
        else:
            upcoming.append(item)

    return ScheduleResponse(route_id=route_id, date=today, previous_trips=previous, next_trips=upcoming)

# 2. Get stops for a route
@router.get("/routes/{route_id}/stops", response_model=RouteStopsResponse)
def get_stops(route_id: int, db: Session = Depends(get_db)):
    route = db.query(models.Route).filter(models.Route.route_id == route_id).first()
    if not route or not route.stops:
        return RouteStopsResponse(route_id=route_id, stops=[])

    stops_q = db.query(models.Stop).filter(models.Stop.stop_id.in_(route.stops)).all()
    stops_map = {s.stop_id: s for s in stops_q}
    ordered = []
    for sid in route.stops:
        s = stops_map.get(sid)
        if not s:
            continue
        ordered.append(
            StopBase(
                stop_id=s.stop_id,
                stop_name=s.stop_name,
                lat=float(s.stop_lat) if s.stop_lat is not None else None,
                lon=float(s.stop_lon) if s.stop_lon is not None else None,
            )
        )
    return RouteStopsResponse(route_id=route_id, stops=ordered)

# 3. Get map for a route
@router.get("/routes/{route_id}/map", response_model=RouteMapResponse)
def route_map(route_id: int, db: Session = Depends(get_db)):
    # same data as stops endpoint
    rs = get_stops(route_id, db)
    return RouteMapResponse(route_id=rs.route_id, stops=rs.stops)
