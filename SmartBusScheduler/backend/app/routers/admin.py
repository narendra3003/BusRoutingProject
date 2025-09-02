from fastapi import APIRouter, Depends
from ..schemas import TripSchema, OverrideSchema
from ..auth import verify_token

router = APIRouter()

# Mock trips
trips_data = [
    {"id": 201, "route_id": 12, "start_time": "06:00", "end_time": "06:40"},
    {"id": 202, "route_id": 12, "start_time": "07:00", "end_time": "07:45"},
]

@router.get("/schedules")
def view_schedules(route_id: int, date: str, token: dict = Depends(verify_token)):
    return {
        "route_id": route_id,
        "date": date,
        "trips": trips_data
    }

@router.get("/kpis")
def kpis(date: str, token: dict = Depends(verify_token)):
    return {
        "date": date,
        "avg_wait_time": 5.3,
        "buses_used": 12,
        "load_factor": 0.82
    }

@router.post("/schedules/override")
def override_schedule(override: OverrideSchema, token: dict = Depends(verify_token)):
    return {"status": "success", "message": f"Override applied to trip {override.trip_id}"}
