from fastapi import FastAPI
from .routers import admin, customer, driver, uploader, auth

app = FastAPI(title="SmartBus API", version="1.0")

# Register Routers
app.include_router(customer.router, prefix="/customer", tags=["Customer"])
app.include_router(uploader.router, prefix="/uploader", tags=["Uploader"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(driver.router, prefix="/drivers", tags=["Driver"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "SmartBus API is running"}
