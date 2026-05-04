# synthetic_ob_data_generator.py

import csv
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Route, RouteStop, ScheduleTrip

# =========================
# CONFIG
# =========================

NUM_DAYS = 15
START_DATE = datetime(2024, 3, 30)
DEFAULT_TRIP_TIMES = ["08:00", "09:00", "10:00", "17:00", "18:00", "19:00"]
OUTPUT_FILE = "synthetic_ob_data.csv"

# =========================
# HELPERS
# =========================

def is_peak(hour: int) -> bool:
    return (7 <= hour <= 10) or (17 <= hour <= 20)

def random_passenger_count(hour: int) -> int:
    return random.randint(30, 50) if is_peak(hour) else random.randint(5, 25)

# =========================
# DB FETCH
# =========================

def fetch_routes_and_stops(db: Session):
    """
    Uses RouteStop table (CORRECT for your schema)
    """
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
    """
    Uses ScheduleTrip (CORRECT model)
    """
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

def generate_ob_data(db: Session):
    rows = []

    route_stops_map = fetch_routes_and_stops(db)

    for day in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day)

        for route_id, stops in route_stops_map.items():
            if not stops:
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

                base_load = random_passenger_count(trip_time.hour)
                onboard_remaining = base_load

                for i, stop_id in enumerate(stops):

                    # Boarding logic
                    if i == 0:
                        boarding = random.randint(10, 20)
                    else:
                        boarding = random.randint(0, 5)

                    # Offboarding logic
                    if i == len(stops) - 1:
                        offboarding = onboard_remaining
                    else:
                        offboarding = random.randint(
                            0, min(5, onboard_remaining)
                        )

                    onboard_remaining += boarding - offboarding
                    onboard_remaining = max(0, onboard_remaining)

                    rows.append({
                        "route_id": route_id,
                        "stop_id": stop_id,
                        "boarding_count": boarding,
                        "offboarding_count": offboarding,
                        "trip_datetime": trip_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    })

    return rows

# =========================
# SAVE
# =========================

def save_to_csv(data):
    with open(OUTPUT_FILE, mode="w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "route_id",
                "stop_id",
                "boarding_count",
                "offboarding_count",
                "trip_datetime",
            ],
        )
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Synthetic OB data saved to {OUTPUT_FILE}")

# =========================
# MAIN
# =========================

def main():
    db = SessionLocal()
    try:
        data = generate_ob_data(db)
        save_to_csv(data)
    finally:
        db.close()

if __name__ == "__main__":
    main()