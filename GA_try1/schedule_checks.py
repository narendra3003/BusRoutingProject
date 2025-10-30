import pandas as pd
import matplotlib.pyplot as plt
from datetime import timedelta

# ======================================
# Helper: Ensure datetime conversions
# ======================================
def preprocess(df):
    df = df.copy()
    df['planned_start'] = pd.to_datetime(df['planned_start'])
    df['planned_end'] = pd.to_datetime(df['planned_end'])
    return df.sort_values(['bus_id', 'planned_start'])

# ======================================
# 1. Data Integrity Checks
# ======================================
def overlapping_trips_per_bus(df):
    df = preprocess(df)
    overlaps = []
    for bus, group in df.groupby('bus_id'):
        group = group.sort_values('planned_start')
        for i in range(1, len(group)):
            prev_end = group.iloc[i-1]['planned_end']
            curr_start = group.iloc[i]['planned_start']
            if curr_start < prev_end:
                overlaps.append((bus, group.iloc[i-1]['trip_id'], group.iloc[i]['trip_id']))
    return overlaps

def overlapping_trips_per_driver(df):
    df = preprocess(df)
    overlaps = []
    for driver, group in df.groupby('assigned_driver_id'):
        group = group.sort_values('planned_start')
        for i in range(1, len(group)):
            prev_end = group.iloc[i-1]['planned_end']
            curr_start = group.iloc[i]['planned_start']
            if curr_start < prev_end:
                overlaps.append((driver, group.iloc[i-1]['trip_id'], group.iloc[i]['trip_id']))
    return overlaps

def invalid_time_sequences(df):
    return df[df['planned_end'] <= df['planned_start']]

# ======================================
# 2. Bus Utilization Metrics
# ======================================
def bus_idle_time(df):
    df = preprocess(df)
    idle_summary = {}
    for bus, group in df.groupby('bus_id'):
        group = group.sort_values('planned_start')
        idle_times = []
        for i in range(1, len(group)):
            gap = group.iloc[i]['planned_start'] - group.iloc[i-1]['planned_end']
            if gap > timedelta(0):
                idle_times.append(gap)
        idle_summary[bus] = sum(idle_times, timedelta()).total_seconds() / 3600  # hours
    return pd.Series(idle_summary, name='idle_hours')

def bus_active_time(df):
    df = preprocess(df)
    active_summary = df.groupby('bus_id').apply(
        lambda g: (g['planned_end'] - g['planned_start']).sum().total_seconds() / 3600
    )
    active_summary.name = 'active_hours'
    return active_summary

def plot_bus_utilization(df):
    idle = bus_idle_time(df)
    active = bus_active_time(df)
    util_df = pd.concat([active, idle], axis=1).fillna(0)
    util_df['utilization_%'] = (util_df['active_hours'] / (util_df['active_hours'] + util_df['idle_hours'])) * 100
    util_df[['utilization_%']].plot(kind='bar', legend=False)
    plt.title('Bus Utilization (%)')
    plt.ylabel('Utilization %')
    plt.xlabel('Bus ID')
    plt.show()
    return util_df

# ======================================
# 3. Route Efficiency Metrics
# ======================================
def bus_frequency_per_route(df):
    freq = df.groupby('route_id')['trip_id'].count().rename('trip_count')
    freq.plot(kind='bar')
    plt.title('Bus Frequency per Route')
    plt.xlabel('Route ID')
    plt.ylabel('Trip Count')
    plt.show()
    return freq

def avg_trip_duration_per_route(df):
    df = preprocess(df)
    df['duration_min'] = (df['planned_end'] - df['planned_start']).dt.total_seconds() / 60
    avg_dur = df.groupby('route_id')['duration_min'].mean()
    avg_dur.plot(kind='bar')
    plt.title('Average Trip Duration per Route (min)')
    plt.xlabel('Route ID')
    plt.ylabel('Minutes')
    plt.show()
    return avg_dur

# ======================================
# 4. Driver Utilization
# ======================================
def driver_working_hours(df):
    df = preprocess(df)
    work = df.groupby('assigned_driver_id').apply(
        lambda g: (g['planned_end'] - g['planned_start']).sum().total_seconds() / 3600
    )
    work.name = 'working_hours'
    work.plot(kind='bar')
    plt.title('Driver Working Hours')
    plt.ylabel('Hours')
    plt.xlabel('Driver ID')
    plt.show()
    return work

# ======================================
# 5. Temporal & Operational Insights
# ======================================
def trips_per_day(df):
    df = preprocess(df)
    df['date'] = df['planned_start'].dt.date
    trips = df.groupby('date')['trip_id'].count()
    trips.plot()
    plt.title('Trips per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of Trips')
    plt.show()
    return trips

def route_trip_gaps(df):
    df = preprocess(df)
    gaps = []
    for route, group in df.groupby('route_id'):
        group = group.sort_values('planned_start')
        gap_times = group['planned_start'].diff().dropna()
        if not gap_times.empty:
            gaps.append((route, gap_times.mean().total_seconds() / 60))
    return pd.DataFrame(gaps, columns=['route_id', 'avg_gap_min']).set_index('route_id')

# ======================================
# 6. Composite Metrics
# ======================================
def fleet_utilization_index(df):
    active = bus_active_time(df)
    idle = bus_idle_time(df)
    total_possible = active.add(idle, fill_value=0)
    return active.sum() / total_possible.sum()

# ======================================
# Example: Run all analyses
# ======================================
def run_all_checks(df):
    results = {}
    results['bus_overlaps'] = overlapping_trips_per_bus(df)
    results['driver_overlaps'] = overlapping_trips_per_driver(df)
    results['invalid_times'] = invalid_time_sequences(df)
    results['bus_idle'] = bus_idle_time(df)
    results['bus_active'] = bus_active_time(df)
    results['utilization'] = plot_bus_utilization(df)
    results['freq_per_route'] = bus_frequency_per_route(df)
    results['avg_trip_duration'] = avg_trip_duration_per_route(df)
    results['driver_hours'] = driver_working_hours(df)
    results['trip_trend'] = trips_per_day(df)
    results['route_gaps'] = route_trip_gaps(df)
    results['fleet_utilization_index'] = fleet_utilization_index(df)
    return results


# Load your CSV
df = pd.read_csv("optimized_schedule.csv")

# Run all efficiency checks
results = run_all_checks(df)

# Example: access specific outputs
print("Fleet Utilization Index:", results['fleet_utilization_index'])
print("Bus Idle Times (hours):")
print(results['bus_idle'])

print("Overlapping Trips per Bus:")
print(results['bus_overlaps'])

print("Overlapping Trips per Driver:")
print(results['driver_overlaps'])

print("Invalid Time Sequences:")
print(results['invalid_times'])

print("Average Trip Duration per Route (min):")
print(results['avg_trip_duration'])

print("Bus Frequency per Route:")
print(results['freq_per_route'])

print("Driver Working Hours:")
print(results['driver_hours'])

print("Trips per Day:")
print(results['trip_trend'])

print("Route Trip Gaps (avg min):")
print(results['route_gaps'])

print("Bus Utilization Details:")
print(results['utilization'])

print("Bus Active Times (hours):")
print(results['bus_active'])
