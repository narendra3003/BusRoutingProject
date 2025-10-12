from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as DateType, datetime, time as TimeType
from ..database import get_db
from .. import models
from ..schemas import OverrideRequest, OverrideResponse, AdminScheduleResponse, AdminTrip, KPIResponse
from ..utils import get_current_user

router = APIRouter()

# 5. Schedule overrides
@router.post("/schedules/override", response_model=OverrideResponse)
def apply_override(request: OverrideRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    ov = models.AdminOverride(
        trip_id=request.trip_id,
        delta_minutes=request.delta_minutes,
        effective_date=request.date,
        reason=request.reason
    )
    db.add(ov)
    db.commit()
    return {"status": "success", "message": "Override applied"}

# 6. Admin view past/future trips
@router.get("/schedules", response_model=AdminScheduleResponse)
def view_schedules(route_id: int, date: DateType, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    trips = db.query(models.Trip).filter(
        models.Trip.route_id == route_id,
        models.Trip.date == date
    ).all()

    admin_trips = []
    for trip in trips:
        if not trip.stop_times:
            continue
        starts = [st.arrival_time for st in trip.stop_times if st.arrival_time]
        ends = [st.departure_time for st in trip.stop_times if st.departure_time]
        if not starts or not ends:
            continue
        admin_trips.append(AdminTrip(trip_id=trip.trip_id, start_time=min(starts), end_time=max(ends)))

    return AdminScheduleResponse(route_id=route_id, date=date, trips=admin_trips)

# 7. KPI calculations
@router.get("/kpis", response_model=KPIResponse)
def get_kpis(date: DateType, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    # simple computations
    trips = db.query(models.Trip).filter(models.Trip.date == date).all()
    buses_used = len({t.service_id for t in trips if t.service_id}) or 0

    # total boardings on the day (all routes)
    day_start = datetime.combine(date, TimeType(0, 0))
    day_end = datetime.combine(date, TimeType(23, 59, 59))
    boardings = db.query(models.ObservationData).filter(
        models.ObservationData.timestamp >= day_start,
        models.ObservationData.timestamp <= day_end
    ).with_entities(models.ObservationData.boarding_count).all()
    total_boardings = sum(r[0] for r in boardings) if boardings else 0

    # naive metrics
    avg_wait_time = 5.0  # placeholder avg wait estimate (minutes)
    capacity = max(1, buses_used) * 40
    load_factor = round(min(1.0, (total_boardings / capacity) if capacity else 0.0), 2)

    return KPIResponse(date=date, avg_wait_time=avg_wait_time, buses_used=buses_used, load_factor=load_factor)
