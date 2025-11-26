from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio

from src.app.db import AsyncSessionLocal
from src.app.models import Booking, ShowSeat, BookingStatus
from src.app.utils.redis_lock import release_lock

scheduler = AsyncIOScheduler()


async def cleanup_expired_locks():
    """
    Periodic background job that frees seats locked for too long.
    """
    print(f"[Scheduler] Running cleanup at {datetime.utcnow()}")
    async with AsyncSessionLocal() as db:
        expiry_time = datetime.utcnow() - timedelta(minutes=2)
        q = select(Booking).where(
            Booking.status == BookingStatus.PENDING,
            Booking.created_at < expiry_time
        )

        res = await db.execute(q)
        expired = res.scalars().all()

        if not expired:
            print("[Scheduler] No expired bookings found.")
            return

        for b in expired:
            seat = await db.get(ShowSeat, b.show_seat_id)
            if seat and seat.status == "locked":
                seat.status = "available"
                db.add(seat)
            b.status = BookingStatus.CANCELLED
            db.add(b)

            # release redis lock if available
            if b.lock_token:
                await release_lock(f"lock:show:{b.show_id}:seat:{b.show_seat_id}", b.lock_token)

        await db.commit()
        print(f"[Scheduler] Cleaned up {len(expired)} expired bookings.")


def start_scheduler():
    scheduler.add_job(cleanup_expired_locks, "interval", minutes=2, id="cleanup_job")
    scheduler.start()
