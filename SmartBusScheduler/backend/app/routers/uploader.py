from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import ObservationUpload, ObservationResponse, OptimizeRequest, OptimizeResponse, OptimizedTrip
from ..utils import get_current_user
from datetime import datetime, date, time, timedelta

router = APIRouter()

# 3. Upload passenger density and bus data
@router.post("/observations/upload", response_model=ObservationResponse)
def upload_observation(data: ObservationUpload, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")

    obs = models.ObservationData(
        bus_no=data.bus_no,
        route_id=data.route_id,
        stop_id=data.stop_id,
        boarding_count=data.boarding_count,
        alighting_count=data.alighting_count,
        timestamp=data.timestamp
    )
    db.add(obs)
    db.commit()
    return {"status": "success", "message": "Observation uploaded"}

# 4. Trigger automated schedule plan
@router.post("/schedules/optimize", response_model=OptimizeResponse)
def optimize_schedule(request: OptimizeRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")

    day_start = datetime.combine(request.date, time(0, 0))
    day_end = datetime.combine(request.date, time(23, 59, 59))

    total_boardings = db.query(models.ObservationData).filter(
        models.ObservationData.route_id == request.route_id,
        models.ObservationData.timestamp >= day_start,
        models.ObservationData.timestamp <= day_end
    ).with_entities(models.ObservationData.boarding_count).all()

    demand = sum(r[0] for r in total_boardings) if total_boardings else 0
    # naive bus count: 40 pax per bus per window
    bus_count = max(1, demand // 40) if demand else 1

    return OptimizeResponse(
        route_id=request.route_id,
        date=request.date,
        optimized_trips=[OptimizedTrip(trip_id=223, start_time=time(7, 0), end_time=time(7, 45), bus_count=bus_count)]
    )
