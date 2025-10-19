import pandas as pd
from datetime import datetime, timedelta
import numpy as np

BUFFER_MIN = 15

def compute_travel_time(stop_from, stop_to, stops_df):
    s1 = stops_df[stops_df['stop_id'] == stop_from].iloc[0]
    s2 = stops_df[stops_df['stop_id'] == stop_to].iloc[0]
    distance = np.sqrt((s1.lat - s2.lat)**2 + (s1.lon - s2.lon)**2)
    travel_time = distance / 0.001
    return max(int(travel_time), 5)

def estimate_trip_duration(route_stops, stops_df):
    duration = 0
    for i in range(len(route_stops) - 1):
        duration += compute_travel_time(route_stops[i], route_stops[i + 1], stops_df)
    return duration

def generate_trips_from_observations(routes_df, observation_df):
    """Generate trips dataframe from observation timestamps and routes."""
    trips_list = []

    route_stops_dict = routes_df.set_index('route_id')['stops'].to_dict()
    for k, v in route_stops_dict.items():
        if isinstance(v, str):
            route_stops_dict[k] = eval(v)

    # Group observations by route_id and date
    grouped = observation_df.groupby(['route_id', 'date'])
    for (route_id, date), group in grouped:
        stops = route_stops_dict[route_id]
        # Find first observed departure at first stop
        first_stop = stops[0]
        first_stop_obs = group[group['stop_id'] == first_stop]
        if first_stop_obs.empty:
            continue
        first_departure = pd.to_datetime(first_stop_obs['observed_departure'].min())
        trips_list.append({
            'trip_id': f"{route_id}_{date}_{first_departure.strftime('%H%M')}",
            'route_id': route_id,
            'start_stop': first_stop,
            'planned_start': first_departure,
            'stops': stops
        })

    return pd.DataFrame(trips_list)

def generate_daily_bus_schedule_from_routes(trips_df, buses_df, stops_df):
    bus_status = {b['bus_id']: {'next_available_time': trips_df['planned_start'].min(),
                                'current_location': None} for _, b in buses_df.iterrows()}
    schedule_records = []

    for _, trip in trips_df.sort_values('planned_start').iterrows():
        trip_id = trip['trip_id']
        route_id = trip['route_id']
        start_stop = trip['start_stop']
        trip_start = trip['planned_start']
        route_stops = trip['stops']
        trip_duration = estimate_trip_duration(route_stops, stops_df)
        trip_end = trip_start + timedelta(minutes=trip_duration)

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
            bus_id = min(bus_status, key=lambda x: bus_status[x]['next_available_time'])
            trip_start = bus_status[bus_id]['next_available_time'] + timedelta(minutes=BUFFER_MIN)
            trip_end = trip_start + timedelta(minutes=trip_duration)

        schedule_records.append({
            'bus_id': bus_id,
            'trip_id': trip_id,
            'route_id': route_id,
            'planned_start': trip_start,
            'planned_end': trip_end
        })

        bus_status[bus_id]['next_available_time'] = trip_end + timedelta(minutes=BUFFER_MIN)
        bus_status[bus_id]['current_location'] = route_stops[-1]
    schedule_records=pd.DataFrame(schedule_records)
    schedule_records.to_csv("daily_bus_schedule.csv", index=False)
    return schedule_records

if __name__ == "__main__":
    stops_data = pd.read_csv("stops_data.csv")
    buses_data = pd.read_csv("buses_data.csv")
    routes_data = pd.read_csv("routes_data.csv")
    observations_data = pd.read_csv("observation_data_20251008.csv")

    trips_data = generate_trips_from_observations(routes_data, observations_data)
    daily_schedule = generate_daily_bus_schedule_from_routes(trips_data, buses_data, stops_data)
    

    print("Generated Trips:\n", trips_data)
    print("\nDaily Schedule:\n", daily_schedule)
