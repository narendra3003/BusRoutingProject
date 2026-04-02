from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from datetime import date, time, datetime
from enum import Enum

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


# =========================
# STOP
# =========================
class DriverStopResponse(BaseModel):
    name: str
    coords: List[float]


# =========================
# TRIP
# =========================
class DriverTripResponse(BaseModel):
    id: int
    busNo: str
    time: str
    busName: str
    status: str
    stops: List[DriverStopResponse]


# =========================
# SCHEDULE
# =========================
class DriverScheduleResponse(BaseModel):
    trips: List[DriverTripResponse]


# =========================
# NOTIFICATIONS
# =========================
class DriverNotificationResponse(BaseModel):
    id: int
    message: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None


class DriverNotificationsResponse(BaseModel):
    notifications: List[DriverNotificationResponse]


# =========================
# CALENDAR STATUS
# =========================
class DriverCalendarStatusResponse(BaseModel):
    statusMap: dict


# =========================
# SUMMARY
# =========================
class DriverSummaryResponse(BaseModel):
    totalTrips: int
    totalHours: int
    shifts: List[str]
    firstRoute: Optional[str]

class CustRouteResponse(BaseModel):
    id: str
    name: str

    from_stop: Optional[str]
    to_stop: Optional[str]

    stops: List[str]
    coords: List[List[float]]
    stopOffsets: List[int]

    liveStop: Optional[str]
    etaFromLive: Dict[str, int]

    timetable: Dict[str, List[str]]


class CustStopResponse(BaseModel):
    name: str
    lat: float
    lon: float

# =========================
# CREATE ROUTE
# =========================
class RouteCreate(BaseModel):
    id: str  # example: 101_UP
    name: str
    start_stop_id: int
    end_stop_id: int
    distance_km: Optional[float] = None


# =========================
# UPDATE ROUTE
# =========================
class RouteUpdate(BaseModel):
    name: Optional[str]
    start_stop_id: Optional[int]
    end_stop_id: Optional[int]
    distance_km: Optional[float]
    is_active: Optional[bool]


# =========================
# RESPONSE
# =========================
class RouteResponse(BaseModel):
    id: str
    name: str
    start_stop_id: int
    end_stop_id: int
    distance_km: Optional[float]
    is_active: bool

# =========================
# ENUM
# =========================
class TripStatusEnum(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    delayed = "delayed"


# =========================
# CREATE TRIP
# =========================
class TripCreate(BaseModel):
    route_id: str
    trip_date: date
    start_time: time
    bus_id: int
    driver_id: int


# =========================
# BULK CREATE
# =========================
class BulkTripCreate(BaseModel):
    trips: List[TripCreate]


# =========================
# UPDATE TRIP
# =========================
class TripUpdate(BaseModel):
    bus_id: Optional[int]
    driver_id: Optional[int]
    status: Optional[TripStatusEnum]


# =========================
# RESPONSE
# =========================
class TripResponse(BaseModel):
    id: int
    route_id: str
    trip_date: date
    start_time: time
    bus_id: int
    driver_id: int
    status: str

# =========================
# ENUM
# =========================
class StopTypeEnum(str, Enum):
    stop = "stop"
    terminal = "terminal"
    depot = "depot"


# =========================
# CREATE STOP
# =========================
class StopCreate(BaseModel):
    name: str
    lat: float
    lon: float
    type: Optional[StopTypeEnum] = StopTypeEnum.stop
    zone: Optional[str] = None


# =========================
# UPDATE STOP
# =========================
class StopUpdate(BaseModel):
    name: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    type: Optional[StopTypeEnum]
    zone: Optional[str]
    is_active: Optional[bool]


# =========================
# RESPONSE
# =========================
class StopResponse(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    type: str
    zone: Optional[str]
    is_active: bool

# =========================
# CREATE OVERRIDE
# =========================
class OverrideCreate(BaseModel):
    trip_id: int

    new_driver_id: Optional[int] = None
    new_bus_id: Optional[int] = None

    reason: Optional[str] = None


# =========================
# RESPONSE
# =========================
class OverrideResponse(BaseModel):
    id: int
    trip_id: int

    old_driver_id: Optional[int]
    new_driver_id: Optional[int]

    old_bus_id: Optional[int]
    new_bus_id: Optional[int]

    reason: Optional[str]
    created_by: Optional[int]

# =========================
# CREATE OVERRIDE
# =========================
class OverrideCreate(BaseModel):
    trip_id: int

    new_driver_id: Optional[int] = None
    new_bus_id: Optional[int] = None

    reason: Optional[str] = None


# =========================
# RESPONSE
# =========================
class OverrideResponse(BaseModel):
    id: int
    trip_id: int

    old_driver_id: Optional[int]
    new_driver_id: Optional[int]

    old_bus_id: Optional[int]
    new_bus_id: Optional[int]

    reason: Optional[str]
    created_by: Optional[int]

# =========================
# ENUM
# =========================
class DriverStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"


# =========================
# CREATE DRIVER
# =========================
class DriverCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

    license_no: str
    experience_years: Optional[int] = 0
    joining_date: Optional[date] = None


# =========================
# UPDATE DRIVER
# =========================
class DriverUpdate(BaseModel):
    name: Optional[str]
    phone: Optional[str]
    status: Optional[DriverStatusEnum]
    experience_years: Optional[int]


# =========================
# RESPONSE
# =========================
class DriverResponse(BaseModel):
    user_id: int
    name: str
    email: str
    phone: Optional[str]

    license_no: str
    experience_years: int
    joining_date: Optional[date]
    status: str

# Request for signup
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # customer/admin/driver/uploader

# Response after signup/login
class AuthResponse(BaseModel):
    status: str = "success"
    message: str = "success"
    access_token: str = None
    token_type: str = "bearer"

# Request for login
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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


# ----------------------
# Database-backed entity schemas
# ----------------------


class StopCreate(BaseModel):
    name: str
    lat: float
    lon: float
    type: Optional[str] = None
    zone: Optional[str] = None
    is_active: Optional[bool] = True


class StopResponse(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    type: Optional[str]
    zone: Optional[str]
    is_active: bool
    created_at: datetime


class RouteCreate(BaseModel):
    id: str
    name: str
    start_stop_id: int
    end_stop_id: int
    distance_km: Optional[float] = None
    is_active: Optional[bool] = True


class RouteResponse(BaseModel):
    id: str
    name: str
    start_stop_id: int
    end_stop_id: int
    distance_km: Optional[float]
    is_active: bool
    created_at: datetime


class RouteStopCreate(BaseModel):
    route_id: str
    stop_id: int
    seq: int
    dist_from_start: Optional[float] = None
    time_from_start: Optional[int] = None


class RouteStopResponse(BaseModel):
    seq: int
    stop: StopResponse
    time_from_start: Optional[int]
    dist_from_start: Optional[float]


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class BusCreate(BaseModel):
    code: str
    sitting_capacity: int
    standing_capacity: Optional[int] = 0
    status: Optional[str] = None


class BusResponse(BaseModel):
    id: int
    code: str
    sitting_capacity: int
    standing_capacity: int
    status: str
    created_at: datetime


class DriverLeaveResponse(BaseModel):
    id: int
    driver_id: int
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    created_at: datetime


class DriverLeaveCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = None


class ScheduleTripCreate(BaseModel):
    route_id: str
    trip_date: date
    start_time: time
    bus_id: int
    driver_id: int


class ScheduleTripResponse(BaseModel):
    id: int
    route_id: str
    trip_date: date
    start_time: time
    bus_id: int
    driver_id: int
    status: str
    created_at: datetime
    updated_at: datetime


class OverrideCreate(BaseModel):
    trip_id: int
    new_driver_id: Optional[int] = None
    new_bus_id: Optional[int] = None
    reason: Optional[str] = None


class OverrideResponse(BaseModel):
    id: int
    trip_id: int
    old_driver_id: Optional[int]
    new_driver_id: Optional[int]
    old_bus_id: Optional[int]
    new_bus_id: Optional[int]
    reason: Optional[str]
    created_by: Optional[int]
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    type: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime


class TripLiveStatusResponse(BaseModel):
    trip_id: int
    current_stop_id: Optional[int]
    delay_minutes: int
    last_lat: Optional[float]
    last_lon: Optional[float]
    last_updated: datetime
