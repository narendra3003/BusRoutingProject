import random
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Route,
    Bus,
    Driver,
    ScheduleTrip,
    DriverLeave,
    Notification,
    Override,
    TripLiveStatus,
    LeaveStatus,
    TripStatus,
    NotificationType
)

db: Session = SessionLocal()


# =========================
# CONFIG
# =========================
DAYS = 5
TRIPS_PER_ROUTE_PER_DAY = 4


# =========================
# FETCH BASE DATA
# =========================
routes = db.query(Route).all()
buses = db.query(Bus).all()
drivers = db.query(Driver).all()

print(f"Routes: {len(routes)}, Buses: {len(buses)}, Drivers: {len(drivers)}")


# =========================
# HELPER
# =========================
def random_time():
    base_hour = random.choice(range(6, 22))
    minute = random.choice([0, 15, 30, 45])
    return time(base_hour, minute)


# =========================
# 1. CREATE DRIVER LEAVES
# =========================
print("Creating driver leaves...")

for _ in range(15):
    driver = random.choice(drivers)
    start = datetime.now().date() + timedelta(days=random.randint(1, 10))
    end = start + timedelta(days=random.randint(1, 3))

    leave = DriverLeave(
        driver_id=driver.user_id,
        start_date=start,
        end_date=end,
        reason="Personal work",
        status=random.choice([
            LeaveStatus.pending,
            LeaveStatus.granted,
            LeaveStatus.rejected
        ])
    )
    db.add(leave)

db.commit()


# =========================
# 2. CREATE SCHEDULE TRIPS
# =========================
print("Creating schedule trips...")

schedule_trips = []

for day in range(DAYS):
    trip_date = datetime.now().date() + timedelta(days=day)

    for route in routes:
        used_times = set()

        for _ in range(TRIPS_PER_ROUTE_PER_DAY):

            start_time = random_time()

            # avoid duplicate route+time
            if start_time in used_times:
                continue
            used_times.add(start_time)

            bus = random.choice(buses)
            driver = random.choice(drivers)

            trip = ScheduleTrip(
                route_id=route.id,
                trip_date=trip_date,
                start_time=start_time,
                bus_id=bus.id,
                driver_id=driver.user_id,
                status=random.choice([
                    TripStatus.scheduled,
                    TripStatus.completed,
                    TripStatus.delayed
                ])
            )

            db.add(trip)
            schedule_trips.append(trip)

db.commit()


# =========================
# 3. CREATE LIVE STATUS
# =========================
print("Creating live trip status...")

for trip in schedule_trips[:50]:  # limit for demo
    live = TripLiveStatus(
        trip_id=trip.id,
        current_stop_id=None,
        delay_minutes=random.randint(0, 10),
        last_lat=19.0 + random.random(),
        last_lon=72.0 + random.random()
    )
    db.add(live)

db.commit()


# =========================
# 4. CREATE OVERRIDES
# =========================
print("Creating overrides...")

for trip in random.sample(schedule_trips, min(20, len(schedule_trips))):
    new_driver = random.choice(drivers)
    new_bus = random.choice(buses)

    override = Override(
        trip_id=trip.id,
        old_driver_id=trip.driver_id,
        new_driver_id=new_driver.user_id,
        old_bus_id=trip.bus_id,
        new_bus_id=new_bus.id,
        reason="Emergency reassignment",
        created_by=new_driver.user_id  # assuming driver user exists
    )

    db.add(override)

db.commit()


# =========================
# 5. CREATE NOTIFICATIONS
# =========================
print("Creating notifications...")

for driver in drivers[:50]:
    notif = Notification(
        user_id=driver.user_id,
        title="Trip Update",
        message="Your schedule has been updated",
        type=random.choice([
            NotificationType.override,
            NotificationType.system,
            NotificationType.leave
        ]),
        is_read=random.choice([True, False])
    )
    db.add(notif)

db.commit()


# =========================
# DONE
# =========================
print("✅ Dummy runtime data created successfully!")