"""
Docstring for SmartBusScheduler.backend.app.routers.public_routes

GET /routes
GET /routes/{route_id}
GET /routes/{route_id}/stops
GET /routes/{route_id}/map

"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import date

from ..database import get_db
from ..models import (
    ScheduleTrip,
    Route,
    RouteStop,
    Stop
)

router = APIRouter()


# =========================
# HELPER: FORMAT TRIP
# =========================
def format_trip(trip: ScheduleTrip):
    return {
        "id": trip.id,
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
        } if trip.bus else None,
        "driver": {
            "id": trip.driver.user_id
        } if trip.driver else None
    }


# =========================
# GET SCHEDULE BY DATE
# =========================
@router.get("/date/{trip_date}")
def get_schedule_by_date(trip_date: date, db: Session = Depends(get_db)):

    trips = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus),
        joinedload(ScheduleTrip.driver)
    ).filter(
        ScheduleTrip.trip_date == trip_date
    ).order_by(ScheduleTrip.start_time).all()

    return {
        "date": trip_date,
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET SCHEDULE BY ROUTE
# =========================
@router.get("/route/{route_id}")
def get_schedule_by_route(route_id: str, db: Session = Depends(get_db)):

    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    trips = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.bus),
        joinedload(ScheduleTrip.driver)
    ).filter(
        ScheduleTrip.route_id == route_id
    ).order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return {
        "route": {
            "id": route.id,
            "name": route.name
        },
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET SCHEDULE BY STOP ⭐
# =========================
@router.get("/stop/{stop_id}")
def get_schedule_by_stop(stop_id: int, db: Session = Depends(get_db)):

    stop = db.query(Stop).filter(Stop.id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    # find routes passing through this stop
    route_ids = (
        db.query(RouteStop.route_id)
        .filter(RouteStop.stop_id == stop_id)
        .distinct()
        .all()
    )
    route_ids = [r[0] for r in route_ids]

    if not route_ids:
        return {
            "stop": {"id": stop.id, "name": stop.name},
            "trips": []
        }

    trips = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(
        ScheduleTrip.route_id.in_(route_ids)
    ).order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return {
        "stop": {
            "id": stop.id,
            "name": stop.name
        },
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET ROUTE TIMETABLE (WITH STOPS) ⭐
# =========================
@router.get("/route/{route_id}/timetable")
def get_route_timetable(route_id: str, db: Session = Depends(get_db)):

    route = db.query(Route).filter(Route.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # get route stops ordered
    route_stops = (
        db.query(RouteStop)
        .options(joinedload(RouteStop.stop))
        .filter(RouteStop.route_id == route_id)
        .order_by(RouteStop.seq)
        .all()
    )

    stops_data = []
    for rs in route_stops:
        stops_data.append({
            "seq": rs.seq,
            "stop": {
                "id": rs.stop.id,
                "name": rs.stop.name
            },
            "time_from_start": rs.time_from_start
        })

    # get trips
    trips = db.query(ScheduleTrip).filter(
        ScheduleTrip.route_id == route_id
    ).order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return {
        "route": {
            "id": route.id,
            "name": route.name
        },
        "stops": stops_data,
        "trips": [
            {
                "trip_id": t.id,
                "trip_date": t.trip_date,
                "start_time": t.start_time,
                "status": t.status.value
            }
            for t in trips
        ]
    }