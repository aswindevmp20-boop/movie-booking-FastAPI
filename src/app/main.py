from fastapi import FastAPI
from src.app.routers import health, auth, movies, theatres, shows, seats, show_seats, bookings, admin

app = FastAPI(
    title="Movie Booking API",
    version="1.0",
    description="Backend service for movie ticket booking",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(theatres.router)
app.include_router(shows.router)
app.include_router(seats.router)
app.include_router(show_seats.router)
app.include_router(bookings.router)
app.include_router(admin.router)
