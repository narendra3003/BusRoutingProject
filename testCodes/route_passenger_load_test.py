import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1️⃣ Load observed dataset
# ---------------------------------------------------------
observed_df = pd.read_csv("observation_data.csv")
stops_df = pd.read_csv("stops.csv")
routes_df = pd.read_csv("routes.csv")

# ensure correct types
observed_df['observed_arrival'] = pd.to_datetime(observed_df['observed_arrival'])
observed_df = observed_df.sort_values(['trip_id', 'stop_id']).reset_index(drop=True)

# ---------------------------------------------------------
# 2️⃣ Compute passenger load per segment
# ---------------------------------------------------------
def compute_trip_loads(df, bus_capacity=80):
    trip_loads = []
    for trip_id, group in df.groupby('trip_id'):
        group = group.sort_values('stop_order')
        load = 0
        for _, row in group.iterrows():
            load += row['boarding_in'] - row['boarding_out']
            load = max(0, load)
            trip_loads.append({
                'trip_id': trip_id,
                'route_id': row['route_id'],
                'stop_id': row['stop_id'],
                'stop_order': row['stop_order'],
                'boarding_in': row['boarding_in'],
                'boarding_out': row['boarding_out'],
                'load': load,
                'over_capacity_flag': load > bus_capacity
            })
    return pd.DataFrame(trip_loads)

trip_load_df = compute_trip_loads(observed_df, bus_capacity=80)
trip_load_df.to_csv("trip_load_analysis.csv", index=False)
print(f"✅ Trip load analysis complete. {len(trip_load_df)} records saved as trip_load_analysis.csv")

# ---------------------------------------------------------
# 3️⃣ Summary statistics
# ---------------------------------------------------------
print("\n📊 Load Summary by Route:")
route_summary = trip_load_df.groupby('route_id')['load'].agg(['mean','max']).reset_index()
route_summary['over_capacity_segments'] = trip_load_df.groupby('route_id')['over_capacity_flag'].sum().values
print(route_summary)

# ---------------------------------------------------------
# 4️⃣ Visualize load profile for a single trip
# ---------------------------------------------------------
def plot_trip_load(trip_id):
    tdf = trip_load_df[trip_load_df['trip_id'] == trip_id].sort_values('stop_order')
    plt.figure(figsize=(8,4))
    plt.plot(tdf['stop_order'], tdf['load'], marker='o')
    plt.title(f"Passenger Load Profile – Trip {trip_id}")
    plt.xlabel("Stop Order")
    plt.ylabel("Passengers on Board")
    plt.grid(True)
    plt.show()

# pick a random trip
sample_trip = trip_load_df['trip_id'].sample(1).iloc[0]
print(f"\n🎨 Visualizing load profile for {sample_trip}...")
plot_trip_load(sample_trip)

# ---------------------------------------------------------
# 5️⃣ Identify overcrowding & underutilization
# ---------------------------------------------------------
def route_load_health(trip_load_df, cap=80):
    summary = trip_load_df.groupby('route_id')['load'].agg(['mean','max'])
    summary['overcrowded_%'] = (trip_load_df.groupby('route_id')['over_capacity_flag'].mean() * 100).values
    summary['underutilized_%'] = (trip_load_df.groupby('route_id')['load'].apply(lambda x: (x < cap*0.3).mean() * 100)).values
    return summary

load_health = route_load_health(trip_load_df)
print("\n🚦 Load Health per Route:")
print(load_health)

# ---------------------------------------------------------
# 6️⃣ Simple OD estimation
# ---------------------------------------------------------
def estimate_od_matrix(observed_df, decay_factor=0.3):
    """
    Estimates OD (origin-destination) probabilities per route
    assuming passengers alight with exponential decay probability
    at downstream stops.
    """
    od_records = []
    for route_id, route_data in observed_df.groupby('route_id'):
        stops = route_data.sort_values('stop_order')['stop_id'].unique()
        n = len(stops)
        for trip_id, tdf in route_data.groupby('trip_id'):
            tdf = tdf.sort_values('stop_order')
            for i, row in enumerate(tdf.itertuples(), start=0):
                board = getattr(row, 'boarding_in')
                if board == 0:
                    continue
                for j in range(i+1, n):
                    dest_stop = stops[j]
                    # exponential decay for probability of alighting
                    prob = np.exp(-decay_factor * (j - i))
                    od_records.append({
                        'route_id': route_id,
                        'trip_id': trip_id,
                        'origin_stop': row.stop_id,
                        'dest_stop': dest_stop,
                        'estimated_passengers': board * prob
                    })
    return pd.DataFrame(od_records)

od_df = estimate_od_matrix(observed_df)
od_summary = od_df.groupby(['origin_stop', 'dest_stop'])['estimated_passengers'].sum().reset_index()
od_summary = od_summary.sort_values('estimated_passengers', ascending=False).head(20)

print("\n🧭 Top OD flows:")
print(od_summary)

# ---------------------------------------------------------
# 7️⃣ Optional visualization: OD heatmap (aggregate)
# ---------------------------------------------------------
def plot_od_heatmap(od_df, top_n=15):
    pivot = od_df.groupby(['origin_stop', 'dest_stop'])['estimated_passengers'].sum().unstack(fill_value=0)
    top_stops = pivot.sum(axis=1).sort_values(ascending=False).head(top_n).index
    pivot = pivot.loc[top_stops, top_stops]
    plt.figure(figsize=(8,6))
    plt.imshow(pivot, cmap='viridis')
    plt.title("Estimated OD Flows (Top Stops)")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=90)
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.colorbar(label="Estimated Passengers")
    plt.tight_layout()
    plt.show()

plot_od_heatmap(od_df)
