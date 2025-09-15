from fastapi import APIRouter, Depends, HTTPException
from ..schemas import ObservationUpload, ObservationResponse, OptimizeRequest, OptimizeResponse, OptimizedTrip
from datetime import date, time
from ..utils.dependencies import role_allowed

router = APIRouter()

# 3. Upload passenger density and bus data
@router.post("/observations/upload", response_model=ObservationResponse)
def upload_observation(data: ObservationUpload, _: None = Depends(role_allowed("admin"))):
    
    return {"status": "success", "message": "Observation uploaded"}

# 4. Trigger automated schedule plan
@router.post("/schedules/optimize", response_model=OptimizeResponse)
def optimize_schedule(request: OptimizeRequest, _: None = Depends(role_allowed("admin"))):
    
    return OptimizeResponse(
        route_id=request.route_id,
        date=request.date,
        optimized_trips=[OptimizedTrip(trip_id=223, start_time=time(7,0), end_time=time(7,45), bus_count=3)]
    )
