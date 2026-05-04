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
from sqlalchemy.exc import IntegrityError
from typing import Any, List, Dict, Set, Tuple
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
    LeaveStatus,
    TripStatus,
    BusStatus,
    DriverStatus,
)
from ..schemas import (
    TripCreate,
    TripUpdate,
    TripResponse,
    TemplateConfig,
    ScheduleGenerationRequest as scheduleRequest,
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
# RESOURCE VALIDATION
# =========================================================
def validate_resources_for_template(db: Session, required_buses: int, required_drivers: int):
    """
    Validates if sufficient resources are available for template creation.
    Returns actual counts and raises HTTPException if insufficient.
    """
    available_buses = db.query(Bus).filter(Bus.status == BusStatus.active).count()
    available_drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).count()

    errors = []
    
    if available_buses < required_buses:
        errors.append(f"Required {required_buses} buses, only {available_buses} active buses available")
    
    if available_drivers < required_drivers:
        errors.append(f"Required {required_drivers} drivers, only {available_drivers} active drivers available")
    
    if errors:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Insufficient resources",
                "details": errors,
                "available_buses": available_buses,
                "available_drivers": available_drivers,
                "required_buses": required_buses,
                "required_drivers": required_drivers,
            }
        )
    
    return available_buses, available_drivers


def validate_resources_for_schedule(
    db: Session, 
    template: Template, 
    start_date: date, 
    end_date: date
) -> Dict[str, Any]:
    """
    Pre-validates if template can be applied to date range.
    Returns detailed resource availability report.
    """
    all_buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    all_drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()

    # Get all leaves in the date range
    leaves = db.query(DriverLeave).filter(
        DriverLeave.status == LeaveStatus.granted,
        DriverLeave.start_date <= end_date,
        DriverLeave.end_date >= start_date
    ).all()

    # Calculate worst-case scenario (day with most drivers on leave)
    drivers_on_leave_by_date = defaultdict(set)
    current = start_date
    while current <= end_date:
        for leave in leaves:
            if leave.start_date <= current <= leave.end_date:
                drivers_on_leave_by_date[current].add(leave.driver_id)
        current += timedelta(days=1)

    max_drivers_on_leave = max(len(v) for v in drivers_on_leave_by_date.values()) if drivers_on_leave_by_date else 0
    min_available_drivers = len(all_drivers) - max_drivers_on_leave

    warnings = []
    
    if len(all_buses) < template.bus_count:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Insufficient buses",
                "required": template.bus_count,
                "available": len(all_buses),
                "message": f"Template requires {template.bus_count} buses, only {len(all_buses)} active buses available"
            }
        )
    
    if min_available_drivers < template.driver_count:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Insufficient drivers",
                "required": template.driver_count,
                "available": min_available_drivers,
                "total_drivers": len(all_drivers),
                "max_on_leave": max_drivers_on_leave,
                "message": f"Template requires {template.driver_count} drivers, minimum {min_available_drivers} available (considering leaves)"
            }
        )
    
    # Warnings for tight resources
    if len(all_buses) == template.bus_count:
        warnings.append("Using all available buses - no buffer")
    
    if min_available_drivers == template.driver_count:
        warnings.append("Using minimum available drivers - no buffer for additional leaves")

    return {
        "valid": True,
        "available_buses": len(all_buses),
        "required_buses": template.bus_count,
        "available_drivers": len(all_drivers),
        "min_available_drivers": min_available_drivers,
        "required_drivers": template.driver_count,
        "max_drivers_on_leave": max_drivers_on_leave,
        "warnings": warnings
    }


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
    """Round datetime to nearest hour for demand aggregation"""
    return dt.replace(minute=0, second=0, microsecond=0)


def compute_route_demand(ob_rows):
    """
    Computes average passenger demand per route per hour slot.
    Returns: {route_id: {datetime_slot: avg_passengers}}
    """
    demand = defaultdict(lambda: defaultdict(list))

    for row in ob_rows:
        route = row.route_id
        slot = time_to_slot(row.trip_datetime)
        # Net passengers (boarding - offboarding)
        passengers = max(0, row.boarding_count - row.offboarding_count)
        demand[route][slot].append(passengers)

    # Average the demand for each route-slot combination
    final = {}
    for route, slots in demand.items():
        final[route] = {}
        for slot, values in slots.items():
            final[route][slot] = int(sum(values) / len(values))

    return final


# =========================================================
# NON-OVERLAPPING RESOURCE ASSIGNMENT
# =========================================================
def assign_non_overlapping_resources(
    route_demands: Dict[str, Dict[datetime, int]],
    bus_count: int,
    driver_count: int,
    avg_capacity: float
) -> List[Dict[str, Any]]:
    """
    Assigns non-overlapping busno and driverno to trips based on demand.
    
    Returns list of template records with:
    - route_id
    - start_time
    - busno (1 to bus_count)
    - driverno (1 to driver_count)
    """
    
    # Track resource usage per time slot
    resource_usage: Dict[time, Dict[str, Set[int]]] = defaultdict(lambda: {"buses": set(), "drivers": set()})
    
    template_records = []
    
    for route, slots in route_demands.items():
        for slot, passengers in slots.items():
            # Calculate trips needed for this demand
            trips_needed = max(1, math.ceil(passengers / avg_capacity))
            
            # Calculate gap between trips (evenly distribute within the hour)
            gap = max(5, int(60 / trips_needed))
            
            for i in range(trips_needed):
                start_time = (
                    datetime.combine(date.today(), slot.time())
                    + timedelta(minutes=i * gap)
                ).time()
                
                # Find available bus and driver for this time slot
                bus_no = None
                driver_no = None
                
                # Try to find an available bus (1 to bus_count)
                for b in range(1, bus_count + 1):
                    if b not in resource_usage[start_time]["buses"]:
                        bus_no = b
                        break
                
                # Try to find an available driver (1 to driver_count)
                for d in range(1, driver_count + 1):
                    if d not in resource_usage[start_time]["drivers"]:
                        driver_no = d
                        break
                
                # If we couldn't assign resources, skip this trip
                if bus_no is None or driver_no is None:
                    # Log warning but continue - this means we need more resources
                    continue
                
                # Mark resources as used
                resource_usage[start_time]["buses"].add(bus_no)
                resource_usage[start_time]["drivers"].add(driver_no)
                
                template_records.append({
                    "route_id": route,
                    "start_time": start_time,
                    "busno": bus_no,
                    "driverno": driver_no,
                })
    
    return template_records


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
    payload: TemplateConfig,
    description: str = "Generated from OB data",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    check_admin(current_user)

    # Fetch OB data
    ob_rows = db.query(OBData).all()
    if not ob_rows:
        raise HTTPException(status_code=400, detail="No OB data found.")

    # Get resource counts
    bus_count = payload.bus_count or db.query(Bus).filter(Bus.status == BusStatus.active).count()
    driver_count = payload.driver_count or db.query(Driver).filter(Driver.status == DriverStatus.active).count()

    # Validate resources BEFORE creating template
    validate_resources_for_template(db, bus_count, driver_count)

    # Get actual buses for capacity calculation
    buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    if not buses:
        raise HTTPException(status_code=400, detail="No active buses available.")

    avg_capacity = sum(b.sitting_capacity for b in buses) / len(buses)
    avg_capacity = max(avg_capacity, 1)

    # Compute demand
    demand = compute_route_demand(ob_rows)

    # Create template
    name = payload.name or f"Template {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    template = Template(
        name=name,
        description=description,
        template_type="auto",
        bus_count=bus_count,
        driver_count=driver_count,
        created_by=current_user.get("id"),
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    # Generate non-overlapping template records
    template_records_data = assign_non_overlapping_resources(
        demand, 
        bus_count, 
        driver_count, 
        avg_capacity
    )

    # Create TemplateRecord objects
    records = []
    for rec_data in template_records_data:
        records.append(
            TemplateRecord(
                template_id=template.id,
                route_id=rec_data["route_id"],
                start_time=rec_data["start_time"],
                busno=rec_data["busno"],
                driverno=rec_data["driverno"],
            )
        )

    if not records:
        # Rollback template creation if no records generated
        db.delete(template)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="No template records generated. Try increasing bus/driver count."
        )

    db.bulk_save_objects(records)
    db.commit()

    # Calculate statistics
    unique_times = len(set(r.start_time for r in records))
    routes_covered = len(set(r.route_id for r in records))

    return {
        "message": "Template generated successfully",
        "template_id": template.id,
        "template_name": name,
        "bus_count": bus_count,
        "driver_count": driver_count,
        "total_records": len(records),
        "unique_time_slots": unique_times,
        "routes_covered": routes_covered,
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

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    records = db.query(TemplateRecord).filter(
        TemplateRecord.template_id == template_id
    ).all()

    return {
        "template": {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "bus_count": template.bus_count,
            "driver_count": template.driver_count,
            "created_at": str(template.created_at),
        },
        "records": [
            {
                "route_id": r.route_id,
                "start_time": str(r.start_time),
                "busno": r.busno,
                "driverno": r.driverno,
            }
            for r in records
        ],
        "total_records": len(records),
    }


# =========================================================
# GENERATE SCHEDULE FROM TEMPLATE
# =========================================================
@router.post("/generate-schedule")
def generate_schedule(
    payload: scheduleRequest,
    overwrite: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    template_id = payload.template_id
    start_date = payload.start_date
    end_date = payload.end_date
    
    check_admin(current_user)

    # -------------------------------
    # Parse Dates
    # -------------------------------
    def parse_date(value: str) -> date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD or DD-MM-YYYY")
    if isinstance(start_date, str):
        start_date_parsed = parse_date(start_date)
    else:
        start_date_parsed = start_date

    if isinstance(end_date, str):
        end_date_parsed = parse_date(end_date)
    else:
        end_date_parsed = end_date

    if end_date_parsed < start_date_parsed:
        raise HTTPException(400, "End date must be after start date")

    # -------------------------------
    # Fetch Template + Records
    # -------------------------------
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")

    records = db.query(TemplateRecord).filter(
        TemplateRecord.template_id == template_id
    ).all()

    if not records:
        raise HTTPException(400, "Template has no records")

    # -------------------------------
    # Pre-validate Resources
    # -------------------------------
    validation_result = validate_resources_for_schedule(
        db, template, start_date_parsed, end_date_parsed
    )

    # -------------------------------
    # Overwrite Existing
    # -------------------------------
    if overwrite:
        deleted_count = db.query(ScheduleTrip).filter(
            ScheduleTrip.trip_date.between(start_date_parsed, end_date_parsed)
        ).delete(synchronize_session=False)
        db.commit()
    else:
        deleted_count = 0

    # -------------------------------
    # Pre-fetch ALL resources once
    # -------------------------------
    all_buses = db.query(Bus).filter(Bus.status == BusStatus.active).all()
    all_drivers = db.query(Driver).filter(Driver.status == DriverStatus.active).all()

    # Pre-fetch all leaves in date range
    all_leaves = db.query(DriverLeave).filter(
        DriverLeave.status == LeaveStatus.granted,
        DriverLeave.start_date <= end_date_parsed,
        DriverLeave.end_date >= start_date_parsed
    ).all()

    # Build leave lookup: {driver_id: [(start, end), ...]}
    driver_leaves = defaultdict(list)
    for leave in all_leaves:
        driver_leaves[leave.driver_id].append((leave.start_date, leave.end_date))

    # Helper function to check if driver is on leave
    def is_on_leave(driver_id: int, check_date: date) -> bool:
        for start, end in driver_leaves.get(driver_id, []):
            if start <= check_date <= end:
                return True
        return False

    # -------------------------------
    # Group template records by time
    # -------------------------------
    records_by_time = defaultdict(list)
    for r in records:
        records_by_time[r.start_time].append(r)

    # -------------------------------
    # Generate trips for each day
    # -------------------------------
    all_trips = []
    skipped_trips = []
    current_date = start_date_parsed

    while current_date <= end_date_parsed:
        # Track used resources per time slot for THIS date
        used_resources_by_time: Dict[time, Dict[str, Set[int]]] = defaultdict(
            lambda: {"buses": set(), "drivers": set()}
        )

        for start_time, template_recs in records_by_time.items():
            # Get available buses for this time slot
            available_buses = [
                b for b in all_buses 
                if b.id not in used_resources_by_time[start_time]["buses"]
            ]

            # Get available drivers for this time slot (not on leave, not used)
            available_drivers = [
                d for d in all_drivers
                if d.user_id not in used_resources_by_time[start_time]["drivers"]
                and not is_on_leave(d.user_id, current_date)
            ]

            # Create mapping: busno -> actual bus_id
            bus_map = {i + 1: bus.id for i, bus in enumerate(available_buses)}

            # Create mapping: driverno -> actual driver_id
            driver_map = {i + 1: driver.user_id for i, driver in enumerate(available_drivers)}

            # Process each template record for this time slot
            for rec in template_recs:
                bus_id = bus_map.get(rec.busno)
                driver_id = driver_map.get(rec.driverno)

                # Skip if resources not available
                if not bus_id or not driver_id:
                    skipped_trips.append({
                        "date": str(current_date),
                        "time": str(rec.start_time),
                        "route": rec.route_id,
                        "reason": "Insufficient resources" if not bus_id and not driver_id
                                 else "No bus available" if not bus_id
                                 else "No driver available"
                    })
                    continue

                # Check for duplicates (shouldn't happen with proper template)
                exists = db.query(ScheduleTrip).filter(
                    ScheduleTrip.route_id == rec.route_id,
                    ScheduleTrip.trip_date == current_date,
                    ScheduleTrip.start_time == rec.start_time,
                ).first()

                if exists:
                    continue

                # Create trip
                trip = ScheduleTrip(
                    route_id=rec.route_id,
                    trip_date=current_date,
                    start_time=rec.start_time,
                    bus_id=bus_id,
                    driver_id=driver_id,
                    status=TripStatus.scheduled,
                )

                # Mark resources as used for this time slot
                used_resources_by_time[start_time]["buses"].add(bus_id)
                used_resources_by_time[start_time]["drivers"].add(driver_id)

                all_trips.append(trip)

        current_date += timedelta(days=1)

    if not all_trips:
        raise HTTPException(
            400, 
            detail={
                "error": "No trips could be generated",
                "skipped_trips": skipped_trips[:10],  # Show first 10
                "total_skipped": len(skipped_trips)
            }
        )

    # -------------------------------
    # Save all trips
    # -------------------------------
    try:
        db.bulk_save_objects(all_trips)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(400, f"Database error: {str(e)}")

    # -------------------------------
    # Generate detailed logs (optimize with joins)
    # -------------------------------
    logs = []
    for trip in all_trips[:100]:  # Limit to first 100 for performance
        route_name = db.query(Route.name).filter(Route.id == trip.route_id).scalar()
        driver_name = db.query(User.name).filter(User.id == trip.driver_id).scalar()
        bus_code = db.query(Bus.code).filter(Bus.id == trip.bus_id).scalar()

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
            "total_trips_created": len(all_trips),
            "total_trips_skipped": len(skipped_trips),
            "trips_deleted": deleted_count if overwrite else 0,
            "start_date": str(start_date_parsed),
            "end_date": str(end_date_parsed),
            "template_used": template.name,
            "days_covered": (end_date_parsed - start_date_parsed).days + 1,
        },
        "validation": validation_result,
        "logs": logs,
        "skipped_sample": skipped_trips[:20] if skipped_trips else [],
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