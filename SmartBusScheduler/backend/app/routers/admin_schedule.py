"""
SmartBusScheduler - Admin Schedule Router
Handles:
- Uploading OB Data
- Generating Templates
- Generating Schedules
- Managing Trips (CRUD)

Designed for the provided PostgreSQL schema.
"""

# =========================================================
# IMPORTS
# =========================================================
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, date, timedelta, time
from collections import defaultdict
from typing import List
import csv
import io
import math

from ..database import get_db
from ..models import (
    ScheduleTrip,
    Driver,
    Bus,
    Route,
    DriverLeave,
    OBData,
    Template,
    TemplateRecord,
    User,
)
from ..models import (
    LeaveStatus,
    TripStatus,
    BusStatus,
    DriverStatus,
)
from ..schemas import (
    TripCreate,
    BulkTripCreate,
    TripUpdate,
    TripResponse,
)
from ..utils import get_current_user

# =========================================================
# ROUTER
# =========================================================
router = APIRouter()

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def check_admin(user: dict):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def format_trip(db: Session, trip: ScheduleTrip):
    route_name = db.query(Route.name).filter(Route.id == trip.route_id).scalar()
    driver_name = db.query(User.name).filter(User.id == trip.driver_id).scalar()
    bus_code = db.query(Bus.code).filter(Bus.id == trip.bus_id).scalar()

    return {
        "id": trip.id,
        "route_id": trip.route_id,
        "route_name": route_name,
        "trip_date": str(trip.trip_date),
        "start_time": str(trip.start_time),
        "driver_id": trip.driver_id,
        "driver_name": driver_name,
        "bus_id": trip.bus_id,
        "bus_code": bus_code,
        "status": trip.status.value,
    }


# =========================================================
# VALIDATION HELPERS
# =========================================================
def check_driver_leave(db, driver_id, trip_date):
    leave = db.query(DriverLeave).filter(
        DriverLeave.driver_id == driver_id,
        DriverLeave.start_date <= trip_date,
        DriverLeave.end_date >= trip_date,
        DriverLeave.status == LeaveStatus.granted,
    ).first()

    if leave:
        raise HTTPException(
            status_code=400,
            detail=f"Driver {driver_id} is on leave."
        )


def check_driver_available(db, driver_id, trip_date, start_time):
    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.driver_id == driver_id,
        ScheduleTrip.trip_date == trip_date,
        ScheduleTrip.start_time == start_time,
    ).first()

    if trip:
        raise HTTPException(
            status_code=400,
            detail=f"Driver {driver_id} is already assigned."
        )


def check_bus_available(db, bus_id, trip_date, start_time):
    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.bus_id == bus_id,
        ScheduleTrip.trip_date == trip_date,
        ScheduleTrip.start_time == start_time,
    ).first()

    if trip:
        raise HTTPException(
            status_code=400,
            detail=f"Bus {bus_id} is already assigned."
        )


# =========================================================
# CSV PARSING
# =========================================================
def parse_csv(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    required_fields = {
        "route_id",
        "stop_id",
        "boarding_count",
        "offboarding_count",
        "trip_datetime",
    }

    if not required_fields.issubset(reader.fieldnames):
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    return list(reader)


# =========================================================
# DEMAND COMPUTATION
# =========================================================
def time_to_slot(dt: datetime):
    return dt.replace(minute=0, second=0, microsecond=0)


def compute_route_demand(ob_rows):
    demand = defaultdict(lambda: defaultdict(list))

    for row in ob_rows:
        route = row.route_id
        slot = time_to_slot(row.trip_datetime)
        passengers = max(0, row.boarding_count - row.offboarding_count)
        demand[route][slot].append(passengers)

    final = {}
    for route, slots in demand.items():
        final[route] = {}
        for slot, values in slots.items():
            final[route][slot] = int(sum(values) / len(values))

    return final


# =========================================================
# RESOURCE ASSIGNMENT
# =========================================================
def assign_resources(db: Session, trips, trip_date):
    buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()

    if not buses or not drivers:
        return []

    assigned = []
    bus_idx = 0
    driver_idx = 0

    for trip in trips:
        driver_assigned = False

        for _ in range(len(drivers)):
            driver = drivers[driver_idx % len(drivers)]
            driver_idx += 1

            leave = db.query(DriverLeave).filter(
                DriverLeave.driver_id == driver.user_id,
                DriverLeave.start_date <= trip_date,
                DriverLeave.end_date >= trip_date,
                DriverLeave.status == LeaveStatus.granted,
            ).first()

            conflict = db.query(ScheduleTrip).filter(
                ScheduleTrip.driver_id == driver.user_id,
                ScheduleTrip.trip_date == trip_date,
                ScheduleTrip.start_time == trip.start_time,
            ).first()

            if not leave and not conflict:
                trip.driver_id = driver.user_id
                driver_assigned = True
                break

        if not driver_assigned:
            continue

        bus = buses[bus_idx % len(buses)]
        trip.bus_id = bus.id
        bus_idx += 1
        assigned.append(trip)

    return assigned


# =========================================================
# UPLOAD OBSERVATIONS
# =========================================================
@router.post("/upload-observations")
def upload_observations(
    file: UploadFile = File(...),
    overwrite: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)
    rows = parse_csv(file)

    if overwrite:
        db.query(OBData).delete()
        db.commit()

    objects = []
    for r in rows:
        dt = datetime.strptime(r["trip_datetime"], "%Y-%m-%d %H:%M:%S")
        objects.append(
            OBData(
                route_id=r["route_id"],
                stop_id=int(r["stop_id"]),
                boarding_count=int(r["boarding_count"]),
                offboarding_count=int(r["offboarding_count"]),
                trip_datetime=dt,
            )
        )

    db.bulk_save_objects(objects)
    db.commit()

    return {"message": f"{len(objects)} records inserted"}


# =========================================================
# GENERATE TEMPLATES
# =========================================================
@router.post("/generate-templates")
def generate_templates(
    name: str = "Auto Template",
    description: str = "Generated from OB data",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    ob_rows = db.query(OBData).all()
    if not ob_rows:
        raise HTTPException(status_code=400, detail="No OB data found.")

    demand = compute_route_demand(ob_rows)

    buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()

    if not buses or not drivers:
        raise HTTPException(status_code=400, detail="No active resources available.")

    avg_capacity = sum(b.sitting_capacity for b in buses) / len(buses)
    avg_capacity = max(avg_capacity, 1)

    template = Template(
        name=name,
        description=description,
        template_type="auto",
        bus_count=len(buses),
        driver_count=len(drivers),
        created_by=current_user.get("id"),
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    records = []
    for route, slots in demand.items():
        for slot, passengers in slots.items():
            trips_needed = max(1, math.ceil(passengers / avg_capacity))
            gap = max(5, int(60 / trips_needed))

            for i in range(trips_needed):
                start_time = (
                    datetime.combine(date.today(), slot.time())
                    + timedelta(minutes=i * gap)
                ).time()

                records.append(
                    TemplateRecord(
                        template_id=template.id,
                        route_id=route,
                        start_time=start_time,
                    )
                )

    db.bulk_save_objects(records)
    db.commit()

    return {
        "message": "Template generated successfully",
        "template_id": template.id,
        "records": len(records),
    }


# =========================================================
# FETCH TEMPLATES
# =========================================================
@router.get("/templates")
def get_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    templates = db.query(Template).order_by(Template.created_at.desc()).all()

    return templates


@router.get("/templates/{template_id}")
def get_template_details(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    records = db.query(TemplateRecord).filter(
        TemplateRecord.template_id == template_id
    ).all()

    return [
        {
            "route_id": r.route_id,
            "start_time": str(r.start_time),
        }
        for r in records
    ]


# =========================================================
# GENERATE SCHEDULE FROM TEMPLATE
# =========================================================
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, date


@router.post("/generate-schedule")
def generate_schedule(
    template_id: int,
    start_date: str,
    end_date: str,
    overwrite: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    # -----------------------------------------------------
    # Helper to parse date in multiple formats
    # -----------------------------------------------------
    def parse_date(value: str) -> date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY."
        )

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    if end_date < start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")

    # -----------------------------------------------------
    # Fetch Template
    # -----------------------------------------------------
    template = db.query(Template).filter(
        Template.id == template_id
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    records = db.query(TemplateRecord).filter(
        TemplateRecord.template_id == template_id
    ).all()

    if not records:
        raise HTTPException(status_code=400, detail="No template records found")

    # -----------------------------------------------------
    # Delete Existing Trips (if overwrite enabled)
    # -----------------------------------------------------
    if overwrite:
        db.query(ScheduleTrip).filter(
            ScheduleTrip.trip_date.between(start_date, end_date)
        ).delete(synchronize_session=False)
        db.commit()

    # -----------------------------------------------------
    # Generate Trips
    # -----------------------------------------------------
    all_trips = []
    existing_keys = set()

    current_date = start_date

    while current_date <= end_date:
        trips = [
            ScheduleTrip(
                route_id=r.route_id,
                trip_date=current_date,
                start_time=r.start_time,
                status=TripStatus.scheduled,
            )
            for r in records
        ]

        assigned_trips = assign_resources(db, trips, current_date)

        for trip in assigned_trips:
            key = (trip.route_id, trip.trip_date, trip.start_time)

            # Prevent duplicates in the same batch
            if key not in existing_keys:
                existing_keys.add(key)

                # Prevent duplicates already in DB
                exists = db.query(ScheduleTrip).filter(
                    ScheduleTrip.route_id == trip.route_id,
                    ScheduleTrip.trip_date == trip.trip_date,
                    ScheduleTrip.start_time == trip.start_time,
                ).first()

                if not exists:
                    all_trips.append(trip)

        current_date += timedelta(days=1)

    if not all_trips:
        raise HTTPException(
            status_code=400,
            detail="No new trips generated. They may already exist."
        )

    # -----------------------------------------------------
    # Save Trips
    # -----------------------------------------------------
    try:
        db.bulk_save_objects(all_trips)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Duplicate trips detected. Please regenerate templates."
        )

    # -----------------------------------------------------
    # Response Logs
    # -----------------------------------------------------
    logs = []
    for trip in all_trips:
        route_name = db.query(Route.name).filter(
            Route.id == trip.route_id
        ).scalar()

        driver_name = db.query(User.name).filter(
            User.id == trip.driver_id
        ).scalar()

        bus_code = db.query(Bus.code).filter(
            Bus.id == trip.bus_id
        ).scalar()

        logs.append({
            "trip_date": str(trip.trip_date),
            "start_time": str(trip.start_time),
            "route_name": route_name,
            "driver_name": driver_name,
            "bus_code": bus_code,
            "status": trip.status.value,
        })

    return {
        "summary": {
            "total_trips": len(all_trips),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "template_used": template.name,
        },
        "logs": logs,
    }


# =========================================================
# CREATE TRIP
# =========================================================
@router.post("/", response_model=TripResponse)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    check_driver_available(
        db, payload.driver_id, payload.trip_date, payload.start_time
    )
    check_bus_available(
        db, payload.bus_id, payload.trip_date, payload.start_time
    )
    check_driver_leave(db, payload.driver_id, payload.trip_date)

    trip = ScheduleTrip(**payload.dict(), status=TripStatus.scheduled)
    db.add(trip)
    db.commit()
    db.refresh(trip)

    return format_trip(db, trip)


# =========================================================
# GET SCHEDULE
# =========================================================
@router.get("/", response_model=List[TripResponse])
def get_schedule(
    trip_date: date | None = Query(None),
    route_id: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    query = db.query(ScheduleTrip)

    if trip_date:
        query = query.filter(ScheduleTrip.trip_date == trip_date)
    if route_id:
        query = query.filter(ScheduleTrip.route_id == route_id)

    trips = query.order_by(
        ScheduleTrip.trip_date,
        ScheduleTrip.start_time
    ).all()

    return [format_trip(db, t) for t in trips]


# =========================================================
# UPDATE TRIP
# =========================================================
@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(trip, key, value)

    db.commit()
    db.refresh(trip)

    return format_trip(db, trip)


# =========================================================
# DELETE TRIP
# =========================================================
@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(
        ScheduleTrip.id == trip_id
    ).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db.delete(trip)
    db.commit()

    return {"status": "deleted", "trip_id": trip_id}