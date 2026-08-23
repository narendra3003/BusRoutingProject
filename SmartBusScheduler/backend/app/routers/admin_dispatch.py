from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..models import ScheduleTrip, Route, Bus, Driver, User, TripLiveStatus
from ..database import get_db
from ..utils import get_current_user
from ..schemas import DispatchResponse
from .auth import check_admin
from typing import List, Optional
from datetime import date


router = APIRouter()

@router.get("/", response_model=List[DispatchResponse])
def get_dispatch(
    date: date = Query(..., description="Trip date in YYYY-MM-DD format"),
    route_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch dispatch trips for a specific date with optional filters.
    """
    check_admin(current_user)

    try:
        query = (
            db.query(
                ScheduleTrip.id,
                ScheduleTrip.start_time,
                Route.name.label("route_name"),
                User.name.label("driver_name"),
                Bus.code.label("bus_code"),
                ScheduleTrip.status,
                TripLiveStatus.delay_minutes,
            )
            .join(Route, ScheduleTrip.route_id == Route.id)
            .join(Bus, ScheduleTrip.bus_id == Bus.id)
            .join(Driver, ScheduleTrip.driver_id == Driver.user_id)
            .join(User, Driver.user_id == User.id)
            .outerjoin(
                TripLiveStatus,
                TripLiveStatus.trip_id == ScheduleTrip.id
            )
            .filter(ScheduleTrip.trip_date == date)
        )

        # Apply optional filters
        if route_id:
            query = query.filter(ScheduleTrip.route_id == route_id)

        if status:
            query = query.filter(ScheduleTrip.status == status)

        results = query.order_by(ScheduleTrip.start_time).all()

        return [
            {
                "id": r.id,
                "start_time": r.start_time.strftime("%H:%M"),
                "route_name": r.route_name,
                "driver_name": r.driver_name,
                "bus_code": r.bus_code,
                "delay_minutes": r.delay_minutes or 0,
                "status": r.status.value if hasattr(r.status, "value") else r.status,
            }
            for r in results
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))