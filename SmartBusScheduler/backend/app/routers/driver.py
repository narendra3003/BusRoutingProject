from fastapi import APIRouter, Depends, HTTPException
from ..utils import get_current_user
from ..schemas import DriverTripsResponse, DriverTrip
from datetime import date as DateType
from ..database import get_db
from .. import models
from sqlalchemy.orm import Session

router = APIRouter()

# 8. Get driver trips
@router.get("/{driver_id}/trips", response_model=DriverTripsResponse)
def get_driver_trips(driver_id: int, date: DateType, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Drivers only")

    trips = db.query(models.Trip).join(models.Service, models.Trip.service_id == models.Service.service_id).filter(
        models.Service.driver_id == driver_id,
        models.Trip.date == date
    ).all()

    assigned = []
    for t in trips:
        if not t.stop_times:
            continue
        # report time = earliest arrival_time for the trip
        starts = [st.arrival_time for st in t.stop_times if st.arrival_time]
        if not starts:
            continue
        assigned.append(DriverTrip(trip_id=t.trip_id, report_time=min(starts), route_id=t.route_id))

    return DriverTripsResponse(driver_id=driver_id, date=date, assigned_trips=assigned)
