from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.app.dependencies import get_current_user, require_role

from src.app.db import AsyncSessionLocal
from src.app.models import Theatre, Seat

router = APIRouter(prefix="/seats", tags=["Seats"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/theatre/{theatre_id}/generate", dependencies=[Depends(require_role("admin"))])
async def generate_seats(theatre_id: int, db: AsyncSession = Depends(get_db)):
    theatre = await db.get(Theatre, theatre_id)
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")

    # Check if seats already exist
    result = await db.execute(select(Seat).where(Seat.theatre_id == theatre_id))
    existing = result.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Seats already generated")

    rows = "ABCDEFGHIJ"
    seats_per_row = 10

    for row in rows:
        for num in range(1, seats_per_row + 1):
            seat = Seat(theatre_id=theatre_id, row=row, number=num)
            db.add(seat)

    await db.commit()
    return {"message": "Seats generated successfully"}


@router.get("/theatre/{theatre_id}", dependencies=[Depends(require_role("admin"))])
async def list_theatre_seats(theatre_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Seat).where(Seat.theatre_id == theatre_id))
    return result.scalars().all()
