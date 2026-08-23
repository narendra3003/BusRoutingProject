# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
import database as db

# =========================
# USERS
# =========================

def create_user(db: Session, user: schemas.UserCreate, password_hash: str):
    db_user = models.User(
        email=user.email,
        pass_hash=password_hash,
        name=user.name,
        phone=user.phone,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 50):
    return db.query(models.User).offset(skip).limit(limit).all()


def deactivate_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user:
        user.is_active = False
        db.commit()
        db.refresh(user)
    return user


# =========================
# DRIVERS
# =========================

def create_driver(db: Session, driver: schemas.DriverCreate):
    db_driver = models.Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


def get_driver(db: Session, driver_id: int):
    return db.query(models.Driver).filter(models.Driver.user_id == driver_id).first()


def get_all_drivers(db: Session):
    return db.query(models.Driver).all()


# =========================
# BUSES
# =========================

def create_bus(db: Session, bus: schemas.BusCreate):
    db_bus = models.Bus(**bus.model_dump())
    db.add(db_bus)
    db.commit()
    db.refresh(db_bus)
    return db_bus


def get_bus(db: Session, bus_id: int):
    return db.query(models.Bus).filter(models.Bus.id == bus_id).first()


def get_buses(db: Session):
    return db.query(models.Bus).all()


def update_bus_status(db: Session, bus_id: int, status):
    bus = get_bus(db, bus_id)
    if bus:
        bus.status = status
        db.commit()
        db.refresh(bus)
    return bus


# =========================
# STOPS
# =========================

def create_stop(db: Session, stop: schemas.StopCreate):
    db_stop = models.Stop(**stop.model_dump())
    db.add(db_stop)
    db.commit()
    db.refresh(db_stop)
    return db_stop


def get_stop(db: Session, stop_id: int):
    return db.query(models.Stop).filter(models.Stop.id == stop_id).first()


def get_stops(db: Session):
    return db.query(models.Stop).filter(models.Stop.is_active == True).all()


# =========================
# ROUTES
# =========================

def create_route(db: Session, route: schemas.RouteCreate):
    db_route = models.Route(**route.model_dump())
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    return db_route


def get_route(db: Session, route_id: str):
    return db.query(models.Route).filter(models.Route.id == route_id).first()


def get_routes(db: Session):
    return db.query(models.Route).all()


# =========================
# ROUTE STOPS
# =========================

def add_stop_to_route(db: Session, route_stop: schemas.RouteStopCreate):
    db_obj = models.RouteStop(**route_stop.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_route_stops(db: Session, route_id: str):
    return (
        db.query(models.RouteStop)
        .filter(models.RouteStop.route_id == route_id)
        .order_by(models.RouteStop.seq)
        .all()
    )


# =========================
# DRIVER LEAVE
# =========================

def apply_driver_leave(db: Session, leave: schemas.DriverLeaveCreate):
    db_leave = models.DriverLeave(**leave.model_dump())
    db.add(db_leave)
    db.commit()
    db.refresh(db_leave)
    return db_leave


def get_driver_leaves(db: Session, driver_id: int):
    return (
        db.query(models.DriverLeave)
        .filter(models.DriverLeave.driver_id == driver_id)
        .all()
    )


def update_leave_status(db: Session, leave_id: int, status):
    leave = db.query(models.DriverLeave).filter(models.DriverLeave.id == leave_id).first()

    if leave:
        leave.status = status
        db.commit()
        db.refresh(leave)

    return leave


# =========================
# TRIPS
# =========================

def create_trip(db: Session, trip: schemas.TripCreate):
    db_trip = models.ScheduleTrip(**trip.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


def get_trip(db: Session, trip_id: int):
    return db.query(models.ScheduleTrip).filter(models.ScheduleTrip.id == trip_id).first()


def get_trips_by_date(db: Session, trip_date):
    return db.query(models.ScheduleTrip).filter(
        models.ScheduleTrip.trip_date == trip_date
    ).all()


def get_driver_trips(db: Session, driver_id: int, trip_date):
    return db.query(models.ScheduleTrip).filter(
        and_(
            models.ScheduleTrip.driver_id == driver_id,
            models.ScheduleTrip.trip_date == trip_date
        )
    ).all()


# =========================
# TRIP OVERRIDES
# =========================

def create_override(db: Session, override: schemas.OverrideCreate, user_id: int):
    db_override = models.Override(
        **override.model_dump(),
        created_by=user_id
    )
    db.add(db_override)
    db.commit()
    db.refresh(db_override)
    return db_override


# =========================
# LIVE TRIP STATUS
# =========================

def update_trip_live_status(
    db: Session,
    trip_id: int,
    lat: float,
    lon: float,
    stop_id: int | None = None,
    delay: int = 0
):

    status = db.query(models.TripLiveStatus).filter(
        models.TripLiveStatus.trip_id == trip_id
    ).first()

    if not status:
        status = models.TripLiveStatus(
            trip_id=trip_id,
            last_lat=lat,
            last_lon=lon,
            current_stop_id=stop_id,
            delay_minutes=delay
        )
        db.add(status)
    else:
        status.last_lat = lat
        status.last_lon = lon
        status.current_stop_id = stop_id
        status.delay_minutes = delay

    db.commit()
    db.refresh(status)

    return status


# =========================
# NOTIFICATIONS
# =========================

def create_notification(db: Session, notif: schemas.NotificationCreate):
    db_notif = models.Notification(**notif.model_dump())
    db.add(db_notif)
    db.commit()
    db.refresh(db_notif)
    return db_notif


def get_user_notifications(db: Session, user_id: int):
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


def mark_notification_read(db: Session, notif_id: int):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notif_id
    ).first()

    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)

    return notif