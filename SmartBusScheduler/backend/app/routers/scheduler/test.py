from sqlalchemy.orm import Session
from ...models import ScheduleTrip, RouteStop, Route
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def get_route_duration(session: Session, route_id: str):
    duration = (
        session.query(RouteStop.time_from_start)
        .filter(RouteStop.route_id == route_id)
        .order_by(RouteStop.time_from_start.desc())
        .first()
    )
    return duration[0] if duration else 0


def get_trips(session: Session, driver_id=None, bus_id=None):
    query = session.query(ScheduleTrip)

    if driver_id:
        query = query.filter(ScheduleTrip.driver_id == driver_id)
    if bus_id:
        query = query.filter(ScheduleTrip.bus_id == bus_id)

    trips = query.order_by(ScheduleTrip.trip_date, ScheduleTrip.start_time).all()

    data = []

    for trip in trips:
        duration_min = get_route_duration(session, trip.route_id)

        start_dt = datetime.combine(trip.trip_date, trip.start_time)
        end_dt = start_dt + timedelta(minutes=duration_min)

        data.append({
            "trip_id": trip.id,
            "start": start_dt,
            "end": end_dt,
            "route": trip.route_id
        })

    return pd.DataFrame(data)


def analyze_and_plot(df, title="Schedule"):
    if df.empty:
        print("No trips found")
        return

    df = df.sort_values("start")

    # Calculate rest time
    df["rest_minutes"] = df["start"].diff().dt.total_seconds() / 60

    print("\n=== Trip Analysis ===")
    print(df[["trip_id", "start", "end", "rest_minutes"]])

    # Detect issues
    print("\n=== Issues ===")
    for i in range(1, len(df)):
        prev_end = df.iloc[i-1]["end"]
        curr_start = df.iloc[i]["start"]

        if curr_start < prev_end:
            print(f"❌ Overlap between trip {df.iloc[i-1]['trip_id']} and {df.iloc[i]['trip_id']}")
        elif (curr_start - prev_end).total_seconds() / 60 < 30:
            print(f"⚠️ Low rest time before trip {df.iloc[i]['trip_id']}")

    # Plot timeline
    plt.figure(figsize=(10, 3))

    for i, row in df.iterrows():
        plt.plot([row["start"], row["end"]], [1, 1], linewidth=10)

    plt.title(title)
    plt.yticks([])
    plt.xlabel("Time")
    plt.show()


# ===== MAIN USAGE =====

def visualize_driver(session: Session, driver_id: int):
    df = get_trips(session, driver_id=driver_id)
    analyze_and_plot(df, title=f"Driver {driver_id} Schedule")


def visualize_bus(session: Session, bus_id: int):
    df = get_trips(session, bus_id=bus_id)
    analyze_and_plot(df, title=f"Bus {bus_id} Schedule")

if __name__ == "__main__":
    from ...database import SessionLocal
    session = SessionLocal()

    # Example usage:
    visualize_driver(session, driver_id=10)
    visualize_bus(session, bus_id=1)