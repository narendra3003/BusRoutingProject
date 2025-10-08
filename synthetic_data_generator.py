import pandas as pd
import random
from datetime import datetime, timedelta

# -------------------
# CONFIGURATION
# -------------------
NUM_ROUTES = 8
TOTAL_STOPS = 60
DATE = "2025-10-08"

# Peak hours (for high frequency)
PEAK_MORNING = (7, 10)
PEAK_EVENING = (17, 22)

# -------------------
# 1️⃣ Create Global Stops Pool
# -------------------
def generate_stops(n_stops=60):
    base_lat, base_lon = 19.07, 72.87
    stops = []
    for i in range(1, n_stops + 1):
        stops.append({
            "stop_id": f"S{i:03}",
            "stop_name": f"Stop_{i}",
            "lat": base_lat + random.uniform(-0.1, 0.1),
            "lon": base_lon + random.uniform(-0.1, 0.1)
        })
    return pd.DataFrame(stops)

# -------------------
# 2️⃣ Create Routes (with overlapping stops)
# -------------------
def generate_routes(stops_df, num_routes=8):
    routes = []
    for r in range(1, num_routes + 1):
        # long routes = 18–20 stops, short routes = 12–15
        num_stops = random.randint(12, 20)
        route_stops = random.sample(list(stops_df["stop_id"]), num_stops)
        routes.append({
            "route_id": f"R{r:03}",
            "stops": route_stops
        })
    return pd.DataFrame(routes)

# -------------------
# 3️⃣ Generate Trips (planned + observed)
# -------------------
def generate_trips(stops_df, routes_df, base_date=DATE):
    planned, observed = [], []
    base_date = datetime.strptime(base_date, "%Y-%m-%d")

    for _, route in routes_df.iterrows():
        route_id = route["route_id"]
        route_stops = route["stops"]

        # route length defines trip frequency
        route_len = len(route_stops)
        if route_len > 17:
            trips_per_day = random.randint(12, 18)  # long route
            avg_trip_duration = 80  # minutes
        elif route_len > 15:
            trips_per_day = random.randint(18, 25)  # medium route
            avg_trip_duration = 60
        else:
            trips_per_day = random.randint(25, 30)  # short route
            avg_trip_duration = 40

        # generate trip start times across the day
        trip_times = []
        current_time = base_date.replace(hour=5, minute=30)
        while current_time.hour < 23:
            # higher chance of trips during peak hours
            if (PEAK_MORNING[0] <= current_time.hour <= PEAK_MORNING[1]) or \
               (PEAK_EVENING[0] <= current_time.hour <= PEAK_EVENING[1]):
                interval = random.randint(15, 25)
            else:
                interval = random.randint(30, 60)
            trip_times.append(current_time)
            current_time += timedelta(minutes=interval)

        # randomly limit number of trips
        trip_times = random.sample(trip_times, min(len(trip_times), trips_per_day))
        trip_times.sort()

        for t_idx, trip_start in enumerate(trip_times, start=1):
            trip_id = f"{route_id}_T{t_idx:03}"
            start_time = trip_start

            for order, stop_id in enumerate(route_stops, start=1):
                travel = random.randint(3, 6) + (route_len // 2)  # longer route → longer gap
                dwell = random.randint(1, 3)
                planned_arrival = start_time + timedelta(minutes=travel)
                planned_departure = planned_arrival + timedelta(minutes=dwell)

                # Planned schedule
                planned.append({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "stop_order": order,
                    "planned_arrival": planned_arrival.strftime("%Y-%m-%d %H:%M:%S"),
                    "planned_departure": planned_departure.strftime("%Y-%m-%d %H:%M:%S")
                })

                # Observed schedule (real-world variance)
                delay = random.randint(-2, 10)
                observed_arrival = planned_arrival + timedelta(minutes=delay)
                observed_departure = observed_arrival + timedelta(minutes=random.randint(1, 4))
                boarding_in = max(0, int(random.gauss(12 + (3 if PEAK_MORNING[0] <= planned_arrival.hour <= PEAK_MORNING[1] or PEAK_EVENING[0] <= planned_arrival.hour <= PEAK_EVENING[1] else 0), 5)))
                boarding_out = max(0, int(random.gauss(8, 3)))

                observed.append({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "observed_arrival": observed_arrival.strftime("%Y-%m-%d %H:%M:%S"),
                    "observed_departure": observed_departure.strftime("%Y-%m-%d %H:%M:%S"),
                    "boarding_in": boarding_in,
                    "boarding_out": boarding_out,
                    "delay_mins": delay
                })

                start_time = planned_departure

    return pd.DataFrame(planned), pd.DataFrame(observed)

# -------------------
# 4️⃣ Run Full Generation
# -------------------
stops_df = generate_stops(TOTAL_STOPS)
routes_df = generate_routes(stops_df, NUM_ROUTES)
planned_df, observed_df = generate_trips(stops_df, routes_df, base_date=DATE)

# Save to CSV
stops_df.to_csv("stops.csv", index=False)
routes_df.to_csv("routes.csv", index=False)
planned_df.to_csv("planned_schedule.csv", index=False)
observed_df.to_csv("observation_data.csv", index=False)

print("✅ Synthetic real-like dataset generated!")
print(f"Stops: {len(stops_df)}, Routes: {len(routes_df)}")
print(f"Planned: {len(planned_df)} rows, Observed: {len(observed_df)} rows")
print("\nSample Planned:")
print(planned_df.head(10))
print("\nSample Observed:")
print(observed_df.head(10))

# ✅ Assuming you already have this function
# generate_trips(date) -> returns DataFrame with columns:
# ['trip_id', 'route_id', 'stop_id', 'stop_order', 'planned_arrival', 'planned_departure', ...]

def generate_dataset_for_range(start_date: str, end_date: str):
    """
    Generates synthetic schedule/observation data for a date range 
    using the existing generate_trips() function.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    all_data = []

    current = start
    while current <= end:
        print(f"Generating data for {current}...")
        df = generate_trips(current)  # reuse your daily generator
        df["date"] = current.strftime("%Y-%m-%d")
        all_data.append(df)
        current += timedelta(days=1)

    # Combine all
    full_df = pd.concat(all_data, ignore_index=True)

    # Save to CSV
    full_df.to_csv("synthetic_observations_range.csv", index=False)
    print(f"\n✅ Combined dataset saved as 'synthetic_observations_range.csv' ({len(full_df)} records).")

    return full_df

def generate_dataset_for_dates(date_input):
    """
    Generates synthetic data for a single date or a date range.
    date_input: str (YYYY-MM-DD) or tuple/list of two str (start, end)
    """
    if isinstance(date_input, str):
        # Single date
        dates = [datetime.strptime(date_input, "%Y-%m-%d").date()]
    elif isinstance(date_input, (tuple, list)) and len(date_input) == 2:
        # Date range
        start = datetime.strptime(date_input[0], "%Y-%m-%d").date()
        end = datetime.strptime(date_input[1], "%Y-%m-%d").date()
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)
    else:
        raise ValueError("date_input must be a string or a tuple/list of two date strings.")

    all_planned, all_observed = [], []
    stops_df = generate_stops(TOTAL_STOPS)
    routes_df = generate_routes(stops_df, NUM_ROUTES)

    for date in dates:
        print(f"Generating data for {date}...")
        planned_df, observed_df = generate_trips(stops_df, routes_df, base_date=date.strftime("%Y-%m-%d"))
        planned_df["date"] = date.strftime("%Y-%m-%d")
        observed_df["date"] = date.strftime("%Y-%m-%d")
        all_planned.append(planned_df)
        all_observed.append(observed_df)

    full_planned = pd.concat(all_planned, ignore_index=True)
    full_observed = pd.concat(all_observed, ignore_index=True)

    # Save to CSV
    stops_df.to_csv("stops.csv", index=False)
    routes_df.to_csv("routes.csv", index=False)
    full_planned.to_csv("planned_schedule.csv", index=False)
    full_observed.to_csv("observation_data.csv", index=False)

    print("✅ Synthetic real-like dataset generated!")
    print(f"Stops: {len(stops_df)}, Routes: {len(routes_df)}")
    print(f"Planned: {len(full_planned)} rows, Observed: {len(full_observed)} rows")
    print("\nSample Planned:")
    print(full_planned.head(10))
    print("\nSample Observed:")
    print(full_observed.head(10))

    return full_planned, full_observed
