from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db import AsyncSessionLocal
from src.app.models import Theatre
from src.app.schemas_showtime import TheatreCreate, TheatreRead, TheatreUpdate

router = APIRouter(prefix="/theatres", tags=["Theatres"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_model=TheatreRead)
async def create_theatre(theatre_in: TheatreCreate, db: AsyncSession = Depends(get_db)):
    theatre = Theatre(**theatre_in.dict())
    db.add(theatre)
    await db.commit()
    await db.refresh(theatre)
    return theatre


@router.get("/", response_model=list[TheatreRead])
async def list_theatres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Theatre))
    return result.scalars().all()


@router.get("/{theatre_id}", response_model=TheatreRead)
async def get_theatre(theatre_id: int, db: AsyncSession = Depends(get_db)):
    theatre = await db.get(Theatre, theatre_id)
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")
    return theatre


@router.put("/{theatre_id}", response_model=TheatreRead)
async def update_theatre(theatre_id: int, theatre_in: TheatreUpdate, db: AsyncSession = Depends(get_db)):
    theatre = await db.get(Theatre, theatre_id)
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")

    update_data = theatre_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(theatre, key, value)

    await db.commit()
    await db.refresh(theatre)
    return theatre


@router.delete("/{theatre_id}")
async def delete_theatre(theatre_id: int, db: AsyncSession = Depends(get_db)):
    theatre = await db.get(Theatre, theatre_id)
    if not theatre:
        raise HTTPException(status_code=404, detail="Theatre not found")

    await db.delete(theatre)
    await db.commit()
    return {"message": "Theatre deleted successfully"}
