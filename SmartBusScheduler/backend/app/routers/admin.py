from fastapi import APIRouter, Depends, HTTPException
from ..schemas import OverrideRequest, OverrideResponse, AdminScheduleResponse, AdminTrip, KPIResponse
from datetime import date, time
from ..utils.dependencies import role_allowed

router = APIRouter()

# 5. Schedule overrides
@router.post("/schedules/override", response_model=OverrideResponse)
def apply_override(
    request: OverrideRequest,
    _: None = Depends(role_allowed("admin"))
):
    return {"status": "success", "message": "Override applied"}

# 6. Admin view past/future trips
@router.get("/schedules", response_model=AdminScheduleResponse)
def view_schedules(
    route_id: int,
    date: date,
    _: None = Depends(role_allowed("admin"))
):
    
    return AdminScheduleResponse(
        route_id=route_id,
        date=date,
        trips=[
            AdminTrip(trip_id=201, start_time=time(6,0), end_time=time(6,40)),
            AdminTrip(trip_id=202, start_time=time(7,0), end_time=time(7,45)),
        ]
    )

# 7. KPI calculations
@router.get("/kpis", response_model=KPIResponse)
def get_kpis(date: date, _: None = Depends(role_allowed("admin"))):
    return KPIResponse(date=date, avg_wait_time=5.3, buses_used=12, load_factor=0.82)
