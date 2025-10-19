# synthetic_transit_generator.py
"""
Synthetic transit dataset generator
- Do NOT run anything on import.
- Functions:
    create_base_data(...)
    generate_day_data(...)
    generate_range_data(...)
- Expects CSVs (optional) in working directory:
    stops.csv, routes.csv, planned_schedule.csv, observed_schedule.csv
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import math

# ----------------------
# Utility / Defaults
# ----------------------
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

DEFAULT_TURNAROUND_MIN = 15  # default buffer between trips for same vehicle
DEFAULT_BUS_CAPACITY = 50
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ----------------------
# Helper functions
# ----------------------
def _parse_datetime(x):
    if pd.isna(x):
        return None
    if isinstance(x, datetime):
        return x
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(str(x), fmt)
        except Exception:
            continue
    # last resort
    return pd.to_datetime(x, errors="coerce")

def _ensure_list_col(df, col):
    """Ensure a column that may represent arrays is converted into actual lists."""
    if col not in df.columns:
        return df
    def _to_list(x):
        if pd.isna(x):
            return []
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            # try JSON parse
            try:
                v = json.loads(x)
                if isinstance(v, list):
                    return v
            except Exception:
                # comma separated
                return [s.strip() for s in x.split(",") if s.strip()]
        # fallback
        return [x]
    df[col] = df[col].apply(_to_list)
    return df

def clean_and_cast_stops(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    expected = {"stop_id", "stop_name", "lat", "lon"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"stops.csv missing columns: {missing}")
    df = df[["stop_id", "stop_name", "lat", "lon"]]
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    # drop rows with missing coords
    df = df.dropna(subset=["stop_id", "lat", "lon"])
    return df.reset_index(drop=True)

def clean_and_cast_routes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "route_id" not in df.columns:
        raise ValueError("routes.csv must include route_id")
    # ensure stops column exists, may be named stops or stop_list
    if "stops" not in df.columns:
        # attempt to detect a candidate col
        for candidate in ("stop_list", "stop_ids", "stops_list"):
            if candidate in df.columns:
                df = df.rename(columns={candidate: "stops"})
                break
        else:
            raise ValueError("routes.csv must include a column with route stops (named 'stops' or similar).")
    df = _ensure_list_col(df, "stops")
    # keep only route_id and stops
    df = df[["route_id", "stops"]]
    # ensure every route has at least 2 stops
    df["stops"] = df["stops"].apply(lambda s: s if isinstance(s, list) and len(s) >= 2 else [])
    if (df["stops"].str.len() == 0).any():
        bad = df[df["stops"].str.len() == 0]["route_id"].tolist()
        raise ValueError(f"routes with no valid stops found: {bad}")
    return df.reset_index(drop=True)

def compute_link_stats_from_observed(observed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes travel time statistics between consecutive stops per route:
    returns DataFrame with columns: route_id, from_stop, to_stop, mean_tt, std_tt, p90, count
    expected observed_df has route_id, stop_id, trip_id, observed_arrival columns (timestamps)
    """
    # require columns
    if observed_df is None or observed_df.empty:
        return pd.DataFrame(columns=["route_id", "from_stop", "to_stop", "mean_tt", "std_tt", "p90", "count"])
    odf = observed_df.copy()
    # parse times
    odf["observed_arrival_dt"] = odf["observed_arrival"].apply(_parse_datetime)
    # sort by trip and stop_order if available
    if "stop_order" in odf.columns:
        odf = odf.sort_values(["trip_id", "stop_order"])
    else:
        odf = odf.sort_values(["trip_id", "observed_arrival_dt"])
    # compute deltas per trip
    records = []
    for trip_id, grp in odf.groupby("trip_id"):
        grp = grp.sort_values("observed_arrival_dt")
        rows = grp.to_dict("records")
        for i in range(len(rows) - 1):
            r1 = rows[i]
            r2 = rows[i+1]
            if r1.get("route_id") != r2.get("route_id"):
                continue
            from_stop = r1["stop_id"]
            to_stop = r2["stop_id"]
            t1 = r1["observed_arrival_dt"]
            t2 = r2["observed_arrival_dt"]
            if t1 is None or t2 is None:
                continue
            delta = (t2 - t1).total_seconds() / 60.0
            if delta < 0 or delta > 240:  # filter unrealistic
                continue
            records.append({
                "route_id": r1["route_id"],
                "from_stop": from_stop,
                "to_stop": to_stop,
                "travel_time_mins": delta
            })
    if not records:
        return pd.DataFrame(columns=["route_id", "from_stop", "to_stop", "mean_tt", "std_tt", "p90", "count"])
    tt_df = pd.DataFrame(records)
    agg = tt_df.groupby(["route_id", "from_stop", "to_stop"])["travel_time_mins"].agg(
        mean_tt="mean", std_tt="std", p90=lambda x: np.percentile(x.dropna(), 90), count="count"
    ).reset_index()
    # fill NaN std with small number
    agg["std_tt"] = agg["std_tt"].fillna(1.0)
    return agg

def estimate_trip_duration_from_template(route_stops: List[str], link_stats: pd.DataFrame, default_speed=1.0) -> float:
    """
    Estimate total trip duration (mins) for route using link stats (sum of means).
    If link missing, use default guess of 4 minutes per link.
    """
    total = 0.0
    for i in range(len(route_stops)-1):
        a = route_stops[i]
        b = route_stops[i+1]
        row = link_stats[(link_stats["from_stop"] == a) & (link_stats["to_stop"] == b)]
        if not row.empty:
            total += float(row["mean_tt"].values[0])
        else:
            total += 4.0  # fallback per link
    return total

def build_trip_start_template(routes_df: pd.DataFrame, common_template: Optional[Dict[str, List[str]]] = None):
    """
    Return a mapping route_id -> list of trip start times (relative times as "HH:MM" strings).
    If common_template provided, use it (should be route->list). Otherwise build a simple template:
      - long routes fewer starts, short routes more starts, concentrated in peak.
    """
    template = {}
    for _, row in routes_df.iterrows():
        rid = row["route_id"]
        nstops = len(row["stops"])
        if common_template and rid in common_template:
            template[rid] = common_template[rid]
            continue
        # create a simple on-the-day template (times as HH:MM)
        if nstops >= 18:
            # long route: fewer departures
            starts = ["05:30", "06:15", "07:00", "08:15", "10:30", "12:00", "14:30", "16:30", "18:00", "20:00"]
        elif nstops >= 15:
            starts = ["05:30", "06:00", "06:45", "07:30", "08:15", "09:30", "11:30", "13:30", "15:30", "17:30", "19:00", "21:00"]
        else:
            starts = ["05:30", "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", "09:30", "11:00", "12:30", "14:00", "15:30", "17:00", "18:00", "19:00", "20:00", "21:00"]
        template[rid] = starts
    return template

def hhmm_to_datetime(date: datetime.date, hhmm: str) -> datetime:
    h, m = [int(x) for x in hhmm.split(":")]
    return datetime.combine(date, datetime.min.time()).replace(hour=h, minute=m, second=0)

# ----------------------
# Public function 1
# ----------------------
def create_base_data(
    stops_csv: str = "stops.csv",
    routes_csv: str = "routes.csv",
    observed_csv: Optional[str] = "observed_schedule.csv",
    bus_data: Optional[pd.DataFrame] = None,
    timing_template: Optional[Dict[str, List[str]]] = None,
    output_dir: str = "."
) -> Dict[str, Any]:
    """
    Loads and validates base datasets and computes link statistics if observed data exists.
    Returns dict with keys:
        stops_df, routes_df, link_stats_df, bus_data (DataFrame), timing_template (mapping)
    """
    # Load stops
    if not os.path.exists(stops_csv):
        raise FileNotFoundError(f"{stops_csv} not found.")
    stops_df = pd.read_csv(stops_csv)
    stops_df = clean_and_cast_stops(stops_df)

    # Load routes
    if not os.path.exists(routes_csv):
        raise FileNotFoundError(f"{routes_csv} not found.")
    routes_df = pd.read_csv(routes_csv)
    routes_df = clean_and_cast_routes(routes_df)

    # --- NEW SECTION: Add reverse routes automatically ---
    reverse_routes = []
    for _, row in routes_df.iterrows():
        rid = str(row["route_id"]).strip()
        stops = row["stops"]
        rev_stops = list(reversed(stops))
        new_route_id = f"{rid}_DOWN"
        reverse_routes.append({"route_id": new_route_id, "stops": rev_stops})
    if reverse_routes:
        routes_df = pd.concat([routes_df, pd.DataFrame(reverse_routes)], ignore_index=True)
    # -------------------------------------------------------

    # optional observed
    link_stats_df = pd.DataFrame(columns=["route_id", "from_stop", "to_stop", "mean_tt", "std_tt", "p90", "count"])
    if observed_csv and os.path.exists(observed_csv):
        obs_df = pd.read_csv(observed_csv)
        if "observed_arrival" in obs_df.columns:
            link_stats_df = compute_link_stats_from_observed(obs_df)
        elif "observed_departure" in obs_df.columns:
            obs_df["observed_arrival"] = obs_df["observed_departure"]
            link_stats_df = compute_link_stats_from_observed(obs_df)

    # bus_data default
    if bus_data is None:
        bus_data = pd.DataFrame([{"bus_id": f"BUS_{i+1:03}", "capacity": DEFAULT_BUS_CAPACITY} for i in range(100)])
    else:
        if "bus_id" not in bus_data.columns or "capacity" not in bus_data.columns:
            raise ValueError("bus_data must include 'bus_id' and 'capacity' columns")

    # timing template
    if timing_template is None:
        timing_template = build_trip_start_template(routes_df, None)

    result = {
        "stops_df": stops_df,
        "routes_df": routes_df,
        "link_stats_df": link_stats_df,
        "bus_data": bus_data,
        "timing_template": timing_template
    }

    os.makedirs(output_dir, exist_ok=True)
    stops_df.to_csv(os.path.join(output_dir, "stops_normalized.csv"), index=False)
    routes_df.to_csv(os.path.join(output_dir, "routes_normalized.csv"), index=False)
    if not link_stats_df.empty:
        link_stats_df.to_csv(os.path.join(output_dir, "link_stats.csv"), index=False)

    return result

# ----------------------
# Assignment & scheduling helpers
# ----------------------
def _create_trip_records_for_route_on_date(route_row, route_tt_list: List[str], link_stats_df: pd.DataFrame, date: datetime.date, trip_id_prefix: Optional[str]=None):
    """
    Creates planned trip records for a route on a given date using the provided start times
    Returns planned_rows: list of dicts (matching planned_schedule format), trip_meta list for assignment
    """
    planned_rows = []
    trip_meta = []  # will contain (trip_id, route_id, start_dt, est_duration_mins, stops_list, planned_stop_times list)
    route_id = route_row["route_id"]
    stops = route_row["stops"]
    est_trip_duration = estimate_trip_duration_from_template(stops, link_stats_df)
    for idx, hhmm in enumerate(route_tt_list, start=1):
        trip_seq = idx
        trip_id = f"{route_id}_T{trip_seq:03}"
        start_dt = hhmm_to_datetime(date, hhmm)
        # propagate times along stops using mean link times
        current = start_dt
        planned_stop_times = []
        for order, stop in enumerate(stops, start=1):
            if order == 1:
                arrival = current
                dwell = timedelta(minutes= random.randint(1,3))
                departure = arrival + dwell
            else:
                # find mean travel time from prev->current
                prev = stops[order-2]
                row = link_stats_df[
                    (link_stats_df["route_id"] == route_id) &
                    (link_stats_df["from_stop"] == prev) &
                    (link_stats_df["to_stop"] == stop)
                ]
                if not row.empty:
                    travel_m = float(row["mean_tt"].values[0])
                else:
                    travel_m = 4.0 + (len(stops) // 10)  # fallback
                arrival = current + timedelta(minutes=travel_m)
                dwell = timedelta(minutes=random.randint(1,3))
                departure = arrival + dwell
            planned_rows.append({
                "trip_id": trip_id,
                "route_id": route_id,
                "stop_id": stop,
                "stop_order": order,
                "planned_arrival": arrival.strftime(DEFAULT_TIME_FORMAT),
                "planned_departure": departure.strftime(DEFAULT_TIME_FORMAT),
            })
            planned_stop_times.append((stop, arrival, departure))
            current = departure
        # store meta
        est_total_mins = (planned_stop_times[-1][2] - planned_stop_times[0][1]).total_seconds() / 60.0
        trip_meta.append({
            "trip_id": trip_id,
            "route_id": route_id,
            "start_time": start_dt,
            "end_time": planned_stop_times[-1][2],
            "est_total_mins": est_total_mins,
            "stops": stops,
            "planned_stop_times": planned_stop_times
        })
    return planned_rows, trip_meta

def assign_buses_to_trips_greedy(trip_meta_list: List[Dict], bus_fleet: pd.DataFrame, turnaround_min: int=DEFAULT_TURNAROUND_MIN):
    """
    Greedy interval-packing algorithm: aim to minimize number of buses.
    Inputs:
        trip_meta_list: list of trip_meta dicts (for all routes) with start_time and end_time
        bus_fleet: DataFrame with bus_id, capacity
    Returns:
        assignments: dict trip_id -> bus_id
        used_buses: list of bus_id used
    Approach:
        - Sort trips by start_time
        - For each trip, find a bus whose last_end_time + turnaround <= trip.start_time
        - If none found, assign next unused bus
    """
    trips = sorted(trip_meta_list, key=lambda x: x["start_time"])
    used_bus_states = {}  # bus_id -> last_end_time
    assignments = {}
    bus_iter = iter(bus_fleet["bus_id"].tolist())
    # We'll maintain a pool of available buses
    active_buses = {}  # bus_id -> last_end_time

    unused_bus_list = bus_fleet["bus_id"].tolist()[:]
    for trip in trips:
        assigned = False
        trip_start = trip["start_time"]
        # try to reuse bus
        candidate_bus = None
        earliest_end = None
        for bus, last_end in active_buses.items():
            if last_end + timedelta(minutes=turnaround_min) <= trip_start:
                # reuse this bus
                candidate_bus = bus
                break
            # keep earliest to consider
            if earliest_end is None or last_end < earliest_end:
                earliest_end = last_end
        if candidate_bus is None and unused_bus_list:
            candidate_bus = unused_bus_list.pop(0)
        if candidate_bus is None:
            # no available bus -> reuse the one that becomes free the earliest (will violate turnaround; record anyway)
            # pick bus with earliest last_end
            if active_buses:
                candidate_bus = min(active_buses.items(), key=lambda x: x[1])[0]
            else:
                # no buses at all (shouldn't happen)
                raise RuntimeError("No buses in fleet to assign")
        # assign
        assignments[trip["trip_id"]] = candidate_bus
        # update last_end for candidate
        active_buses[candidate_bus] = trip["end_time"]
        used_bus_states[candidate_bus] = active_buses[candidate_bus]
    used_buses = sorted(list(used_bus_states.keys()))
    return assignments, used_buses

def simulate_observed_from_planned(planned_rows: List[Dict], trip_meta_map: Dict[str, Dict], demand_profile: Dict[str, int], bus_assignments: Dict[str, str], bus_capacity_map: Dict[str, int], peak_delta_std=3):
    """
    Generate observed rows from planned by adding random noise, delays per stop, and boarding/alighting.
    planned_rows: list of planned dicts
    trip_meta_map: trip_id -> meta
    demand_profile: route_id -> expected passengers per trip (simple)
    bus_assignments: trip_id -> bus_id
    bus_capacity_map: bus_id -> capacity
    Returns observed_rows list of dicts
    """
    observed_rows = []
    # convert planned rows into per-trip ordering
    planned_df = pd.DataFrame(planned_rows)
    if planned_df.empty:
        return []
    grouped = planned_df.sort_values(["trip_id", "stop_order"]).groupby("trip_id")
    for trip_id, grp in grouped:
        route_id = grp["route_id"].iloc[0]
        planned_list = grp.to_dict("records")
        # demand estimate
        expected_boarding_total = demand_profile.get(route_id, 12)  # passengers per trip
        # distribute across stops proportionally (simple): higher boarding earlier during peaks
        # We'll make boarding_in a Poisson/Gaussian around share
        remaining = expected_boarding_total
        bus_id = bus_assignments.get(trip_id, None)
        capacity = bus_capacity_map.get(bus_id, DEFAULT_BUS_CAPACITY)
        onboard = 0
        for row in planned_list:
            # add small stochastic delay proportional to route length
            planned_arrival_dt = _parse_datetime(row["planned_arrival"])
            # random delay: negative allowed (early) but not too large
            delay = int(random.gauss(1.5, peak_delta_std))
            # peak multiplier: if in peak hours add positive bias
            if 7 <= planned_arrival_dt.hour <= 10 or 17 <= planned_arrival_dt.hour <= 21:
                delay = int(delay + abs(random.gauss(3, 2)))
            observed_arrival = planned_arrival_dt + timedelta(minutes=delay)
            # departure delay depends on dwell variation
            observed_departure = _parse_datetime(row["planned_departure"]) + timedelta(minutes=max(0, delay + random.randint(0,2)))
            # boarding logic
            # allocate boarding_in roughly proportional to remaining stops
            if remaining <= 0:
                boarding_in = 0
            else:
                # probability to board at earlier stops higher
                prob = 0.4 if row["stop_order"] <= max(2, int(len(planned_list) * 0.2)) else 0.1
                boarding_in = int(min(remaining, max(0, int(np.random.poisson(lam=max(1, expected_boarding_total * prob))))))
            # enforce capacity
            can_board = max(0, capacity - onboard)
            boarding_actual = min(boarding_in, can_board)
            # alighting approx 60% of onboard random
            alight = int(min(onboard, max(0, int(np.random.binomial(onboard, 0.15)))))
            onboard = max(0, onboard - alight) + boarding_actual
            remaining -= boarding_actual
            observed_rows.append({
                "trip_id": trip_id,
                "route_id": route_id,
                "stop_id": row["stop_id"],
                "observed_arrival": observed_arrival.strftime(DEFAULT_TIME_FORMAT),
                "observed_departure": observed_departure.strftime(DEFAULT_TIME_FORMAT),
                "boarding_in": boarding_actual,
                "boarding_out": alight,
                "delay_mins": delay
            })
        # after trip, if onboard > 0, that may indicate overload or we assume they alight at final stops
    return observed_rows

# ----------------------
# Public function 2
# ----------------------
def generate_day_data(
    date_str: str,
    base_data: Dict[str, Any],
    bus_fleet_override: Optional[pd.DataFrame] = None,
    turnaround_min: int = DEFAULT_TURNAROUND_MIN,
    admin_overrides: Optional[Dict[str, Any]] = None,
    output_dir: str = ".",
    save_csv: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate planned & observed schedules for a single date.
    Inputs:
      date_str: "YYYY-MM-DD"
      base_data: dict returned by create_base_data
      bus_fleet_override: optional DataFrame to override bus_data
      turnaround_min: minutes buffer between trips for same bus
      admin_overrides: dict for overrides. Supported keys:
         - fixed_trip_times: dict route_id -> list of HH:MM strings (replace template)
         - route_disable: list of route_id to skip
         - bus_capacity_overrides: dict bus_id -> capacity
      output_dir, save_csv
    Returns:
      planned_df, observed_df (DataFrames)
    """
    # parse date
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    stops_df = base_data["stops_df"]
    routes_df = base_data["routes_df"]
    link_stats_df = base_data.get("link_stats_df", pd.DataFrame())
    bus_data = bus_fleet_override if bus_fleet_override is not None else base_data.get("bus_data")
    timing_template = base_data.get("timing_template", {})
    if admin_overrides is None:
        admin_overrides = {}
    # apply overrides to template
    fixed_times = admin_overrides.get("fixed_trip_times", {})
    route_disable = set(admin_overrides.get("route_disable", []))
    bus_capacity_overrides = admin_overrides.get("bus_capacity_overrides", {})

    planned_rows_all = []
    trip_meta_list = []

    # Build demand profile per route (basic): use observed boarding stats if link_stats exists
    demand_profile = {}
    # If observed_schedule.csv exists in base_data, try to derive average boarding per route
    # We'll look for 'boarding_in' in the observed file if provided earlier (link_stats_df derived from observed file)
    # For now generate simple heuristic: longer routes -> more passengers per trip
    for _, r in routes_df.iterrows():
        if r["route_id"] in route_disable:
            continue
        nstops = len(r["stops"])
        if nstops >= 18:
            demand_profile[r["route_id"]] = 25
        elif nstops >= 15:
            demand_profile[r["route_id"]] = 18
        else:
            demand_profile[r["route_id"]] = 12

    # Build planned entries per route
    for _, route_row in routes_df.iterrows():
        rid = route_row["route_id"]
        if rid in route_disable:
            continue
        route_template = timing_template.get(rid, None)
        if rid in fixed_times:
            route_template = fixed_times[rid]
        if route_template is None:
            route_template = build_trip_start_template(pd.DataFrame([route_row]))[rid]

        planned_rows, trip_meta = _create_trip_records_for_route_on_date(route_row, route_template, link_stats_df, date)
        planned_rows_all.extend(planned_rows)
        trip_meta_list.extend(trip_meta)

    # Assign buses
    bus_fleet = bus_data.copy().reset_index(drop=True)
    assignments, used_buses = assign_buses_to_trips_greedy(trip_meta_list, bus_fleet, turnaround_min=turnaround_min)

    # bus capacity map
    bus_capacity_map = {row["bus_id"]: int(row["capacity"]) for _, row in bus_fleet.iterrows()}
    # apply overrides
    for b, cap in bus_capacity_overrides.items():
        bus_capacity_map[b] = int(cap)

    # Build trip_meta_map
    trip_meta_map = {m["trip_id"]: m for m in trip_meta_list}

    # Simulate observed
    observed_rows = simulate_observed_from_planned(planned_rows_all, trip_meta_map, demand_profile, assignments, bus_capacity_map)

    planned_df = pd.DataFrame(planned_rows_all)
    observed_df = pd.DataFrame(observed_rows)

    # Add metadata columns (date, assigned_bus) to planned and observed
    planned_df["date"] = date_str
    # map assigned bus to planned rows
    planned_df["assigned_bus"] = planned_df["trip_id"].map(assignments)
    if not observed_df.empty:
        observed_df["date"] = date_str
        observed_df["assigned_bus"] = observed_df["trip_id"].map(assignments)

    # Flag capacity violations in observed
    # compute per-trip total boarding and compare to capacity
    if not observed_df.empty:
        trip_boarding = observed_df.groupby("trip_id")["boarding_in"].sum().reset_index().rename(columns={"boarding_in": "total_boarding"})
        if "assigned_bus" not in observed_df.columns:
            observed_df = observed_df.merge(trip_boarding, on="trip_id", how="left")
        else:
            observed_df = observed_df.merge(trip_boarding, on="trip_id", how="left")
        # map capacity
        observed_df["bus_capacity"] = observed_df["assigned_bus"].map(bus_capacity_map)
        observed_df["over_capacity_flag"] = observed_df["total_boarding"] > observed_df["bus_capacity"]

    # Save CSVs if requested
    os.makedirs(output_dir, exist_ok=True)
    if save_csv:
        planned_df.to_csv(os.path.join(output_dir, f"planned_schedule_{date_str}.csv"), index=False)
        observed_df.to_csv(os.path.join(output_dir, f"observed_schedule_{date_str}.csv"), index=False)

    return planned_df, observed_df

# ----------------------
# Public function 3
# ----------------------
def generate_range_data(
    start_date: str,
    end_date: str,
    base_data: Dict[str, Any],
    output_dir: str = ".",
    turnaround_min: int = DEFAULT_TURNAROUND_MIN,
    admin_overrides: Optional[Dict[str, Any]] = None,
    save_daily: bool = False
):
    """
    Generate dataset for a date range inclusive.
    Saves combined CSVs: planned_schedule_RANGE_{start}_{end}.csv and observed_schedule_RANGE_{start}_{end}.csv
    If save_daily True, also saves per-day CSVs.
    Returns combined DataFrames (planned_all, observed_all)
    """
    s = datetime.strptime(start_date, "%Y-%m-%d").date()
    e = datetime.strptime(end_date, "%Y-%m-%d").date()
    if e < s:
        raise ValueError("end_date must be >= start_date")
    current = s
    all_planned = []
    all_observed = []
    while current <= e:
        ds = current.strftime("%Y-%m-%d")
        print(f"Generating for {ds} ...")
        p_df, o_df = generate_day_data(
            ds,
            base_data,
            turnaround_min=turnaround_min,
            admin_overrides=admin_overrides,
            output_dir=output_dir,
            save_csv=save_daily
        )
        p_df["date_generated"] = datetime.now().strftime(DEFAULT_TIME_FORMAT)
        if not o_df.empty:
            o_df["date_generated"] = datetime.now().strftime(DEFAULT_TIME_FORMAT)
        all_planned.append(p_df)
        all_observed.append(o_df if not o_df.empty else pd.DataFrame())
        current += timedelta(days=1)
    if all_planned:
        planned_all = pd.concat(all_planned, ignore_index=True)
    else:
        planned_all = pd.DataFrame()
    if any(not df.empty for df in all_observed):
        observed_all = pd.concat([df for df in all_observed if not df.empty], ignore_index=True)
    else:
        observed_all = pd.DataFrame()

    os.makedirs(output_dir, exist_ok=True)
    planned_all.to_csv(os.path.join(output_dir, f"planned_schedule_RANGE_{start_date}_{end_date}.csv"), index=False)
    observed_all.to_csv(os.path.join(output_dir, f"observed_schedule_RANGE_{start_date}_{end_date}.csv"), index=False)

    return planned_all, observed_all

# ----------------------
# Example usage (commented)
# ----------------------
# To use (example):
base = create_base_data(stops_csv="stops.csv", routes_csv="routes.csv", observed_csv="observation_data.csv")
planned_day, observed_day = generate_day_data("2025-10-08", base)
planned_range, observed_range = generate_range_data("2025-10-01", "2025-10-08", base)

# End of module
