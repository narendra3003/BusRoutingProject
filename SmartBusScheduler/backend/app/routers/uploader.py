from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
from ..schemas import ObservationUpload, ObservationResponse, OptimizeRequest, OptimizeResponse, OptimizedTrip
from ..utils import get_current_user
from datetime import datetime, date, time, timedelta
# from .transit_optimizer import load_and_prepare_data, nsga2, decode_solution, assign_drivers, compute_demand, generate_linear_trips
from typing import List, Optional
from ..models import Route, BusData, CrewData
import pandas as pd
import tempfile
import os

router = APIRouter()

# 3. Upload passenger density and bus data
@router.post("/observations/upload", response_model=ObservationResponse)
def upload_observation(data: ObservationUpload, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")

    obs = models.ObservationData(
        bus_no=data.bus_no,
        route_id=data.route_id,
        stop_id=data.stop_id,
        boarding_count=data.boarding_count,
        alighting_count=data.alighting_count,
        timestamp=data.timestamp
    )
    db.add(obs)
    db.commit()
    return {"status": "success", "message": "Observation uploaded"}

# 4. Trigger automated schedule plan
@router.post("/schedules/optimize", response_model=OptimizeResponse)
def optimize_schedule(request: OptimizeRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="uploader only")

    day_start = datetime.combine(request.date, time(0, 0))
    day_end = datetime.combine(request.date, time(23, 59, 59))

    total_boardings = db.query(models.ObservationData).filter(
        models.ObservationData.route_id == request.route_id,
        models.ObservationData.timestamp >= day_start,
        models.ObservationData.timestamp <= day_end
    ).with_entities(models.ObservationData.boarding_count).all()

    demand = sum(r[0] for r in total_boardings) if total_boardings else 0
    # naive bus count: 40 pax per bus per window
    bus_count = max(1, demand // 40) if demand else 1

    return OptimizeResponse(
        route_id=request.route_id,
        date=request.date,
        optimized_trips=[OptimizedTrip(trip_id=223, start_time=time(7, 0), end_time=time(7, 45), bus_count=bus_count)]
    )

@router.get("/admin/optimize/test")
def admin_optimize_test():
    return {"status": "ok"}
import os
import tempfile
import pandas as pd
import numpy as np
import math
import random
import ast
from datetime import timedelta
from fastapi import APIRouter, UploadFile, File
import heapq

router = APIRouter()

# ============================================================
# CONFIG
# ============================================================

SAME_ROUTE_COOLING = 10
ROUTE_CHANGE_OVERHEAD = 20

SHIFT_DURATION = 8
TOTAL_SHIFTS = 3


# ============================================================
# DATA LOADER
# ============================================================

def load_data(routes_path, buses_path, drivers_path, stops_path, observations_path):

    routes_df = pd.read_csv(routes_path)
    buses_df = pd.read_csv(buses_path)
    drivers_df = pd.read_csv(drivers_path)
    stops_df = pd.read_csv(stops_path)
    obs_df = pd.read_csv(observations_path)

    obs_df["observed_departure"] = pd.to_datetime(
        obs_df["observed_departure"],
        errors="coerce"
    )

    obs_df = obs_df.dropna(subset=["observed_departure"])

    obs_df["boarding_in"] = pd.to_numeric(
        obs_df["boarding_in"], errors="coerce"
    ).fillna(0)

    obs_df["boarding_out"] = pd.to_numeric(
        obs_df["boarding_out"], errors="coerce"
    ).fillna(0)

    return routes_df, buses_df, drivers_df, stops_df, obs_df


# ============================================================
# ROUTE REAL TRIP TIME
# ============================================================

def compute_route_trip_times(routes_df):

    route_trip_time = {}

    for _, row in routes_df.iterrows():

        stop_times = row["stop_time"]

        # If coming from CSV (string)
        if isinstance(stop_times, str):
            stop_times = ast.literal_eval(stop_times)

        # If coming from DB (already list)
        elif isinstance(stop_times, list):
            stop_times = stop_times

        else:
            raise ValueError(
                f"Invalid stop_time format for route {row['route_id']}"
            )

        if not stop_times:
            continue

        total_time = max(stop_times)
        route_trip_time[row["route_id"]] = int(total_time)

    return route_trip_time


# ============================================================
# TRANSITION TIME
# ============================================================

def compute_transition_time(current_route, new_route):

    if current_route is None:
        return 0

    if current_route == new_route:
        return SAME_ROUTE_COOLING

    return ROUTE_CHANGE_OVERHEAD


# ============================================================
# DRIVER SHIFT SYSTEM
# ============================================================

def assign_driver_shifts(drivers_df):

    driver_matrix = {}

    for _, row in drivers_df.iterrows():

        shift_count = random.choice([1, 2])
        shifts = random.sample(range(TOTAL_SHIFTS), shift_count)

        driver_matrix[row["driver_id"]] = {
            "shifts": shifts,
            "available_at": None
        }

    return driver_matrix


def is_driver_available(driver_info, current_time):

    current_shift = current_time.hour // SHIFT_DURATION

    if current_shift not in driver_info["shifts"]:
        return False

    if driver_info["available_at"] is not None and driver_info["available_at"] > current_time:
        return False

    return True


# ============================================================
# SLIDING DEMAND WINDOW
# ============================================================

def update_sliding_demand(
    obs_df,
    demand_matrix,
    last_check_time,
    current_time
):

    window_end = current_time + timedelta(hours=1)

    new_entries = obs_df[
        (obs_df["observed_departure"] >= last_check_time) &
        (obs_df["observed_departure"] < window_end)
    ]

    for route_id in new_entries["route_id"].unique():
        route_data = new_entries[new_entries["route_id"] == route_id]
        net = (route_data["boarding_in"] - route_data["boarding_out"]).clip(lower=0).sum()
        demand_matrix[route_id] = demand_matrix.get(route_id, 0) + int(net)

    expired_entries = obs_df[
        (obs_df["observed_departure"] >= last_check_time - timedelta(hours=1)) &
        (obs_df["observed_departure"] < current_time)
    ]

    for route_id in expired_entries["route_id"].unique():
        route_data = expired_entries[expired_entries["route_id"] == route_id]
        net = (route_data["boarding_in"] - route_data["boarding_out"]).clip(lower=0).sum()
        demand_matrix[route_id] = max(
            0,
            demand_matrix.get(route_id, 0) - int(net)
        )

    return demand_matrix


# ============================================================
# MAIN SIMULATION
# ============================================================

def simulate_dynamic(
    routes_df,
    buses_df,
    drivers_df,
    obs_df,
    start_time
):
    route_trip_time = compute_route_trip_times(routes_df)

    # Initialize bus state
    bus_matrix = {
        row["bus_id"]: {
            "capacity": int(row["max_capacity"]),
            "current_route": None,
            "available_at": start_time
        }
        for _, row in buses_df.iterrows()
    }

    # Initialize drivers
    driver_matrix = assign_driver_shifts(drivers_df)

    schedule_records = []
    demand_matrix = {}

    current_time = start_time
    last_check_time = start_time
    trip_id_counter = 1

    simulation_end_time = obs_df["observed_departure"].max() + timedelta(hours=2)

    # ============================================================
    # FIXED 5-MINUTE TIME STEP LOOP
    # ============================================================
    while current_time <= simulation_end_time:

        # --------------------------------------------------------
        # 1️⃣ Update demand (sliding window)
        # --------------------------------------------------------
        demand_matrix = update_sliding_demand(
            obs_df,
            demand_matrix,
            last_check_time,
            current_time
        )
        last_check_time = current_time

        total_demand = sum(demand_matrix.values())

        # --------------------------------------------------------
        # 2️⃣ Get ONLY FREE resources at this moment
        # --------------------------------------------------------
        available_buses = sorted(
            [
                b for b, info in bus_matrix.items()
                if info["available_at"] <= current_time
            ],
            key=lambda x: bus_matrix[x]["capacity"],
            reverse=True
        )

        available_drivers = sorted(
            [
                d for d, info in driver_matrix.items()
                if is_driver_available(info, current_time)
            ]
        )

        # --------------------------------------------------------
        # 3️⃣ Scheduling decision (every 5 minutes)
        # --------------------------------------------------------
        if total_demand > 0 and available_buses and available_drivers:

            routes_sorted = sorted(
                demand_matrix.items(),
                key=lambda x: x[1],
                reverse=True
            )

            for route_id, route_demand in routes_sorted:

                if route_demand <= 0:
                    continue

                if not available_buses or not available_drivers:
                    break

                # Take currently free resources ONLY
                bus_id = available_buses.pop(0)
                driver_id = available_drivers.pop(0)

                capacity = bus_matrix[bus_id]["capacity"]
                previous_route = bus_matrix[bus_id]["current_route"]

                transition = compute_transition_time(
                    previous_route,
                    route_id
                )

                departure = current_time + timedelta(minutes=transition)
                arrival = departure + timedelta(
                    minutes=route_trip_time[route_id]
                )

                # Demand snapshot
                route_demand_before = demand_matrix[route_id]
                total_demand_before = sum(demand_matrix.values())

                served = min(capacity, route_demand_before)
                demand_matrix[route_id] -= served

                route_demand_after = demand_matrix[route_id]
                total_demand_after = sum(demand_matrix.values())

                bus_utilization = (
                    round((served / capacity) * 100, 2)
                    if capacity > 0 else 0
                )

                # Active resources (currently busy)
                active_buses = len([
                    b for b in bus_matrix.values()
                    if b["available_at"] > current_time
                ])

                active_drivers = len([
                    d for d in driver_matrix.values()
                    if d["available_at"] and d["available_at"] > current_time
                ])

                schedule_records.append({
                    "trip_id": f"T{trip_id_counter}",
                    "route_id": route_id,
                    "bus_id": bus_id,
                    "assigned_driver_id": driver_id,

                    "planned_start": departure,
                    "planned_end": arrival,

                    "passengers_served": served,
                    "bus_capacity": capacity,
                    "bus_utilization_percent": bus_utilization,

                    "route_demand_before": route_demand_before,
                    "route_demand_after": route_demand_after,
                    "total_demand_before": total_demand_before,
                    "total_demand_after": total_demand_after,

                    "available_buses_count": len(available_buses) + 1,
                    "available_drivers_count": len(available_drivers) + 1,

                    "active_buses": active_buses,
                    "active_drivers": active_drivers,

                    "bus_previous_route": previous_route,
                    "transition_time_minutes": transition,

                    "driver_shift_blocks": driver_matrix[driver_id]["shifts"]
                })

                trip_id_counter += 1

                # Mark resources busy until arrival
                bus_matrix[bus_id]["available_at"] = arrival
                bus_matrix[bus_id]["current_route"] = route_id
                driver_matrix[driver_id]["available_at"] = arrival

        # --------------------------------------------------------
        # 4️⃣ Advance time strictly by 5 minutes
        # --------------------------------------------------------
        current_time += timedelta(minutes=5)

        # Early stop condition
        if sum(demand_matrix.values()) == 0 and all(
            b["available_at"] <= current_time for b in bus_matrix.values()
        ):
            break

    return pd.DataFrame(schedule_records)


def test_schedule(schedule_data, output_file=None):
    """
    Validate schedule, generate multi-sheet Excel report.
    """
    if output_file is None:
        output_file = os.path.join(tempfile.gettempdir(), "bus_schedule_report.xlsx")

    MIN_COOLING_TIME = 10
    MIN_DIRECTION_CHANGE_TIME = 20

    data = pd.DataFrame(schedule_data)

    if "assigned_driver_id" in data.columns:
        data = data.rename(columns={"assigned_driver_id": "driver_id"})

    # Datetime parsing
    data["planned_start"] = pd.to_datetime(data["planned_start"], errors="coerce")
    data["planned_end"] = pd.to_datetime(data["planned_end"], errors="coerce")
    data = data.sort_values(by=["bus_id", "planned_start"])

    # Helper
    def check_overlap(start1, end1, start2, end2):
        return start1 < end2 and start2 < end1

    # Violations
    violations = []

    # Invalid time window
    invalid_trips = data[data["planned_end"] <= data["planned_start"]]
    for _, row in invalid_trips.iterrows():
        violations.append({
            "type": "Invalid Time Window",
            "message": f"Trip {row.trip_id} has invalid time window."
        })

    # Bus checks
    for bus, group in data.groupby("bus_id"):
        group = group.sort_values("planned_start")
        for i in range(len(group) - 1):
            current = group.iloc[i]
            next_trip = group.iloc[i + 1]

            # Overlap
            if check_overlap(current.planned_start, current.planned_end,
                             next_trip.planned_start, next_trip.planned_end):
                violations.append({
                    "type": "Bus Overlap",
                    "message": f"Bus {bus}: {current.trip_id} overlaps {next_trip.trip_id}"
                })

            gap = (next_trip.planned_start - current.planned_end).total_seconds() / 60

            # Cooling
            if gap < MIN_COOLING_TIME:
                violations.append({
                    "type": "Cooling Time Violation",
                    "message": f"Bus {bus}: insufficient cooling between "
                               f"{current.trip_id} and {next_trip.trip_id}"
                })

            # Direction change
            current_base = str(current.route_id).split("_")[0]
            next_base = str(next_trip.route_id).split("_")[0]
            if current_base == next_base and current.route_id != next_trip.route_id:
                if gap < MIN_DIRECTION_CHANGE_TIME:
                    violations.append({
                        "type": "Direction Change Violation",
                        "message": f"Bus {bus}: insufficient turnaround between "
                                   f"{current.trip_id} and {next_trip.trip_id}"
                    })

    # Driver overlap
    for driver, group in data.groupby("driver_id"):
        group = group.sort_values("planned_start")
        for i in range(len(group) - 1):
            current = group.iloc[i]
            next_trip = group.iloc[i + 1]
            if check_overlap(current.planned_start, current.planned_end,
                             next_trip.planned_start, next_trip.planned_end):
                violations.append({
                    "type": "Driver Overlap",
                    "message": f"Driver {driver}: {current.trip_id} overlaps {next_trip.trip_id}"
                })

    violations_df = pd.DataFrame(violations)

    # Driver activity
    driver_activity = data[[
        "driver_id", "trip_id", "route_id", "bus_id", "planned_start", "planned_end",
        "passengers_served"
    ]].sort_values(["driver_id", "planned_start"])

    # Bus utilization
    bus_utilization = data.groupby("bus_id").apply(
        lambda x: pd.Series({
            "Total Trips": len(x),
            "Total Operating Minutes": (x["planned_end"] - x["planned_start"]).dt.total_seconds().sum() / 60,
            "Total Passengers": x["passengers_served"].sum(),
            "Average Utilization (%)": x["bus_utilization_percent"].mean() if "bus_utilization_percent" in x.columns else None
        })
    ).reset_index()

    # Route summary
    route_summary = data.groupby("route_id").agg(
        total_trips=("trip_id", "count"),
        unique_buses=("bus_id", "nunique"),
        unique_drivers=("driver_id", "nunique"),
        total_passengers=("passengers_served", "sum"),
        avg_demand_before=("route_demand_before", "mean"),
        avg_demand_after=("route_demand_after", "mean")
    ).reset_index()

    # System demand snapshot
    demand_summary = pd.DataFrame({
        "Metric": [
            "Average Total Demand Before Dispatch",
            "Average Total Demand After Dispatch",
            "Max Total Demand Before Dispatch",
            "Max Total Demand After Dispatch"
        ],
        "Value": [
            data["total_demand_before"].mean(),
            data["total_demand_after"].mean(),
            data["total_demand_before"].max(),
            data["total_demand_after"].max()
        ]
    })

    # Bus idle time
    idle_records = []
    for bus, group in data.groupby("bus_id"):
        group = group.sort_values("planned_start")
        total_idle = 0
        for i in range(len(group) - 1):
            idle = (group.iloc[i + 1].planned_start - group.iloc[i].planned_end).total_seconds() / 60
            if idle > 0:
                total_idle += idle
        idle_records.append({"bus_id": bus, "total_idle_minutes": total_idle})
    idle_df = pd.DataFrame(idle_records)

    # Resource pressure
    resource_pressure = data[[
        "trip_id", "available_buses_count", "available_drivers_count",
        "active_buses", "active_drivers"
    ]].copy()

    # Save to Excel
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        data.to_excel(writer, sheet_name="Raw Schedule", index=False)
        violations_df.to_excel(writer, sheet_name="Violations", index=False)
        driver_activity.to_excel(writer, sheet_name="Driver Activity", index=False)
        bus_utilization.to_excel(writer, sheet_name="Bus Utilization", index=False)
        route_summary.to_excel(writer, sheet_name="Route Summary", index=False)
        idle_df.to_excel(writer, sheet_name="Bus Idle Time", index=False)
        demand_summary.to_excel(writer, sheet_name="Demand Summary", index=False)
        resource_pressure.to_excel(writer, sheet_name="Resource Pressure", index=False)

    return output_file  # Return path for download

# ============================================================
# FASTAPI ENDPOINT
# ============================================================


@router.post("/admin/optimize-and-report")
async def admin_optimize(
    observations: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Now:
    - routes, buses, drivers → from DB
    - only observations → from CSV
    """

    # ============================================================
    # 1️⃣ LOAD OBSERVATION FILE (ONLY FILE INPUT)
    # ============================================================

    tmpdir = tempfile.gettempdir()
    obs_path = os.path.join(tmpdir, "observations.csv")

    with open(obs_path, "wb") as f:
        f.write(await observations.read())

    obs_df = pd.read_csv(obs_path)

    # Datatype correction
    obs_df["observed_departure"] = pd.to_datetime(
        obs_df["observed_departure"], errors="coerce"
    )

    obs_df["boarding_in"] = pd.to_numeric(
        obs_df["boarding_in"], errors="coerce"
    ).fillna(0).astype(int)

    obs_df["boarding_out"] = pd.to_numeric(
        obs_df["boarding_out"], errors="coerce"
    ).fillna(0).astype(int)

    obs_df["route_id"] = obs_df["route_id"].astype(str)

    obs_df = obs_df.dropna(subset=["observed_departure"])

    # Keep only required simulation columns
    obs_df = obs_df[[
        "route_id",
        "observed_departure",
        "boarding_in",
        "boarding_out"
    ]]

    # ============================================================
    # 2️⃣ LOAD ROUTES FROM DB
    # ============================================================

    routes_query = db.query(Route).all()

    routes_df = pd.DataFrame([
        {
            "route_id": str(route.route_code),   # route_code used as route_id
            "stop_time": list(route.stop_time) if route.stop_time else []
        }
        for route in routes_query
    ])

    # Ensure correct datatype
    routes_df["route_id"] = routes_df["route_id"].astype(str)

    # ============================================================
    # 3️⃣ LOAD BUSES FROM DB
    # ============================================================

    buses_query = db.query(BusData).all()

    buses_df = pd.DataFrame([
        {
            "bus_id": str(bus.bus_no),   # bus_no used as bus_id
            "max_capacity": int(bus.max_capacity or 0)
        }
        for bus in buses_query
    ])

    buses_df["max_capacity"] = buses_df["max_capacity"].astype(int)

    # ============================================================
    # 4️⃣ LOAD DRIVERS FROM DB
    # ============================================================

    crew_query = db.query(CrewData).all()

    drivers_df = pd.DataFrame([
        {
            "driver_id": str(crew.crew_id)
        }
        for crew in crew_query
    ])

    # ============================================================
    # 5️⃣ VALIDATION CHECKS
    # ============================================================

    if routes_df.empty:
        return {"status": "error", "message": "No routes found in DB"}

    if buses_df.empty:
        return {"status": "error", "message": "No buses found in DB"}

    if drivers_df.empty:
        return {"status": "error", "message": "No drivers found in DB"}

    if obs_df.empty:
        return {"status": "error", "message": "Observation file empty or invalid"}

    # ============================================================
    # 6️⃣ RUN SIMULATION
    # ============================================================

    start_time = obs_df["observed_departure"].min()

    schedule_df = simulate_dynamic(
        routes_df,
        buses_df,
        drivers_df,
        obs_df,
        start_time
    )

    # ============================================================
    # 7️⃣ FORMAT OUTPUT
    # ============================================================

    if not schedule_df.empty:
        schedule_df["planned_start"] = schedule_df[
            "planned_start"
        ].dt.strftime("%Y-%m-%d %H:%M:%S")

        schedule_df["planned_end"] = schedule_df[
            "planned_end"
        ].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    preview_json = schedule_df.to_dict(orient="records")

    # Generate Excel report
    output_file = os.path.join(tmpdir, "bus_schedule_report.xlsx")
    test_schedule(preview_json, output_file)

    return {
        "status": "success",
        "total_trips": len(schedule_df),
        "preview": preview_json,
        "excel_download": f"/admin/download-report?file={os.path.basename(output_file)}"
    }

@router.get("/admin/download-report")
def download_report(file: str):
    tmpdir = tempfile.gettempdir()
    file_path = os.path.join(tmpdir, file)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file
    )

# code for transit opimizer endpoint (commented out for now, as it requires the full optimization pipeline to be implemented)
# @router.post("/admin/optimize")
# async def admin_optimize(
#     stops: UploadFile = File(...),
#     routes: UploadFile = File(...),
#     routes_timeplan: UploadFile = File(...),
#     buses: UploadFile = File(...),
#     drivers: UploadFile = File(...),
#     observations: UploadFile = File(...),
#     pop_size: Optional[int] = Form(30),
#     ngen: Optional[int] = Form(40)
# ):
#     """
#     Full optimization pipeline:
#     1. Save uploaded CSVs
#     2. Load & preprocess
#     3. Compute demand
#     4. Generate trips
#     5. Run NSGA-II
#     6. Decode schedule
#     7. Assign drivers
#     """

#     tmpdir = tempfile.gettempdir()

#     paths = {}
#     for name, file in {
#         "stops": stops,
#         "routes": routes,
#         "buses": buses,
#         "drivers": drivers,
#         "observations": observations
#     }.items():
#         path = os.path.join(tmpdir, f"{name}.csv")
#         with open(path, "wb") as f:
#             f.write(await file.read())
#         paths[name] = path

#     # -----------------------------
#     # 1️⃣ LOAD DATA
#     # -----------------------------
#     stops_df, routes_df, buses_df, drivers_df, obs_df = \
#         load_and_prepare_data(
#             paths["stops"],
#             paths["routes"],
#             paths["buses"],
#             paths["drivers"],
#             paths["observations"]
#         )

#     # -----------------------------
#     # 2️⃣ COMPUTE DEMAND
#     # -----------------------------
#     demand_df = compute_demand(obs_df)

#     # -----------------------------
#     # 3️⃣ GENERATE TRIPS
#     # -----------------------------
#     trips = generate_linear_trips(demand_df)

#     # -----------------------------
#     # 4️⃣ RUN NSGA-II
#     # -----------------------------
#     best_genome = nsga2(
#         trips,
#         buses_df,
#         generations=ngen,
#         pop_size=pop_size
#     )

#     # -----------------------------
#     # 5️⃣ DECODE BUS SCHEDULE
#     # -----------------------------
#     schedule_df = decode_solution(best_genome, trips)

#     # -----------------------------
#     # 6️⃣ ASSIGN DRIVERS
#     # -----------------------------
#     final_schedule = assign_drivers(
#         schedule_df,
#         drivers_df
#     )

#     # -----------------------------
#     # 7️⃣ RESPONSE
#     # -----------------------------
#     preview = final_schedule.to_dict(orient="records")

#     return {
#         "status": "success",
#         "total_trips": len(trips),
#         "scheduled_trips": len(final_schedule),
#         "preview": preview
#     }

