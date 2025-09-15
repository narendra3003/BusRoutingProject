from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, time, datetime

# schemas.py (add these)
from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # 'customer' | 'driver' | 'admin'

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    status: str
    message: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None

class UserInfoResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    role: str



# ----------------------
# Shared Base Schemas
# ----------------------

class StopBase(BaseModel):
    stop_id: int
    stop_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class TripBase(BaseModel):
    trip_id: int
    route_id: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class StopTimeBase(BaseModel):
    trip_id: int
    stop_id: int
    stop_name: str
    arrival_time: time
    departure_time: time


class ObservationUpload(BaseModel):
    bus_no: str
    route_id: int
    stop_id: int
    boarding_count: int
    alighting_count: int
    timestamp: datetime


class OverrideRequest(BaseModel):
    trip_id: int
    delta_minutes: int
    date: date
    reason: str


# ----------------------
# Customer Schemas
# ----------------------

class ScheduleResponse(BaseModel):
    route_id: int
    date: date
    previous_trips: List[StopTimeBase]
    next_trips: List[StopTimeBase]


class RouteStopsResponse(BaseModel):
    route_id: int
    stops: List[StopBase]


# ----------------------
# Uploader Schemas
# ----------------------

class ObservationResponse(BaseModel):
    status: str
    message: str


class OptimizeRequest(BaseModel):
    route_id: int
    date: date


class OptimizedTrip(BaseModel):
    trip_id: int
    start_time: time
    end_time: time
    bus_count: int


class OptimizeResponse(BaseModel):
    route_id: int
    date: date
    optimized_trips: List[OptimizedTrip]


# ----------------------
# Admin Schemas
# ----------------------

class OverrideResponse(BaseModel):
    status: str
    message: str


class AdminTrip(BaseModel):
    trip_id: int
    start_time: time
    end_time: time


class AdminScheduleResponse(BaseModel):
    route_id: int
    date: date
    trips: List[AdminTrip]


class KPIResponse(BaseModel):
    date: date
    avg_wait_time: float
    buses_used: int
    load_factor: float


# ----------------------
# Driver Schemas
# ----------------------

class DriverTrip(BaseModel):
    trip_id: int
    report_time: time
    route_id: int


class DriverTripsResponse(BaseModel):
    driver_id: int
    date: date
    assigned_trips: List[DriverTrip]


# ----------------------
# Map Schemas
# ----------------------

class RouteMapResponse(BaseModel):
    route_id: int
    stops: List[StopBase]
