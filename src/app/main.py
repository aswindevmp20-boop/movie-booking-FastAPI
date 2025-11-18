from fastapi import FastAPI
from src.app.routers import health

app = FastAPI(title="Movie Booking - API")

app.include_router(health.router)

# placeholder - other routers will be included in Day2
