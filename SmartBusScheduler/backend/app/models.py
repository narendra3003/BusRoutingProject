# models.py
from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
    Float,
    Date,
    Time,
    Text,
    ForeignKey,
    Boolean,
    DateTime,
    Enum,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from .database import Base
import enum

class UserRole(str, enum.Enum):
    admin = "admin"
    driver = "driver"
    crew = "crew"

class DriverStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"

class BusStatus(str, enum.Enum):
    active = "active"
    maintenance = "maintenance"
    inactive = "inactive"

class LeaveStatus(str, enum.Enum):
    pending = "pending"
    granted = "granted"
    rejected = "rejected"


class TripStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    delayed = "delayed"


class NotificationType(str, enum.Enum):
    override = "override"
    leave = "leave"
    system = "system"


class StopType(str, enum.Enum):
    stop = "stop"
    terminal = "terminal"
    depot = "depot"

user_role_enum = ENUM(UserRole, name="user_role", create_type=False)
driver_status_enum = ENUM(DriverStatus, name="driver_status", create_type=False)
bus_status_enum = ENUM(BusStatus, name="bus_status", create_type=False)
leave_status_enum = ENUM(LeaveStatus, name="leave_status", create_type=False)
trip_status_enum = ENUM(TripStatus, name="trip_status", create_type=False)
notification_type_enum = ENUM(
    NotificationType, name="notification_type", create_type=False
)
stop_type_enum = ENUM(StopType, name="stop_type", create_type=False)

class Stop(Base):
    __tablename__ = "stops"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    type = Column(stop_type_enum, default=StopType.stop, nullable=True)
    zone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

class Route(Base):
    __tablename__ = "routes"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    start_stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    end_stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    distance_km = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    start_stop = relationship("Stop", foreign_keys=[start_stop_id])
    end_stop = relationship("Stop", foreign_keys=[end_stop_id])

class RouteStop(Base):
    __tablename__ = "route_stops"
    id = Column(Integer, primary_key=True)
    route_id = Column(
        String, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    seq = Column(Integer, nullable=False)
    dist_from_start = Column(Float)
    time_from_start = Column(Integer)
    __table_args__ = (
        UniqueConstraint("route_id", "seq"),
        UniqueConstraint("route_id", "stop_id"),
    )
    route = relationship("Route")
    stop = relationship("Stop")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    pass_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(user_role_enum, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

class Driver(Base):
    __tablename__ = "drivers"
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    license_no = Column(String, unique=True, nullable=False)
    experience_years = Column(Integer, default=0)
    joining_date = Column(Date)
    status = Column(driver_status_enum, default=DriverStatus.active)
    user = relationship("User")

class Bus(Base):
    __tablename__ = "buses"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    sitting_capacity = Column(Integer, nullable=False)
    standing_capacity = Column(Integer, default=0)
    status = Column(bus_status_enum, default=BusStatus.active)
    created_at = Column(DateTime, server_default=func.now())

class DriverLeave(Base):
    __tablename__ = "driver_leave"
    id = Column(Integer, primary_key=True)
    driver_id = Column(
        Integer, ForeignKey("drivers.user_id", ondelete="CASCADE"), nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(leave_status_enum, default=LeaveStatus.pending, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    driver = relationship("Driver")

class ScheduleTrip(Base):
    __tablename__ = "schedule_trips"
    id = Column(Integer, primary_key=True)
    route_id = Column(String, ForeignKey("routes.id"), nullable=False)
    trip_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    bus_id = Column(Integer, ForeignKey("buses.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.user_id"), nullable=False)
    status = Column(trip_status_enum, default=TripStatus.scheduled, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("route_id", "trip_date", "start_time", "bus_id"),)
    route = relationship("Route")
    bus = relationship("Bus")
    driver = relationship("Driver")

class Override(Base):
    __tablename__ = "overrides"
    id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey("schedule_trips.id", ondelete="CASCADE"))
    old_driver_id = Column(Integer)
    new_driver_id = Column(Integer)
    old_bus_id = Column(Integer)
    new_bus_id = Column(Integer)
    reason = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    trip = relationship("ScheduleTrip")
    creator = relationship("User")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(notification_type_enum, default=NotificationType.system)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    user = relationship("User")

class TripLiveStatus(Base):
    __tablename__ = "trip_live_status"
    trip_id = Column(
        Integer, ForeignKey("schedule_trips.id", ondelete="CASCADE"), primary_key=True
    )
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
    __table_args__ = (Index("idx_templates_type", "template_type"),)


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

    route_id = Column(
        String, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False
    )

    origin_stop_id = Column(
        Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False
    )

    destination_stop_id = Column(
        Integer, ForeignKey("stops.id", ondelete="CASCADE"), nullable=False
    )

    trip_datetime = Column(DateTime, nullable=False)

    boarding_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    route = relationship("Route")

    origin_stop = relationship("Stop", foreign_keys=[origin_stop_id])
    destination_stop = relationship("Stop", foreign_keys=[destination_stop_id])

    __table_args__ = (
        # Prevent duplicate aggregated rows
        UniqueConstraint(
            "route_id",
            "origin_stop_id",
            "destination_stop_id",
            "trip_datetime",
            name="uq_od_route_time",
        ),

        # Indexes for scheduling queries
        Index("idx_ob_route_time", "route_id", "trip_datetime"),
        Index("idx_ob_od_pair", "origin_stop_id", "destination_stop_id"),
        Index("idx_ob_time", "trip_datetime"),
    )
