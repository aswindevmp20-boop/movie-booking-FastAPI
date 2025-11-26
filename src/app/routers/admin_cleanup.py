from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from src.app.db import AsyncSessionLocal
from src.app.models import Booking, ShowSeat, BookingStatus
from src.app.utils.redis_lock import release_lock
from src.app.dependencies import require_role

router = APIRouter(prefix="/admin", tags=["Admin Maintenance"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/cleanup-locks", dependencies=[Depends(require_role("admin"))])
async def cleanup_expired_locks(db: AsyncSession = Depends(get_db)):
    """
    Frees up seats that were locked (pending bookings) but expired after 2 minutes.
    Admin-only endpoint, simulates scheduled cleanup job.
    """
    expiry_time = datetime.utcnow() - timedelta(minutes=2)
    q = select(Booking).where(
        Booking.status == BookingStatus.PENDING,
        Booking.created_at < expiry_time
    )

    res = await db.execute(q)
    expired = res.scalars().all()
    if not expired:
        return {"message": "No expired locks found"}

    unlocked = []
    for booking in expired:
        seat = await db.get(ShowSeat, booking.show_seat_id)
        if seat and seat.status == "locked":
            seat.status = "available"
            db.add(seat)
        booking.status = BookingStatus.CANCELLED
        db.add(booking)

        # Optional: release Redis lock if still active
        await release_lock(f"lock:show:{booking.show_id}:seat:{booking.show_seat_id}", booking.lock_token or "")
        unlocked.append(booking.id)

    await db.commit()
    return {"message": "Expired locks cleaned up", "unlocked_bookings": unlocked}
