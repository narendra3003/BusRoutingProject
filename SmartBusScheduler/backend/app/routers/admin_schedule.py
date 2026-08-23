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
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, and_, case
from datetime import datetime, date, timedelta, time
from collections import defaultdict
from typing import List
import csv
import io
import math

from ..database import get_db
from ..models import (
    RouteStop,
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
        "route_id","origin_stop_id","destination_stop_id","trip_datetime","boarding_count"
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
                origin_stop_id=r["origin_stop_id"],
                destination_stop_id=r["destination_stop_id"],
                trip_datetime=dt,
                boarding_count=int(r["boarding_count"]),
            )
        )

    db.bulk_save_objects(objects)
    db.commit()

    return {"message": f"{len(objects)} records inserted"}

# =========================================================
# CONFIG
# =========================================================
SLOT_MINUTES = 30
LOOKAHEAD_WINDOWS = 3
SAME_ROUTE_REST = 10
DIFF_ROUTE_REST = 20
DEFAULT_RUNTIME = 60
DEFAULT_CAPACITY = 50

# =========================================================
# HELPERS
# =========================================================
def floor_to_slot(dt):
    return dt.replace(minute=(dt.minute // SLOT_MINUTES) * SLOT_MINUTES, second=0, microsecond=0)

def get_rest(prev, curr):
    if not prev:
        return 0
    return SAME_ROUTE_REST if prev["route_id"] == curr["route_id"] else DIFF_ROUTE_REST

# =========================================================
# DEMAND
# =========================================================
def compute_demand(db, category):
    dow = func.extract("dow", OBData.trip_datetime)

    if category == "weekday":
        day_filter = dow.in_([1,2,3,4,5])
    elif category == "saturday":
        day_filter = dow == 6
    else:
        day_filter = dow == 0

    direction = case(
        (OBData.origin_stop_id < OBData.destination_stop_id, "UP"),
        else_="DOWN"
    )

    rows = (
        db.query(
            OBData.route_id,
            direction.label("direction"),
            func.date_trunc("minute", OBData.trip_datetime).label("ts"),
            func.sum(OBData.boarding_count)
        )
        .filter(day_filter)
        .group_by(OBData.route_id, "direction", "ts")
        .all()
    )

    demand = defaultdict(dict)

    for route_id, direction, ts, passengers in rows:
        slot = floor_to_slot(ts)
        key = f"{route_id}:{direction}"
        demand[key][slot] = demand[key].get(slot, 0) + float(passengers)

    # smoothing
    smoothed = defaultdict(dict)

    for key in demand:
        slots = sorted(demand[key].keys())
        for i, slot in enumerate(slots):
            total = 0
            for j in range(i, min(i + LOOKAHEAD_WINDOWS, len(slots))):
                total += demand[key][slots[j]]
            smoothed[key][slot] = total

    return smoothed

# =========================================================
# RUNTIME + CAPACITY
# =========================================================
def compute_runtime(db):
    rows = (
        db.query(
            RouteStop.route_id,
            func.max(RouteStop.time_from_start)
        )
        .group_by(RouteStop.route_id)
        .all()
    )
    return {r: max(int(t or DEFAULT_RUNTIME), 10) for r, t in rows}

def compute_capacity(db):
    avg = (
        db.query(func.avg(Bus.sitting_capacity + Bus.standing_capacity))
        .filter(Bus.status == BusStatus.active)
        .scalar()
    )
    return int(avg or DEFAULT_CAPACITY)

# =========================================================
# TRIP GENERATION
# =========================================================
def generate_trips(demand, runtime_map, capacity):
    trips = []

    for key, slots in demand.items():
        route_id, direction = key.split(":")
        runtime = runtime_map.get(route_id, DEFAULT_RUNTIME)

        for slot, passengers in slots.items():
            required = math.ceil(passengers / capacity)
            if required <= 0:
                continue

            slot_end = slot + timedelta(minutes=SLOT_MINUTES)
            spacing = (slot_end - slot) / required

            for i in range(required):
                start = slot + spacing * i
                end = start + timedelta(minutes=runtime)

                trips.append({
                    "route_id": route_id,
                    "direction": direction,
                    "start_time": start,
                    "end_time": end,
                })

    return sorted(trips, key=lambda x: x["start_time"])

# =========================================================
# RESOURCE ASSIGNMENT
# =========================================================
def assign_resources(db, trips, schedule_date):

    # Fetch active resources
    buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()

    if not buses or not drivers:
        return []

    # -------------------------------
    # GET USAGE (FAIRNESS)
    # -------------------------------
    driver_usage = dict(
        db.query(
            ScheduleTrip.driver_id,
            func.count()
        ).group_by(ScheduleTrip.driver_id).all()
    )

    bus_usage = dict(
        db.query(
            ScheduleTrip.bus_id,
            func.count()
        ).group_by(ScheduleTrip.bus_id).all()
    )

    # Sort least-used first
    drivers = sorted(drivers, key=lambda d: driver_usage.get(d.user_id, 0))
    buses = sorted(buses, key=lambda b: bus_usage.get(b.id, 0))

    # -------------------------------
    # LEAVES
    # -------------------------------
    leaves = db.query(DriverLeave).filter(
        DriverLeave.start_date <= schedule_date,
        DriverLeave.end_date >= schedule_date,
        DriverLeave.status == LeaveStatus.granted
    ).all()

    leave_set = {l.driver_id for l in leaves}

    # -------------------------------
    # LIMIT RESOURCES (SUBSET)
    # -------------------------------
    max_needed = len(trips)

    drivers = drivers[:max_needed]
    buses = buses[:max_needed]

    assigned = []

    # -------------------------------
    # ASSIGNMENT LOOP
    # -------------------------------
    for trip in trips:

        # -------- DRIVER --------
        driver_assigned = None
        for d in drivers:

            if d.user_id in leave_set:
                continue

            conflict = db.query(ScheduleTrip).filter(
                ScheduleTrip.driver_id == d.user_id,
                ScheduleTrip.trip_date == schedule_date,
                ScheduleTrip.start_time == trip["start_time"],
            ).first()

            if not conflict:
                driver_assigned = d
                break

        if not driver_assigned:
            continue

        # -------- BUS --------
        bus_assigned = None
        for b in buses:

            conflict = db.query(ScheduleTrip).filter(
                ScheduleTrip.bus_id == b.id,
                ScheduleTrip.trip_date == schedule_date,
                ScheduleTrip.start_time == trip["start_time"],
            ).first()

            if not conflict:
                bus_assigned = b
                break

        if not bus_assigned:
            continue

        # Assign
        trip["driver_id"] = driver_assigned.user_id
        trip["bus_id"] = bus_assigned.id

        assigned.append(trip)

    return assigned

# =========================================================
# TEMPLATE STORE
# =========================================================
def store_template(db, category, trips):
    template = Template(
        name=f"{category}_auto",
        template_type=category,
        bus_count=len(set(t["bus_id"] for t in trips)),
        driver_count=len(set(t["driver_id"] for t in trips)),
    )

    db.add(template)
    db.flush()

    records = [
        TemplateRecord(
            template_id=template.id,
            route_id=t["route_id"],
            start_time=t["start_time"].time(),
            busno=t["bus_id"],
            driverno=t["driver_id"],
        )
        for t in trips
    ]

    db.bulk_save_objects(records)
    db.commit()

    return template

# =========================================================
# API: GENERATE TEMPLATES
# =========================================================
@router.post("/generate-templates")
def generate_templates(db: Session = Depends(get_db)):

    categories = ["weekday", "saturday", "sunday"]
    created = []

    for cat in categories:
        demand = compute_demand(db, cat)
        runtime = compute_runtime(db)
        capacity = compute_capacity(db)

        trips = generate_trips(demand, runtime, capacity)
        assigned = assign_resources(db, trips, date.today())

        template = store_template(db, cat, assigned)

        created.append({
            "id": template.id,
            "name": template.name
        })

    return {
        "message": "Templates generated",
        "templates": created
    }

# =========================================================
# API: GENERATE SCHEDULE
# =========================================================
@router.post("/generate-schedule")
def generate_schedule(payload: dict, db: Session = Depends(get_db)):

    template_id = payload.get("template_id")
    start_date = datetime.fromisoformat(payload.get("start_date")).date()
    end_date = datetime.fromisoformat(payload.get("end_date")).date()

    template = db.query(Template).filter(Template.id == template_id).first()

    if not template:
        raise HTTPException(404, "Template not found")

    logs = []
    total = 0
    current = start_date

    while current <= end_date:

        for rec in template.records:

            # 🚫 CHECK DUPLICATE BEFORE INSERT
            exists = db.query(ScheduleTrip).filter(
                ScheduleTrip.route_id == rec.route_id,
                ScheduleTrip.trip_date == current,
                ScheduleTrip.start_time == rec.start_time,
                ScheduleTrip.bus_id == rec.busno,
            ).first()

            if exists:
                continue

            trip = ScheduleTrip(
                route_id=rec.route_id,
                trip_date=current,
                start_time=rec.start_time,
                bus_id=rec.busno,
                driver_id=rec.driverno,
                status=TripStatus.scheduled
            )

            db.add(trip)

            route = db.query(Route).filter(Route.id == rec.route_id).first()
            bus = db.query(Bus).filter(Bus.id == rec.busno).first()
            driver = db.query(Driver).filter(Driver.user_id == rec.driverno).first()

            logs.append({
                "trip_date": str(current),
                "start_time": str(rec.start_time),
                "route_name": route.name if route else rec.route_id,
                "driver_name": driver.user.name if driver else str(rec.driverno),
                "bus_code": bus.code if bus else str(rec.busno),
                "status": "scheduled"
            })

            total += 1

        current += timedelta(days=1)

    # ✅ SAFE COMMIT
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Duplicate trips detected, skipped conflicting entries")

    return {
        "summary": {"total_trips": total},
        "logs": logs
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