from fastapi import FastAPI
# from .routers import admin, customer, driver, uploader, auth
from .routers import (public_routes, 
                      auth, 
                      public_stops, 
                      public_schedule, 
                      notifications, 
                      driver, 
                      driver_profile, 
                      driver_trips, 
                      driver_leaves,
                      admin_buses,
                      admin_drivers,
                      admin_override,
                      admin_schedule,
                        admin_routes,
                        admin_stops,
                        analytics,
                       admin_leaves,
                       admin_dispatch,
                       admin_schedule2,
                       admin_schedule3,
                       admin_routeStops
)
from .database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SmartBus API", version="1.0")

#allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables at startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Register Routers to align with spec:
# - Customer endpoints at root (no '/customer' prefix)
# - Uploader endpoints at root (no '/uploader' prefix)
# - Admin under '/admin'
# - Drivers under '/drivers'
# - Auth under '/auth'
# app.include_router(customer.router, tags=["Customer"])

app.include_router(auth.router, prefix="/auth", tags=["Auth Routes"])

app.include_router(public_routes.router, prefix="/public", tags=["Public Routes"])
app.include_router(public_schedule.router, prefix="/schedule", tags=["Public Schedule"])
app.include_router(public_stops.router, prefix="/stops", tags=["Public Stops"])

app.include_router(driver.router, prefix="/drivers", tags=["Driver"])
app.include_router(driver_profile.router, prefix="/driver/profile", tags=["Driver Profile"])
app.include_router(driver_trips.router, prefix="/driver/trips", tags=["Driver Trips"])
app.include_router(driver_leaves.router, prefix="/driver/leaves", tags=["Driver Leaves"])

app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(admin_drivers.router, prefix="/admin/drivers", tags=["Admin Drivers"])
app.include_router(admin_buses.router, prefix="/admin/buses", tags=["Admin Buses"])
app.include_router(admin_routes.router, prefix="/admin/routes", tags=["Admin Routes"])
app.include_router(admin_stops.router, prefix="/admin/stops", tags=["Admin Stops"])
app.include_router(admin_schedule2.router, prefix="/admin/schedule", tags=["Admin Schedule"])
app.include_router(admin_leaves.router, prefix="/admin/leaves", tags=["Admin Leaves"])
app.include_router(admin_dispatch.router, prefix="/admin/dispatch", tags=["Admin Dispatch"])
app.include_router(admin_override.router, prefix="/admin/dispatch/overrides", tags=["Admin Override"])
app.include_router(admin_schedule3.router, prefix="/admin/schedule/optimize", tags=["Admin Schedule Optimization"])
app.include_router(admin_routeStops.router, prefix="/admin/route-stops", tags=["Admin Route Stops"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

@app.get("/", tags=["Health"])
def root():
    return {"message": "SmartBus API is running"}
