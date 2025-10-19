"""
test_synthetic_dataset.py
=========================
Helper / playground script for exploring the synthetic dataset
generated using `synthetic_transit_generator.py`.

Run this interactively (e.g., Jupyter Notebook or standard Python).
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
from test1 import create_base_data, generate_day_data, generate_range_data

# ---------------------------------------------------------
# 1️⃣ Setup & generation
# ---------------------------------------------------------

OUTPUT_DIR = "synthetic_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\n🚀 Creating base data...")
base_data = create_base_data(
    stops_csv="stops.csv",
    routes_csv="routes.csv",
    observed_csv="observation_data.csv",
    output_dir=OUTPUT_DIR
)

# Generate data for a single date
DATE = "2025-10-08"
print(f"\n🚌 Generating synthetic data for {DATE}...")
planned_df, observed_df = generate_day_data(DATE, base_data, output_dir=OUTPUT_DIR)

print(f"\n✅ Generated data for {DATE}")
print(f"Planned trips: {planned_df['trip_id'].nunique()} | Observed records: {len(observed_df)}")

# ---------------------------------------------------------
# 2️⃣ Preview the data
# ---------------------------------------------------------
print("\n=== Sample planned schedule ===")
print(planned_df.head(10))
print("\n=== Sample observed schedule ===")
print(observed_df.head(10))

# ---------------------------------------------------------
# 3️⃣ Basic statistics
# ---------------------------------------------------------

def summarize_data(planned_df, observed_df):
    print("\n📊 Dataset Summary\n-------------------")
    print(f"Unique Routes: {planned_df['route_id'].nunique()}")
    print(f"Unique Trips: {planned_df['trip_id'].nunique()}")
    print(f"Unique Stops: {planned_df['stop_id'].nunique()}")
    print(f"Unique Buses: {planned_df['assigned_bus'].nunique()}")
    print(f"Total Records: Planned={len(planned_df)}, Observed={len(observed_df)}")

    # Average delay
    if 'delay_mins' in observed_df.columns:
        avg_delay = observed_df['delay_mins'].mean()
        max_delay = observed_df['delay_mins'].max()
        print(f"\n⏱️ Average Delay: {avg_delay:.2f} min, Max Delay: {max_delay:.2f} min")

    # Passenger stats
    if 'boarding_in' in observed_df.columns:
        total_boarded = observed_df['boarding_in'].sum()
        total_alight = observed_df['boarding_out'].sum()
        print(f"\n👥 Passenger Flow:")
        print(f"Total Boarded: {total_boarded:,}")
        print(f"Total Alighted: {total_alight:,}")

    # Capacity violations
    if 'over_capacity_flag' in observed_df.columns:
        over = observed_df['over_capacity_flag'].sum()
        print(f"\n⚠️ Over-capacity trips: {over}")

summarize_data(planned_df, observed_df)

# ---------------------------------------------------------
# 4️⃣ Visualizations
# ---------------------------------------------------------

def plot_stops_map(stops_df):
    """Simple scatter plot of stop locations."""
    plt.figure(figsize=(6,6))
    plt.scatter(stops_df['lon'], stops_df['lat'], s=30, alpha=0.7)
    for _, row in stops_df.iterrows():
        plt.text(row['lon'], row['lat'], row['stop_id'], fontsize=6, alpha=0.6)
    plt.title("🗺️ Stop Locations")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

def plot_delay_distribution(observed_df):
    """Histogram of delay (minutes)."""
    if 'delay_mins' not in observed_df.columns:
        print("No delay data found.")
        return
    plt.figure(figsize=(6,4))
    observed_df['delay_mins'].hist(bins=20)
    plt.title("⏰ Distribution of Arrival Delays")
    plt.xlabel("Delay (minutes)")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()

def plot_boarding_over_time(observed_df):
    """Plot boarding activity vs time."""
    if 'observed_arrival' not in observed_df.columns:
        print("No observed_arrival timestamps.")
        return
    df = observed_df.copy()
    df['observed_arrival'] = pd.to_datetime(df['observed_arrival'])
    df['hour'] = df['observed_arrival'].dt.hour
    grouped = df.groupby('hour')['boarding_in'].sum().reset_index()
    plt.figure(figsize=(6,4))
    plt.plot(grouped['hour'], grouped['boarding_in'], marker='o')
    plt.title("👥 Boardings per Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Total Boarding In")
    plt.grid(True)
    plt.show()

print("\n📍 Plotting stops map...")
plot_stops_map(base_data['stops_df'])

print("\n📈 Plotting delay distribution...")
plot_delay_distribution(observed_df)

print("\n👥 Plotting boarding trend over the day...")
plot_boarding_over_time(observed_df)

# ---------------------------------------------------------
# 5️⃣ Bus utilization analysis
# ---------------------------------------------------------

def bus_utilization_summary(planned_df, observed_df):
    """Show which buses were used and how intensively."""
    usage = planned_df.groupby('assigned_bus')['trip_id'].nunique().reset_index().rename(columns={'trip_id':'trips_handled'})
    usage = usage.sort_values('trips_handled', ascending=False)
    print("\n🚍 Bus Utilization (top 10):")
    print(usage.head(10))
    plt.figure(figsize=(8,4))
    plt.bar(usage['assigned_bus'], usage['trips_handled'])
    plt.title("🚍 Trips per Bus")
    plt.xlabel("Bus ID")
    plt.ylabel("Trips Handled")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()

bus_utilization_summary(planned_df, observed_df)

# ---------------------------------------------------------
# 6️⃣ Optional: generate range data
# ---------------------------------------------------------

DO_RANGE = False  # flip to True if you want multi-day dataset

if DO_RANGE:
    print("\n🗓️ Generating 5-day dataset...")
    p_all, o_all = generate_range_data("2025-10-08", "2025-10-12", base_data, output_dir=OUTPUT_DIR)
    print(f"Combined planned rows: {len(p_all)}, observed rows: {len(o_all)}")
    summarize_data(p_all, o_all)
