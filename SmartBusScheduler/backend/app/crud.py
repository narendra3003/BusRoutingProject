from sqlalchemy.orm import Session
from .models import Bus, Driver, Route, Stop, RouteStop, Service, Trip, TripStop, PassengerDensity, ScheduleOverride
from . import schemas as schema

# -----------------
# Bus CRUD
# -----------------
def create_bus(db: Session, bus: schema.BusCreate):
    new_bus = Bus(**bus.dict())
    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)
    return new_bus

def get_buses(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Bus).offset(skip).limit(limit).all()

def delete_bus(db: Session, bus_id: int):
    bus = db.query(Bus).filter(Bus.bus_id == bus_id).first()
    if bus:
        db.delete(bus)
        db.commit()
    return bus

# -----------------
# Driver CRUD
# -----------------
def create_driver(db: Session, driver: schema.DriverCreate):
    new_driver = Driver(**driver.dict())
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return new_driver

def get_drivers(db: Session):
    return db.query(Driver).all()

# -----------------
# Route & Stops
# -----------------
def create_route(db: Session, route: schema.RouteCreate):
    new_route = Route(**route.dict())
    db.add(new_route)
    db.commit()
    db.refresh(new_route)
    return new_route

def add_stop_to_route(db: Session, route_stop: schema.RouteStopCreate):
    new_rs = RouteStop(**route_stop.dict())
    db.add(new_rs)
    db.commit()
    return new_rs

def get_route_stops(db: Session, route_id: int):
    return db.query(RouteStop).filter(RouteStop.route_id == route_id).order_by(RouteStop.stop_order).all()

# -----------------
# Trip CRUD
# -----------------
def create_trip(db: Session, trip: schema.TripCreate):
    new_trip = Trip(**trip.dict())
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip

def get_trips_by_date(db: Session, trip_date):
    return db.query(Trip).filter(Trip.trip_date == trip_date).all()

def update_trip_driver(db: Session, trip_id: int, driver_id: int):
    trip = db.query(Trip).filter(Trip.trip_id == trip_id).first()
    if trip:
        trip.driver_id = driver_id
        db.commit()
        db.refresh(trip)
    return trip

# -----------------
# Passenger Density
# -----------------
def add_passenger_density(db: Session, density: schema.PassengerDensityCreate):
    new_density = PassengerDensity(**density.dict())
    db.add(new_density)
    db.commit()
    db.refresh(new_density)
    return new_density

def get_trip_density(db: Session, trip_id: int):
    return db.query(PassengerDensity).filter(PassengerDensity.trip_id == trip_id).all()

# -----------------
# Schedule Overrides
# -----------------
def add_schedule_override(db: Session, override: schema.ScheduleOverrideCreate):
    new_override = ScheduleOverride(**override.dict())
    db.add(new_override)
    db.commit()
    db.refresh(new_override)
    return new_override

def get_overrides_for_trip(db: Session, trip_id: int):
    return db.query(ScheduleOverride).filter(ScheduleOverride.trip_id == trip_id).all()
