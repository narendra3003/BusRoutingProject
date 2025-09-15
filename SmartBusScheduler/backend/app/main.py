from fastapi import FastAPI
from .routers import admin, customer, driver, uploader, auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SmartBus API", version="1.0")

# list of allowed origins
origins = [
    "http://localhost:3000",   # your React dev frontend
    # add production domain here later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/ping", tags=["Health"])
def ping():
    return {"message": "pong"}

# Register Routers
app.include_router(customer.router, prefix="/customer", tags=["Customer"])
app.include_router(uploader.router, prefix="/uploader", tags=["Uploader"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(driver.router, prefix="/drivers", tags=["Driver"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "SmartBus API is running"}
