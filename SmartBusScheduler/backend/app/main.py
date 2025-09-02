from fastapi import FastAPI
from .database import Base, engine
from .routers import customer, admin, driver, uploader

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartBus Scheduler Portal")

app.include_router(customer.router, prefix="/customer", tags=["Customer"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(driver.router, prefix="/driver", tags=["Driver"])
app.include_router(uploader.router, prefix="/uploader", tags=["Uploader"])
