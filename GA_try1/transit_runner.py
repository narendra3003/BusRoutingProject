# ============================================================
# run_optimizer.py
# Entry point to run NSGA-II Bus Scheduling Optimization
# ============================================================

from transit_optimizer import (
    load_and_prepare_data, nsga2, decode_solution
)

# ---- Provide your CSV paths here ----
stops_path = "stops_data.csv"
routes_path = "routes_data.csv"
routes_timeplan_path = "routes_timeplan.csv"
buses_path = "buses_data.csv"
drivers_path = "drivers_data.csv"
obs_path = "observation_data_20251008.csv"  # or merged observation file

# ---- Load and preprocess data ----
trips, buses, drivers, buses_df, drivers_df, route_demand = load_and_prepare_data(
    stops_path, routes_path, routes_timeplan_path,
    buses_path, drivers_path, obs_path
)

# ---- Run NSGA-II optimization ----
pareto_front = nsga2(trips, buses, drivers, buses_df, drivers_df, route_demand,
                     pop_size=30, ngen=50, cxpb=0.9, mutpb=0.2)

# ---- Choose best compromise solution (first in Pareto) ----
best_solution = pareto_front[0] 

# ---- Decode and export final schedule ----
final_df = decode_solution(best_solution, trips)
final_df.to_csv("optimized_schedule.csv", index=False)
print("✅ Optimized schedule saved → optimized_schedule.csv")
