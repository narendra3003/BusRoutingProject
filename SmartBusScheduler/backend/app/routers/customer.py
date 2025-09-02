from fastapi import APIRouter, Depends
from typing import List
from ..schemas import TripSchema, StopSchema
from ..auth import verify_token

router = APIRouter()

# Mock data
stops_data = [
    {"id": 56, "name": "Central", "lat": 19.123, "lon": 72.835},
    {"id": 57, "name": "Park", "lat": 19.130, "lon": 72.840},
]

trips_data = [
    {"id": 101, "route_id": 12, "start_time": "08:00", "end_time": "08:45"},
    {"id": 102, "route_id": 12, "start_time": "09:00", "end_time": "09:45"},
]

@router.get("/schedules/{route_id}")
def get_schedules(route_id: int, stop_id: int = None, token: dict = Depends(verify_token)):
    previous_trips = [trip for trip in trips_data if trip["start_time"] < "09:00"]
    next_trips = [trip for trip in trips_data if trip["start_time"] >= "09:00"]
    return {
        "route_id": route_id,
        "date": "2025-09-02",
        "previous_trips": previous_trips,
        "next_trips": next_trips
    }

@router.get("/routes/{route_id}/stops", response_model=List[StopSchema])
def get_stops(route_id: int, token: dict = Depends(verify_token)):
    return stops_data
