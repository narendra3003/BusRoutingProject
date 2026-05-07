from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime, timedelta

from ..database import get_db
from ..models import (
    User,
    Driver,
    ScheduleTrip,
    RouteStop,
    Stop,
    Route,
    Bus,
    TripLiveStatus,
    TripStatus,
    Notification,
    DriverLeave
)
from ..schemas import (
    DriverScheduleResponse,
    DriverTripResponse,
    DriverStopResponse,
    DriverNotificationsResponse,
    DriverNotificationResponse,
    DriverCalendarStatusResponse,
    DriverSummaryResponse,
    ScheduleResponse,
)
from ..utils import get_current_user

router = APIRouter()


# =========================
# HELPER
# =========================
def format_trip(trip: ScheduleTrip):
    return {
        "trip_id": trip.id,
        "trip_date": trip.trip_date,
        "start_time": trip.start_time,
        "status": trip.status.value,
        "route": {
            "id": trip.route.id,
            "name": trip.route.name
        } if trip.route else None,
        "bus": {
            "id": trip.bus.id,
            "code": trip.bus.code
        } if trip.bus else None
    }


# =========================
# GET DRIVER PROFILE
# =========================
@router.get("/profile")
def get_driver_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    driver = db.query(Driver).filter(Driver.user_id == current_user["user_id"]).first()

    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    return {
        "user_id": driver.user_id,
        "name": driver.user.name,
        "email": driver.user.email,
        "phone": driver.user.phone,
        "license_no": driver.license_no,
        "experience_years": driver.experience_years,
        "status": driver.status.value
    }

# =========================
# GET TODAY'S TRIPS
# =========================
@router.get("/trips/today")
def get_today_trips(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    today = date.today()

    trips = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(
        ScheduleTrip.driver_id == current_user["user_id"],
        ScheduleTrip.trip_date == today
    ).order_by(ScheduleTrip.start_time).all()

    return {
        "date": today,
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# GET ALL TRIPS (FILTER)
# =========================
@router.get("/trips")
def get_driver_trips(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    query = db.query(ScheduleTrip).options(
        joinedload(ScheduleTrip.route),
        joinedload(ScheduleTrip.bus)
    ).filter(ScheduleTrip.driver_id == current_user["user_id"])

    if start_date:
        query = query.filter(ScheduleTrip.trip_date >= start_date)

    if end_date:
        query = query.filter(ScheduleTrip.trip_date <= end_date)

    trips = query.order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return {
        "total_trips": len(trips),
        "trips": [format_trip(t) for t in trips]
    }


# =========================
# UPDATE TRIP STATUS
# =========================
@router.put("/trips/{trip_id}/status")
def update_trip_status(
    trip_id: int,
    status: TripStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    trip.status = status
    db.commit()

    return {
        "status": "updated",
        "trip_id": trip_id,
        "new_status": status.value
    }


# =========================
# GET LIVE STATUS
# =========================
@router.get("/trips/{trip_id}/live")
def get_live_status(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user["role"] != "driver":
        raise HTTPException(status_code=403, detail="Only drivers allowed")

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if trip.driver_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not your trip")

    live = db.query(TripLiveStatus).filter(
        TripLiveStatus.trip_id == trip_id
    ).first()

    if not live:
        return {"message": "No live data available"}

    return {
        "trip_id": trip_id,
        "current_stop_id": live.current_stop_id,
        "delay_minutes": live.delay_minutes,
        "last_location": {
            "lat": live.last_lat,
            "lon": live.last_lon
        },
        "last_updated": live.last_updated
    }

# =========================
# GET SCHEDULE
# =========================
@router.get("/schedule", response_model=DriverScheduleResponse)
def get_schedule(
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trips = (
        db.query(ScheduleTrip)
        .filter(
            ScheduleTrip.trip_date == date,
            ScheduleTrip.driver_id == current_user["user_id"],
        )
        .all()
    )

    response_trips = []

    for trip in trips:
        route = db.query(Route).filter(Route.id == trip.route_id).first()
        bus = db.query(Bus).filter(Bus.id == trip.bus_id).first()

        route_stops = (
            db.query(RouteStop)
            .filter(RouteStop.route_id == route.id)
            .order_by(RouteStop.seq)
            .all()
        )

        stops = []
        for rs in route_stops:
            stop = db.query(Stop).filter(Stop.id == rs.stop_id).first()
            stops.append(
                DriverStopResponse(
                    name=stop.name,
                    coords=[stop.lat, stop.lon],
                )
            )

        """
            Instead of fixed 2 hours, you can later:
            Use route_stops.time_from_start
            Or store duration_minutes in route
        """
        end_time = (
            datetime.combine(date, trip.start_time) + timedelta(hours=2)
        ).time()

        time = f"{trip.start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"

        response_trips.append(
            DriverTripResponse(
                id=trip.id,
                busno=bus.code,
                time=time,
                busName=f"{route.name}",
                status=trip.status.value,
                stops=stops,
            )
        )

    return {"trips": response_trips}

@router.get("/notifications", response_model=DriverNotificationsResponse)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notes = (
        db.query(Notification)
        .filter(Notification.user_id == current_user["user_id"])
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "notifications": [
            DriverNotificationResponse(
                id=n.id,
                message=n.message,
                created_at=n.created_at,
                title=n.title
            )
            for n in notes
        ]
    }

@router.get("/calendar-status", response_model=DriverCalendarStatusResponse)
def get_calendar_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    status_map = {}

    # Trips → assigned
    trips = db.query(ScheduleTrip).filter(
         # user user_id to get driver_id 
        ScheduleTrip.driver_id == current_user["user_id"]
    ).all()

    for t in trips:
        status_map[str(t.trip_date)] = "assigned"

    # Leaves
    leaves = db.query(DriverLeave).filter(
        DriverLeave.driver_id == current_user["user_id"]
    ).all()

    for l in leaves:
        current = l.start_date
        while current <= l.end_date:
            status_map[str(current)] = (
                "leave-applied"
                if l.status.value == "pending"
                else "holiday"
            )
            current += timedelta(days=1)

    return {"statusMap": status_map}
from datetime import timedelta

@router.get("/summary", response_model=DriverSummaryResponse)
def get_summary(
    date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trips = db.query(ScheduleTrip).filter(
        ScheduleTrip.driver_id == current_user["user_id"],
        ScheduleTrip.trip_date == date
    ).all()

    total_trips = len(trips)

    # total hours (simple calculation)
    total_hours = 0
    shifts = set()
    first_route = None

    for trip in trips:
        if trip.start_time:
            end_time = datetime.combine(date, trip.start_time) + timedelta(hours=2)

            duration = end_time - datetime.combine(date, trip.start_time)

            total_hours += duration.total_seconds() / 3600

        # Example shift logic
        if trip.start_time.hour < 12:
            shifts.add("Morning")
        else:
            shifts.add("Afternoon")

        if not first_route:
            route = db.query(Route).filter(Route.id == trip.route_id).first()
            first_route = route.name if route else None

    return {
        "totalTrips": total_trips,
        "totalHours": round(total_hours),
        "shifts": list(shifts),
        "firstRoute": first_route
    }