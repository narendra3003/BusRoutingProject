from pydantic import BaseModel
from typing import List, Optional

class StopSchema(BaseModel):
    id: int
    name: str
    lat: float
    lon: float

    class Config:
        orm_mode = True

class TripSchema(BaseModel):
    id: int
    route_id: int
    start_time: str
    end_time: str

    class Config:
        orm_mode = True

class ObservationCreate(BaseModel):
    bus_no: str
    route_id: int
    stop_id: int
    boarding_count: int
    alighting_count: int
    timestamp: str

class OverrideSchema(BaseModel):
    trip_id: int
    delta_minutes: int
    date: str
    reason: Optional[str] = None
