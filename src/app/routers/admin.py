from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Literal

from src.app.db import AsyncSessionLocal
from src.app.models import User, Movie, Theatre, Show, Booking, BookingStatus
from src.app.dependencies import get_current_user, require_role
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])


# Dependency to get DB
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/overview", dependencies=[Depends(require_role("admin"))])
async def admin_overview(db: AsyncSession = Depends(get_db)):

    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_movies = (await db.execute(select(func.count(Movie.id)))).scalar()
    total_theatres = (await db.execute(select(func.count(Theatre.id)))).scalar()
    total_bookings = (await db.execute(select(func.count(Booking.id)))).scalar()

    confirmed = (
        await db.execute(
            select(func.count()).where(Booking.status == BookingStatus.CONFIRMED)
        )
    ).scalar()

    cancelled = (
        await db.execute(
            select(func.count()).where(Booking.status == BookingStatus.CANCELLED)
        )
    ).scalar()

    # === Top 3 Most Booked Movies ===
    movie_query = (
        select(Movie.title, func.count(Booking.id).label("booking_count"))
        .join(Show, Show.movie_id == Movie.id)
        .join(Booking, Booking.show_id == Show.id)
        .where(Booking.status == BookingStatus.CONFIRMED)
        .group_by(Movie.id)
        .order_by(func.count(Booking.id).desc())
        .limit(3)
    )
    top_movies_result = await db.execute(movie_query)
    top_movies = [
        {"title": m.title, "bookings": m.booking_count}
        for m in top_movies_result
    ]

    # === Top 3 Theatres by Bookings ===
    theatre_query = (
        select(Theatre.name, func.count(Booking.id).label("booking_count"))
        .join(Show, Show.theatre_id == Theatre.id)
        .join(Booking, Booking.show_id == Show.id)
        .where(Booking.status == BookingStatus.CONFIRMED)
        .group_by(Theatre.id)
        .order_by(func.count(Booking.id).desc())
        .limit(3)
    )
    top_theatres_result = await db.execute(theatre_query)
    top_theatres = [
        {"name": t.name, "bookings": t.booking_count}
        for t in top_theatres_result
    ]

    return {
            "summary": {
                "total_users": total_users,
                "total_movies": total_movies,
                "total_theatres": total_theatres,
                "total_bookings": total_bookings,
                "confirmed_bookings": confirmed,
                "cancelled_bookings": cancelled,
            },
            "insights": {
                "top_movies": top_movies,
                "top_theatres": top_theatres
            }
        }


@router.get("/bookings", dependencies=[Depends(require_role("admin"))])
async def list_all_bookings(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Lists all bookings with joined user/movie/theatre info for admin panel."""

    stmt = (
        select(
            Booking.id.label("booking_id"),
            User.email.label("user_email"),
            Movie.title.label("movie_title"),
            Theatre.name.label("theatre_name"),
            Show.start_time.label("show_time"),
            Booking.status.label("status")
        )
        .join(User, User.id == Booking.user_id)
        .join(Show, Show.id == Booking.show_id)
        .join(Movie, Movie.id == Show.movie_id)
        .join(Theatre, Theatre.id == Show.theatre_id)
        .order_by(Booking.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "booking_id": r.booking_id,
            "user": r.user_email,
            "movie": r.movie_title,
            "theatre": r.theatre_name,
            "status": r.status,
            "show_time": r.show_time,
        }
        for r in rows
    ]


class PromoteRequest(BaseModel):
    user_id: int
    new_role: Literal["admin", "customer"]


@router.post("/promote", dependencies=[Depends(require_role("admin"))])
async def promote_user(data: PromoteRequest, db: AsyncSession = Depends(get_db)):
    """Allows an admin to promote or demote a user."""

    user = await db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == data.new_role:
        raise HTTPException(
            status_code=400,
            detail=f"User is already {data.new_role}"
        )

    user.role = data.new_role
    db.add(user)
    await db.commit()

    return {"message": f"User role updated to {data.new_role}", "user_id": user.id}
