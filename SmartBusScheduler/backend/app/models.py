from sqlalchemy import Column, Integer, String, Float, Date, Time, Text, ForeignKey, CheckConstraint, ARRAY, DECIMAL, TIMESTAMP
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

    # relations
    services_as_driver = relationship("Service", back_populates="driver", foreign_keys="Service.driver_id")
    services_as_conductor = relationship("Service", back_populates="conductor", foreign_keys="Service.conductor_id")


# -----------------
# STOPS
# -----------------
class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(Integer, primary_key=True, index=True)
    stop_code = Column(String, unique=True)
    stop_name = Column(String, nullable=False)
    stop_lat = Column(DECIMAL(9, 6))
    stop_lon = Column(DECIMAL(9, 6))

    stop_times = relationship("StopTime", back_populates="stop")
    observations = relationship("ObservationData", back_populates="stop")


# -----------------
# ROUTES
# -----------------
class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True)
    route_short_name = Column(String)
    route_long_name = Column(String)
    stops = Column(ARRAY(Integer))  # Array of stop_ids

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
    notes = Column(Text)

    driver = relationship("User", back_populates="services_as_driver", foreign_keys=[driver_id])
    conductor = relationship("User", back_populates="services_as_conductor", foreign_keys=[conductor_id])
    trips = relationship("Trip", back_populates="service")


# -----------------
# TRIPS
# -----------------
class Trip(Base):
    __tablename__ = "trips"

    trip_id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"))
    service_id = Column(Integer, ForeignKey("service.service_id"))
    date = Column(Date, nullable=False)

    route = relationship("Route", back_populates="trips")
    service = relationship("Service", back_populates="trips")
    stop_times = relationship("StopTime", back_populates="trip")
    overrides = relationship("AdminOverride", back_populates="trip")


# -----------------
# STOP TIMES
# -----------------
class StopTime(Base):
    __tablename__ = "stop_times"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.trip_id"))
    stop_id = Column(Integer, ForeignKey("stops.stop_id"))
    arrival_time = Column(Time)
    departure_time = Column(Time)
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
    trip_id = Column(Integer, ForeignKey("trips.trip_id"))
    delta_minutes = Column(Integer)
    effective_date = Column(Date)
    reason = Column(Text)

    trip = relationship("Trip", back_populates="overrides")


# -----------------
# OBSERVATION DATA
# -----------------
class ObservationData(Base):
    __tablename__ = "observation_data"

    id = Column(Integer, primary_key=True, index=True)
    bus_no = Column(String)
    route_id = Column(Integer, ForeignKey("routes.route_id"))
    stop_id = Column(Integer, ForeignKey("stops.stop_id"))
    boarding_count = Column(Integer)
    alighting_count = Column(Integer)
    timestamp = Column(TIMESTAMP)

    route = relationship("Route", back_populates="observations")
    stop = relationship("Stop", back_populates="observations")


# -----------------
# BUS DATA
# -----------------
class BusData(Base):
    __tablename__ = "bus_data"

    bus_id = Column(Integer, primary_key=True, index=True)
    passenger_cap_count = Column(Integer, nullable=False)


# -----------------
# CREW DATA
# -----------------
class CrewData(Base):
    __tablename__ = "crew_data"

    crew_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    post = Column(String)  # Driver / Conductor
    experience = Column(Integer)
