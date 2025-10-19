import pandas as pd
import random
from datetime import datetime, timedelta

# -------------------
# CONFIGURATION
# -------------------
NUM_ROUTES = 8               # base routes count (will become 16: up/down)
TOTAL_STOPS = 60
DATE = "2025-10-08"
PEAK_MORNING = (7, 10)
PEAK_EVENING = (17, 22)

# -------------------
# 1️⃣ Generate Stops
# -------------------
def generate_stops(n_stops=60):
    """Generates global pool of bus stops."""
    base_lat, base_lon = 19.07, 72.87
    stops = []
    for i in range(1, n_stops + 1):
        stops.append({
            "stop_id": f"S{i:03}",
            "stop_name": f"Stop_{i}",
            "lat": base_lat + random.uniform(-0.1, 0.1),
            "lon": base_lon + random.uniform(-0.1, 0.1)
        })
    stops_df = pd.DataFrame(stops)
    stops_df.to_csv("stops_data.csv", index=False)
    print(f"✅ Generated {n_stops} stops.")
    return stops_df

# -------------------
# 2️⃣ Generate Routes (Up + Down)
# -------------------
def generate_routes(stops_df, num_routes=8):
    """Generates route definitions — both Up and Down (R001_up / R001_down)."""
    routes = []
    for r in range(1, num_routes + 1):
        num_stops = random.randint(12, 20)
        route_stops = random.sample(list(stops_df["stop_id"]), num_stops)
        routes.append({
            "route_id": f"R{r:03}_up",
            "stops": route_stops
        })
        # Down route (reverse order)
        routes.append({
            "route_id": f"R{r:03}_down",
            "stops": list(reversed(route_stops))
        })
    routes_df = pd.DataFrame(routes)
    routes_df.to_csv("routes_data.csv", index=False)
    print(f"✅ Generated {num_routes * 2} routes (Up/Down).")
    return routes_df

# -------------------
# 3️⃣ Generate Buses
# -------------------
def generate_buses(num_buses=25):
    """Generates bus fleet with unique IDs and capacities."""
    buses = []
    for i in range(1, num_buses + 1):
        seating_cap = random.choice([30, 35, 40])
        max_cap = seating_cap + random.randint(10, 20)
        buses.append({
            "bus_id": f"B{i:03}",
            "seating_capacity": seating_cap,
            "max_capacity": max_cap
        })
    buses_df = pd.DataFrame(buses)
    buses_df.to_csv("buses_data.csv", index=False)
    print(f"✅ Generated {num_buses} buses.")
    return buses_df

# -------------------
# 4️⃣ Generate Observation Data for a Single Date
# -------------------
def generate_observation_for_date(stops_df, routes_df, buses_df, base_date="2025-10-08"):
    """
    Generates observation data (real-like arrival/departure with load) for a given date.
    """
    observed = []
    base_date = datetime.strptime(base_date, "%Y-%m-%d")

    for _, route in routes_df.iterrows():
        route_id = route["route_id"]
        route_stops = route["stops"]
        direction = "up" if "up" in route_id else "down"

        # trip frequency and duration
        route_len = len(route_stops)
        if route_len > 17:
            trips_per_day = random.randint(10, 15)
        elif route_len > 15:
            trips_per_day = random.randint(15, 20)
        else:
            trips_per_day = random.randint(20, 25)

        current_time = base_date.replace(hour=5, minute=30)
        trip_times = []
        while current_time.hour < 23:
            if (PEAK_MORNING[0] <= current_time.hour <= PEAK_MORNING[1]) or \
               (PEAK_EVENING[0] <= current_time.hour <= PEAK_EVENING[1]):
                interval = random.randint(15, 25)
            else:
                interval = random.randint(30, 60)
            trip_times.append(current_time)
            current_time += timedelta(minutes=interval)
        trip_times = random.sample(trip_times, min(len(trip_times), trips_per_day))
        trip_times.sort()

        for t_idx, trip_start in enumerate(trip_times, start=1):
            trip_id = f"{route_id}_T{t_idx:03}"
            start_time = trip_start

            # assign a random bus
            assigned_bus = random.choice(buses_df["bus_id"].tolist())

            for order, stop_id in enumerate(route_stops, start=1):
                travel = random.randint(3, 6)
                dwell = random.randint(1, 3)
                observed_arrival = start_time + timedelta(minutes=travel)
                observed_departure = observed_arrival + timedelta(minutes=dwell)
                delay = random.randint(-2, 8)

                # Boarding / Offboarding pattern:
                # - Morning peak → high boarding for "up", high offboarding for "down"
                # - Evening peak → opposite
                hour = observed_arrival.hour
                if PEAK_MORNING[0] <= hour <= PEAK_MORNING[1]:
                    if direction == "up":
                        boarding_in = max(0, int(random.gauss(15, 5)))
                        boarding_out = max(0, int(random.gauss(6, 3)))
                    else:
                        boarding_in = max(0, int(random.gauss(6, 3)))
                        boarding_out = max(0, int(random.gauss(14, 5)))
                elif PEAK_EVENING[0] <= hour <= PEAK_EVENING[1]:
                    if direction == "up":
                        boarding_in = max(0, int(random.gauss(6, 3)))
                        boarding_out = max(0, int(random.gauss(14, 5)))
                    else:
                        boarding_in = max(0, int(random.gauss(14, 5)))
                        boarding_out = max(0, int(random.gauss(6, 3)))
                else:
                    boarding_in = max(0, int(random.gauss(8, 3)))
                    boarding_out = max(0, int(random.gauss(6, 3)))

                observed.append({
                    "trip_id": trip_id,
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "observed_arrival": (observed_arrival + timedelta(minutes=delay)).strftime("%Y-%m-%d %H:%M:%S"),
                    "observed_departure": (observed_departure + timedelta(minutes=delay)).strftime("%Y-%m-%d %H:%M:%S"),
                    "boarding_in": boarding_in,
                    "boarding_out": boarding_out,
                    "delay_mins": delay,
                    "date": base_date.strftime("%Y-%m-%d"),
                    "assigned_bus_id": assigned_bus
                })

                start_time = observed_departure

    observed_df = pd.DataFrame(observed)
    observed_df.to_csv(f"observation_data_{base_date.strftime('%Y%m%d')}.csv", index=False)
    print(f"✅ Observation data generated for {base_date.date()} ({len(observed_df)} records)")
    return observed_df

# -------------------
# 5️⃣ Generate Observation Data for a Date Range
# -------------------
def generate_observation_for_range(start_date: str, end_date: str):
    """
    Generates synthetic observation data for a date range.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    stops_df = generate_stops(TOTAL_STOPS)
    routes_df = generate_routes(stops_df, NUM_ROUTES)
    buses_df = generate_buses(num_buses=25)

    all_obs = []

    current = start
    while current <= end:
        print(f"Generating for {current}...")
        obs_df = generate_observation_for_date(stops_df, routes_df, buses_df, base_date=current.strftime("%Y-%m-%d"))
        all_obs.append(obs_df)
        current += timedelta(days=1)

    full_obs = pd.concat(all_obs, ignore_index=True)
    full_obs.to_csv("observation_data_range.csv", index=False)
    print(f"✅ Combined dataset saved ({len(full_obs)} records total)")
    return full_obs

# -------------------
# MAIN EXAMPLE
# -------------------
if __name__ == "__main__":
    stops_df = generate_stops(TOTAL_STOPS)
    routes_df = generate_routes(stops_df, NUM_ROUTES)
    buses_df = generate_buses(25)

    # Single day example
    observed_df = generate_observation_for_date(stops_df, routes_df, buses_df, DATE)

    # Date range example
    # observed_df_range = generate_observation_for_range("2025-10-08", "2025-10-10")
