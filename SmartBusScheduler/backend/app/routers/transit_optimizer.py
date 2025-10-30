# ============================================================
# transit_optimizer.py
# Modularized NSGA-II Transit Optimization Framework
# ============================================================

import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


# ============================================================
# PHASE 1 — DATA LOADING & PREPROCESSING
# ============================================================

def load_and_prepare_data(
    stops_path, routes_path, routes_timeplan_path,
    buses_path, drivers_path, obs_path,
    bucket_minutes=15
):
    """Load all CSVs, preprocess, and prepare optimization structures."""
    # --- Load all CSVs ---
    stops_df = pd.read_csv(stops_path)
    routes_df = pd.read_csv(routes_path)
    routes_timeplan_df = pd.read_csv(routes_timeplan_path)
    buses_df = pd.read_csv(buses_path)
    drivers_df = pd.read_csv(drivers_path)
    obs_df = pd.read_csv(obs_path)

    # Convert timestamps
    for col in ["observed_arrival", "observed_departure"]:
        if col in obs_df.columns:
            obs_df[col] = pd.to_datetime(obs_df[col], errors="coerce")
    obs_df["date"] = pd.to_datetime(obs_df["date"], errors="coerce")

    # --- Route duration ---
    route_duration = (
        routes_timeplan_df.groupby("route_id")["time_from_start_min"]
        .max().reset_index()
        .rename(columns={"time_from_start_min": "route_duration_min"})
    )
    routes_df = routes_df.merge(route_duration, on="route_id", how="left")

    # --- Planned trip times ---
    trip_times = (
        obs_df.groupby(["trip_id", "route_id"])
        .agg(
            planned_start=("observed_departure", "min"),
            planned_end=("observed_arrival", "max"),
        )
        .reset_index()
    )
    trip_times["planned_start"] = trip_times["planned_start"].fillna(
        trip_times["route_id"].map(lambda r: obs_df.loc[obs_df["route_id"] == r, "date"].min())
    )
    trip_times["planned_end"] = trip_times["planned_end"].fillna(
        trip_times["planned_start"] + pd.to_timedelta(
            trip_times["route_id"].map(routes_df.set_index("route_id")["route_duration_min"]),
            unit="m"
        )
    )
    trip_times = trip_times.merge(
        obs_df[["trip_id", "assigned_bus_id"]].drop_duplicates(),
        on="trip_id", how="left"
    )

    # --- Occupancy computation ---
    def compute_trip_occupancy(df):
        df = df.sort_values("observed_arrival")
        df["occupancy"] = (df["boarding_in"] - df["boarding_out"]).cumsum()
        return df

    obs_df = obs_df.groupby("trip_id", group_keys=False).apply(compute_trip_occupancy)

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

    # --- Demand estimation ---
    def get_bucket(dt):
        if pd.isna(dt): return np.nan
        return (dt.hour * 60 + dt.minute) // bucket_minutes

    obs_df["bucket"] = obs_df["observed_arrival"].apply(get_bucket)
    demand_buckets = (
        obs_df.groupby(["route_id", "bucket"])
        .agg(demand=("boarding_in", "sum"))
        .reset_index()
    )

    # fill missing buckets
    all_buckets = pd.DataFrame({"bucket": np.arange(0, (24*60)//bucket_minutes)})
    routes_list = routes_df["route_id"].unique()
    full_idx = pd.MultiIndex.from_product([routes_list, all_buckets["bucket"]], names=["route_id", "bucket"])
    demand_buckets = (
        demand_buckets.set_index(["route_id", "bucket"])
        .reindex(full_idx, fill_value=0)
        .reset_index()
    )

    # --- Structures ---
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

    buses = buses_df.to_dict("records")
    drivers = drivers_df.to_dict("records")

    route_demand = {
        (r, int(b)): d for r, b, d in demand_buckets[["route_id", "bucket", "demand"]].to_numpy()
    }

    return trips, buses, drivers, buses_df, drivers_df, route_demand


# ============================================================
# PHASE 2 — OBJECTIVE FUNCTIONS
# ============================================================

def random_individual(trips, buses, drivers):
    bus_ids = [b["bus_id"] for b in buses]
    driver_ids = [d["driver_id"] for d in drivers]
    return {t: (random.choice(bus_ids), random.choice(driver_ids)) for t in trips.keys()}


def objective_crowding(individual, trips, buses_df):
    genome = individual.get('genome', individual)
    bus_capacity = buses_df.set_index("bus_id")["max_capacity"].to_dict()
    penalty = 0.0
    for trip_id, assignment in genome.items():
        try:
            bus_id, _ = assignment
        except Exception:
            continue
        trip = trips.get(trip_id)
        if trip is None: continue
        max_occ = trip.get("max_occupancy")
        if pd.isna(max_occ): continue
        cap = bus_capacity.get(bus_id, 50)
        load_factor = max_occ / cap if cap > 0 else 1
        if load_factor > 1:
            penalty += (load_factor - 1) ** 2
    return float(penalty)


def objective_demand_alignment(individual, trips, route_demand, bucket_minutes=15):
    genome = individual.get('genome', individual)
    route_bucket_trips = {}
    for trip_id, assignment in genome.items():
        trip = trips.get(trip_id)
        if not trip: continue
        start = trip.get("planned_start")
        if pd.isna(start): continue
        start = pd.to_datetime(start)
        bucket = int((start.hour * 60 + start.minute) // bucket_minutes)
        key = (trip["route_id"], bucket)
        route_bucket_trips[key] = route_bucket_trips.get(key, 0) + 1

    penalty = 0.0
    for key, trips_in_bucket in route_bucket_trips.items():
        demand = route_demand.get(key, 0)
        expected_trips = max(1, int(demand // 50))
        penalty += abs(trips_in_bucket - expected_trips)
    return float(penalty)


def objective_wait_time(individual, trips):
    genome = individual.get('genome', individual)
    route_trips = {}
    for t, assign in genome.items():
        tr = trips.get(t)
        if not tr or pd.isna(tr.get("planned_start")): continue
        route_trips.setdefault(tr["route_id"], []).append(pd.to_datetime(tr["planned_start"]))

    total_wait = 0.0
    route_count = 0
    for r, starts in route_trips.items():
        starts = sorted(starts)
        if len(starts) > 1:
            gaps = [(starts[i+1] - starts[i]).total_seconds()/60 for i in range(len(starts)-1)]
            total_wait += np.mean(gaps)
            route_count += 1
    return total_wait / route_count if route_count > 0 else 0.0


def objective_idle_time(individual, trips):
    genome = individual.get('genome', individual)
    bus_trips = {}
    for t, (bus, _) in genome.items():
        bus_trips.setdefault(bus, []).append(trips.get(t))
    total_idle = 0.0
    for bus, tlist in bus_trips.items():
        tlist = [x for x in tlist if x and not pd.isna(x.get("planned_start"))]
        tlist = sorted(tlist, key=lambda x: x["planned_start"])
        for i in range(len(tlist)-1):
            gap = (pd.to_datetime(tlist[i+1]["planned_start"]) - pd.to_datetime(tlist[i]["planned_end"])).total_seconds()/60
            if gap > 0:
                total_idle += gap
    return float(total_idle)


def objective_driver_fairness(individual, trips, drivers_df):
    genome = individual.get('genome', individual)
    driver_work = {}
    for t, (_, drv) in genome.items():
        tr = trips.get(t)
        if not tr: continue
        s, e = tr["planned_start"], tr["planned_end"]
        if pd.isna(s) or pd.isna(e): continue
        dur = (pd.to_datetime(e) - pd.to_datetime(s)).total_seconds()/60
        driver_work[drv] = driver_work.get(drv, 0) + dur
    if not driver_work:
        return 0.0
    return float(np.var(list(driver_work.values())))

# ============================================================
# PHASE 3 — NSGA-II COMPONENTS (MODULAR VERSION)
# ============================================================

def repair_genome(genome, trips, buses_df, drivers_df):
    """Ensure genome has valid bus and driver assignments."""
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


# ---------------- Selection ----------------

def tournament_selection(population, k=2):
    """Select one individual via tournament selection."""
    contenders = random.sample(population, k)
    contenders.sort(key=lambda ind: (ind['rank'], -ind.get('distance', 0)))
    return contenders[0]


# ---------------- Crossover ----------------

def crossover(parent1, parent2, crossover_rate=0.9):
    """Perform uniform crossover between two parent genomes."""
    if random.random() > crossover_rate:
        return parent1.copy(), parent2.copy()

    child1, child2 = {}, {}
    for trip_id in parent1.keys():
        if random.random() < 0.5:
            child1[trip_id] = parent1[trip_id]
            child2[trip_id] = parent2[trip_id]
        else:
            child1[trip_id] = parent2[trip_id]
            child2[trip_id] = parent1[trip_id]
    return child1, child2


# ---------------- Mutation ----------------

def mutate(genome, buses_df, drivers_df, mutation_rate=0.2):
    """Randomly reassign some bus/driver combinations."""
    if random.random() > mutation_rate:
        return genome
    valid_buses = buses_df["bus_id"].tolist()
    valid_drivers = drivers_df["driver_id"].tolist()
    for trip_id in genome.keys():
        if random.random() < mutation_rate:
            genome[trip_id] = (
                random.choice(valid_buses),
                random.choice(valid_drivers)
            )
    return genome


# ---------------- Evaluate ----------------

def evaluate(individual, trips, buses_df, drivers_df, route_demand):
    genome = repair_genome(individual.get('genome', individual), trips, buses_df, drivers_df)
    F1 = objective_crowding(genome, trips, buses_df)
    F2 = objective_demand_alignment(genome, trips, route_demand)
    F3 = objective_wait_time(genome, trips)
    F4 = objective_idle_time(genome, trips)
    F5 = objective_driver_fairness(genome, trips, drivers_df)
    return [F1, F2, F3, F4, F5]


# ---------------- Dominance Logic ----------------

def dominates(ind1, ind2):
    """Check Pareto dominance between two individuals."""
    return (
        all(a <= b for a, b in zip(ind1['fitness'], ind2['fitness'])) and
        any(a < b for a, b in zip(ind1['fitness'], ind2['fitness']))
    )


def non_dominated_sort(pop):
    """Fast non-dominated sorting for NSGA-II."""
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
    fronts.pop()
    return [[pop[idx] for idx in front] for front in fronts]


def crowding_distance(front):
    """Compute crowding distance for individuals in a front."""
    if not front:
        return
    num_obj = len(front[0]['fitness'])
    for ind in front:
        ind['distance'] = 0
    for m in range(num_obj):
        front.sort(key=lambda x: x['fitness'][m])
        front[0]['distance'] = front[-1]['distance'] = float('inf')
        fmin, fmax = front[0]['fitness'][m], front[-1]['fitness'][m]
        if fmax == fmin:
            continue
        for i in range(1, len(front) - 1):
            next_f, prev_f = front[i + 1]['fitness'][m], front[i - 1]['fitness'][m]
            front[i]['distance'] += (next_f - prev_f) / (fmax - fmin)


# ---------------- NSGA-II Core ----------------

def nsga2(trips, buses, drivers, buses_df, drivers_df, route_demand,
          pop_size=50, ngen=100, cxpb=0.9, mutpb=0.2):
    """Main NSGA-II evolutionary loop."""
    # --- Initialization ---
    population = [{"genome": random_individual(trips, buses, drivers)} for _ in range(pop_size)]
    for ind in population:
        ind["fitness"] = evaluate(ind, trips, buses_df, drivers_df, route_demand)

    # --- Evolutionary loop ---
    for gen in range(ngen):
        # 1. Rank and crowding distance
        fronts = non_dominated_sort(population)
        for i, front in enumerate(fronts):
            for ind in front:
                ind["rank"] = i
            crowding_distance(front)

        # 2. Generate offspring
        offspring = []
        while len(offspring) < pop_size:
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)
            c1_genome, c2_genome = crossover(parent1["genome"], parent2["genome"], crossover_rate=cxpb)
            c1_genome = mutate(c1_genome, buses_df, drivers_df, mutation_rate=mutpb)
            c2_genome = mutate(c2_genome, buses_df, drivers_df, mutation_rate=mutpb)
            offspring.extend([
                {"genome": c1_genome},
                {"genome": c2_genome}
            ])

        # 3. Evaluate new individuals
        for child in offspring:
            child["fitness"] = evaluate(child, trips, buses_df, drivers_df, route_demand)

        # 4. Combine & truncate population (elitism)
        combined = population + offspring
        new_population = []
        fronts = non_dominated_sort(combined)
        for front in fronts:
            crowding_distance(front)
            if len(new_population) + len(front) <= pop_size:
                new_population.extend(front)
            else:
                front.sort(key=lambda x: -x["distance"])
                needed = pop_size - len(new_population)
                new_population.extend(front[:needed])
                break

        population = new_population
        print(f"Generation {gen+1}/{ngen} complete. Pareto front size: {len(fronts[0])}")

    # Return final Pareto front
    final_fronts = non_dominated_sort(population)
    return final_fronts[0]

# ============================================================
# PHASE 4 — SOLUTION DECODING & EXPORT
# ============================================================

def decode_solution(individual, trips):
    """Convert optimized genome into a flat schedule DataFrame."""
    genome = individual.get("genome", individual)
    records = []
    for trip_id, (bus_id, driver_id) in genome.items():
        trip = trips.get(trip_id)
        if not trip:
            continue
        records.append({
            "bus_id": bus_id,
            "trip_id": trip_id,
            "route_id": trip["route_id"],
            "planned_start": trip["planned_start"],
            "planned_end": trip["planned_end"],
            "assigned_driver_id": driver_id
        })
    return pd.DataFrame(records)
