from fastapi import APIRouter, Depends, HTTPException
from ..schemas import DriverTripsResponse, DriverTrip
from datetime import date, time
from ..utils.dependencies import role_allowed

router = APIRouter()

# 8. Get driver trips
@router.get("/{driver_id}/trips", response_model=DriverTripsResponse)
def get_driver_trips(driver_id: int, date: date, _: None = Depends(role_allowed("driver"))):
    return DriverTripsResponse(
        driver_id=driver_id,
        date=date,
        assigned_trips=[
            DriverTrip(trip_id=1234, report_time=time(6,30), route_id=12)
        ]
    )
