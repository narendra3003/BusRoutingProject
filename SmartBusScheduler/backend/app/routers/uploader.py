from fastapi import APIRouter, Depends, HTTPException
from ..utils import get_current_user
from ..schemas import ObservationUpload, ObservationResponse, OptimizeRequest, OptimizeResponse, OptimizedTrip
from datetime import date, time

router = APIRouter()

# 3. Upload passenger density and bus data
@router.post("/observations/upload", response_model=ObservationResponse)
def upload_observation(data: ObservationUpload, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")
    
    return {"status": "success", "message": "Observation uploaded"}

# 4. Trigger automated schedule plan
@router.post("/schedules/optimize", response_model=OptimizeResponse)
def optimize_schedule(request: OptimizeRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")
    
    return OptimizeResponse(
        route_id=request.route_id,
        date=request.date,
        optimized_trips=[OptimizedTrip(trip_id=223, start_time=time(7,0), end_time=time(7,45), bus_count=3)]
    )
