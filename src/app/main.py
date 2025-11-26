from fastapi import FastAPI
from src.app.routers import health, auth, movies, theatres, shows, seats, show_seats, bookings, admin, admin_cleanup
from src.app.scheduler import start_scheduler

app = FastAPI(
    title="Movie Booking API",
    version="1.0",
    description="Backend service for movie ticket booking",
    swagger_ui_parameters={"persistAuthorization": True},
)

# ✅ Start background scheduler on app startup
@app.on_event("startup")
async def startup_event():
    start_scheduler()
    print("[App] Background scheduler started.")


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(theatres.router)
app.include_router(shows.router)
app.include_router(seats.router)
app.include_router(show_seats.router)
app.include_router(bookings.router)
app.include_router(admin.router)
app.include_router(admin_cleanup.router)
