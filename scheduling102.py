import pandas as pd
from datetime import datetime, timedelta
import numpy as np

BUFFER_MIN = 15

def compute_travel_time(stop_from, stop_to, stops_df):
    """Estimate travel time between two stops (minutes). Use Euclidean distance."""
    s1 = stops_df[stops_df['stop_id'] == stop_from].iloc[0]
    s2 = stops_df[stops_df['stop_id'] == stop_to].iloc[0]
    distance = np.sqrt((s1.lat - s2.lat)**2 + (s1.lon - s2.lon)**2)
    travel_time = distance / 0.001  # scaling factor to minutes
    return max(int(travel_time), 5)  # minimum 5 minutes

def estimate_trip_duration(route_stops, stops_df):
    """Compute total estimated duration of a route in minutes."""
    duration = 0
    for i in range(len(route_stops)-1):
        duration += compute_travel_time(route_stops[i], route_stops[i+1], stops_df)
    return duration

def generate_daily_bus_schedule(trips_df, buses_df, stops_df, routes_df):
    """
    Assign buses to trips for a day considering:
    - Buffer time
    - Travel time between trips if route changes
    """
    trips_df = trips_df.copy()
    trips_df['planned_start'] = pd.to_datetime(trips_df['observed_departure'])
    trips_df = trips_df.sort_values('planned_start')

    # Build route stop sequences dict
    route_stops_dict = routes_df.set_index('route_id')['stops'].to_dict()
    for k, v in route_stops_dict.items():
        if isinstance(v, str):
            # Convert from string representation of list to actual list
            route_stops_dict[k] = eval(v)

    # Initialize bus status
    bus_status = {}
    for _, b in buses_df.iterrows():
        bus_status[b['bus_id']] = {
            'next_available_time': trips_df['planned_start'].min(),
            'current_location': None,
            'assigned_trips': []
        }

    schedule_records = []

    for _, trip in trips_df.iterrows():
        trip_id = trip['trip_id']
        route_id = trip['route_id']
        start_stop = trip['stop_id']
        trip_start = trip['planned_start']

        # Estimate trip duration
        route_stops = route_stops_dict[route_id]
        trip_duration_min = estimate_trip_duration(route_stops, stops_df)
        trip_end = trip_start + timedelta(minutes=trip_duration_min)

        # Find feasible buses
        feasible_buses = []
        for bus_id, status in bus_status.items():
            available_time = status['next_available_time']
            location = status['current_location']
            travel_time = 0 if location is None else compute_travel_time(location, start_stop, stops_df)
            if available_time + timedelta(minutes=travel_time + BUFFER_MIN) <= trip_start:
                feasible_buses.append((bus_id, available_time))

        if feasible_buses:
            bus_id = min(feasible_buses, key=lambda x: x[1])[0]
        else:
            # Pick earliest available bus and delay start
            bus_id = min(bus_status, key=lambda x: bus_status[x]['next_available_time'])
            trip_start = bus_status[bus_id]['next_available_time'] + timedelta(minutes=BUFFER_MIN)
            trip_end = trip_start + timedelta(minutes=trip_duration_min)

        # Record schedule
        schedule_records.append({
            'bus_id': bus_id,
            'trip_id': trip_id,
            'route_id': route_id,
            'start_stop': start_stop,
            'planned_start': trip_start,
            'planned_end': trip_end
        })

        # Update bus status
        bus_status[bus_id]['next_available_time'] = trip_end + timedelta(minutes=BUFFER_MIN)
        bus_status[bus_id]['current_location'] = route_stops[-1]  # assume bus ends at last stop

    return pd.DataFrame(schedule_records)

def generate_demand_aware_schedule(trips_df, buses_df, stops_df, routes_df, observation_df):
    """
    Assign buses considering expected demand and capacity constraints.
    """
    trips_df = trips_df.copy()
    trips_df['planned_start'] = pd.to_datetime(trips_df['observed_departure'])
    trips_df = trips_df.sort_values('planned_start')

    # Route stop sequences
    route_stops_dict = routes_df.set_index('route_id')['stops'].to_dict()
    for k, v in route_stops_dict.items():
        if isinstance(v, str):
            route_stops_dict[k] = eval(v)

    # Compute expected load per trip
    trip_loads = observation_df.groupby("trip_id")["boarding_in"].sum().to_dict()

    # Initialize bus status
    bus_status = {}
    for _, b in buses_df.iterrows():
        bus_status[b['bus_id']] = {
            'next_available_time': trips_df['planned_start'].min(),
            'current_location': None,
            'assigned_trips': [],
            'capacity': b['max_capacity']
        }

    schedule_records = []

    for _, trip in trips_df.iterrows():
        trip_id = trip['trip_id']
        route_id = trip['route_id']
        start_stop = trip['stop_id']
        trip_start = trip['planned_start']
        expected_load = trip_loads.get(trip_id, 0)

        route_stops = route_stops_dict[route_id]
        trip_duration_min = estimate_trip_duration(route_stops, stops_df)
        trip_end = trip_start + timedelta(minutes=trip_duration_min)

        # Find feasible buses (time + capacity)
        feasible_buses = []
        for bus_id, status in bus_status.items():
            available_time = status['next_available_time']
            location = status['current_location']
            travel_time = 0 if location is None else compute_travel_time(location, start_stop, stops_df)
            if available_time + timedelta(minutes=travel_time + BUFFER_MIN) <= trip_start:
                if status['capacity'] >= expected_load:
                    feasible_buses.append((bus_id, available_time))

        if feasible_buses:
            bus_id = min(feasible_buses, key=lambda x: x[1])[0]
        else:
            # Pick earliest available bus anyway (may exceed capacity)
            bus_id = min(bus_status, key=lambda x: bus_status[x]['next_available_time'])

        schedule_records.append({
            'bus_id': bus_id,
            'trip_id': trip_id,
            'route_id': route_id,
            'start_stop': start_stop,
            'planned_start': trip_start,
            'planned_end': trip_end,
            'expected_load': expected_load,
            'bus_capacity': bus_status[bus_id]['capacity'],
            'over_capacity': max(0, expected_load - bus_status[bus_id]['capacity'])
        })

        # Update bus status
        bus_status[bus_id]['next_available_time'] = trip_end + timedelta(minutes=BUFFER_MIN)
        bus_status[bus_id]['current_location'] = route_stops[-1]

    return pd.DataFrame(schedule_records)

if __name__ == "__main__":
    stops_data = pd.read_csv("stops_data.csv")
    trips_data = pd.read_csv("trips_data.csv")
    buses_data = pd.read_csv("buses_data.csv")
    routes_data = pd.read_csv("routes_data.csv")
    observations_data = pd.read_csv("observation_data_20251008.csv")

    daily_schedule = generate_daily_bus_schedule(trips_data, buses_data, stops_data, routes_data)
    demand_aware_schedule = generate_demand_aware_schedule(trips_data, buses_data, stops_data, routes_data, observations_data)

    print("Daily Schedule:\n", daily_schedule)
    print("\nDemand-Aware Schedule:\n", demand_aware_schedule)
