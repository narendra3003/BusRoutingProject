# crud.py
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from . import models, schemas

# -----------------
# User CRUD
# -----------------
def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    # password hashing should be added in utils/auth but omitted per instruction
    new = models.User(
        name=user_in.name,
        email=user_in.email,
        role=user_in.role,
        password_hash=user_in.password  # replace with hashed value when adding auth
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


# -----------------
# Stops CRUD
# -----------------
def create_stop(db: Session, stop_in: schemas.StopCreate) -> models.Stop:
    new = models.Stop(
        stop_code=stop_in.stop_code,
        stop_name=stop_in.stop_name,
        stop_lat=stop_in.stop_lat,
        stop_lon=stop_in.stop_lon
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_stop(db: Session, stop_id: int) -> Optional[models.Stop]:
    return db.query(models.Stop).filter(models.Stop.stop_id == stop_id).first()

def list_stops(db: Session, skip: int = 0, limit: int = 100) -> List[models.Stop]:
    return db.query(models.Stop).offset(skip).limit(limit).all()


# -----------------
# Routes CRUD
# -----------------
def create_route(db: Session, route_in: schemas.RouteCreate) -> models.Route:
    new = models.Route(
        route_short_name=route_in.route_short_name,
        route_long_name=route_in.route_long_name,
        stops=route_in.stops
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_route(db: Session, route_id: int) -> Optional[models.Route]:
    return db.query(models.Route).filter(models.Route.route_id == route_id).first()

def list_routes(db: Session, skip: int = 0, limit: int = 100) -> List[models.Route]:
    return db.query(models.Route).offset(skip).limit(limit).all()

def update_route_stops(db: Session, route_id: int, stops: List[int]) -> Optional[models.Route]:
    route = get_route(db, route_id)
    if not route:
        return None
    route.stops = stops
    db.commit()
    db.refresh(route)
    return route


# -----------------
# Service CRUD
# -----------------
def create_service(db: Session, svc_in: schemas.ServiceCreate) -> models.Service:
    new = models.Service(driver_id=svc_in.driver_id, conductor_id=svc_in.conductor_id, notes=svc_in.notes)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_service(db: Session, service_id: int) -> Optional[models.Service]:
    return db.query(models.Service).filter(models.Service.service_id == service_id).first()


# -----------------
# Trip CRUD
# -----------------
def create_trip(db: Session, trip_in: schemas.TripCreate) -> models.Trip:
    new = models.Trip(route_id=trip_in.route_id, service_id=trip_in.service_id, date=trip_in.date)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_trip(db: Session, trip_id: int) -> Optional[models.Trip]:
    return db.query(models.Trip).filter(models.Trip.trip_id == trip_id).first()

def list_trips_on_date(db: Session, trip_date: date) -> List[models.Trip]:
    return db.query(models.Trip).filter(models.Trip.date == trip_date).all()

def assign_service_to_trip(db: Session, trip_id: int, service_id: int) -> Optional[models.Trip]:
    trip = get_trip(db, trip_id)
    if not trip:
        return None
    trip.service_id = service_id
    db.commit()
    db.refresh(trip)
    return trip

def delete_trip(db: Session, trip_id: int) -> Optional[models.Trip]:
    trip = get_trip(db, trip_id)
    if not trip:
        return None
    db.delete(trip)
    db.commit()
    return trip


# -----------------
# StopTime CRUD
# -----------------
def create_stop_time(db: Session, st_in: schemas.StopTimeCreate) -> models.StopTime:
    new = models.StopTime(
        trip_id=st_in.trip_id,
        stop_id=st_in.stop_id,
        arrival_time=st_in.arrival_time,
        departure_time=st_in.departure_time,
        boarding_in=st_in.boarding_in or 0,
        boarding_out=st_in.boarding_out or 0
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def list_stop_times_for_trip(db: Session, trip_id: int) -> List[models.StopTime]:
    return db.query(models.StopTime).filter(models.StopTime.trip_id == trip_id).order_by(models.StopTime.id).all()

def update_stop_time_boarding(db: Session, stop_time_id: int, boarding_in: Optional[int] = None, boarding_out: Optional[int] = None):
    st = db.query(models.StopTime).filter(models.StopTime.id == stop_time_id).first()
    if not st:
        return None
    if boarding_in is not None:
        st.boarding_in = boarding_in
    if boarding_out is not None:
        st.boarding_out = boarding_out
    db.commit()
    db.refresh(st)
    return st


# -----------------
# AdminOverride CRUD
# -----------------
def add_admin_override(db: Session, ov_in: schemas.AdminOverrideCreate) -> models.AdminOverride:
    new = models.AdminOverride(
        trip_id=ov_in.trip_id,
        delta_minutes=ov_in.delta_minutes,
        effective_date=ov_in.effective_date,
        reason=ov_in.reason
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_overrides_for_trip(db: Session, trip_id: int) -> List[models.AdminOverride]:
    return db.query(models.AdminOverride).filter(models.AdminOverride.trip_id == trip_id).all()


# -----------------
# ObservationData CRUD
# -----------------
def add_observation(db: Session, obs_in: schemas.ObservationCreate) -> models.ObservationData:
    new = models.ObservationData(
        bus_no=obs_in.bus_no,
        route_id=obs_in.route_id,
        stop_id=obs_in.stop_id,
        boarding_count=obs_in.boarding_count,
        alighting_count=obs_in.alighting_count,
        timestamp=obs_in.timestamp
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def add_observations_batch(db: Session, obs_list: List[schemas.ObservationCreate]) -> List[models.ObservationData]:
    created = []
    for obs in obs_list:
        created.append(add_observation(db, obs))
    return created

def get_observations_for_route_date(db: Session, route_id: int, start_ts, end_ts) -> List[models.ObservationData]:
    return db.query(models.ObservationData).filter(
        models.ObservationData.route_id == route_id,
        models.ObservationData.timestamp >= start_ts,
        models.ObservationData.timestamp <= end_ts
    ).all()


# -----------------
# BusData & CrewData CRUD
# -----------------
def create_bus_data(db: Session, bus_in: schemas.BusDataCreate) -> models.BusData:
    new = models.BusData(passenger_cap_count=bus_in.passenger_cap_count)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_bus(db: Session, bus_id: int) -> Optional[models.BusData]:
    return db.query(models.BusData).filter(models.BusData.bus_id == bus_id).first()

def create_crew(db: Session, crew_in: schemas.CrewDataCreate) -> models.CrewData:
    new = models.CrewData(name=crew_in.name, post=crew_in.post, experience=crew_in.experience)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def get_crew(db: Session, crew_id: int) -> Optional[models.CrewData]:
    return db.query(models.CrewData).filter(models.CrewData.crew_id == crew_id).first()
