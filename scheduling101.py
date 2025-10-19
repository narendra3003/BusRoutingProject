import pandas as pd
from datetime import datetime, timedelta
import numpy as np

BUFFER_MIN = 15

def compute_travel_time(stop_from, stop_to, stops_df):
    """Estimate travel time between two stops (minutes). Use Euclidean distance for simplicity."""
    s1 = stops_df[stops_df['stop_id']==stop_from].iloc[0]
    s2 = stops_df[stops_df['stop_id']==stop_to].iloc[0]
    distance = np.sqrt((s1.lat - s2.lat)**2 + (s1.lon - s2.lon)**2)
    travel_time = distance / 0.001  # approx scaling factor to minutes
    return int(travel_time)+5  # minimum 5 min

def generate_daily_bus_schedule(trips_df, buses_df, stops_df):
    """
    Assigns buses to trips for a day considering:
    - Buffer time
    - Travel time between trips if route changes
    """
    trips_df = trips_df.copy()
    trips_df['planned_start'] = pd.to_datetime(trips_df['observed_departure'])
    trips_df['planned_end'] = pd.to_datetime(trips_df['observed_departure'])  # Using observed for schedule
    trips_df = trips_df.sort_values('planned_start')

    # Initialize bus status
    bus_status = {}
    for _, b in buses_df.iterrows():
        bus_status[b['bus_id']] = {
            'next_available_time': trips_df['planned_start'].min(),
            'current_location': None,  # assume depot
            'assigned_trips': []
        }

    schedule_records = []

    for _, trip in trips_df.iterrows():
        trip_id = trip['trip_id']
        route_id = trip['route_id']
        start_stop = trip['stop_id']
        trip_start = trip['planned_start']
        trip_end = trip['planned_end']

        # Find buses that can take this trip
        feasible_buses = []
        for bus_id, status in bus_status.items():
            available_time = status['next_available_time']
            location = status['current_location']
            # travel time if different location
            travel_time = 0 if location is None else compute_travel_time(location, start_stop, stops_df)
            if available_time + timedelta(minutes=travel_time+BUFFER_MIN) <= trip_start:
                feasible_buses.append((bus_id, available_time))

        if not feasible_buses:
            # No bus can reach in time, pick the earliest available bus and delay start
            bus_id, available_time = min(bus_status.items(), key=lambda x: x[1]['next_available_time'])[0], None
            bus_start_time = bus_status[bus_id]['next_available_time'] + timedelta(minutes=BUFFER_MIN)
            delay = (trip_start - bus_start_time).total_seconds()/60
            trip_start = bus_start_time
            trip_end = trip_start + (trip_end - trip_start)
        else:
            # Pick the bus available earliest
            bus_id = min(feasible_buses, key=lambda x: x[1])[0]

        # Assign trip to bus
        schedule_records.append({
            'bus_id': bus_id,
            'trip_id': trip_id,
            'route_id': route_id,
            'start_stop': start_stop,
            'planned_start': trip_start,
            'planned_end': trip_end,
            'next_action': 'reverse'  # simplification: assume reverse if same route exists
        })

        # Update bus status
        bus_status[bus_id]['next_available_time'] = trip_end + timedelta(minutes=BUFFER_MIN)
        bus_status[bus_id]['current_location'] = start_stop

    schedule_df = pd.DataFrame(schedule_records)
    return schedule_df

def generate_demand_aware_schedule(trips_df, buses_df, stops_df, observation_df):
    BUFFER_MIN = 15
    trips_df = trips_df.copy()
    trips_df['planned_start'] = pd.to_datetime(trips_df['observed_departure'])
    trips_df['planned_end'] = pd.to_datetime(trips_df['observed_departure'])
    trips_df = trips_df.sort_values('planned_start')

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
        trip_end = trip['planned_end']
        expected_load = trip_loads.get(trip_id, 0)

        # Filter feasible buses (available + sufficient capacity)
        feasible_buses = []
        for bus_id, status in bus_status.items():
            available_time = status['next_available_time']
            location = status['current_location']
            travel_time = 0 if location is None else compute_travel_time(location, start_stop, stops_df)
            if available_time + timedelta(minutes=travel_time+BUFFER_MIN) <= trip_start:
                if status['capacity'] >= expected_load:
                    feasible_buses.append((bus_id, available_time))

        if not feasible_buses:
            # pick the earliest available bus anyway (may exceed capacity)
            bus_id = min(bus_status, key=lambda x: bus_status[x]['next_available_time'])
        else:
            bus_id = min(feasible_buses, key=lambda x: x[1])[0]

        # Assign trip
        schedule_records.append({
            'bus_id': bus_id,
            'trip_id': trip_id,
            'route_id': route_id,
            'start_stop': start_stop,
            'planned_start': trip_start,
            'planned_end': trip_end,
            'expected_load': expected_load,
            'bus_capacity': bus_status[bus_id]['capacity'],
            'over_capacity': max(0, expected_load - bus_status[bus_id]['capacity']),
            'next_action': 'reverse'
        })

        # Update bus status
        bus_status[bus_id]['next_available_time'] = trip_end + timedelta(minutes=BUFFER_MIN)
        bus_status[bus_id]['current_location'] = start_stop

    return pd.DataFrame(schedule_records)

if __name__ == "__main__":
    stops_data = pd.read_csv("stops_data.csv")
    trips_data = pd.read_csv("trips_data.csv") 
    buses_data = pd.read_csv("buses_data.csv")
    observations_data = pd.read_csv("observation_data_20251008.csv")
    daily_schedule = generate_daily_bus_schedule(trips_data, buses_data, stops_data)
    demand_aware_schedule = generate_demand_aware_schedule(trips_data, buses_data, stops_data, observations_data)
    print(daily_schedule)
    print(demand_aware_schedule)