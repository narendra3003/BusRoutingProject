import pandas as pd
import random
from datetime import datetime, timedelta

# -------------------
# CONFIGURATION
# -------------------
NUM_ROUTES = 8
TOTAL_STOPS = 60
DATE = "2025-10-08"
PEAK_MORNING = (7, 10)
PEAK_EVENING = (17, 22)

# -------------------
# 1️⃣ Generate Stops
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
    stops_df = pd.DataFrame(stops)
    stops_df.to_csv("stops_data.csv", index=False)
    print(f"✅ Generated {n_stops} stops.")
    return stops_df

# -------------------
# 2️⃣ Generate Routes + Time Plan
# -------------------
def generate_routes(stops_df, num_routes=8):
    routes = []
    route_timeplans = []

    for r in range(1, num_routes + 1):
        num_stops = random.randint(12, 20)
        route_stops = random.sample(list(stops_df["stop_id"]), num_stops)

        # create cumulative travel time sequence (in minutes)
        cumulative_time = 0
        for order, stop in enumerate(route_stops, start=1):
            travel_time = 0 if order == 1 else random.randint(4, 8)
            cumulative_time += travel_time
            route_timeplans.append({
                "route_id": f"R{r:03}_up",
                "stop_order": order,
                "stop_id": stop,
                "time_from_start_min": cumulative_time
            })

        # down direction (reverse)
        reversed_stops = list(reversed(route_stops))
        cumulative_time = 0
        for order, stop in enumerate(reversed_stops, start=1):
            travel_time = 0 if order == 1 else random.randint(4, 8)
            cumulative_time += travel_time
            route_timeplans.append({
                "route_id": f"R{r:03}_down",
                "stop_order": order,
                "stop_id": stop,
                "time_from_start_min": cumulative_time
            })

        routes.append({"route_id": f"R{r:03}_up", "stops": route_stops})
        routes.append({"route_id": f"R{r:03}_down", "stops": list(reversed(route_stops))})

    routes_df = pd.DataFrame(routes)
    routes_df.to_csv("routes_data.csv", index=False)
    route_timeplan_df = pd.DataFrame(route_timeplans)
    route_timeplan_df.to_csv("routes_timeplan.csv", index=False)

    print(f"✅ Generated {num_routes * 2} routes + time plans.")
    return routes_df, route_timeplan_df

# -------------------
# 3️⃣ Generate Buses
# -------------------
def generate_buses(num_buses=25):
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
# 4️⃣ Generate Observation Using Route Time Plan
# -------------------
def generate_observation_for_date(stops_df, routes_df, buses_df, route_timeplan_df, base_date="2025-10-08"):
    observed = []
    base_date = datetime.strptime(base_date, "%Y-%m-%d")

    for _, route in routes_df.iterrows():
        route_id = route["route_id"]
        direction = "up" if "up" in route_id else "down"

        # lookup route’s time plan
        timeplan = route_timeplan_df[route_timeplan_df["route_id"] == route_id].sort_values("stop_order")
        route_stops = timeplan["stop_id"].tolist()
        cumulative_times = timeplan["time_from_start_min"].tolist()

        # number of trips per day (based on length)
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

        # generate each trip
        for t_idx, trip_start in enumerate(trip_times, start=1):
            trip_id = f"{route_id}_T{t_idx:03}"
            assigned_bus = random.choice(buses_df["bus_id"].tolist())

            for i, stop_id in enumerate(route_stops):
                # get planned difference between stops using time plan
                if i == 0:
                    time_from_start = 0
                else:
                    # difference from previous stop
                    time_from_start = cumulative_times[i] - cumulative_times[i-1]

                # apply variation ±15–25% to simulate conditions
                adjusted_travel = time_from_start * random.uniform(0.85, 1.25)
                if i == 0:
                    observed_arrival = trip_start
                else:
                    observed_arrival = observed_departure + timedelta(minutes=adjusted_travel)

                dwell = random.uniform(1, 3)  # dwell time
                observed_departure = observed_arrival + timedelta(minutes=dwell)

                delay = random.randint(-2, 8)

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

    observed_df = pd.DataFrame(observed)
    observed_df.to_csv(f"observation_data_{base_date.strftime('%Y%m%d')}.csv", index=False)
    print(f"✅ Observation (using route time plan) generated for {base_date.date()} ({len(observed_df)} rows)")
    return observed_df

# -------------------
# 5️⃣ Trip Summary
# -------------------
def generate_trip_summary(observed_df):
    trip_summary = (
        observed_df.groupby(["trip_id", "route_id", "assigned_bus_id"])
        .agg(start_time=("observed_arrival", "min"),
             end_time=("observed_departure", "max"))
        .reset_index()
    )
    trip_summary.to_csv("trip_summary.csv", index=False)
    print(f"✅ Trip summary created ({len(trip_summary)} trips)")
    return trip_summary

# -------------------
# 6️⃣ Driver Data + Assignments
# -------------------
def generate_driver_data(num_drivers=30):
    drivers = []
    for i in range(1, num_drivers + 1):
        drivers.append({
            "driver_id": f"D{i:03}",
            "driver_name": f"Driver_{i}",
            "license_number": f"LIC{random.randint(10000,99999)}",
            "experience_years": random.randint(1, 15)
        })
    df = pd.DataFrame(drivers)
    df.to_csv("drivers_data.csv", index=False)
    print(f"✅ Generated {num_drivers} drivers.")
    return df

def generate_driver_assignments(drivers_df, buses_df, start_date="2025-10-08", num_days=3):
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    assignments = []

    for day_offset in range(num_days):
        day = start_date + timedelta(days=day_offset)
        for bus_id in buses_df["bus_id"]:
            driver = random.choice(drivers_df["driver_id"])
            shift_start = day.replace(hour=5, minute=0)
            shift_end = day.replace(hour=23, minute=0)
            assignments.append({
                "date": day.strftime("%Y-%m-%d"),
                "bus_id": bus_id,
                "driver_id": driver,
                "shift_start": shift_start.strftime("%Y-%m-%d %H:%M:%S"),
                "shift_end": shift_end.strftime("%Y-%m-%d %H:%M:%S")
            })

    df = pd.DataFrame(assignments)
    df.to_csv("driver_assignments.csv", index=False)
    print(f"✅ Driver assignments generated ({len(df)} rows for {num_days} days)")
    return df

# -------------------
# MAIN
# -------------------
if __name__ == "__main__":
    stops_df = generate_stops(TOTAL_STOPS)
    routes_df, route_timeplan_df = generate_routes(stops_df, NUM_ROUTES)
    buses_df = generate_buses(25)

    observed_df = generate_observation_for_date(stops_df, routes_df, buses_df, route_timeplan_df, DATE)
    trip_summary_df = generate_trip_summary(observed_df)

    drivers_df = generate_driver_data(30)
    driver_assignments_df = generate_driver_assignments(drivers_df, buses_df, start_date=DATE, num_days=3)
