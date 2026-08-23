# synthetic_od_data_generator.py

import csv
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from SmartBusScheduler.backend.app.database import SessionLocal
from SmartBusScheduler.backend.app.models import Route, RouteStop, ScheduleTrip

# =========================
# CONFIG
# =========================

NUM_DAYS = 15
START_DATE = datetime(2024, 3, 30)
DEFAULT_TRIP_TIMES = ["08:00", "09:00", "10:00", "17:00", "18:00", "19:00"]
OUTPUT_FILE = "synthetic_od_data.csv"

# Demand tuning
PEAK_MULTIPLIER = 2.0
BASE_MIN = 5
BASE_MAX = 20

# =========================
# HELPERS
# =========================

def is_peak(hour: int) -> bool:
    return (7 <= hour <= 10) or (17 <= hour <= 20)


def get_base_demand(hour: int) -> int:
    base = random.randint(BASE_MIN, BASE_MAX)
    return int(base * PEAK_MULTIPLIER) if is_peak(hour) else base


def choose_destination(i, stops, hour):
    """
    More realistic destination selection:
    - Morning: forward bias (work commute)
    - Evening: reverse bias (return home)
    - Midday: random shorter trips
    """

    if i >= len(stops) - 1:
        return None

    remaining_stops = stops[i + 1 :]

    if not remaining_stops:
        return None

    # Morning: longer forward trips
    if 7 <= hour <= 10:
        weights = [j + 1 for j in range(len(remaining_stops))]

    # Evening: shorter trips (reverse commute pattern simplified)
    elif 17 <= hour <= 20:
        weights = list(reversed([j + 1 for j in range(len(remaining_stops))]))

    # Midday: short random hops
    else:
        weights = [1] * len(remaining_stops)

    return random.choices(remaining_stops, weights=weights, k=1)[0]


# =========================
# DB FETCH
# =========================

def fetch_routes_and_stops(db: Session):
    route_stops = {}

    routes = db.query(Route).filter(Route.is_active == True).all()

    for route in routes:
        stops = (
            db.query(RouteStop)
            .filter(RouteStop.route_id == route.id)
            .order_by(RouteStop.seq)
            .all()
        )

        route_stops[route.id] = [rs.stop_id for rs in stops]

    return route_stops


def fetch_trip_times(db: Session, route_id: str):
    trips = (
        db.query(ScheduleTrip)
        .filter(ScheduleTrip.route_id == route_id)
        .all()
    )

    if not trips:
        return DEFAULT_TRIP_TIMES

    trip_times = []

    for trip in trips:
        if trip.start_time:
            trip_times.append(trip.start_time.strftime("%H:%M"))

    return list(set(trip_times)) or DEFAULT_TRIP_TIMES


# =========================
# GENERATOR
# =========================

def generate_od_data(db: Session):
    rows = []

    route_stops_map = fetch_routes_and_stops(db)

    for day in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day)

        for route_id, stops in route_stops_map.items():
            if len(stops) < 2:
                continue

            trip_times = fetch_trip_times(db, route_id)

            for trip_time_str in trip_times:
                trip_time = datetime.strptime(trip_time_str, "%H:%M")

                trip_datetime = current_date.replace(
                    hour=trip_time.hour,
                    minute=trip_time.minute,
                    second=0,
                    microsecond=0,
                )

                hour = trip_time.hour

                for i, origin_stop in enumerate(stops[:-1]):

                    demand = get_base_demand(hour)

                    # Split demand into OD pairs
                    for _ in range(demand):

                        destination = choose_destination(i, stops, hour)

                        if not destination:
                            continue

                        rows.append({
                            "route_id": route_id,
                            "origin_stop_id": origin_stop,
                            "destination_stop_id": destination,
                            "trip_datetime": trip_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            "boarding_count": 1,  # each row = 1 passenger
                        })

    return rows


# =========================
# AGGREGATION (IMPORTANT)
# =========================

def aggregate_rows(rows):
    """
    Convert per-passenger rows → aggregated counts
    to match your DB schema + UNIQUE constraint
    """

    agg = {}

    for r in rows:
        key = (
            r["route_id"],
            r["origin_stop_id"],
            r["destination_stop_id"],
            r["trip_datetime"],
        )

        if key not in agg:
            agg[key] = 0

        agg[key] += 1

    result = []

    for (route_id, origin, dest, dt), count in agg.items():
        result.append({
            "route_id": route_id,
            "origin_stop_id": origin,
            "destination_stop_id": dest,
            "trip_datetime": dt,
            "boarding_count": count,
        })

    return result


# =========================
# SAVE
# =========================

def save_to_csv(data):
    with open(OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "route_id",
                "origin_stop_id",
                "destination_stop_id",
                "trip_datetime",
                "boarding_count",
            ],
        )
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Synthetic OD data saved to {OUTPUT_FILE}")


# =========================
# MAIN
# =========================

def main():
    db = SessionLocal()
    try:
        raw_rows = generate_od_data(db)
        aggregated = aggregate_rows(raw_rows)
        save_to_csv(aggregated)
    finally:
        db.close()


if __name__ == "__main__":
    main()