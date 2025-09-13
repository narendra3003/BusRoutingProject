from fastapi import APIRouter, Depends, HTTPException
from ..utils import get_current_user
from ..schemas import DriverTripsResponse, DriverTrip
from datetime import date, time

router = APIRouter()

# 8. Get driver trips
@router.get("/{driver_id}/trips", response_model=DriverTripsResponse)
def get_driver_trips(driver_id: int, date: date, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Drivers only")
    return DriverTripsResponse(
        driver_id=driver_id,
        date=date,
        assigned_trips=[
            DriverTrip(trip_id=1234, report_time=time(6,30), route_id=12)
        ]
    )
