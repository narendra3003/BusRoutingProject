from fastapi import FastAPI
from .routers import admin, customer, driver, uploader, auth
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
app.include_router(customer.router, tags=["Customer"])
app.include_router(uploader.router, tags=["Uploader"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(driver.router, prefix="/drivers", tags=["Driver"])

@app.get("/", tags=["Health"])
def root():
    return {"message": "SmartBus API is running"}
