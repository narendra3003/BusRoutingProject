# scheduler_engine.py

from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from ...database import SessionLocal

from ...models import (
    OBData,
    RouteStop,
    Bus,
    Driver,
    DriverLeave,
    ScheduleTrip,
    Template,
    TemplateRecord,
    BusStatus,
    DriverStatus,
)

# =========================================================
# CONFIG
# =========================================================

SLOT_MINUTES = 30

LOOKAHEAD_WINDOWS = 3

SAME_ROUTE_REST_MINUTES = 10

DIFFERENT_ROUTE_REST_MINUTES = 20

DEFAULT_RUNTIME = 60

DEFAULT_CAPACITY = 50


# =========================================================
# HELPERS
# =========================================================

def floor_to_slot(dt, slot_minutes=SLOT_MINUTES):

    return dt.replace(
        minute=(dt.minute // slot_minutes) * slot_minutes,
        second=0,
        microsecond=0,
    )


def get_day_filter(category, column):

    dow = func.extract("dow", column)

    if category == "weekday":
        return dow.in_([1, 2, 3, 4, 5])

    if category == "saturday":
        return dow == 6

    return dow == 0


def get_rest_minutes(prev_trip, curr_trip):

    if not prev_trip:
        return 0

    if prev_trip["route_id"] == curr_trip["route_id"]:
        return SAME_ROUTE_REST_MINUTES

    return DIFFERENT_ROUTE_REST_MINUTES


# =========================================================
# ROUTE RUNTIME
# =========================================================

def compute_route_runtime_map(db: Session):

    rows = (
        db.query(
            RouteStop.route_id,
            func.max(RouteStop.time_from_start).label("runtime"),
        )
        .group_by(RouteStop.route_id)
        .all()
    )

    runtime_map = {}

    for route_id, runtime in rows:

        runtime_map[route_id] = max(
            int(runtime or DEFAULT_RUNTIME),
            10
        )

    return runtime_map


# =========================================================
# CAPACITY
# =========================================================

def compute_average_capacity(db: Session):

    avg_capacity = (
        db.query(
            func.avg(
                Bus.sitting_capacity +
                Bus.standing_capacity
            )
        )
        .filter(Bus.status == BusStatus.active)
        .scalar()
    )

    return int(avg_capacity or DEFAULT_CAPACITY)


# =========================================================
# DEMAND
# =========================================================

def compute_demand(
    db: Session,
    category: str,
):

    day_filter = get_day_filter(
        category,
        OBData.trip_datetime,
    )

    direction_expr = case(
        (
            OBData.origin_stop_id <
            OBData.destination_stop_id,
            "UP",
        ),
        else_="DOWN",
    )

    rows = (
        db.query(
            OBData.route_id,
            direction_expr.label("direction"),
            func.date_trunc(
                "minute",
                OBData.trip_datetime
            ).label("ts"),
            func.sum(
                OBData.boarding_count
            ).label("passengers"),
        )
        .filter(day_filter)
        .group_by(
            OBData.route_id,
            "direction",
            "ts",
        )
        .all()
    )

    demand = defaultdict(dict)

    for route_id, direction, ts, passengers in rows:

        slot = floor_to_slot(ts)

        key = f"{route_id}:{direction}"

        demand[key][slot] = (
            demand[key].get(slot, 0) +
            float(passengers)
        )

    # smoothing

    smoothed = defaultdict(dict)

    for key in demand:

        slots = sorted(demand[key].keys())

        for i, slot in enumerate(slots):

            rolling_total = 0

            for j in range(
                i,
                min(i + LOOKAHEAD_WINDOWS, len(slots))
            ):

                rolling_total += (
                    demand[key].get(slots[j], 0)
                )

            smoothed[key][slot] = rolling_total

    return smoothed


# =========================================================
# TRIP GENERATION
# =========================================================

def generate_trips(
    demand,
    runtime_map,
    capacity,
):

    trips = []

    for route_key, slots in demand.items():

        route_id, direction = route_key.split(":")

        runtime = runtime_map.get(
            route_id,
            DEFAULT_RUNTIME,
        )

        for slot, passengers in slots.items():

            required_trips = ceil(
                passengers / capacity
            )

            if required_trips <= 0:
                continue

            slot_end = slot + timedelta(
                minutes=SLOT_MINUTES
            )

            spacing = (
                (slot_end - slot) /
                required_trips
            )

            for i in range(required_trips):

                start_time = slot + (
                    spacing * i
                )

                end_time = start_time + timedelta(
                    minutes=runtime
                )

                trips.append({
                    "route_id": route_id,
                    "direction": direction,
                    "start_time": start_time,
                    "end_time": end_time,
                })

    return sorted(
        trips,
        key=lambda x: x["start_time"]
    )


# =========================================================
# DRIVER LEAVE
# =========================================================

def driver_on_leave(
    driver_id,
    schedule_date,
    leaves,
):

    for leave in leaves:

        if leave.driver_id != driver_id:
            continue

        if (
            leave.start_date <= schedule_date <= leave.end_date
        ):
            return True

    return False


# =========================================================
# RESOURCE ASSIGNMENT
# =========================================================

def assign_resources(
    db: Session,
    trips,
    schedule_date,
):

    buses = (
        db.query(Bus)
        .filter(
            Bus.status == BusStatus.active
        )
        .order_by(Bus.id)
        .all()
    )

    drivers = (
        db.query(Driver)
        .filter(
            Driver.status == DriverStatus.active
        )
        .order_by(
            Driver.experience_years.desc()
        )
        .all()
    )

    leaves = (
        db.query(DriverLeave)
        .filter(
            DriverLeave.start_date <= schedule_date,
            DriverLeave.end_date >= schedule_date,
        )
        .all()
    )

    bus_state = {}

    driver_state = {}

    assigned_trips = []

    for trip in trips:

        assigned_bus = None

        assigned_driver = None

        # BUS ASSIGNMENT

        for bus in buses:

            state = bus_state.get(bus.id)

            if not state:
                assigned_bus = bus
                break

            rest_minutes = get_rest_minutes(
                state["last_trip"],
                trip,
            )

            available_at = (
                state["free_at"] +
                timedelta(minutes=rest_minutes)
            )

            if available_at <= trip["start_time"]:
                assigned_bus = bus
                break

        if not assigned_bus:
            continue

        # DRIVER ASSIGNMENT

        for driver in drivers:

            if driver_on_leave(
                driver.user_id,
                schedule_date,
                leaves,
            ):
                continue

            state = driver_state.get(
                driver.user_id
            )

            if not state:
                assigned_driver = driver
                break

            rest_minutes = get_rest_minutes(
                state["last_trip"],
                trip,
            )

            available_at = (
                state["free_at"] +
                timedelta(minutes=rest_minutes)
            )

            if available_at <= trip["start_time"]:
                assigned_driver = driver
                break

        if not assigned_driver:
            continue

        trip["bus_id"] = assigned_bus.id

        trip["driver_id"] = assigned_driver.user_id

        bus_state[assigned_bus.id] = {
            "free_at": trip["end_time"],
            "last_trip": trip,
        }

        driver_state[assigned_driver.user_id] = {
            "free_at": trip["end_time"],
            "last_trip": trip,
        }

        assigned_trips.append(trip)

    return assigned_trips


# =========================================================
# TEMPLATE STORAGE
# =========================================================

def store_template(
    db: Session,
    category,
    trips,
    user_id,
):

    template = Template(
        name=f"{category}_auto",
        template_type=category,
        bus_count=len(
            set(t["bus_id"] for t in trips)
        ),
        driver_count=len(
            set(t["driver_id"] for t in trips)
        ),
        created_by=user_id,
    )

    db.add(template)

    db.flush()

    records = []

    for trip in trips:

        records.append(
            TemplateRecord(
                template_id=template.id,
                route_id=trip["route_id"],
                start_time=trip["start_time"].time(),
                busno=trip["bus_id"],
                driverno=trip["driver_id"],
            )
        )

    db.bulk_save_objects(records)

    db.commit()

    db.refresh(template)

    return template


# =========================================================
# CONFLICT CHECK
# =========================================================

def has_conflict(
    existing_trips,
    bus_id,
    driver_id,
    start_dt,
    end_dt,
    runtime_map,
):

    for existing in existing_trips:

        same_bus = existing.bus_id == bus_id

        same_driver = (
            existing.driver_id == driver_id
        )

        if not (same_bus or same_driver):
            continue

        existing_runtime = runtime_map.get(
            existing.route_id,
            DEFAULT_RUNTIME,
        )

        existing_start = datetime.combine(
            existing.trip_date,
            existing.start_time,
        )

        existing_end = (
            existing_start +
            timedelta(minutes=existing_runtime)
        )

        overlap = (
            start_dt < existing_end and
            end_dt > existing_start
        )

        if overlap:
            return True

    return False


# =========================================================
# SCHEDULE GENERATION
# =========================================================

def generate_schedule(
    db: Session,
    template,
    schedule_date,
    runtime_map,
):

    existing_trips = (
        db.query(ScheduleTrip)
        .filter(
            ScheduleTrip.trip_date == schedule_date
        )
        .all()
    )

    new_schedule = []

    for rec in template.records:

        runtime = runtime_map.get(
            rec.route_id,
            DEFAULT_RUNTIME,
        )

        start_dt = datetime.combine(
            schedule_date,
            rec.start_time,
        )

        end_dt = start_dt + timedelta(
            minutes=runtime
        )

        if has_conflict(
            existing_trips,
            rec.busno,
            rec.driverno,
            start_dt,
            end_dt,
            runtime_map,
        ):
            continue

        trip = ScheduleTrip(
            route_id=rec.route_id,
            trip_date=schedule_date,
            start_time=rec.start_time,
            bus_id=rec.busno,
            driver_id=rec.driverno,
        )

        new_schedule.append(trip)

        existing_trips.append(trip)

    db.bulk_save_objects(new_schedule)

    db.commit()

    return new_schedule


# =========================================================
# MAIN
# =========================================================

def run_scheduler():

    db = SessionLocal()

    try:

        category = "weekday"

        user_id = 1

        schedule_date = datetime(
            2026,
            5,
            11,
        ).date()

        print("STEP 1 -> Computing demand")

        demand = compute_demand(
            db,
            category,
        )

        print("STEP 2 -> Computing route runtimes")

        runtime_map = compute_route_runtime_map(db)

        print("STEP 3 -> Computing capacity")

        capacity = compute_average_capacity(db)

        print("Average capacity:", capacity)

        print("STEP 4 -> Generating trips")

        trips = generate_trips(
            demand,
            runtime_map,
            capacity,
        )

        print("Generated trips:", len(trips))

        print("STEP 5 -> Assigning resources")

        assigned_trips = assign_resources(
            db,
            trips,
            schedule_date,
        )

        print(
            "Assigned trips:",
            len(assigned_trips)
        )

        print("STEP 6 -> Storing template")

        template = store_template(
            db,
            category,
            assigned_trips,
            user_id,
        )

        print(
            "Template created:",
            template.id
        )

        print("STEP 7 -> Generating schedule")

        schedule = generate_schedule(
            db,
            template,
            schedule_date,
            runtime_map,
        )

        print(
            "Final scheduled trips:",
            len(schedule)
        )

        print("SUCCESS")

    except Exception as e:

        db.rollback()

        print("FAILED")

        print(str(e))

        raise

    finally:

        db.close()


if __name__ == "__main__":

    run_scheduler()