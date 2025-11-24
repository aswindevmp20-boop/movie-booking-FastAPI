from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db import AsyncSessionLocal
from src.app.models import Show, Seat, ShowSeat

router = APIRouter(prefix="/show-seats", tags=["Show Seats"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/{show_id}/generate")
async def generate_show_seats(show_id: int, db: AsyncSession = Depends(get_db)):
    show = await db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    # Check if already generated
    result = await db.execute(select(ShowSeat).where(ShowSeat.show_id == show_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Show seats already generated")

    # Get theatre seats
    result = await db.execute(select(Seat).where(Seat.theatre_id == show.theatre_id))
    theatre_seats = result.scalars().all()

    if not theatre_seats:
        raise HTTPException(status_code=400, detail="Theatre seats not generated yet")

    # Copy to show seats
    for ts in theatre_seats:
        seat = ShowSeat(
            show_id=show_id,
            row=ts.row,
            number=ts.number,
            status="available"
        )
        db.add(seat)

    await db.commit()
    return {"message": "Show seats generated"}


@router.get("/{show_id}")
async def list_show_seats(show_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ShowSeat).where(ShowSeat.show_id == show_id))
    return result.scalars().all()

# Seat Availability for a show
@router.get("/{show_id}/seats")
async def get_show_seats(show_id: int, db: AsyncSession = Depends(get_db)):
    """Return all seats for a given show with their current status."""
    result = await db.execute(select(ShowSeat).where(ShowSeat.show_id == show_id))
    seats = result.scalars().all()
    if not seats:
        raise HTTPException(status_code=404, detail="Show not found or no seats available")

    return [
        {"id": s.id, "row": s.row, "number": s.number, "status": s.status}
        for s in seats
    ]