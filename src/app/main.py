from fastapi import FastAPI
from src.app.routers import health, auth

app = FastAPI(title="Movie Booking API")

app.include_router(health.router)
app.include_router(auth.router)