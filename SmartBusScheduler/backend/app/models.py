# models.py
from sqlalchemy import (
<<<<<<< Updated upstream
    Column, Integer, String, Float, Date, Time, Text, ForeignKey,
    ARRAY, DECIMAL, TIMESTAMP
=======
    Column, Index, Integer, String, Float, Date, Time, Text, ForeignKey, Boolean, DateTime, Enum, UniqueConstraint, func
>>>>>>> Stashed changes
)
from sqlalchemy.orm import relationship
from .database import Base

# -----------------
# USERS
# -----------------
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)  # customer/admin/driver/uploader
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    # relationships
    services_as_driver = relationship("Service", back_populates="driver", foreign_keys="Service.driver_id")
    services_as_conductor = relationship("Service", back_populates="conductor", foreign_keys="Service.conductor_id")


# -----------------
# STOPS
# -----------------
class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(Integer, primary_key=True, index=True)
    stop_code = Column(String, unique=True, nullable=True)
    stop_name = Column(String, nullable=False)
    stop_lat = Column(DECIMAL(9, 6), nullable=True)
    stop_lon = Column(DECIMAL(9, 6), nullable=True)

    stop_times = relationship("StopTime", back_populates="stop")
    observations = relationship("ObservationData", back_populates="stop")


# -----------------
# ROUTES
# -----------------
class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True)
    route_short_name = Column(String, nullable=True)
    route_long_name = Column(String, nullable=True)
    # simple storage of stop order as integer array of stop_ids (Postgres) - nullable for sqlite
    stops = Column(ARRAY(Integer), nullable=True)

    trips = relationship("Trip", back_populates="route")
    observations = relationship("ObservationData", back_populates="route")


# -----------------
# SERVICE
# -----------------
class Service(Base):
    __tablename__ = "service"

    service_id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("users.user_id"))
    conductor_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    notes = Column(Text, nullable=True)

    driver = relationship("User", back_populates="services_as_driver", foreign_keys=[driver_id])
    conductor = relationship("User", back_populates="services_as_conductor", foreign_keys=[conductor_id])
    trips = relationship("Trip", back_populates="service")


# -----------------
# TRIPS
# -----------------
class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)
    service_id = Column(Integer, ForeignKey("service.service_id"), nullable=True)
    date = Column(Date, nullable=False)

    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip", cascade="all, delete-orphan")
    overrides = relationship("AdminOverride", back_populates="trip", cascade="all, delete-orphan")


# -----------------
# STOP TIMES
# -----------------
class StopTime(Base):
    __tablename__ = "stop_times"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.trip_id"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.stop_id"), nullable=False)
    arrival_time = Column(Time, nullable=True)
    departure_time = Column(Time, nullable=True)
    boarding_in = Column(Integer, default=0)
    boarding_out = Column(Integer, default=0)

    trip = relationship("Trip", back_populates="stop_times")
    stop = relationship("Stop", back_populates="stop_times")


# -----------------
# ADMIN OVERRIDES
# -----------------
class AdminOverride(Base):
    __tablename__ = "admin_overrides"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.trip_id"), nullable=False)
    delta_minutes = Column(Integer, nullable=False)
    effective_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)

    trip = relationship("Trip", back_populates="overrides")


# -----------------
# OBSERVATION DATA
# -----------------
class ObservationData(Base):
    __tablename__ = "observation_data"

    id = Column(Integer, primary_key=True, index=True)
    bus_no = Column(String, nullable=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.stop_id"), nullable=False)
    boarding_count = Column(Integer, nullable=False, default=0)
    alighting_count = Column(Integer, nullable=False, default=0)
    timestamp = Column(TIMESTAMP, nullable=False)

    route = relationship("Route", back_populates="observations")
    stop = relationship("Stop", back_populates="observations")


# -----------------
# BUS DATA
# -----------------
class BusData(Base):
    __tablename__ = "bus_data"

    bus_id = Column(Integer, primary_key=True, index=True)
    passenger_cap_count = Column(Integer, nullable=False)


<<<<<<< Updated upstream
# -----------------
# CREW DATA
# -----------------
class CrewData(Base):
    __tablename__ = "crew_data"

    crew_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    post = Column(String, nullable=True)  # Driver / Conductor
    experience = Column(Integer, nullable=True)
=======
# =========================
# BUSES
# =========================

class Bus(Base):
    __tablename__ = "buses"

    id = Column(Integer, primary_key=True)

    code = Column(String, unique=True, nullable=False)

    sitting_capacity = Column(Integer, nullable=False)

    standing_capacity = Column(Integer, default=0)

    status = Column(bus_status_enum, default=BusStatus.active)

    created_at = Column(DateTime, server_default=func.now())


# =========================
# DRIVER LEAVE
# =========================

class DriverLeave(Base):
    __tablename__ = "driver_leave"

    id = Column(Integer, primary_key=True)

    driver_id = Column(Integer, ForeignKey("drivers.user_id", ondelete="CASCADE"))

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    reason = Column(Text)

    status = Column(
    leave_status_enum, default=LeaveStatus.pending,
    nullable=False
)

    created_at = Column(DateTime, server_default=func.now())

    driver = relationship("Driver")


# =========================
# SCHEDULE TRIPS
# =========================

class ScheduleTrip(Base):
    __tablename__ = "schedule_trips"

    id = Column(Integer, primary_key=True)

    route_id = Column(String, ForeignKey("routes.id"), nullable=False)

    trip_date = Column(Date, nullable=False)

    start_time = Column(Time, nullable=False)

    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)

    driver_id = Column(Integer, ForeignKey("drivers.user_id"), nullable=False)

    status = Column(trip_status_enum, default=TripStatus.scheduled)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("route_id", "trip_date", "start_time"),
    )

    route = relationship("Route")
    bus = relationship("Bus")
    driver = relationship("Driver")


# =========================
# OVERRIDES
# =========================

class Override(Base):
    __tablename__ = "overrides"

    id = Column(Integer, primary_key=True)

    trip_id = Column(Integer, ForeignKey("schedule_trips.id", ondelete="CASCADE"))

    old_driver_id = Column(Integer)
    new_driver_id = Column(Integer)

    old_bus_id = Column(Integer)
    new_bus_id = Column(Integer)

    reason = Column(Text)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    created_at = Column(DateTime, server_default=func.now())

    trip = relationship("ScheduleTrip")
    creator = relationship("User")


# =========================
# NOTIFICATIONS
# =========================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    title = Column(Text, nullable=False)

    message = Column(Text, nullable=False)

    type = Column(notification_type_enum, default=NotificationType.system)

    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")


# =========================
# TRIP LIVE STATUS
# =========================

class TripLiveStatus(Base):
    __tablename__ = "trip_live_status"

    trip_id = Column(Integer, ForeignKey("schedule_trips.id", ondelete="CASCADE"), primary_key=True)

    current_stop_id = Column(Integer, ForeignKey("stops.id"))

    delay_minutes = Column(Integer, default=0)

    last_lat = Column(Float)
    last_lon = Column(Float)

    last_updated = Column(DateTime, server_default=func.now())

    trip = relationship("ScheduleTrip")
    stop = relationship("Stop")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String, default="auto")

    bus_count = Column(Integer, nullable=False)
    driver_count = Column(Integer, nullable=False)

    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    records = relationship(
        "TemplateRecord",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    creator = relationship("User")

    __table_args__ = (
        Index("idx_templates_type", "template_type"),
    )

class TemplateRecord(Base):
    __tablename__ = "template_records"

    id = Column(Integer, primary_key=True, index=True)

    template_id = Column(
        Integer,
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    route_id = Column(
        String,
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
    )

    start_time = Column(Time, nullable=False)
    busno = Column(Integer, nullable=False)
    driverno = Column(Integer, nullable=False)

    # Relationships
    template = relationship("Template", back_populates="records")
    route = relationship("Route")

    __table_args__ = (
        Index("idx_template_records_template", "template_id"),
        Index("idx_template_records_route", "route_id"),
        Index(
            "uq_template_route_time",
            "template_id",
            "route_id",
            "start_time",
            unique=True,
        ),
    )

class OBData(Base):
    __tablename__ = "ob_data"

    id = Column(Integer, primary_key=True)

    route_id = Column(String, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)

    stop_id = Column(Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False)

    boarding_count = Column(Integer, default=0)

    offboarding_count = Column(Integer, default=0)

    trip_datetime = Column(DateTime, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    route = relationship("Route")
    stop = relationship("Stop")

    __table_args__ = (
        Index("idx_ob_route_time", "route_id", "trip_datetime"),
        Index("idx_ob_stop", "stop_id"),
    )
>>>>>>> Stashed changes
