"""
SmartBusScheduler - Admin Schedule Router (REDESIGNED)
=====================================================
Implements:
- Two-layer architecture: Template Generator + Schedule Generator
- Resource locking with demand accumulation
- Deterministic scheduling simulator
- Real resource mapping with fairness

Based on:
1. Template Generation Router (Simulation Engine)
2. Scheduler Engine with resource pool management
3. Schedule Generation Router (Real DB Persistence)
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
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import csv
import io
import math
import logging

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
# LOGGING
# =========================================================
logger = logging.getLogger(__name__)

# =========================================================
# ROUTER
# =========================================================
router = APIRouter()

# =========================================================
# CONFIG & CONSTANTS
# =========================================================
SLOT_MINUTES = 30
LOOKAHEAD_WINDOWS = 3
SAME_ROUTE_REST = 10  # minutes
DIFF_ROUTE_REST = 20  # minutes
DEFAULT_RUNTIME = 60  # minutes
DEFAULT_CAPACITY = 50  # passengers

# Dispatch threshold: dispatch when demand >= 70% * capacity * 3 lookahead slots
DISPATCH_THRESHOLD_MULTIPLIER = 0.7

DAY_START = time(5, 0)
DAY_END = time(3, 0)  # Next day 3 AM


# =========================================================
# DATA STRUCTURES (Resource Pools)
# =========================================================
@dataclass
class ResourceUnit:
    """Represents a bus or driver in the resource pool during simulation"""
    id: int
    available_at: datetime
    route: Optional[str] = None
    shift: Optional[int] = None


@dataclass
class AbstractTrip:
    """Internal trip representation during template generation"""
    route_id: str
    direction: str
    start_time: datetime
    end_time: datetime
    bus_id: int
    driver_id: int


@dataclass
class SchedulerState:
    """Encapsulates the scheduler engine state"""
    bus_pool: List[ResourceUnit]
    driver_pool: List[ResourceUnit]
    route_demand: Dict[Tuple[str, str], int]
    trips: List[AbstractTrip] = field(default_factory=list)
    dispatch_threshold: float = 0.0


# =========================================================
# VALIDATION HELPERS
# =========================================================
def check_admin(user: dict):
    """Verify admin role"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def format_trip(db: Session, trip: ScheduleTrip) -> Dict:
    """Format a ScheduleTrip for API response"""
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
# CSV PARSING
# =========================================================
def parse_csv(file: UploadFile) -> List[Dict]:
    """Parse and validate OB data CSV"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    required_fields = {
        "route_id",
        "origin_stop_id",
        "destination_stop_id",
        "trip_datetime",
        "boarding_count",
    }

    if not reader.fieldnames or not required_fields.issubset(set(reader.fieldnames)):
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    return list(reader)


# =========================================================
# DEMAND COMPUTATION
# =========================================================
def compute_demand(db: Session, category: str) -> Dict[str, Dict[datetime, float]]:
    """
    Compute demand per route:direction:time_slot
    
    Args:
        db: Database session
        category: "weekday", "saturday", or "sunday"
    
    Returns:
        {
            "route_id:direction": {
                datetime_slot: accumulated_passengers,
                ...
            },
            ...
        }
    """
    dow = func.extract("dow", OBData.trip_datetime)

    # Filter by day of week
    if category == "weekday":
        day_filter = dow.in_([1, 2, 3, 4, 5])
    elif category == "saturday":
        day_filter = dow == 6
    else:  # sunday
        day_filter = dow == 0

    # Determine direction (UP/DOWN) based on stop sequence
    direction = case(
        (OBData.origin_stop_id < OBData.destination_stop_id, "UP"),
        else_="DOWN",
    )

    # Query OB data grouped by route, direction, and time
    rows = (
        db.query(
            OBData.route_id,
            direction.label("direction"),
            func.date_trunc("hour", OBData.trip_datetime).label("ts"),
            func.sum(OBData.boarding_count).label("passengers"),
        )
        .filter(day_filter)
        .group_by(OBData.route_id, "direction", "ts")
        .all()
    )

    # Step 1: Aggregate by slot
    demand = defaultdict(dict)
    for route_id, direction, ts, passengers in rows:
        slot = floor_to_slot(ts)
        key = f"{route_id}:{direction}"
        demand[key][slot] = demand[key].get(slot, 0) + float(passengers or 0)

    # Step 2: Apply lookahead smoothing (3-slot window)
    smoothed = defaultdict(dict)
    for key in demand:
        slots = sorted(demand[key].keys())
        for i, slot in enumerate(slots):
            total = 0
            for j in range(i, min(i + LOOKAHEAD_WINDOWS, len(slots))):
                total += demand[key][slots[j]]
            smoothed[key][slot] = total

    logger.info(f"Computed demand for {category}: {len(smoothed)} route:direction pairs")
    return dict(smoothed)


def floor_to_slot(dt: datetime) -> datetime:
    """Round datetime down to nearest SLOT_MINUTES"""
    minutes = (dt.minute // SLOT_MINUTES) * SLOT_MINUTES
    return dt.replace(minute=minutes, second=0, microsecond=0)


# =========================================================
# RUNTIME & CAPACITY
# =========================================================
def compute_runtime(db: Session) -> Dict[str, int]:
    """
    Get runtime (minutes) for each route from max stop time
    
    Returns:
        {route_id: runtime_minutes, ...}
    """
    rows = (
        db.query(
            RouteStop.route_id,
            func.max(RouteStop.time_from_start).label("max_time"),
        )
        .group_by(RouteStop.route_id)
        .all()
    )

    runtime_map = {}
    for route_id, max_time in rows:
        runtime_map[route_id] = max(int(max_time or DEFAULT_RUNTIME), 10)

    logger.info(f"Computed runtime for {len(runtime_map)} routes")
    return runtime_map


def compute_capacity(db: Session) -> int:
    """
    Get average bus capacity from active fleet
    
    Returns:
        Average capacity in passengers
    """
    avg = (
        db.query(func.avg(Bus.sitting_capacity + Bus.standing_capacity))
        .filter(Bus.status == BusStatus.active)
        .scalar()
    )

    capacity = int(avg or DEFAULT_CAPACITY)
    logger.info(f"Computed average capacity: {capacity}")
    return capacity


# =========================================================
# RESOURCE POOL INITIALIZATION
# =========================================================
def init_resource_pool(db: Session, resource_type: str) -> List[ResourceUnit]:
    """
    Initialize resource pool (buses or drivers)
    
    Args:
        db: Database session
        resource_type: "bus" or "driver"
    
    Returns:
        List of ResourceUnit objects
    """
    pool = []

    if resource_type == "bus":
        buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
        for bus in buses:
            pool.append(
                ResourceUnit(
                    id=bus.id,
                    available_at=datetime.combine(date.today(), DAY_START),
                    route=None,
                    shift=None,
                )
            )
    else:  # driver
        drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()
        for i, driver in enumerate(drivers):
            # Assign shifts: 1-3 round-robin
            shift = (i % 3) + 1
            pool.append(
                ResourceUnit(
                    id=driver.user_id,
                    available_at=datetime.combine(date.today(), DAY_START),
                    route=None,
                    shift=shift,
                )
            )

    logger.info(f"Initialized {resource_type} pool with {len(pool)} resources")
    return pool


# =========================================================
# SHIFT LOGIC
# =========================================================
def get_shift(time_slot: datetime) -> int:
    """
    Determine shift based on time of day
    
    Shift 1: 05:00 - 13:00
    Shift 2: 13:00 - 21:00
    Shift 3: 21:00 - 05:00 (wraps to next day)
    """
    hour = time_slot.hour

    if 5 <= hour < 13:
        return 1
    elif 13 <= hour < 21:
        return 2
    else:
        return 3


# =========================================================
# REST LOGIC
# =========================================================
def get_rest(resource: ResourceUnit, new_route: str) -> timedelta:
    """
    Calculate rest time before next trip
    
    - Same route: 10 minutes
    - Different route: 20 minutes
    """
    if resource.route is None:
        return timedelta(minutes=0)

    if resource.route == new_route:
        return timedelta(minutes=SAME_ROUTE_REST)
    else:
        return timedelta(minutes=DIFF_ROUTE_REST)


# =========================================================
# RESOURCE FINDERS
# =========================================================
def find_available_bus(pool: List[ResourceUnit], time_slot: datetime) -> Optional[ResourceUnit]:
    """Find first available bus at given time"""
    for bus in pool:
        if bus.available_at <= time_slot:
            return bus
    return None


def find_available_driver(
    pool: List[ResourceUnit], time_slot: datetime, current_shift: int
) -> Optional[ResourceUnit]:
    """Find first available driver in correct shift"""
    for driver in pool:
        if driver.shift == current_shift and driver.available_at <= time_slot:
            return driver
    return None


# =========================================================
# SCHEDULER ENGINE (CORE LOGIC)
# =========================================================
def run_scheduler_engine(
    db: Session,
    demand_data: Dict[str, Dict[datetime, float]],
    runtime_map: Dict[str, int],
    capacity: int,
) -> List[AbstractTrip]:
    """
    Run the scheduling simulator engine (stateful resource allocation)
    
    This is the CORE algorithm:
    1. Initialize resource pools (buses, drivers)
    2. Generate time slots (05:00 -> 03:00, 30-min steps)
    3. For each time slot:
       a. Accumulate demand
       b. Dispatch trips when demand >= threshold
       c. Update resource availability
    
    Returns:
        List of AbstractTrip objects (without real bus/driver IDs yet)
    """
    logger.info("=" * 60)
    logger.info("SCHEDULER ENGINE START")
    logger.info("=" * 60)

    # Init state
    bus_pool = init_resource_pool(db, "bus")
    driver_pool = init_resource_pool(db, "driver")

    bus_count = len(bus_pool)
    driver_count = len(driver_pool)
    logger.info(f"Active resources: {bus_count} buses, {driver_count} drivers")

    # Route demand accumulator: (route, direction) -> accumulated_passengers
    route_demand = defaultdict(int)

    # Dispatch threshold: 70% of capacity * 3 lookahead windows
    dispatch_threshold = capacity * DISPATCH_THRESHOLD_MULTIPLIER * LOOKAHEAD_WINDOWS
    logger.info(f"Dispatch threshold: {dispatch_threshold} passengers")

    # Generate timeline: 05:00 to 03:00 next day, 30-min steps
    timeline = generate_timeline(datetime.combine(date.today(), DAY_START))

    trips = []

    # ====== MAIN SCHEDULING LOOP ======
    for time_slot in timeline:

        current_shift = get_shift(time_slot)

        # ------
        # STEP 1: ACCUMULATE DEMAND
        # ------
        for route_key, slots in demand_data.items():
            route_id, direction = route_key.split(":")
            incoming = slots.get(time_slot, 0)
            key = (route_id, direction)
            route_demand[key] += incoming

        # ------
        # STEP 2: DISPATCH LOOP
        # ------
        for route_key in list(route_demand.keys()):
            route_id, direction = route_key

            while route_demand[route_key] >= dispatch_threshold:

                # ------
                # STEP 3: FIND RESOURCES
                # ------
                bus = find_available_bus(bus_pool, time_slot)
                driver = find_available_driver(driver_pool, time_slot, current_shift)

                if bus is None or driver is None:
                    logger.warning(
                        f"@{time_slot}: No resources for {route_id}:{direction} "
                        f"(bus={bus is not None}, driver={driver is not None})"
                    )
                    break

                # ------
                # STEP 4: CALCULATE REST & START TIME
                # ------
                bus_rest = get_rest(bus, route_id)
                driver_rest = get_rest(driver, route_id)

                bus_ready_time = bus.available_at + bus_rest
                driver_ready_time = driver.available_at + driver_rest

                actual_start = max(time_slot, bus_ready_time, driver_ready_time)

                # ------
                # STEP 5: CALCULATE END TIME
                # ------
                runtime = runtime_map.get(route_id, DEFAULT_RUNTIME)
                end_time = actual_start + timedelta(minutes=runtime)

                # ------
                # STEP 6: LOCK RESOURCES
                # ------
                bus.available_at = end_time
                bus.route = route_id

                driver.available_at = end_time
                driver.route = route_id

                # ------
                # STEP 7: STORE ABSTRACT TRIP
                # ------
                trip = AbstractTrip(
                    route_id=route_id,
                    direction=direction,
                    start_time=actual_start,
                    end_time=end_time,
                    bus_id=bus.id,
                    driver_id=driver.id,
                )
                trips.append(trip)

                logger.debug(
                    f"@{actual_start}: Scheduled trip {route_id}:{direction} "
                    f"Bus={bus.id}, Driver={driver.id}"
                )

                # ------
                # STEP 8: REDUCE DEMAND
                # ------
                route_demand[route_key] -= int(dispatch_threshold)

    logger.info(f"Scheduler engine completed: {len(trips)} trips generated")
    logger.info("=" * 60)

    return trips


def generate_timeline(start: datetime) -> List[datetime]:
    """
    Generate timeline from 05:00 today to 03:00 tomorrow
    in 30-minute slots
    """
    timeline = []
    current = start

    # 24 hours = 1440 minutes
    # 1440 / 30 = 48 slots
    for _ in range(48):
        timeline.append(current)
        current += timedelta(minutes=SLOT_MINUTES)

    return timeline


# =========================================================
# TEMPLATE STORAGE
# =========================================================
def store_template(
    db: Session, category: str, trips: List[AbstractTrip]
) -> Template:
    """
    Store generated trips as a reusable template
    
    Args:
        db: Database session
        category: "weekday", "saturday", or "sunday"
        trips: List of AbstractTrip objects
    
    Returns:
        Created Template object
    """
    bus_ids = set(t.bus_id for t in trips)
    driver_ids = set(t.driver_id for t in trips)

    template = Template(
        name=f"{category}_auto",
        template_type=category,
        bus_count=len(bus_ids),
        driver_count=len(driver_ids),
    )

    db.add(template)
    db.flush()  # Get template.id

    # Create template records
    records = [
        TemplateRecord(
            template_id=template.id,
            route_id=t.route_id,
            start_time=t.start_time.time(),
            busno=t.bus_id,
            driverno=t.driver_id,
        )
        for t in trips
    ]

    db.bulk_save_objects(records)
    db.commit()

    logger.info(f"Stored template: {template.name} with {len(records)} records")
    return template


# =========================================================
# REAL RESOURCE MAPPING
# =========================================================
def map_abstract_to_real(
    db: Session,
    abstract_ids: set,
    resource_type: str,
) -> Dict[int, int]:
    """
    Map abstract resource IDs (from template) to real resource IDs
    using fair distribution (least-used first)
    
    Args:
        db: Database session
        abstract_ids: Set of abstract bus/driver IDs from template
        resource_type: "bus" or "driver"
    
    Returns:
        {abstract_id: real_id, ...}
    """
    mapping = {}

    if resource_type == "bus":
        # Get all active buses with usage stats
        usage = dict(
            db.query(ScheduleTrip.bus_id, func.count())
            .group_by(ScheduleTrip.bus_id)
            .all()
        )

        buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
        # Sort by usage (ascending)
        sorted_buses = sorted(buses, key=lambda b: usage.get(b.id, 0))

        for i, abstract_id in enumerate(sorted(abstract_ids)):
            if i < len(sorted_buses):
                mapping[abstract_id] = sorted_buses[i].id

    else:  # driver
        # Get all active drivers with usage stats
        usage = dict(
            db.query(ScheduleTrip.driver_id, func.count())
            .group_by(ScheduleTrip.driver_id)
            .all()
        )

        drivers = (
            db.query(Driver)
            .join(User)
            .filter(Driver.status == DriverStatus.active)
            .all()
        )
        # Sort by usage (ascending)
        sorted_drivers = sorted(drivers, key=lambda d: usage.get(d.user_id, 0))

        for i, abstract_id in enumerate(sorted(abstract_ids)):
            if i < len(sorted_drivers):
                mapping[abstract_id] = sorted_drivers[i].user_id

    logger.info(f"Created mapping for {len(mapping)} {resource_type}s")
    return mapping


# =========================================================
# SCHEDULE TRIP CREATION BATCH
# =========================================================
def create_schedule_trips_batch(
    db: Session,
    template: Template,
    start_date: date,
    end_date: date,
) -> Tuple[int, List[str]]:
    """
    Create actual ScheduleTrip records from template
    using real resource mapping (fairness-based allocation)
    
    Args:
        db: Database session
        template: Template object
        start_date: Start date for schedule
        end_date: End date for schedule
    
    Returns:
        (total_created, logs)
    """
    logger.info(f"Creating schedule from template {template.name}")
    logger.info(f"Date range: {start_date} to {end_date}")

    # Extract abstract IDs from template records
    abstract_bus_ids = set(r.busno for r in template.records)
    abstract_driver_ids = set(r.driverno for r in template.records)

    # Create mappings to real resources
    bus_mapping = map_abstract_to_real(db, abstract_bus_ids, "bus")
    driver_mapping = map_abstract_to_real(db, abstract_driver_ids, "driver")

    logger.info(f"Bus mapping: {len(bus_mapping)} abstract -> real")
    logger.info(f"Driver mapping: {len(driver_mapping)} abstract -> real")

    # Batch insert
    trips_to_create = []
    seen = set()
    total = 0
    logs = []

    current_date = start_date
    while current_date <= end_date:

        for record in template.records:

            # Create unique key to avoid duplicates
            key = (record.route_id, current_date, record.start_time, record.busno)

            if key in seen:
                continue
            seen.add(key)

            # Check if trip already exists
            exists = (
                db.query(ScheduleTrip)
                .filter(
                    ScheduleTrip.route_id == record.route_id,
                    ScheduleTrip.trip_date == current_date,
                    ScheduleTrip.start_time == record.start_time,
                )
                .first()
            )

            if exists:
                logs.append(f"SKIP: Trip already exists for {record.route_id} on {current_date}")
                continue

            # Map abstract to real
            real_bus_id = bus_mapping.get(record.busno)
            real_driver_id = driver_mapping.get(record.driverno)

            if not real_bus_id or not real_driver_id:
                logs.append(
                    f"SKIP: Missing mapping for bus={record.busno}, "
                    f"driver={record.driverno}"
                )
                continue

            trip = ScheduleTrip(
                route_id=record.route_id,
                trip_date=current_date,
                start_time=record.start_time,
                bus_id=real_bus_id,
                driver_id=real_driver_id,
                status=TripStatus.scheduled,
            )

            trips_to_create.append(trip)
            total += 1

        current_date += timedelta(days=1)

    # Bulk insert with conflict handling
    if trips_to_create:
        try:
            db.bulk_save_objects(trips_to_create)
            db.commit()
            logger.info(f"Successfully created {total} schedule trips")
        except IntegrityError as e:
            db.rollback()
            logs.append(f"ERROR: {str(e)}")
            logger.error(f"Integrity error during bulk insert: {e}")
            raise HTTPException(
                status_code=400,
                detail="Some trips could not be created (duplicate or constraint violation)",
            )

    return total, logs


# =========================================================
# API ENDPOINTS
# =========================================================

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
    """
    Upload OB (Onboard) data from CSV
    
    CSV format:
        route_id, origin_stop_id, destination_stop_id, trip_datetime, boarding_count
    """
    check_admin(current_user)

    rows = parse_csv(file)

    if overwrite:
        db.query(OBData).delete()
        db.commit()
        logger.info("Cleared existing OB data")

    objects = []
    for row in rows:
        try:
            dt = datetime.strptime(row["trip_datetime"], "%Y-%m-%d %H:%M:%S")
            objects.append(
                OBData(
                    route_id=row["route_id"],
                    origin_stop_id=int(row["origin_stop_id"]),
                    destination_stop_id=int(row["destination_stop_id"]),
                    trip_datetime=dt,
                    boarding_count=int(row["boarding_count"]),
                )
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Skipping invalid row: {row} ({e})")
            continue

    db.bulk_save_objects(objects)
    db.commit()

    logger.info(f"Uploaded {len(objects)} OB records")
    return {"message": f"{len(objects)} records inserted", "count": len(objects)}


# =========================================================
# GENERATE TEMPLATES
# =========================================================
@router.post("/generate-templates")
def generate_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate schedule templates for all day categories
    (weekday, saturday, sunday)
    
    Process:
    1. Compute demand from OB data
    2. Run scheduler engine (resource allocation simulator)
    3. Store as reusable templates
    """
    check_admin(current_user)

    categories = ["weekday", "saturday", "sunday"]
    created = []

    for category in categories:
        try:
            logger.info(f"Generating template for {category}...")

            # Step 1: Compute parameters
            demand = compute_demand(db, category)
            runtime_map = compute_runtime(db)
            capacity = compute_capacity(db)

            # Step 2: Run scheduler engine (simulation)
            abstract_trips = run_scheduler_engine(db, demand, runtime_map, capacity)

            if not abstract_trips:
                logger.warning(f"No trips generated for {category}")
                continue

            # Step 3: Store template
            template = store_template(db, category, abstract_trips)

            created.append({"id": template.id, "name": template.name, "trips": len(abstract_trips)})

        except Exception as e:
            logger.error(f"Error generating {category} template: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating {category} template")

    return {
        "message": "Templates generated successfully",
        "templates": created,
        "total": len(created),
    }


# =========================================================
# GENERATE SCHEDULE
# =========================================================
@router.post("/generate-schedule")
def generate_schedule(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate actual schedule from a template
    
    Input:
    {
        "template_id": 1,
        "start_date": "2024-01-15",
        "end_date": "2024-01-21"
    }
    
    Process:
    1. Fetch template
    2. Map abstract resources to real ones (fairness)
    3. Create ScheduleTrip records in DB
    """
    check_admin(current_user)

    template_id = payload.get("template_id")
    start_date = datetime.fromisoformat(payload.get("start_date")).date()
    end_date = datetime.fromisoformat(payload.get("end_date")).date()

    if not template_id or not start_date or not end_date:
        raise HTTPException(status_code=400, detail="Missing required fields")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    # Fetch template
    template = db.query(Template).filter(Template.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    logger.info(f"Generating schedule from template {template.name}")

    # Create schedule trips
    total, logs = create_schedule_trips_batch(db, template, start_date, end_date)

    return {
        "success": True,
        "summary": {"total_trips": total, "date_range": f"{start_date} to {end_date}"},
        "logs": logs[:100],  # Limit logs
    }


# =========================================================
# FETCH TEMPLATES
# =========================================================
@router.get("/templates")
def get_templates(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Fetch all templates"""
    check_admin(current_user)

    templates = db.query(Template).order_by(Template.created_at.desc()).all()

    return [
        {
            "id": t.id,
            "name": t.name,
            "type": t.template_type,
            "bus_count": t.bus_count,
            "driver_count": t.driver_count,
            "record_count": len(t.records),
            "created_at": str(t.created_at),
        }
        for t in templates
    ]


@router.get("/templates/{template_id}")
def get_template_details(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Fetch template records"""
    check_admin(current_user)

    template = db.query(Template).filter(Template.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "id": template.id,
        "name": template.name,
        "type": template.template_type,
        "bus_count": template.bus_count,
        "driver_count": template.driver_count,
        "records": [
            {
                "route_id": r.route_id,
                "start_time": str(r.start_time),
                "bus_id": r.busno,
                "driver_id": r.driverno,
            }
            for r in template.records
        ],
    }


# =========================================================
# TRIP MANAGEMENT (CRUD)
# =========================================================
@router.post("/", response_model=TripResponse)
def create_trip(
    payload: TripCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a single trip (manual)"""
    check_admin(current_user)

    # Validation
    driver_leave = db.query(DriverLeave).filter(
        DriverLeave.driver_id == payload.driver_id,
        DriverLeave.start_date <= payload.trip_date,
        DriverLeave.end_date >= payload.trip_date,
        DriverLeave.status == LeaveStatus.granted,
    ).first()

    if driver_leave:
        raise HTTPException(status_code=400, detail="Driver is on leave")

    existing = db.query(ScheduleTrip).filter(
        ScheduleTrip.driver_id == payload.driver_id,
        ScheduleTrip.trip_date == payload.trip_date,
        ScheduleTrip.start_time == payload.start_time,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Driver already assigned at this time")

    existing_bus = db.query(ScheduleTrip).filter(
        ScheduleTrip.bus_id == payload.bus_id,
        ScheduleTrip.trip_date == payload.trip_date,
        ScheduleTrip.start_time == payload.start_time,
    ).first()

    if existing_bus:
        raise HTTPException(status_code=400, detail="Bus already assigned at this time")

    # Create
    trip = ScheduleTrip(**payload.dict(), status=TripStatus.scheduled)
    db.add(trip)
    db.commit()
    db.refresh(trip)

    logger.info(f"Created trip {trip.id}")
    return format_trip(db, trip)


@router.get("/", response_model=List[TripResponse])
def get_schedule(
    trip_date: Optional[date] = Query(None),
    route_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Fetch trips with filters"""
    check_admin(current_user)

    query = db.query(ScheduleTrip)

    if trip_date:
        query = query.filter(ScheduleTrip.trip_date == trip_date)
    if route_id:
        query = query.filter(ScheduleTrip.route_id == route_id)

    trips = query.order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    return [format_trip(db, t) for t in trips]


@router.put("/{trip_id}", response_model=TripResponse)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a trip"""
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(trip, key, value)

    db.commit()
    db.refresh(trip)

    logger.info(f"Updated trip {trip_id}")
    return format_trip(db, trip)


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a trip"""
    check_admin(current_user)

    trip = db.query(ScheduleTrip).filter(ScheduleTrip.id == trip_id).first()

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    db.delete(trip)
    db.commit()

    logger.info(f"Deleted trip {trip_id}")
    return {"status": "deleted", "trip_id": trip_id}


# =========================================================
# HEALTH CHECK
# =========================================================
@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}