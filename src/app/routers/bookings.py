from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import logging

from src.app.db import AsyncSessionLocal
from src.app.models import ShowSeat, Booking, BookingStatus
from src.app.utils.redis_lock import acquire_lock, release_lock
from src.app.dependencies import get_current_user
from src.app.schemas_booking import SeatReserveRequest

router = APIRouter(prefix="/bookings", tags=["Bookings"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


def lock_key_for_seat(show_id: int, seat_id: int) -> str:
    return f"lock:show:{show_id}:seat:{seat_id}"


@router.post("/reserve")
async def reserve_seats(
    show_id: int,
    body: SeatReserveRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user)
):

    logging.warning(f"DEBUG: Incoming reserve for user={user}, show_id={show_id}, body={body.dict()}")

    seat_ids = body.seat_ids

    if not seat_ids:
        raise HTTPException(status_code=400, detail="No seats provided")

    locks: dict[int, str] = {}

    try:
        # 1️⃣ Acquire Redis Locks
        for seat_id in seat_ids:
            key = lock_key_for_seat(show_id, seat_id)
            token = await acquire_lock(key, ttl=60, timeout=3.0)

            if not token:
                raise HTTPException(
                    status_code=409,
                    detail=f"Seat {seat_id} is locked or unavailable"
                )

            locks[seat_id] = token

        # 2️⃣ DB Transaction
        async with db.begin():
            q = (
                select(ShowSeat)
                .where(ShowSeat.id.in_(seat_ids), ShowSeat.show_id == show_id)
                .with_for_update()
            )

            result = await db.execute(q)
            seats = result.scalars().all()

            if len(seats) != len(seat_ids):
                raise HTTPException(status_code=404, detail="Some seats do not exist")

            # 3️⃣ Ensure all seats are available
            for s in seats:
                if s.status != "available":
                    raise HTTPException(
                        status_code=409,
                        detail=f"Seat {s.id} is not available"
                    )

            # 4️⃣ Lock seat + create bookings
            created_bookings = []

            for s in seats:
                s.status = "locked"
                db.add(s)

                booking = Booking(
                    user_id=user["id"],
                    show_id=show_id,
                    show_seat_id=s.id,
                    status=BookingStatus.PENDING.value,
                    lock_token=locks.get(s.id)
                )
                db.add(booking)
                created_bookings.append(booking)

        # 5️⃣ Success response
        return {
            "message": "Seats reserved successfully",
            "reservation_id": str(uuid.uuid4()),
            "booking_ids": [b.id for b in created_bookings]
        }

    except HTTPException as e:
            # ✅ Handle known exceptions safely
            for seat_id, token in locks.items():
                await release_lock(lock_key_for_seat(show_id, seat_id), token)
            logging.error(f"HTTPException caught: {getattr(e, 'detail', str(e))}")
            raise

    except Exception as e:
        # ✅ Handle all other errors
        for seat_id, token in locks.items():
            await release_lock(lock_key_for_seat(show_id, seat_id), token)
        logging.error(f"General Exception caught: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



# ---------- Confirm reservation (simulate payment) ----------
@router.post("/confirm")
async def confirm_reservation(booking_ids: List[int], db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not booking_ids:
        raise HTTPException(status_code=400, detail="No bookings provided")

    async with db.begin():
        q = select(Booking).where(Booking.id.in_(booking_ids), Booking.user_id == user.id).with_for_update()
        res = await db.execute(q)
        bookings = res.scalars().all()
        if len(bookings) != len(booking_ids):
            raise HTTPException(status_code=404, detail="Some bookings not found")

        for bk in bookings:
            # ensure seat is in locked state and booking pending
            seat = await db.get(ShowSeat, bk.show_seat_id)
            if seat is None:
                raise HTTPException(status_code=404, detail="ShowSeat not found")
            if seat.status != "locked" or bk.status != BookingStatus.PENDING:
                raise HTTPException(status_code=409, detail=f"Seat {seat.id} not in locked state")

            # mark seat booked & booking confirmed
            seat.status = "booked"
            bk.status = BookingStatus.CONFIRMED
            db.add(seat)
            db.add(bk)

    # release redis locks for seats (use stored lock token)
    for bk in bookings:
        if bk.lock_token:
            await release_lock(lock_key_for_seat(bk.show_id, bk.show_seat_id), bk.lock_token)

    return {"message": "Booking confirmed", "bookings": [b.id for b in bookings]}


# ---------- Cancel reservation ----------
@router.post("/cancel")
async def cancel_reservation(booking_ids: List[int], db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not booking_ids:
        raise HTTPException(status_code=400, detail="No bookings provided")

    async with db.begin():
        q = select(Booking).where(Booking.id.in_(booking_ids), Booking.user_id == user.id).with_for_update()
        res = await db.execute(q)
        bookings = res.scalars().all()
        if not bookings:
            raise HTTPException(status_code=404, detail="Bookings not found")

        for bk in bookings:
            if bk.status == BookingStatus.CONFIRMED:
                raise HTTPException(status_code=400, detail="Cannot cancel confirmed booking via this endpoint")

            # set seat back to available
            seat = await db.get(ShowSeat, bk.show_seat_id)
            if seat:
                seat.status = "available"
                db.add(seat)

            bk.status = BookingStatus.CANCELLED
            db.add(bk)

    # release redis locks if token present
    for bk in bookings:
        if bk.lock_token:
            await release_lock(lock_key_for_seat(bk.show_id, bk.show_seat_id), bk.lock_token)

    return {"message": "Cancelled", "bookings": [b.id for b in bookings]}


# ---------- User bookings ----------
@router.get("/me")
async def my_bookings(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    q = select(Booking).where(Booking.user_id == user.id)
    res = await db.execute(q)
    return res.scalars().all()
