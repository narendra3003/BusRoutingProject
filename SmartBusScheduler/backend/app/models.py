from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)  # "customer", "admin", "driver", "uploader"

class Route(Base):
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    stops = relationship("Stop", back_populates="route")

class Stop(Base):
    __tablename__ = "stops"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    lat = Column(Float)
    lon = Column(Float)
    route_id = Column(Integer, ForeignKey("routes.id"))
    route = relationship("Route", back_populates="stops")

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"))
    start_time = Column(String)
    end_time = Column(String)

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    bus_no = Column(String)
    route_id = Column(Integer)
    stop_id = Column(Integer)
    boarding_count = Column(Integer)
    alighting_count = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
