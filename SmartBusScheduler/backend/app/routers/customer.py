from fastapi import APIRouter, Depends, HTTPException
from typing import List
from ..schemas import ScheduleResponse, RouteStopsResponse, StopBase
from datetime import date, time
from ..utils import get_current_user

router = APIRouter()

# 1. Get schedules for route or stop (today)
@router.get("/schedules/{route_id}", response_model=ScheduleResponse)
def get_schedule(route_id: int, stop_id: int, current_user: dict = Depends(get_current_user)):
    # current_user = {"user_id": 1, "role": "customer"}
    if current_user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Access denied")
    return ScheduleResponse(
        route_id=route_id,
        date=date.today(),
        previous_trips=[{
            "trip_id": 101, "arrival_time": time(8, 0), "departure_time": time(8, 5), 
            "stop_id": stop_id, "stop_name": "Central"
        }],
        next_trips=[{
            "trip_id": 102, "arrival_time": time(9, 0), "departure_time": time(9, 5), 
            "stop_id": stop_id, "stop_name": "Central"
        }]
    )

# 2. Get stops for a route
@router.get("/routes/{route_id}/stops", response_model=RouteStopsResponse)
def get_stops(route_id: int):
    return RouteStopsResponse(
        route_id=route_id,
        stops=[
            StopBase(stop_id=56, stop_name="Central", lat=19.123, lon=72.835),
            StopBase(stop_id=57, stop_name="Park", lat=19.130, lon=72.840),
        ]
    )
