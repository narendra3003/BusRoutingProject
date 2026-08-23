from datetime import datetime
from ...database import SessionLocal
# from ...models import Route, RouteStop
# from sqlalchemy.orm import joinedload
# from 
from ...models import Bus, Driver, DriverLeave, ScheduleTrip, OBData, Template, TemplateRecord
from datetime import datetime, timedelta
from collections import defaultdict
import math
"""

1. get the data from db and all functions to compute demand, build template, assign resources, generate schedule
2. run the main function to execute the flow

flow of template generation:
1. Compute demand using historical OBData
2. Build a template based on demand (abstract busno/driverno)

compute demand on 3 categories - weekday, saturday, sunday and store templates for each. This allows us to quickly generate schedule for any date by picking the right template and mapping resources.
use bus_count and driver_count in template to know how many resources to pull while generating schedule.
use simple 1 to bus_count mapping in template and then map to real bus IDs based on availability and usage. This allows us to decouple template from actual resources and handle dynamic changes in fleet/driver availability.
use on allowed no of buses/drivers in template to control max resources used for that day and avoid overallocation.
use driver usage in last 3 days to prefer less used drivers while assigning, to balance workload.
use driver shifts divide available count of drivers and assign shifts to them in template creation only and if needed assign double shifts to meet demand, this allows us to have a more balanced schedule and avoid overworking drivers.
bus capacity and all constants to be dynamic from db
correct logic of resources reuse after trip completion and using resuces less than or max to max equal to bus_count and driver_count with no double assignment of resource before completion of trip and having a bit of rest time 5-10 mins for normal trips (if same route just going up to down) or 20 min gap if route changes totally
future 30 mins demand count based bus and driver allocation in a ratio based way
resources go to and fro untill ratio of demnd changes drastically
route end time from route and route stop tables to be used to calculate when a bus/driver will be free after trip start and assign next trip accordingly

"""
CAPACITY_PER_BUS = 50  # adjust
def get_available_buses(session):
    return session.query(Bus).filter(Bus.status == "active").all()


def get_available_drivers(session, date):
    drivers = session.query(Driver).filter(Driver.status == "active").all()

    leaves = session.query(DriverLeave).filter(
        DriverLeave.start_date <= date,
        DriverLeave.end_date >= date,
        DriverLeave.status == "granted"
    ).all()

    leave_ids = {l.driver_id for l in leaves}

    return [d for d in drivers if d.user_id not in leave_ids]

def get_driver_usage(session, days=3):

    since = datetime.now() - timedelta(days=days)

    usage = {}

    trips = session.query(ScheduleTrip).filter(
        ScheduleTrip.created_at >= since
    ).all()

    for t in trips:
        usage[t.driver_id] = usage.get(t.driver_id, 0) + 1

    return usage

def assign_resources(template, buses, drivers, usage):
    """
    Map abstract busno/driverno → real IDs
    """

    # Sort drivers by least usage
    drivers_sorted = sorted(
        drivers, key=lambda d: usage.get(d.user_id, 0)
    )

    mapping = {
        "bus": {},
        "driver": {}
    }

    for i, bus in enumerate(buses):
        mapping["bus"][i + 1] = bus.id

    for i, driver in enumerate(drivers_sorted):
        mapping["driver"][i + 1] = driver.user_id

    return mapping

TIME_BUCKET_MIN = 30


def get_time_bucket(dt: datetime):
    return dt.replace(
        minute=(dt.minute // TIME_BUCKET_MIN) * TIME_BUCKET_MIN,
        second=0,
        microsecond=0,
    )

def compute_demand(session, target_date, lookback_days=20):
    """
    Computes average demand per route per time bucket
    using historical OBData.

    Returns:
    {
        route_id: {
            time_bucket: avg_passenger_count
        }
    }
    """

    start_date = target_date - timedelta(days=lookback_days)

    # Step 1: Fetch historical data
    rows = (
        session.query(OBData)
        .all()
    )

    print(f"Using {len(rows)} OBData rows from {start_date} → {target_date}")

    # Step 2: Aggregate
    demand_sum = defaultdict(lambda: defaultdict(int))
    demand_days = defaultdict(lambda: defaultdict(set))

    for row in rows:
        bucket = get_time_bucket(row.trip_datetime)
        route_id = row.route_id
        day = row.trip_datetime.date()

        demand_sum[route_id][bucket] += row.boarding_count
        demand_days[route_id][bucket].add(day)

    # Step 3: Convert to average demand
    demand_avg = defaultdict(dict)

    for route_id, buckets in demand_sum.items():
        for bucket, total in buckets.items():
            days_count = len(demand_days[route_id][bucket]) or 1
            demand_avg[route_id][bucket] = total / days_count

    print("Sample demand output:",
          {k: dict(list(v.items())[:5]) for k, v in list(demand_avg.items())[:3]})

    return demand_avg

def rebalance_system(session):
    """
    Called periodically (e.g., every 10 mins)
    """

    from models import TripLiveStatus, ScheduleTrip

    # 1. Get live delays
    delayed_trips = session.query(TripLiveStatus).filter(
        TripLiveStatus.delay_minutes > 10
    ).all()

    # 2. Identify impacted routes
    impacted_routes = {t.trip.route_id for t in delayed_trips}

    # 3. Pull future trips of those routes
    future_trips = session.query(ScheduleTrip).filter(
        ScheduleTrip.route_id.in_(impacted_routes),
        ScheduleTrip.status == "scheduled"
    ).all()

def generate_schedule(session, template, date):
    buses = get_available_buses(session)
    drivers = get_available_drivers(session, date)

    usage = get_driver_usage(session)
    mapping = assign_resources(template, buses, drivers, usage)

    for r in template.records:
        trip = ScheduleTrip(
            route_id=r.route_id,
            trip_date=date,
            start_time=r.start_time,
            bus_id=mapping["bus"].get(r.busno),
            driver_id=mapping["driver"].get(r.driverno),
        )

        session.add(trip)

    session.commit()



def estimate_buses(passengers, capacity=50):
    if not passengers or passengers <= 0:
        return 1  # minimum service

    return int(math.ceil(passengers / capacity))

def get_day_type(date):
    if date.weekday() == 6:
        return "sunday"
    elif date.weekday() == 5:
        return "saturday"
    return "weekday"

def build_template(session, date, demand_data, created_by, bus_count=20, driver_count=50):
    day_type = get_day_type(date)

    template = Template(
        name=f"{day_type}_template_{date}",
        template_type=day_type,
        bus_count=bus_count,
        driver_count=driver_count,
        created_by=created_by,
    )

    session.add(template)
    session.flush()

    bus_counter = 0
    driver_counter = 0

    for route_id, time_map in demand_data.items():
        for bucket, passengers in time_map.items():

            buses_needed = estimate_buses(passengers)

            for _ in range(buses_needed):
                bus_counter += 1
                driver_counter += 1

                record = TemplateRecord(
                    template_id=template.id,
                    route_id=route_id,
                    start_time=bucket.time(),
                    busno=bus_counter,
                    driverno=driver_counter,
                )

                session.add(record)

    template.bus_count = bus_counter
    template.driver_count = driver_counter

    session.commit()
    return template


def run(date: datetime, admin_user_id: int):
    session = SessionLocal()

    print("1. Computing demand...")
    demand = compute_demand(session, date)

    print("2. Building template...")
    template = build_template(session, date, demand, admin_user_id)

    print("3. Generating schedule...")
    generate_schedule(session, template, date)

    print("✅ Scheduling complete!")


if __name__ == "__main__":
    run(datetime(2026, 5, 6), admin_user_id=1)