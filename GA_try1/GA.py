# ============================================================
# PHASE 1: Data Initialization and Preprocessing
# ============================================================
# Libraries
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ---------------------------
# 1. Load all CSVs
# ---------------------------
stops_df = pd.read_csv("stops_data.csv")
routes_df = pd.read_csv("routes_data.csv")
routes_timeplan_df = pd.read_csv("routes_timeplan.csv")
buses_df = pd.read_csv("buses_data.csv")
drivers_df = pd.read_csv("drivers_data.csv")

# You can change this to a merged file covering a date range
obs_df = pd.read_csv("observation_data_20251008.csv")

# Convert timestamps if not already datetime
for col in ["observed_arrival", "observed_departure"]:
    if col in obs_df.columns:
        obs_df[col] = pd.to_datetime(obs_df[col], errors='coerce')

obs_df["date"] = pd.to_datetime(obs_df["date"], errors='coerce')

# ============================================================
# STEP 1 — Compute Route Duration (minutes)
# ============================================================

# each route_id has many stop orders with cumulative time_from_start_min
route_duration = (
    routes_timeplan_df
    .groupby("route_id")["time_from_start_min"]
    .max()
    .reset_index()
    .rename(columns={"time_from_start_min": "route_duration_min"})
)

# Merge into route info
routes_df = routes_df.merge(route_duration, on="route_id", how="left")

# ============================================================
# STEP 2 — Derive Planned Start / End for Each Trip
# ============================================================

# Trips come from observation data (one row per stop observation)
# For planned start/end, we approximate from earliest & latest observed times
trip_times = (
    obs_df.groupby(["trip_id", "route_id"])
    .agg(
        planned_start=("observed_departure", "min"),
        planned_end=("observed_arrival", "max"),
    )
    .reset_index()
)

# Fallback if planned times missing: use date + route_duration
trip_times["planned_start"] = trip_times["planned_start"].fillna(
    trip_times["route_id"].map(lambda r: obs_df.loc[obs_df["route_id"] == r, "date"].min())
)
trip_times["planned_end"] = trip_times["planned_end"].fillna(
    trip_times["planned_start"] + pd.to_timedelta(
        trip_times["route_id"].map(routes_df.set_index("route_id")["route_duration_min"]),
        unit="m"
    )
)

# Merge bus and driver assignments if given historically
trip_times = trip_times.merge(
    obs_df[["trip_id", "assigned_bus_id"]].drop_duplicates(),
    on="trip_id", how="left"
)

# ============================================================
# STEP 3 — Build Route Segment Info
# ============================================================

# For each route, ordered stops and segment travel times
routes_timeplan_df = routes_timeplan_df.sort_values(["route_id", "stop_order"])
routes_timeplan_df["next_time"] = routes_timeplan_df.groupby("route_id")["time_from_start_min"].shift(-1)
routes_timeplan_df["segment_time_min"] = routes_timeplan_df["next_time"] - routes_timeplan_df["time_from_start_min"]

segments_df = (
    routes_timeplan_df[["route_id", "stop_order", "stop_id", "segment_time_min"]]
    .dropna(subset=["segment_time_min"])
)

# ============================================================
# STEP 4 — Estimate Occupancy Along Trip (from observations)
# ============================================================

# Compute cumulative occupancy along each trip
def compute_trip_occupancy(df):
    df = df.sort_values("observed_arrival")
    df["occupancy"] = (df["boarding_in"] - df["boarding_out"]).cumsum()
    return df

obs_df = obs_df.groupby(["trip_id"], group_keys=False).apply(compute_trip_occupancy)

# For each trip, store max occupancy and average occupancy
trip_occupancy_stats = (
    obs_df.groupby("trip_id")
    .agg(
        max_occupancy=("occupancy", "max"),
        avg_occupancy=("occupancy", "mean"),
        total_boarding=("boarding_in", "sum"),
        total_alighting=("boarding_out", "sum")
    )
    .reset_index()
)

trip_data = trip_times.merge(trip_occupancy_stats, on="trip_id", how="left")

# ============================================================
# STEP 5 — Estimate Demand per Route-Time Bucket
# ============================================================

# Define time buckets (e.g., 15 min)
bucket_minutes = 15

# Compute start time in minutes since midnight
def get_bucket(dt):
    if pd.isna(dt):
        return np.nan
    return (dt.hour * 60 + dt.minute) // bucket_minutes

obs_df["bucket"] = obs_df["observed_arrival"].apply(get_bucket)

# total boardings per route per bucket
demand_buckets = (
    obs_df.groupby(["route_id", "bucket"])
    .agg(demand=("boarding_in", "sum"))
    .reset_index()
)

# Ensure buckets exist even with 0 demand
all_buckets = pd.DataFrame({"bucket": np.arange(0, (24*60)//bucket_minutes)})
routes_list = routes_df["route_id"].unique()
full_idx = pd.MultiIndex.from_product([routes_list, all_buckets["bucket"]], names=["route_id", "bucket"])
demand_buckets = (
    demand_buckets.set_index(["route_id", "bucket"])
    .reindex(full_idx, fill_value=0)
    .reset_index()
)

# ============================================================
# STEP 6 — Store Key Structures for Optimization
# ============================================================

# Trips dictionary
trips = {
    row.trip_id: {
        "route_id": row.route_id,
        "planned_start": row.planned_start,
        "planned_end": row.planned_end,
        "avg_occupancy": row.avg_occupancy,
        "max_occupancy": row.max_occupancy,
        "total_boarding": row.total_boarding,
        "total_alighting": row.total_alighting,
    }
    for _, row in trip_data.iterrows()
}

# Bus and driver pools
buses = buses_df.to_dict("records")
drivers = drivers_df.to_dict("records")

# Demand structure for F2 / F3 calculations
route_demand = {
    (r, int(b)): d for r, b, d in demand_buckets[["route_id", "bucket", "demand"]].to_numpy()
}

print(f"Loaded {len(trips)} trips, {len(buses)} buses, {len(drivers)} drivers.")
print(f"Example trip: {list(trips.items())[0]}")
print(f"Demand buckets example:\n{demand_buckets.head()}")

# ============================================================
# End of Phase 1 (Data Ready for NSGA-II definitions)
# ============================================================

# ============================================================
# PHASE 2 — Objective Definitions (Fitness Functions)
# ============================================================
import random

# ---------------------------
# 0. Chromosome Definition
# ---------------------------
# Each individual (solution) is a mapping:
# trip_id → (bus_id, driver_id)

# Example representation:
# individual = {trip_id: (bus_id, driver_id)}

def random_individual(trips, buses, drivers):
    """Generate a random valid assignment of buses and drivers to trips."""
    bus_ids = [b["bus_id"] for b in buses]
    driver_ids = [d["driver_id"] for d in drivers]
    return {
        t: (
            random.choice(bus_ids),
            random.choice(driver_ids)
        )
        for t in trips.keys()
    }

# ============================================================
# Objective 1 — Minimize Crowding (F1)  (robust to wrapper or genome)
# ============================================================
def objective_crowding(individual, trips, buses_df):
    """Penalize overcrowding based on occupancy vs bus capacity.
    Accepts either:
      - individual = {'genome': {trip_id: (bus,drv)}, ...}
      - individual = {trip_id: (bus,drv), ...}
    """
    genome = individual.get('genome', individual)
    bus_capacity = buses_df.set_index("bus_id")["max_capacity"].to_dict()
    penalty = 0.0

    for trip_id, assignment in genome.items():
        # defensive unpacking (in case assignment malformed)
        try:
            bus_id, _ = assignment
        except Exception:
            continue
        trip = trips.get(trip_id)
        if trip is None:
            continue
        max_occ = trip.get("max_occupancy")
        if pd.isna(max_occ) or max_occ is None:
            continue
        cap = bus_capacity.get(bus_id, 50)
        # avoid division by zero
        if cap <= 0:
            cap = 50
        load_factor = max_occ / cap
        if load_factor > 1:
            penalty += (load_factor - 1) ** 2  # nonlinear penalty
    return float(penalty)


# ============================================================
# Objective 2 — Passenger Load vs Bus Frequency (F2)
# ============================================================
def objective_demand_alignment(individual, trips, route_demand, bucket_minutes=15):
    """Penalize mismatch between bus frequency and route demand.
    Robust to wrapper or genome input.
    """
    genome = individual.get('genome', individual)
    route_bucket_trips = {}

    for trip_id, assignment in genome.items():
        try:
            bus_id, _ = assignment
        except Exception:
            continue
        trip = trips.get(trip_id)
        if trip is None:
            continue
        r = trip.get("route_id")
        start = trip.get("planned_start")
        if pd.isna(start) or start is None:
            continue
        # ensure start is datetime-like
        if isinstance(start, (str, int, float)):
            try:
                start = pd.to_datetime(start)
            except Exception:
                continue
        bucket = int((start.hour * 60 + start.minute) // bucket_minutes)
        route_bucket_trips.setdefault((r, bucket), 0)
        route_bucket_trips[(r, bucket)] += 1

    penalty = 0.0
    for (r, b), trips_in_bucket in route_bucket_trips.items():
        demand = route_demand.get((r, b), 0)
        # expected trips heuristic (tunable): assume each trip supplies ~50 seats
        expected_trips = max(1, int(demand // 50))
        diff = abs(trips_in_bucket - expected_trips)
        penalty += diff
    return float(penalty)


# ============================================================
# Objective 3 — Minimize Passenger Wait Time (F3)
# ============================================================
def objective_wait_time(individual, trips):
    """Approximation: minimize gap between successive trips on same route.
    Robust to wrapper or genome input.
    Returns average gap sum across routes (smaller better).
    """
    genome = individual.get('genome', individual)
    route_trips = {}

    for t, assignment in genome.items():
        try:
            _, _ = assignment
        except Exception:
            continue
        tr = trips.get(t)
        if tr is None:
            continue
        r = tr.get("route_id")
        start = tr.get("planned_start")
        if pd.isna(start) or start is None:
            continue
        # ensure datetime
        if isinstance(start, (str, int, float)):
            try:
                start = pd.to_datetime(start)
            except Exception:
                continue
        route_trips.setdefault(r, []).append(start)

    total_wait = 0.0
    route_count = 0
    for r, starts in route_trips.items():
        starts = sorted([s for s in starts if not pd.isna(s)])
        if len(starts) <= 1:
            continue
        gaps = [(starts[i+1] - starts[i]).total_seconds() / 60.0 for i in range(len(starts)-1)]
        if len(gaps) > 0:
            total_wait += float(np.mean(gaps))
            route_count += 1

    # if no multi-trip routes, return 0
    if route_count == 0:
        return 0.0
    # return average of route mean-gaps (minutes)
    return float(total_wait / route_count)


# ============================================================
# Objective 4 — Minimize Bus Idle Time (F4)
# ============================================================
def objective_idle_time(individual, trips):
    """Penalize large idle gaps between consecutive trips of the same bus.
    Robust to wrapper or genome input.
    """
    genome = individual.get('genome', individual)
    bus_trips = {}

    for t, assignment in genome.items():
        try:
            bus, drv = assignment
        except Exception:
            continue
        tr = trips.get(t)
        if tr is None:
            continue
        bus_trips.setdefault(bus, []).append(tr)

    total_idle = 0.0
    for bus, tlist in bus_trips.items():
        tlist = sorted([x for x in tlist if not pd.isna(x.get("planned_start")) and not pd.isna(x.get("planned_end"))],
                       key=lambda x: x["planned_start"])
        for i in range(len(tlist)-1):
            s1 = tlist[i]["planned_end"]
            s2 = tlist[i+1]["planned_start"]
            # ensure datetimes
            if isinstance(s1, (str, int, float)):
                try:
                    s1 = pd.to_datetime(s1)
                except Exception:
                    continue
            if isinstance(s2, (str, int, float)):
                try:
                    s2 = pd.to_datetime(s2)
                except Exception:
                    continue
            gap = (s2 - s1).total_seconds() / 60.0
            if gap > 0:
                total_idle += gap
    return float(total_idle)


# ============================================================
# Objective 5 — Fairness Among Driver Allocations (F5)
# ============================================================
def objective_driver_fairness(individual, trips, drivers_df):
    """Fairness = minimize variance in total assigned driving durations.
    Robust to wrapper or genome input.
    """
    genome = individual.get('genome', individual)
    driver_work = {}

    for t, assignment in genome.items():
        try:
            _, drv = assignment
        except Exception:
            continue
        tr = trips.get(t)
        if tr is None:
            continue
        s = tr.get("planned_start")
        e = tr.get("planned_end")
        # ensure datetimes
        if s is None or e is None or pd.isna(s) or pd.isna(e):
            continue
        if isinstance(s, (str, int, float)):
            try:
                s = pd.to_datetime(s)
            except Exception:
                continue
        if isinstance(e, (str, int, float)):
            try:
                e = pd.to_datetime(e)
            except Exception:
                continue
        duration = (e - s).total_seconds() / 60.0
        driver_work.setdefault(drv, 0.0)
        driver_work[drv] += duration

    if len(driver_work) == 0:
        return 0.0
    workloads = np.array(list(driver_work.values()), dtype=float)
    fairness_score = float(np.var(workloads))
    return fairness_score


# ============================================================
# PHASE 3 — Constraints and Feasibility
# ============================================================

def constraint_check(individual, trips, buses_df, drivers_df):
    """Check hard constraints for an individual's genome."""
    # 🔧 Ensure genome is consistent
    genome = individual.get('genome', individual)
    clean_genome = {}
    for t, val in genome.items():
        if isinstance(val, tuple) and len(val) == 2:
            clean_genome[t] = val
        else:
            # repair invalid entries
            clean_genome[t] = (
                random.choice(buses_df["bus_id"]),
                random.choice(drivers_df["driver_id"])
            )

    # Replace genome reference
    genome = clean_genome

    # ---- Now do the actual constraint logic safely ----
    feasible = True
    violations = 0
    used = set()

    for t, (bus, drv) in genome.items():
        # Example constraint checks (yours may differ)
        if bus not in list(buses_df["bus_id"]):
            feasible = False
            violations += 1
        if drv not in list(drivers_df["driver_id"]):
            feasible = False
            violations += 1
        if (bus, t) in used:  # same bus reused incorrectly
            feasible = False
            violations += 1
        used.add((bus, t))

    return feasible, violations


# ============================================================
# PHASE 4 — Analysis and Visualization
# ============================================================
import matplotlib.pyplot as plt

def visualize_route_load(trips, buses_df):
    """Visualize route load factors vs capacities."""
    load_data = []
    for t, info in trips.items():
        if pd.isna(info["max_occupancy"]):
            continue
        cap = buses_df["max_capacity"].mean()
        lf = info["max_occupancy"] / cap
        load_data.append(lf)
    plt.figure(figsize=(8,4))
    plt.hist(load_data, bins=20, edgecolor="k")
    plt.title("Bus Load Factor Distribution")
    plt.xlabel("Load Factor (Occupancy / Capacity)")
    plt.ylabel("Count")
    plt.show()


def visualize_route_demand(route_demand):
    """Show average demand pattern per route over day."""
    df = pd.DataFrame(list(route_demand.items()), columns=["route_bucket", "demand"])
    df[["route_id", "bucket"]] = pd.DataFrame(df["route_bucket"].tolist(), index=df.index)
    avg = df.groupby("bucket")["demand"].mean()
    plt.plot(avg.index * 15 / 60, avg.values)
    plt.title("Average Route Demand by Time of Day")
    plt.xlabel("Hour of Day")
    plt.ylabel("Avg Passenger Demand")
    plt.show()


# ============================================================
# EXAMPLE RUN
# ============================================================
individual = random_individual(trips, buses, drivers)
feasible, viol = constraint_check(individual, trips, buses_df, drivers_df)

F1 = objective_crowding(individual, trips, buses_df)
F2 = objective_demand_alignment(individual, trips, route_demand)
F3 = objective_wait_time(individual, trips)
F4 = objective_idle_time(individual, trips)
F5 = objective_driver_fairness(individual, trips, drivers_df)

print(f"Feasible: {feasible}, Violations: {viol}")
print(f"Objectives → F1:{F1:.2f}, F2:{F2:.2f}, F3:{F3:.2f}, F4:{F4:.2f}, F5:{F5:.2f}")

visualize_route_load(trips, buses_df)
visualize_route_demand(route_demand)


# ============================================================
# PHASE 5 — Population Initialization
# ============================================================

POP_SIZE = 50          # population size
NGEN = 100             # number of generations
CXPB = 0.9             # crossover probability
MUTPB = 0.2            # mutation probability

def initialize_population(pop_size, trips, buses, drivers):
    return [random_individual(trips, buses, drivers) for _ in range(pop_size)]


# ============================================================
# PHASE 6 — Evaluation (Fitness Calculation)
# ============================================================

def evaluate(individual):
    """Evaluate fitness safely."""
    genome = individual.get('genome', individual)
    genome = repair_genome(genome, trips, buses_df, drivers_df)

    F1 = objective_crowding(genome, trips, buses_df)
    F2 = objective_demand_alignment(genome, trips, route_demand)
    F3 = objective_wait_time(genome, trips)
    F4 = objective_idle_time(genome, trips)
    F5 = objective_driver_fairness(genome, trips, drivers_df)

    feasible, viol = constraint_check(genome, trips, buses_df, drivers_df)
    penalty = viol * 10_000 if not feasible else 0

    return [F1 + penalty, F2 + penalty, F3 + penalty, F4 + penalty, F5 + penalty]

def repair_genome(genome, trips, buses_df, drivers_df):
    """Ensure genome is a valid trip→(bus,driver) dict."""
    if not isinstance(genome, dict):
        genome = {}

    valid_buses = buses_df["bus_id"].tolist()
    valid_drivers = drivers_df["driver_id"].tolist()

    repaired = {}
    for t in trips.keys():
        v = genome.get(t)
        if isinstance(v, tuple) and len(v) == 2:
            bus, drv = v
            if bus not in valid_buses:
                bus = random.choice(valid_buses)
            if drv not in valid_drivers:
                drv = random.choice(valid_drivers)
            repaired[t] = (bus, drv)
        else:
            repaired[t] = (random.choice(valid_buses), random.choice(valid_drivers))
    return repaired

# ============================================================
# PHASE 7 — Non-Dominated Sorting (Pareto Ranking)
# ============================================================

def dominates(ind1, ind2):
    """Return True if ind1 dominates ind2 (all objectives <= and at least one <)."""
    return all(a <= b for a, b in zip(ind1['fitness'], ind2['fitness'])) and any(a < b for a, b in zip(ind1['fitness'], ind2['fitness']))

def non_dominated_sort(pop):
    """Return list of fronts (each front = list of individuals)."""
    S = [[] for _ in range(len(pop))]
    n = [0] * len(pop)
    rank = [0] * len(pop)
    fronts = [[]]

    for p_idx, p in enumerate(pop):
        for q_idx, q in enumerate(pop):
            if p_idx == q_idx:
                continue
            if dominates(p, q):
                S[p_idx].append(q_idx)
            elif dominates(q, p):
                n[p_idx] += 1

        if n[p_idx] == 0:
            rank[p_idx] = 0
            fronts[0].append(p_idx)

    i = 0
    while fronts[i]:
        Q = []
        for p_idx in fronts[i]:
            for q_idx in S[p_idx]:
                n[q_idx] -= 1
                if n[q_idx] == 0:
                    rank[q_idx] = i + 1
                    Q.append(q_idx)
        i += 1
        fronts.append(Q)

    fronts.pop()  # remove empty
    # return actual individuals instead of indices
    ranked_fronts = [[pop[idx] for idx in front] for front in fronts]
    return ranked_fronts



# ============================================================
# PHASE 8 — Crowding Distance Assignment
# ============================================================

def crowding_distance(front):
    """Assign crowding distance for a front (list of individuals)."""
    if not front:
        return
    num_obj = len(front[0]['fitness'])
    for ind in front:
        ind['distance'] = 0.0
    for m in range(num_obj):
        front.sort(key=lambda x: x['fitness'][m])
        front[0]['distance'] = front[-1]['distance'] = float('inf')
        fmin, fmax = front[0]['fitness'][m], front[-1]['fitness'][m]
        if fmax == fmin:
            continue
        for i in range(1, len(front)-1):
            next_f = front[i+1]['fitness'][m]
            prev_f = front[i-1]['fitness'][m]
            front[i]['distance'] += (next_f - prev_f) / (fmax - fmin)


# ============================================================
# PHASE 9 — Selection (Binary Tournament)
# ============================================================

def tournament_select(pop):
    """Select one individual based on rank and crowding distance."""
    a, b = random.sample(pop, 2)
    if a['rank'] < b['rank']:
        return a
    elif b['rank'] < a['rank']:
        return b
    else:
        return a if a['distance'] > b['distance'] else b


# ============================================================
# PHASE 10 — Crossover (Uniform/Trip Swap)
# ============================================================

def crossover(p1, p2):
    """Uniform crossover returning valid genomes."""
    g1 = p1.get('genome', p1)
    g2 = p2.get('genome', p2)

    g1 = repair_genome(g1, trips, buses_df, drivers_df)
    g2 = repair_genome(g2, trips, buses_df, drivers_df)

    child1, child2 = {}, {}
    for t in trips.keys():
        if random.random() < 0.5:
            child1[t] = g1[t]
            child2[t] = g2[t]
        else:
            child1[t] = g2[t]
            child2[t] = g1[t]
    return child1, child2

# ============================================================
# PHASE 11 — Mutation (Random Reassignment)
# ============================================================

def mutate(genome, buses, drivers, mutation_rate=0.05):
    """Mutate a genome with small probability per gene."""
    genome = repair_genome(genome, trips, buses_df, drivers_df)
    new_g = genome.copy()

    bus_ids = [b["bus_id"] for b in buses]
    driver_ids = [d["driver_id"] for d in drivers]

    for t in new_g.keys():
        if random.random() < mutation_rate:
            new_bus = random.choice(bus_ids)
            new_drv = random.choice(driver_ids)
            new_g[t] = (new_bus, new_drv)
    return new_g

def replacement(old_pop, offspring):
    """
    Combine parents and offspring, perform non-dominated sorting,
    and select next generation based on rank and crowding distance.
    """
    # Combine
    combined = old_pop + offspring

    # Non-dominated sort
    fronts = non_dominated_sort(combined)

    new_pop = []
    for front in fronts:
        crowding_distance(front)

        if len(new_pop) + len(front) <= POP_SIZE:
            new_pop.extend(front)
        else:
            # Sort this front by descending crowding distance
            front_sorted = sorted(front, key=lambda x: x.get('crowding_distance', 0), reverse=True)
            remaining = POP_SIZE - len(new_pop)
            new_pop.extend(front_sorted[:remaining])
            break

    return new_pop

# ============================================================
# PHASE 12 — NSGA-II Main Evolution Loop
# ============================================================

def nsga2():
    population = initialize_population(POP_SIZE, trips, buses, drivers)
    # evaluate initial
    for ind in population:
        ind['fitness'] = evaluate(ind)
    print("Initial population evaluated.")

    for gen in range(NGEN):
        fronts = non_dominated_sort(population)
        for i, front in enumerate(fronts):
            for ind in front:
                ind['rank'] = i
            crowding_distance(front)

        offspring = []
        while len(offspring) < POP_SIZE:
            p1 = tournament_select(population)
            p2 = tournament_select(population)

            # --- always repair before using ---
            p1['genome'] = repair_genome(p1.get('genome', p1), trips, buses_df, drivers_df)
            p2['genome'] = repair_genome(p2.get('genome', p2), trips, buses_df, drivers_df)

            if random.random() < CXPB:
                c1, c2 = crossover(p1, p2)
            else:
                c1, c2 = p1['genome'].copy(), p2['genome'].copy()

            if random.random() < MUTPB:
                c1 = mutate(c1, buses, drivers)
            if random.random() < MUTPB:
                c2 = mutate(c2, buses, drivers)

            offspring.extend([{'genome': c1}, {'genome': c2}])

        for child in offspring:
            child['genome'] = repair_genome(child.get('genome', child), trips, buses_df, drivers_df)
            child.update({'fitness': evaluate(child)})

        population = replacement(population, offspring)
        print(f"Gen {gen+1}/{NGEN} completed. Pareto front size: {len(fronts[0])}")


    return fronts[0]


# ============================================================
# PHASE 13 — Run Optimization
# ============================================================

pareto_front = nsga2()
print(f"\nOptimization completed. Final Pareto front size = {len(pareto_front)}")


# ============================================================
# PHASE 14 — Pareto Front Visualization
# ============================================================

import itertools

def plot_pareto_2d(pareto_front, x_idx=0, y_idx=1, labels=None):
    X = [ind['fitness'][x_idx] for ind in pareto_front]
    Y = [ind['fitness'][y_idx] for ind in pareto_front]
    plt.scatter(X, Y, c='blue', alpha=0.6)
    plt.xlabel(labels[x_idx] if labels else f'F{x_idx+1}')
    plt.ylabel(labels[y_idx] if labels else f'F{y_idx+1}')
    plt.title('Pareto Front (2D Projection)')
    plt.show()

labels = [
    "Crowding", "Demand Alignment", "Wait Time",
    "Bus Idle Time", "Driver Fairness"
]

plot_pareto_2d(pareto_front, 0, 1, labels)
plot_pareto_2d(pareto_front, 2, 3, labels)


# ============================================================
# PHASE 15 — Extract Best Compromise Solutions
# ============================================================

def find_best_compromise(pareto_front):
    """Weighted min-max normalization to find balanced solution."""
    arr = np.array([ind['fitness'] for ind in pareto_front])
    mins = arr.min(axis=0)
    maxs = arr.max(axis=0)
    norm = (arr - mins) / (maxs - mins + 1e-9)
    scores = norm.mean(axis=1)
    best_idx = np.argmin(scores)
    return pareto_front[best_idx]

best_sol = find_best_compromise(pareto_front)
print("Selected balanced solution with fitness:", best_sol['fitness'])


# ============================================================
# PHASE 16 — Decode Solution to Output Format
# ============================================================

def decode_solution(individual):
    rows = []
    for trip_id, (bus_id, driver_id) in individual['genome'].items():
        tr = trips[trip_id]
        rows.append({
            "bus_id": bus_id,
            "trip_id": trip_id,
            "route_id": tr["route_id"],
            "planned_start": tr["planned_start"],
            "planned_end": tr["planned_end"],
            "assigned_driver_id": driver_id
        })
    return pd.DataFrame(rows)

final_df = decode_solution(best_sol)
final_df.to_csv("optimized_schedule.csv", index=False)
print("✅ Optimized schedule exported → optimized_schedule.csv")


# ============================================================
# PHASE 17 — Performance Reporting
# ============================================================

def report_summary(front):
    fits = np.array([ind['fitness'] for ind in front])
    print("\nObjective summary across Pareto front:")
    for i, lab in enumerate(labels):
        print(f"{lab:25s} min={fits[:,i].min():8.2f}  max={fits[:,i].max():8.2f}  mean={fits[:,i].mean():8.2f}")


# --- Collect objective values from Pareto front ---
fitness_data = [ind['fitness'] for ind in pareto_front]
df = pd.DataFrame(fitness_data, columns=['Crowding', 'Demand', 'WaitTime', 'IdleTime', 'DriverFairness'])

print(df.describe())

plt.figure(figsize=(7,5))
plt.scatter(df['Crowding'], df['IdleTime'], alpha=0.7)
plt.xlabel("Crowding Penalty (F1)")
plt.ylabel("Bus Idle Time (F4, minutes)")
plt.title("Trade-off: Crowding vs Bus Idle Time")
plt.grid(True)
plt.show()

plt.figure(figsize=(7,5))
plt.scatter(df['IdleTime'], df['DriverFairness'], alpha=0.7, c='tab:green')
plt.xlabel("Bus Idle Time (F4)")
plt.ylabel("Driver Fairness Variance (F5)")
plt.title("Trade-off: Efficiency vs Fairness")
plt.grid(True)
plt.show()

plt.figure(figsize=(7,5))
plt.scatter(df['Crowding'], df['WaitTime'], alpha=0.7, c='tab:orange')
plt.xlabel("Crowding Penalty (F1)")
plt.ylabel("Average Passenger Wait Time (F3, minutes)")
plt.title("Trade-off: Crowding vs Wait Time")
plt.grid(True)
plt.show()

from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure(figsize=(8,6))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(df['Crowding'], df['IdleTime'], df['DriverFairness'], c='tab:blue', alpha=0.7)
ax.set_xlabel("Crowding (F1)")
ax.set_ylabel("Idle Time (F4)")
ax.set_zlabel("Driver Fairness (F5)")
ax.set_title("3D Pareto Front: Comfort vs Efficiency vs Fairness")
plt.show()

plt.savefig("pareto_F1_F4.png", dpi=300)

report_summary(pareto_front)
