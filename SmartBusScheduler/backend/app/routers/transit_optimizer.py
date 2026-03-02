# ============================================================
# FULL TRANSIT SCHEDULING + NSGA-II OPTIMIZER (SINGLE FILE)
# ============================================================

# import pandas as pd
# import numpy as np
# import random
# from datetime import timedelta

# # ============================================================
# # 1️⃣ LOAD & PREPARE DATA
# # ============================================================

# def load_and_prepare_data(
#     stops_path, routes_path,
#     buses_path, drivers_path, obs_path,
#     bucket_minutes=15
# ):

#     stops_df = pd.read_csv(stops_path)
#     routes_df = pd.read_csv(routes_path)
#     buses_df = pd.read_csv(buses_path)
#     drivers_df = pd.read_csv(drivers_path)
#     obs_df = pd.read_csv(obs_path)

#     obs_df["observed_arrival"] = pd.to_datetime(obs_df["observed_arrival"])
#     obs_df["observed_departure"] = pd.to_datetime(obs_df["observed_departure"])
#     obs_df["date"] = pd.to_datetime(obs_df["date"])

#     obs_df["time_bucket"] = obs_df["observed_departure"].dt.floor(
#         f"{bucket_minutes}min"
#     )

#     return stops_df, routes_df, buses_df, drivers_df, obs_df


# # ============================================================
# # 2️⃣ CREATE OD MATRIX
# # ============================================================

# def create_od_matrix(obs_df, output_path="od_matrix.csv"):

#     od_records = []

#     for trip_id, group in obs_df.groupby("trip_id"):

#         group = group.sort_values("observed_departure")
#         stops = list(group["stop_id"])
#         boardings = list(group["boarding_in"])

#         for i in range(len(stops)):
#             for j in range(i + 1, len(stops)):
#                 od_records.append({
#                     "origin": stops[i],
#                     "destination": stops[j],
#                     "flow": boardings[i] * 0.5
#                 })

#     od_df = pd.DataFrame(od_records)
#     if len(od_df) > 0:
#         od_df = od_df.groupby(
#             ["origin", "destination"]
#         ).sum().reset_index()
#         od_df.to_csv(output_path, index=False)

#     return od_df

# # ============================================================
# # CONFLICT CHECK
# # ============================================================

# def conflicts(existing_trips, new_trip, cooling_minutes=15):

#     gap = timedelta(minutes=cooling_minutes)

#     for trip in existing_trips:

#         if not (
#             new_trip["planned_start"] >= trip["planned_end"] + gap or
#             new_trip["planned_end"] + gap <= trip["planned_start"]
#         ):
#             return True

#     return False


# # ============================================================
# # 5️⃣ INITIAL POPULATION
# # ============================================================

# def generate_initial_population(trips, buses_df, population_size=30):

#     population = []
#     bus_ids = buses_df["bus_id"].tolist()

#     for _ in range(population_size):

#         genome = {}
#         bus_schedule = {bus: [] for bus in bus_ids}

#         for trip_id, trip in trips.items():

#             feasible = []

#             for bus in bus_ids:
#                 if not conflicts(bus_schedule[bus], trip):
#                     feasible.append(bus)

#             if feasible:
#                 chosen = random.choice(feasible)
#                 genome[trip_id] = chosen
#                 bus_schedule[chosen].append(trip)
#             else:
#                 genome[trip_id] = None

#         population.append(genome)

#     return population


# # ============================================================
# # 6️⃣ FITNESS FUNCTION
# # ============================================================

# def evaluate_solution(genome, trips, buses_df):

#     unassigned = 0
#     utilization = {bus: 0 for bus in buses_df["bus_id"]}

#     for trip_id, bus_id in genome.items():

#         if bus_id is None:
#             unassigned += 1
#         else:
#             duration = (
#                 trips[trip_id]["planned_end"] -
#                 trips[trip_id]["planned_start"]
#             ).total_seconds() / 3600
#             utilization[bus_id] += duration

#     values = list(utilization.values())
#     variance = np.var(values)

#     return (
#         unassigned,
#         -sum(values),
#         variance
#     )


# # ============================================================
# # 7️⃣ NSGA-II COMPONENTS
# # ============================================================

# def dominates(f1, f2):
#     return all(a <= b for a, b in zip(f1, f2)) and any(
#         a < b for a, b in zip(f1, f2)
#     )


# def fast_non_dominated_sort(population, fitnesses):

#     S = {}
#     n = {}
#     rank = {}
#     fronts = [[]]

#     for p in range(len(population)):
#         S[p] = []
#         n[p] = 0

#         for q in range(len(population)):
#             if dominates(fitnesses[p], fitnesses[q]):
#                 S[p].append(q)
#             elif dominates(fitnesses[q], fitnesses[p]):
#                 n[p] += 1

#         if n[p] == 0:
#             rank[p] = 0
#             fronts[0].append(p)

#     i = 0
#     while fronts[i]:
#         next_front = []
#         for p in fronts[i]:
#             for q in S[p]:
#                 n[q] -= 1
#                 if n[q] == 0:
#                     rank[q] = i + 1
#                     next_front.append(q)
#         i += 1
#         fronts.append(next_front)

#     fronts.pop()
#     return fronts


# def crowding_distance(front, fitnesses):

#     distance = {i: 0 for i in front}
#     num_objectives = len(fitnesses[0])

#     for m in range(num_objectives):

#         front_sorted = sorted(front, key=lambda i: fitnesses[i][m])
#         distance[front_sorted[0]] = float("inf")
#         distance[front_sorted[-1]] = float("inf")

#         f_min = fitnesses[front_sorted[0]][m]
#         f_max = fitnesses[front_sorted[-1]][m]

#         if f_max == f_min:
#             continue

#         for i in range(1, len(front_sorted) - 1):
#             prev_f = fitnesses[front_sorted[i - 1]][m]
#             next_f = fitnesses[front_sorted[i + 1]][m]
#             distance[front_sorted[i]] += (
#                 (next_f - prev_f) / (f_max - f_min)
#             )

#     return distance


# def crossover(parent1, parent2):

#     child = {}
#     for key in parent1:
#         child[key] = parent1[key] if random.random() < 0.5 else parent2[key]
#     return child


# def mutate(genome, buses_df, mutation_rate=0.05):

#     bus_ids = buses_df["bus_id"].tolist()

#     for trip_id in genome:
#         if random.random() < mutation_rate:
#             genome[trip_id] = random.choice(bus_ids)

#     return genome


# # ============================================================
# # 8️⃣ NSGA-II MAIN LOOP
# # ============================================================

# def nsga2(trips, buses_df, generations=50, pop_size=30):

#     population = generate_initial_population(
#         trips, buses_df, pop_size
#     )

#     for _ in range(generations):

#         fitnesses = [
#             evaluate_solution(ind, trips, buses_df)
#             for ind in population
#         ]

#         fronts = fast_non_dominated_sort(population, fitnesses)

#         new_population = []

#         for front in fronts:

#             if len(new_population) + len(front) > pop_size:
#                 distances = crowding_distance(front, fitnesses)
#                 sorted_front = sorted(
#                     front,
#                     key=lambda i: distances[i],
#                     reverse=True
#                 )
#                 for idx in sorted_front:
#                     if len(new_population) < pop_size:
#                         new_population.append(population[idx])
#                 break
#             else:
#                 for idx in front:
#                     new_population.append(population[idx])

#         offspring = []
#         while len(offspring) < pop_size:
#             p1, p2 = random.sample(new_population, 2)
#             child = crossover(p1, p2)
#             child = mutate(child, buses_df)
#             offspring.append(child)

#         population = offspring

#     fitnesses = [
#         evaluate_solution(ind, trips, buses_df)
#         for ind in population
#     ]

#     best_index = np.argmin([f[0] for f in fitnesses])
#     return population[best_index]


# # ============================================================
# # 9️⃣ DECODE SCHEDULE
# # ============================================================

# def decode_solution(genome, trips):

#     records = []

#     for trip_id, bus_id in genome.items():

#         if bus_id is None:
#             continue

#         trip = trips[trip_id]

#         records.append({
#             "bus_id": bus_id,
#             "trip_id": trip_id,
#             "route_id": trip["route_id"],
#             "planned_start": trip["planned_start"],
#             "planned_end": trip["planned_end"],
#         })

#     return pd.DataFrame(records)


# # ============================================================
# # 🔟 DRIVER ASSIGNMENT
# # ============================================================

# def assign_drivers(schedule_df, drivers_df, cooling_minutes=15):

#     schedule_df = schedule_df.sort_values("planned_start")
#     driver_ids = drivers_df["driver_id"].tolist()
#     driver_schedule = {d: [] for d in driver_ids}

#     assigned = []

#     for _, row in schedule_df.iterrows():

#         assigned_driver = None

#         for driver in driver_ids:
#             if not conflicts(driver_schedule[driver], row, cooling_minutes):
#                 assigned_driver = driver
#                 driver_schedule[driver].append(row)
#                 break

#         assigned.append(assigned_driver)

#     schedule_df["assigned_driver_id"] = assigned

#     return schedule_df


# ============================================================
# 🚀 FULL PIPELINE
# ============================================================

# def run_full_pipeline():

#     stops_df, routes_df, buses_df, drivers_df, obs_df = \
#         load_and_prepare_data(
#             "stops.csv",
#             "routes.csv",
#             "buses.csv",
#             "drivers.csv",
#             "obs.csv"
#         )

#     print("Creating OD Matrix...")
#     create_od_matrix(obs_df)

#     print("Computing Demand...")
#     demand_df = compute_demand(obs_df)

#     print("Generating Trips...")
#     trips = generate_linear_trips(demand_df)

#     print("Running NSGA-II Optimization...")
#     best_genome = nsga2(trips, buses_df)

#     print("Decoding Schedule...")
#     schedule_df = decode_solution(best_genome, trips)

#     print("Assigning Drivers...")
#     final_schedule = assign_drivers(schedule_df, drivers_df)

#     final_schedule.to_csv("final_schedule.csv", index=False)

#     print("Optimization Complete.")
#     return final_schedule


# # ============================================================
# # RUN
# # ============================================================

# if __name__ == "__main__":
#     run_full_pipeline()


# # ============================================================
# # 3️⃣ DEMAND COMPUTATION
# # ============================================================

def compute_demand(obs_df):

    demand = (
        obs_df
        .groupby(["route_id", "time_bucket"])["boarding_in"]
        .sum()
        .reset_index()
        .rename(columns={"boarding_in": "demand"})
    )

    return demand


# # ============================================================
# # 4️⃣ GENERATE LINEAR TRIPS
# # ============================================================

def generate_linear_trips(
    demand_df,
    trip_duration_minutes=60,
    bus_capacity=40
):

    trips = {}
    trip_counter = 0

    for _, row in demand_df.iterrows():

        route_id = row["route_id"]
        demand = row["demand"]
        start_time = row["time_bucket"]

        num_trips = max(1, int(np.ceil(demand / bus_capacity)))

        for _ in range(num_trips):

            trip_id = f"T{trip_counter}"
            trip_counter += 1

            trips[trip_id] = {
                "route_id": route_id,
                "planned_start": start_time,
                "planned_end": start_time + timedelta(
                    minutes=trip_duration_minutes
                )
            }

    return trips

import pandas as pd
import numpy as np
import random
from datetime import timedelta


# ============================================================
# 1️⃣ LOAD & PREPARE DATA
# ============================================================

def load_and_prepare_data(
    stops_path, routes_path,
    buses_path, drivers_path, obs_path,
    bucket_minutes=15
):

    stops_df = pd.read_csv(stops_path)
    routes_df = pd.read_csv(routes_path)
    buses_df = pd.read_csv(buses_path)
    drivers_df = pd.read_csv(drivers_path)
    obs_df = pd.read_csv(obs_path)

    obs_df["observed_departure"] = pd.to_datetime(obs_df["observed_departure"])
    obs_df["date"] = pd.to_datetime(obs_df["date"])

    obs_df["time_bucket"] = obs_df["observed_departure"].dt.floor(
        f"{bucket_minutes}min"
    )

    return stops_df, routes_df, buses_df, drivers_df, obs_df


# ============================================================
# 2️⃣ DYNAMIC DEMAND COMPUTATION (QUEUE MODEL)
# ============================================================

def compute_dynamic_trips(
    obs_df,
    trip_duration_minutes=60,
    bus_capacity=40
):

    demand_df = (
        obs_df
        .groupby(["route_id", "time_bucket"])["boarding_in"]
        .sum()
        .reset_index()
        .rename(columns={"boarding_in": "new_demand"})
        .sort_values("time_bucket")
    )

    trips = {}
    trip_counter = 0

    for route_id, group in demand_df.groupby("route_id"):

        remaining_demand = 0

        for _, row in group.iterrows():

            remaining_demand += row["new_demand"]
            start_time = row["time_bucket"]

            if remaining_demand <= 0:
                continue

            num_trips = int(np.ceil(remaining_demand / bus_capacity))

            if num_trips == 0:
                continue

            headway = trip_duration_minutes / max(num_trips, 1)

            for i in range(num_trips):

                planned_start = start_time + timedelta(
                    minutes=i * headway
                )

                trip_id = f"T{trip_counter}"
                trip_counter += 1

                trips[trip_id] = {
                    "route_id": route_id,
                    "planned_start": planned_start,
                    "planned_end": planned_start + timedelta(
                        minutes=trip_duration_minutes
                    )
                }

                remaining_demand -= bus_capacity

    return trips


# ============================================================
# 3️⃣ CONFLICT CHECK
# ============================================================

def conflicts(existing_trips, new_trip, cooling_minutes=15):

    gap = timedelta(minutes=cooling_minutes)

    for trip in existing_trips:

        if not (
            new_trip["planned_start"] >= trip["planned_end"] + gap or
            new_trip["planned_end"] + gap <= trip["planned_start"]
        ):
            return True

    return False


# ============================================================
# 4️⃣ SCHEDULE ENTITY
# ============================================================

class Schedule:

    def __init__(self):
        self.bus_trips = {}

    def add_trip(self, bus_id, trip):
        if bus_id not in self.bus_trips:
            self.bus_trips[bus_id] = []
        self.bus_trips[bus_id].append(trip)

    def is_feasible(self, bus_id, trip):
        if bus_id not in self.bus_trips:
            return True
        return not conflicts(self.bus_trips[bus_id], trip)


# ============================================================
# 5️⃣ INITIAL POPULATION
# ============================================================

def generate_initial_population(trips, buses_df, population_size=30):

    population = []
    bus_ids = buses_df["bus_id"].tolist()

    for _ in range(population_size):

        genome = {}
        schedule = Schedule()

        for trip_id, trip in trips.items():

            feasible_buses = [
                bus for bus in bus_ids
                if schedule.is_feasible(bus, trip)
            ]

            if feasible_buses:
                chosen = random.choice(feasible_buses)
                genome[trip_id] = chosen
                schedule.add_trip(chosen, trip)
            else:
                genome[trip_id] = None

        population.append(genome)

    return population


# ============================================================
# 6️⃣ REPAIR GENOME (CRITICAL FIX)
# ============================================================

def repair_genome(genome, trips):

    schedule = Schedule()

    for trip_id, bus_id in genome.items():

        if bus_id is None:
            continue

        trip = trips[trip_id]

        if schedule.is_feasible(bus_id, trip):
            schedule.add_trip(bus_id, trip)
        else:
            genome[trip_id] = None

    return genome


# ============================================================
# 7️⃣ FITNESS FUNCTION (MULTI-OBJECTIVE)
# ============================================================

def evaluate_solution(genome, trips, buses_df):

    unassigned = 0
    utilization = {bus: 0 for bus in buses_df["bus_id"]}

    for trip_id, bus_id in genome.items():

        if bus_id is None:
            unassigned += 1
        else:
            duration = (
                trips[trip_id]["planned_end"] -
                trips[trip_id]["planned_start"]
            ).total_seconds() / 3600
            utilization[bus_id] += duration

    values = list(utilization.values())
    variance = np.var(values)
    buses_used = len([v for v in values if v > 0])

    return (
        unassigned,
        -sum(values),
        variance,
        buses_used
    )


# ============================================================
# 8️⃣ NSGA-II CORE
# ============================================================

def dominates(f1, f2):
    return all(a <= b for a, b in zip(f1, f2)) and any(
        a < b for a, b in zip(f1, f2)
    )


def fast_non_dominated_sort(population, fitnesses):

    S = {}
    n = {}
    fronts = [[]]

    for p in range(len(population)):
        S[p] = []
        n[p] = 0

        for q in range(len(population)):
            if dominates(fitnesses[p], fitnesses[q]):
                S[p].append(q)
            elif dominates(fitnesses[q], fitnesses[p]):
                n[p] += 1

        if n[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for q in S[p]:
                n[q] -= 1
                if n[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)

    fronts.pop()
    return fronts


def crowding_distance(front, fitnesses):

    distance = {i: 0 for i in front}
    num_objectives = len(fitnesses[0])

    for m in range(num_objectives):

        front_sorted = sorted(front, key=lambda i: fitnesses[i][m])

        distance[front_sorted[0]] = float("inf")
        distance[front_sorted[-1]] = float("inf")

        f_min = fitnesses[front_sorted[0]][m]
        f_max = fitnesses[front_sorted[-1]][m]

        if f_max == f_min:
            continue

        for i in range(1, len(front_sorted) - 1):
            prev_f = fitnesses[front_sorted[i - 1]][m]
            next_f = fitnesses[front_sorted[i + 1]][m]
            distance[front_sorted[i]] += (
                (next_f - prev_f) / (f_max - f_min)
            )

    return distance


def crossover(parent1, parent2):
    return {
        key: parent1[key] if random.random() < 0.5 else parent2[key]
        for key in parent1
    }


def mutate(genome, buses_df, mutation_rate=0.05):

    bus_ids = buses_df["bus_id"].tolist()

    for trip_id in genome:
        if random.random() < mutation_rate:
            genome[trip_id] = random.choice(bus_ids)

    return genome


# ============================================================
# 9️⃣ NSGA-II MAIN
# ============================================================

def nsga2(trips, buses_df, generations=50, pop_size=30):

    population = generate_initial_population(
        trips, buses_df, pop_size
    )

    for _ in range(generations):

        fitnesses = [
            evaluate_solution(ind, trips, buses_df)
            for ind in population
        ]

        fronts = fast_non_dominated_sort(population, fitnesses)

        new_population = []

        for front in fronts:

            if len(new_population) + len(front) > pop_size:
                distances = crowding_distance(front, fitnesses)
                sorted_front = sorted(
                    front,
                    key=lambda i: distances[i],
                    reverse=True
                )
                for idx in sorted_front:
                    if len(new_population) < pop_size:
                        new_population.append(population[idx])
                break
            else:
                for idx in front:
                    new_population.append(population[idx])

        offspring = []

        while len(offspring) < pop_size:
            p1, p2 = random.sample(new_population, 2)
            child = crossover(p1, p2)
            child = mutate(child, buses_df)
            child = repair_genome(child, trips)
            offspring.append(child)

        population = offspring

    fitnesses = [
        evaluate_solution(ind, trips, buses_df)
        for ind in population
    ]

    best_index = np.argmin([f[0] for f in fitnesses])
    return population[best_index]


# ============================================================
# 🔟 DECODE FINAL SCHEDULE
# ============================================================

def decode_solution(genome, trips):

    records = []

    for trip_id, bus_id in genome.items():

        if bus_id is None:
            continue

        trip = trips[trip_id]

        records.append({
            "bus_id": bus_id,
            "trip_id": trip_id,
            "route_id": trip["route_id"],
            "planned_start": trip["planned_start"],
            "planned_end": trip["planned_end"],
        })

    return pd.DataFrame(records)


# ============================================================
# 1️⃣1️⃣ DRIVER ASSIGNMENT WITH SHIFTS
# ============================================================

def assign_drivers(schedule_df, drivers_df):

    shift_hours = 8
    max_shift_hours = 8

    driver_ids = drivers_df["driver_id"].tolist()

    driver_shifts = []

    for driver in driver_ids:

        base_time = schedule_df["planned_start"].min().normalize()

        for s in range(3):
            shift_start = base_time + timedelta(hours=s * shift_hours)
            shift_end = shift_start + timedelta(hours=shift_hours)

            driver_shifts.append({
                "driver_id": driver,
                "shift_id": f"{driver}_S{s}",
                "shift_start": shift_start,
                "shift_end": shift_end,
                "worked_hours": 0,
                "trips": []
            })

    schedule_df = schedule_df.sort_values("planned_start")
    assigned = []

    for _, row in schedule_df.iterrows():

        trip_duration = (
            row["planned_end"] - row["planned_start"]
        ).total_seconds() / 3600

        assigned_driver = None

        for shift in driver_shifts:

            if (
                row["planned_start"] >= shift["shift_start"] and
                row["planned_end"] <= shift["shift_end"] and
                shift["worked_hours"] + trip_duration <= max_shift_hours and
                not conflicts(shift["trips"], row)
            ):
                assigned_driver = shift["driver_id"]
                shift["worked_hours"] += trip_duration
                shift["trips"].append(row)
                break

        assigned.append(assigned_driver)

    schedule_df["assigned_driver_id"] = assigned

    return schedule_df