# =========================================================
# SCHEDULE PERFORMANCE ANALYZER
# =========================================================
#
# This script analyzes transit schedule quality using:
#
# 1. Average Passenger Waiting Time
# 2. Maximum Waiting Time
# 3. System Throughput
# 4. Resource Utilization
# 5. Queue Length Average
# 6. Queue Length Peak
# 7. Response Time
# 8. Idle Time of Resources
# 9. Trip Distribution Fairness
# 10. Driver Route Change Frequency
# 11. Overtime Beyond Shift
# 12. Driver Idle Time
# 13. Rest Compliance Rate
# 14. Shift Allocation Fairness
#
# =========================================================

from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean
from math import sqrt

from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database import SessionLocal

from ...models import (
    ScheduleTrip,
    TemplateRecord,
    RouteStop,
    Bus,
    Driver,
    OBData,
)

# =========================================================
# CONFIG
# =========================================================

SHIFT_HOURS = 8

MAX_SHIFT_MINUTES = SHIFT_HOURS * 60

MIN_REST_SAME_ROUTE = 10

MIN_REST_DIFFERENT_ROUTE = 20

DEFAULT_RUNTIME = 60

PEAK_CAPACITY = 50

# =========================================================
# HELPERS
# =========================================================

def compute_runtime_map(db: Session):

    rows = (
        db.query(
            RouteStop.route_id,
            func.max(RouteStop.time_from_start)
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


def get_trip_end(trip, runtime_map):

    runtime = runtime_map.get(
        trip.route_id,
        DEFAULT_RUNTIME
    )

    start_dt = datetime.combine(
        trip.trip_date,
        trip.start_time
    )

    end_dt = start_dt + timedelta(
        minutes=runtime
    )

    return end_dt


def std_dev(values):

    if len(values) <= 1:
        return 0

    avg = mean(values)

    variance = sum(
        (x - avg) ** 2 for x in values
    ) / len(values)

    return sqrt(variance)


# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze_schedule(schedule_date):

    db = SessionLocal()

    try:

        runtime_map = compute_runtime_map(db)

        trips = (
            db.query(ScheduleTrip)
            .filter(
                ScheduleTrip.trip_date == schedule_date
            )
            .order_by(
                ScheduleTrip.start_time
            )
            .all()
        )

        if not trips:
            print("No trips found")
            return

        # =================================================
        # LOAD PASSENGER DEMAND
        # =================================================

        ob_rows = (
            db.query(
                OBData.route_id,
                OBData.trip_datetime,
                func.sum(
                    OBData.boarding_count
                )
            )
            .group_by(
                OBData.route_id,
                OBData.trip_datetime
            )
            .all()
        )

        demand_by_route = defaultdict(list)

        for route_id, dt, count in ob_rows:

            demand_by_route[route_id].append({
                "time": dt,
                "count": count
            })

        # =================================================
        # METRIC VARIABLES
        # =================================================

        passenger_wait_times = []

        queue_lengths = []

        total_passengers = 0

        bus_trip_count = defaultdict(int)

        bus_active_minutes = defaultdict(int)

        driver_active_minutes = defaultdict(int)

        driver_idle_minutes = defaultdict(int)

        driver_route_changes = defaultdict(int)

        driver_shift_minutes = defaultdict(int)

        rest_compliance_checks = 0

        rest_compliance_success = 0

        driver_routes = defaultdict(list)

        # =================================================
        # PROCESS TRIPS
        # =================================================

        trips_by_driver = defaultdict(list)

        trips_by_bus = defaultdict(list)

        for trip in trips:

            trips_by_driver[trip.driver_id].append(trip)

            trips_by_bus[trip.bus_id].append(trip)

        # =================================================
        # WAITING TIME + QUEUE ESTIMATION
        # =================================================

        for route_id in demand_by_route:

            route_trips = [
                t for t in trips
                if t.route_id == route_id
            ]

            route_trips.sort(
                key=lambda x: x.start_time
            )

            if not route_trips:
                continue

            for demand in demand_by_route[route_id]:

                passenger_time = demand["time"]

                passengers = demand["count"]

                total_passengers += passengers

                future_trip = None

                for trip in route_trips:

                    trip_dt = datetime.combine(
                        trip.trip_date,
                        trip.start_time
                    )

                    if trip_dt >= passenger_time:
                        future_trip = trip_dt
                        break

                if future_trip:

                    wait = (
                        future_trip -
                        passenger_time
                    ).total_seconds() / 60

                    passenger_wait_times.append(wait)

                    queue_estimate = (
                        wait / 30
                    ) * passengers

                    queue_lengths.append(queue_estimate)

        # =================================================
        # BUS UTILIZATION
        # =================================================

        for bus_id, bus_trips in trips_by_bus.items():

            total_runtime = 0

            for trip in bus_trips:

                runtime = runtime_map.get(
                    trip.route_id,
                    DEFAULT_RUNTIME
                )

                total_runtime += runtime

                bus_trip_count[bus_id] += 1

            bus_active_minutes[bus_id] = total_runtime

        # =================================================
        # DRIVER ANALYSIS
        # =================================================

        for driver_id, driver_trips in trips_by_driver.items():

            driver_trips.sort(
                key=lambda x: x.start_time
            )

            previous_trip = None

            total_shift = 0

            total_idle = 0

            route_changes = 0

            for trip in driver_trips:

                runtime = runtime_map.get(
                    trip.route_id,
                    DEFAULT_RUNTIME
                )

                total_shift += runtime

                current_start = datetime.combine(
                    trip.trip_date,
                    trip.start_time
                )

                current_end = current_start + timedelta(
                    minutes=runtime
                )

                driver_routes[driver_id].append(
                    trip.route_id
                )

                if previous_trip:

                    prev_end = get_trip_end(
                        previous_trip,
                        runtime_map
                    )

                    idle = (
                        current_start - prev_end
                    ).total_seconds() / 60

                    total_idle += max(idle, 0)

                    # Route changes

                    if (
                        previous_trip.route_id !=
                        trip.route_id
                    ):
                        route_changes += 1
                        required_rest = (
                            MIN_REST_DIFFERENT_ROUTE
                        )
                    else:
                        required_rest = (
                            MIN_REST_SAME_ROUTE
                        )

                    # Rest compliance

                    rest_compliance_checks += 1

                    if idle >= required_rest:
                        rest_compliance_success += 1

                previous_trip = trip

            driver_shift_minutes[driver_id] = total_shift

            driver_idle_minutes[driver_id] = total_idle

            driver_route_changes[driver_id] = route_changes

            driver_active_minutes[driver_id] = total_shift

        # =================================================
        # FINAL METRICS
        # =================================================

        avg_wait = round(
            mean(passenger_wait_times), 2
        ) if passenger_wait_times else 0

        max_wait = round(
            max(passenger_wait_times), 2
        ) if passenger_wait_times else 0

        throughput = round(
            total_passengers / 24,
            2
        )

        total_bus_capacity = (
            len(bus_active_minutes) *
            24 * 60
        )

        used_bus_minutes = sum(
            bus_active_minutes.values()
        )

        resource_utilization = round(
            (used_bus_minutes /
             total_bus_capacity) * 100,
            2
        ) if total_bus_capacity else 0

        avg_queue = round(
            mean(queue_lengths), 2
        ) if queue_lengths else 0

        peak_queue = round(
            max(queue_lengths), 2
        ) if queue_lengths else 0

        response_time = avg_wait

        idle_resource_pct = round(
            100 - resource_utilization,
            2
        )

        # Trip fairness

        trip_counts = list(
            bus_trip_count.values()
        )

        fairness_std = std_dev(trip_counts)

        trip_distribution_fairness = round(
            max(0, 100 - fairness_std * 5),
            2
        )

        avg_route_changes = round(
            mean(
                driver_route_changes.values()
            ),
            2
        ) if driver_route_changes else 0

        overtime_minutes = []

        for mins in driver_shift_minutes.values():

            overtime_minutes.append(
                max(0, mins - MAX_SHIFT_MINUTES)
            )

        avg_overtime = round(
            mean(overtime_minutes),
            2
        ) if overtime_minutes else 0

        avg_driver_idle = round(
            mean(
                driver_idle_minutes.values()
            ),
            2
        ) if driver_idle_minutes else 0

        rest_compliance_rate = round(
            (
                rest_compliance_success /
                rest_compliance_checks
            ) * 100,
            2
        ) if rest_compliance_checks else 100

        # Shift fairness

        shift_values = list(
            driver_shift_minutes.values()
        )

        shift_std = std_dev(shift_values)

        shift_fairness = round(
            max(0, 100 - shift_std / 5),
            2
        )

        # =================================================
        # PRINT RESULTS
        # =================================================

        print("\n=================================================")
        print("SCHEDULE PERFORMANCE REPORT")
        print("=================================================\n")

        print(
            f"Average Passenger Waiting Time (mins): {avg_wait}"
        )

        print(
            f"Maximum Waiting Time (mins): {max_wait}"
        )

        print(
            f"System Throughput (passengers/hour): {throughput}"
        )

        print(
            f"Resource Utilization (%): {resource_utilization}"
        )

        print(
            f"Queue Length - Average (passengers): {avg_queue}"
        )

        print(
            f"Queue Length - Peak (passengers): {peak_queue}"
        )

        print(
            f"Response Time (mins): {response_time}"
        )

        print(
            f"Idle Time of Resources (%): {idle_resource_pct}"
        )

        print(
            f"Trip Distribution Fairness (%): "
            f"{trip_distribution_fairness}"
        )

        print(
            f"Driver Route Change Frequency "
            f"(changes/driver/day): "
            f"{avg_route_changes}"
        )

        print(
            f"Overtime Beyond Shift (mins): "
            f"{avg_overtime}"
        )

        print(
            f"Driver Idle Time (mins): "
            f"{avg_driver_idle}"
        )

        print(
            f"Rest Compliance Rate (%): "
            f"{rest_compliance_rate}"
        )

        print(
            f"Shift Allocation Fairness (%): "
            f"{shift_fairness}"
        )

        print("\n=================================================\n")

    except Exception as e:

        print("FAILED:", str(e))

        raise

    finally:

        db.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    analyze_schedule(
        schedule_date=datetime(
            2026,
            5,
            11
        ).date()
    )