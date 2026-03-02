from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date as DateType, datetime, time as TimeType
from ..database import get_db
from .. import models
from ..schemas import OverrideRequest, OverrideResponse, AdminScheduleResponse, AdminTrip, KPIResponse
from ..utils import get_current_user
from fastapi import UploadFile, File
import csv
import io

router = APIRouter()

# 5. Schedule overrides
@router.post("/schedules/override", response_model=OverrideResponse)
def apply_override(request: OverrideRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    ov = models.AdminOverride(
        trip_id=request.trip_id,
        delta_minutes=request.delta_minutes,
        effective_date=request.date,
        reason=request.reason
    )
    db.add(ov)
    db.commit()
    return {"status": "success", "message": "Override applied"}

# 6. Admin view past/future trips
@router.get("/schedules", response_model=AdminScheduleResponse)
def view_schedules(route_id: int, date: DateType, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    trips = db.query(models.Trip).filter(
        models.Trip.route_id == route_id,
        models.Trip.date == date
    ).all()

    admin_trips = []
    for trip in trips:
        if not trip.stop_times:
            continue
        starts = [st.arrival_time for st in trip.stop_times if st.arrival_time]
        ends = [st.departure_time for st in trip.stop_times if st.departure_time]
        if not starts or not ends:
            continue
        admin_trips.append(AdminTrip(trip_id=trip.trip_id, start_time=min(starts), end_time=max(ends)))

    return AdminScheduleResponse(route_id=route_id, date=date, trips=admin_trips)

# 7. KPI calculations
@router.get("/kpis", response_model=KPIResponse)
def get_kpis(date: DateType, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    # simple computations
    trips = db.query(models.Trip).filter(models.Trip.date == date).all()
    buses_used = len({t.service_id for t in trips if t.service_id}) or 0

    # total boardings on the day (all routes)
    day_start = datetime.combine(date, TimeType(0, 0))
    day_end = datetime.combine(date, TimeType(23, 59, 59))
    boardings = db.query(models.ObservationData).filter(
        models.ObservationData.timestamp >= day_start,
        models.ObservationData.timestamp <= day_end
    ).with_entities(models.ObservationData.boarding_count).all()
    total_boardings = sum(r[0] for r in boardings) if boardings else 0

    # naive metrics
    avg_wait_time = 5.0  # placeholder avg wait estimate (minutes)
    capacity = max(1, buses_used) * 40
    load_factor = round(min(1.0, (total_boardings / capacity) if capacity else 0.0), 2)

    return KPIResponse(date=date, avg_wait_time=avg_wait_time, buses_used=buses_used, load_factor=load_factor)


# /stops/upload-csv post, put, delete endpoints for admin to manage stops data feed

# /admin/stops/${stopData.stop_id} delete endpoint to delete a stop by id
@router.delete("/stops/{stop_id}")
def delete_stop(stop_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    stop = db.query(models.Stop).filter(models.Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    db.delete(stop)
    db.commit()
    return {"status": "success", "message": f"Stop {stop_id} deleted"}

@router.get("/stops/{stop_id}")
def get_stop(
    stop_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # to check we reach this
    print("get_stop endpoint called with stop_id:", stop_id)
    print("current_user:", current_user)

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    stop = db.query(models.Stop).filter(models.Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    return {
        "stop_id": stop.stop_id,
        "stop_code": stop.stop_code,
        "stop_name": stop.stop_name,
        "stop_lat": stop.stop_lat,
        "stop_lon": stop.stop_lon
    }

# router put for stops by id
@router.put("/stops/{stop_id}")
def update_stop(stop_id: int, stop_data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    stop = db.query(models.Stop).filter(models.Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=404, detail="Stop not found")

    for key, value in stop_data.items():
        setattr(stop, key, value)

    db.commit()
    return {"status": "success", "message": f"Stop {stop_id} updated"}

router = APIRouter(prefix="/admin", tags=["Admin Routes"])


# -----------------------------
# CREATE ROUTE
# -----------------------------
@router.post("/routes")
def create_route(
    route_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    stops_list = route_data.get("stops", [])

    # Validate stops exist
    existing_stops = (
        db.query(models.Stop.stop_id)
        .filter(models.Stop.stop_id.in_(stops_list))
        .all()
    )
    existing_stop_ids = [s[0] for s in existing_stops]

    if set(stops_list) != set(existing_stop_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more stop_ids do not exist",
        )

    new_route = models.Route(
        route_short_name=route_data.get("route_short_name"),
        route_long_name=route_data.get("route_long_name"),
        stops=stops_list,
    )

    db.add(new_route)
    db.commit()
    db.refresh(new_route)

    return {"status": "success", "route_id": new_route.route_id}


# -----------------------------
# GET ROUTE BY ID
# -----------------------------
@router.get("/routes/{route_id}")
def get_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    route = db.query(models.Route).filter(models.Route.route_id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    return {
        "route_id": route.route_id,
        "route_short_name": route.route_short_name,
        "route_long_name": route.route_long_name,
        "stops": route.stops,
    }


# -----------------------------
# UPDATE ROUTE
# -----------------------------
@router.put("/routes/{route_id}")
def update_route(
    route_id: int,
    route_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    route = db.query(models.Route).filter(models.Route.route_id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    stops_list = route_data.get("stops", route.stops)

    # Validate stops exist
    existing_stops = (
        db.query(models.Stop.stop_id)
        .filter(models.Stop.stop_id.in_(stops_list))
        .all()
    )
    existing_stop_ids = [s[0] for s in existing_stops]

    if set(stops_list) != set(existing_stop_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more stop_ids do not exist",
        )

    route.route_short_name = route_data.get("route_short_name", route.route_short_name)
    route.route_long_name = route_data.get("route_long_name", route.route_long_name)
    route.stops = stops_list

    db.commit()

    return {"status": "success", "message": f"Route {route_id} updated"}


# -----------------------------
# DELETE ROUTE
# -----------------------------
@router.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    route = db.query(models.Route).filter(models.Route.route_id == route_id).first()

    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    db.delete(route)
    db.commit()

    return {"status": "success", "message": f"Route {route_id} deleted"}

# ------------------------------------------------
# CSV UPLOAD
# ------------------------------------------------
@router.post("/bus/upload-csv")
def upload_bus_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    for row in reader:
        existing_bus = db.query(models.BusData).filter(
            models.BusData.bus_no == row["bus_no"]
        ).first()

        if existing_bus:
            continue  # skip duplicates

        new_bus = models.BusData(
            bus_no=row["bus_no"],
            passenger_seats=int(row["passenger_seats"]),
            passenger_cap=int(row["passenger_cap"]),
        )
        db.add(new_bus)

    db.commit()

    return {"status": "success", "message": "CSV uploaded successfully"}
    

# ------------------------------------------------
# ADD BUS (NORMAL FORM)
# ------------------------------------------------
@router.post("/bus")
def add_bus(
    bus_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    existing = db.query(models.BusData).filter(
        models.BusData.bus_no == bus_data["bus_no"]
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Bus number already exists")

    new_bus = models.BusData(
        bus_no=bus_data["bus_no"],
        passenger_seats=bus_data["passenger_seats"],
        passenger_cap=bus_data["passenger_cap"],
    )

    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)

    return {"status": "success", "bus_id": new_bus.bus_id}


# ------------------------------------------------
# SEARCH BUS BY ID
# ------------------------------------------------
@router.get("/bus/{bus_id}")
def get_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    bus = db.query(models.BusData).filter(
        models.BusData.bus_id == bus_id
    ).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    return {
        "bus_id": bus.bus_id,
        "bus_no": bus.bus_no,
        "passenger_seats": bus.passenger_seats,
        "passenger_cap": bus.passenger_cap,
    }


# ------------------------------------------------
# UPDATE BUS
# ------------------------------------------------
@router.put("/bus/{bus_id}")
def update_bus(
    bus_id: int,
    bus_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    bus = db.query(models.BusData).filter(
        models.BusData.bus_id == bus_id
    ).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    # Check unique bus_no
    if bus_data["bus_no"] != bus.bus_no:
        exists = db.query(models.BusData).filter(
            models.BusData.bus_no == bus_data["bus_no"]
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Bus number already exists")

    bus.bus_no = bus_data["bus_no"]
    bus.passenger_seats = bus_data["passenger_seats"]
    bus.passenger_cap = bus_data["passenger_cap"]

    db.commit()

    return {"status": "success", "message": f"Bus {bus_id} updated"}


# ------------------------------------------------
# DELETE BUS
# ------------------------------------------------
@router.delete("/bus/{bus_id}")
def delete_bus(
    bus_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    bus = db.query(models.BusData).filter(
        models.BusData.bus_id == bus_id
    ).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    db.delete(bus)
    db.commit()

    return {"status": "success", "message": f"Bus {bus_id} deleted"}