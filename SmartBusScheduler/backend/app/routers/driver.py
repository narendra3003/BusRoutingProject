from fastapi import APIRouter, Depends
from ..auth import verify_token

router = APIRouter()

# Mock assigned trips
assigned_trips = [
    {"trip_id": 1234, "report_time": "06:30", "route_id": 12}
]

@router.get("/{driver_id}/trips")
def driver_trips(driver_id: int, date: str, token: dict = Depends(verify_token)):
    return {
        "driver_id": driver_id,
        "date": date,
        "assigned_trips": assigned_trips
    }
