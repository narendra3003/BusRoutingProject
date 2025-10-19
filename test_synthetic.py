"""
Passenger Flow & Density Analysis
---------------------------------
Focus: passenger distribution by time, stop, and route
"""

import pandas as pd
import matplotlib.pyplot as plt

def passenger_flow_over_time(df):
    """Plot total boardings per hour."""
    df["hour"] = pd.to_datetime(df["observed_arrival"]).dt.hour
    hourly = df.groupby("hour")["boarding_in"].sum()
    hourly.plot(kind="line", title="Total Passenger Boardings per Hour", xlabel="Hour", ylabel="Passengers")
    plt.tight_layout()
    plt.show()

def passenger_density_per_stop(df):
    """Show net passenger flow (boarding_in - boarding_out) per stop."""
    stop_density = df.groupby("stop_id")[["boarding_in", "boarding_out"]].sum()
    stop_density["net_flow"] = stop_density["boarding_in"] - stop_density["boarding_out"]
    stop_density["net_flow"].sort_values(ascending=False).plot(kind="bar", title="Passenger Density per Stop")
    plt.tight_layout()
    plt.show()

def passenger_heatmap(df):
    """Route vs Hour heatmap of boardings."""
    import seaborn as sns
    df["hour"] = pd.to_datetime(df["observed_arrival"]).dt.hour
    pivot = df.pivot_table(index="route_id", columns="hour", values="boarding_in", aggfunc="sum", fill_value=0)
    plt.figure(figsize=(10,6))
    sns.heatmap(pivot, cmap="YlGnBu")
    plt.title("Passenger Flow Heatmap (Route vs Hour)")
    plt.tight_layout()
    plt.show()


"""
Bus Usage & Load Factor Analysis
--------------------------------
Focus: occupancy, utilization, and overcrowding patterns
"""

import pandas as pd
import matplotlib.pyplot as plt

def avg_occupancy_by_route(df):
    """Estimate average occupancy per route (boarding - alighting cumulatively)."""
    route_occupancy = df.groupby("route_id")[["boarding_in", "boarding_out"]].sum()
    route_occupancy["net_passengers"] = route_occupancy["boarding_in"] - route_occupancy["boarding_out"]
    route_occupancy["net_passengers"].plot(kind="bar", title="Average Passenger Occupancy per Route")
    plt.tight_layout()
    plt.show()

def bus_utilization(df):
    """Total passengers per bus."""
    bus_usage = df.groupby("assigned_bus_id")[["boarding_in", "boarding_out"]].sum()
    bus_usage["total_passengers"] = bus_usage["boarding_in"] + bus_usage["boarding_out"]
    bus_usage["total_passengers"].sort_values(ascending=False).plot(kind="bar", title="Bus Utilization (Passengers per Bus)")
    plt.tight_layout()
    plt.show()

def overcrowding_index(df, buses_df):
    """Estimate trips exceeding bus capacity."""
    merged = df.merge(buses_df, left_on="assigned_bus_id", right_on="bus_id", how="left")
    merged["net_load"] = merged["boarding_in"] - merged["boarding_out"]
    over = merged.groupby("trip_id")["net_load"].sum() > merged["max_capacity"].mean()
    overcrowded = over.sum()
    print(f"Overcrowded Trips: {overcrowded} ({overcrowded/len(over)*100:.1f}% of trips)")

"""
Delay & Punctuality Analysis
----------------------------
Focus: route delay patterns and correlations
"""

import pandas as pd
import matplotlib.pyplot as plt

def avg_delay_per_route(df):
    """Bar plot of mean delay per route."""
    delay = df.groupby("route_id")["delay_mins"].mean()
    delay.plot(kind="bar", title="Average Delay per Route (minutes)")
    plt.tight_layout()
    plt.show()

def delay_vs_hour(df):
    """Line plot of average delay by hour of day."""
    df["hour"] = pd.to_datetime(df["observed_arrival"]).dt.hour
    delay_hour = df.groupby("hour")["delay_mins"].mean()
    delay_hour.plot(kind="line", title="Delay vs Time of Day", xlabel="Hour", ylabel="Avg Delay (min)")
    plt.tight_layout()
    plt.show()

def delay_vs_load(df):
    """Scatter plot between passenger load and delay."""
    df["load"] = df["boarding_in"] - df["boarding_out"]
    plt.scatter(df["load"], df["delay_mins"], alpha=0.3)
    plt.title("Delay vs Passenger Load")
    plt.xlabel("Passenger Load")
    plt.ylabel("Delay (minutes)")
    plt.tight_layout()
    plt.show()

"""
Passenger Waiting Time Estimation
---------------------------------
Focus: estimate and visualize passenger waiting times.
"""

import pandas as pd
import matplotlib.pyplot as plt

def estimate_waiting_time(df):
    """Estimate average waiting time per route based on trip spacing."""
    df["arrival_time"] = pd.to_datetime(df["observed_arrival"])
    route_wait = []
    for route, grp in df.groupby("route_id"):
        grp = grp.sort_values("arrival_time")
        intervals = grp["arrival_time"].diff().dt.total_seconds() / 60
        route_wait.append({
            "route_id": route,
            "avg_wait_time_min": intervals.mean()
        })
    wait_df = pd.DataFrame(route_wait)
    wait_df.plot(x="route_id", y="avg_wait_time_min", kind="bar", title="Average Passenger Waiting Time per Route")
    plt.ylabel("Minutes")
    plt.tight_layout()
    plt.show()
    return wait_df

def waiting_time_by_hour(df):
    """Approximate waiting time trend across the day."""
    df["arrival_time"] = pd.to_datetime(df["observed_arrival"])
    df["hour"] = df["arrival_time"].dt.hour
    wait = df.groupby("hour")["delay_mins"].mean() + 5  # baseline 5 min + delay
    wait.plot(kind="line", title="Estimated Waiting Time vs Time of Day", xlabel="Hour", ylabel="Minutes")
    plt.tight_layout()
    plt.show()

"""
Peak Hour Pattern Comparison
----------------------------
Focus: morning vs evening travel directions and passenger trends.
"""

import pandas as pd
import matplotlib.pyplot as plt

def morning_vs_evening_boardings(df):
    """Compare total boardings in morning vs evening."""
    df["hour"] = pd.to_datetime(df["observed_arrival"]).dt.hour
    morning = df[df["hour"].between(7, 10)].groupby("route_id")["boarding_in"].sum()
    evening = df[df["hour"].between(17, 22)].groupby("route_id")["boarding_in"].sum()
    comparison = pd.DataFrame({"Morning": morning, "Evening": evening}).fillna(0)
    comparison.plot(kind="bar", title="Morning vs Evening Boardings (per Route)")
    plt.tight_layout()
    plt.show()

def route_direction_flow(df):
    """Compare Up vs Down routes to highlight commute direction bias."""
    df["hour"] = pd.to_datetime(df["observed_arrival"]).dt.hour
    up = df[df["route_id"].str.contains("_up")].groupby("hour")["boarding_in"].sum()
    down = df[df["route_id"].str.contains("_down")].groupby("hour")["boarding_in"].sum()
    plt.plot(up.index, up.values, label="Up Routes")
    plt.plot(down.index, down.values, label="Down Routes")
    plt.title("Directional Passenger Flow (Up vs Down)")
    plt.xlabel("Hour")
    plt.ylabel("Passengers")
    plt.legend()
    plt.tight_layout()
    plt.show()

"""
Service Efficiency Metrics
--------------------------
Focus: operational KPIs for reliability and utilization
"""

import pandas as pd

def on_time_performance(df):
    """Calculate percentage of on-time trips (delay <= 3 min)."""
    on_time = (df["delay_mins"] <= 3).mean() * 100
    print(f"On-Time Performance: {on_time:.2f}%")

def load_factor(df, buses_df):
    """Calculate average load factor = total passengers / total capacity."""
    merged = df.merge(buses_df, left_on="assigned_bus_id", right_on="bus_id", how="left")
    merged["net_load"] = merged["boarding_in"] - merged["boarding_out"]
    avg_load = merged["net_load"].mean() / merged["max_capacity"].mean()
    print(f"Average Load Factor: {avg_load*100:.1f}%")

def overcrowding_index(df, buses_df):
    """Calculate % of trips exceeding capacity."""
    merged = df.merge(buses_df, left_on="assigned_bus_id", right_on="bus_id", how="left")
    trip_load = merged.groupby("trip_id")["boarding_in"].sum()
    over = trip_load > merged["max_capacity"].mean()
    rate = over.mean() * 100
    print(f"Overcrowded Trips: {rate:.2f}%")

def passenger_km_proxy(df):
    """Approximate passenger productivity (notional)."""
    df["load"] = df["boarding_in"] - df["boarding_out"]
    passenger_km = df["load"].sum() * 0.8  # assume ~0.8 km avg stop distance
    print(f"Estimated Passenger-Km Served: {passenger_km:,.0f}")



if __name__ == "__main__":
    # 1
    data_df = pd.read_csv("observation_data_20251008.csv")
    passenger_flow_over_time(data_df)
    passenger_density_per_stop(data_df)
    passenger_heatmap(data_df)

    # 2
    buses_df = pd.read_csv("buses_data.csv")
    avg_occupancy_by_route(data_df)
    bus_utilization(data_df)
    overcrowding_index(data_df, buses_df)
    # 3
    avg_delay_per_route(data_df)
    delay_vs_hour(data_df)
    delay_vs_load(data_df)
    # 4
    wait_df = estimate_waiting_time(data_df)
    waiting_time_by_hour(data_df)
    # 5
    morning_vs_evening_boardings(data_df)
    route_direction_flow(data_df)
    # 6
    on_time_performance(data_df)
    load_factor(data_df, buses_df)
    overcrowding_index(data_df, buses_df)
    passenger_km_proxy(data_df)
