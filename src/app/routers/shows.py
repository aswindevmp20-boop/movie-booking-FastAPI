from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.app.dependencies import get_current_user, require_role

from src.app.db import AsyncSessionLocal
from src.app.models import Show, Movie, Theatre
from src.app.schemas_showtime import ShowCreate, ShowRead, ShowUpdate

router = APIRouter(prefix="/shows", tags=["Shows"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ----- Create Show -----
@router.post("/", response_model=ShowRead, dependencies=[Depends(require_role("admin"))])
async def create_show(show_in: ShowCreate, db: AsyncSession = Depends(get_db)):

    # ensure movie exists
    if not (await db.get(Movie, show_in.movie_id)):
        raise HTTPException(status_code=404, detail="Movie does not exist")

    # ensure theatre exists
    if not (await db.get(Theatre, show_in.theatre_id)):
        raise HTTPException(status_code=404, detail="Theatre does not exist")

    show = Show(**show_in.dict())
    db.add(show)
    await db.commit()
    await db.refresh(show)

    return show


# ----- List Shows -----
@router.get("/", response_model=list[ShowRead], dependencies=[Depends(require_role("admin"))])
async def list_shows(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Show))
    return result.scalars().all()


# ----- Get Show -----
@router.get("/{show_id}", response_model=ShowRead, dependencies=[Depends(require_role("admin"))])
async def get_show(show_id: int, db: AsyncSession = Depends(get_db)):
    show = await db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return show


# ----- Update Show -----
@router.put("/{show_id}", response_model=ShowRead, dependencies=[Depends(require_role("admin"))])
async def update_show(show_id: int, show_in: ShowUpdate, db: AsyncSession = Depends(get_db)):
    show = await db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    update_data = show_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(show, key, value)

    await db.commit()
    await db.refresh(show)
    return show


# ----- Delete Show -----
@router.delete("/{show_id}", dependencies=[Depends(require_role("admin"))])
async def delete_show(show_id: int, db: AsyncSession = Depends(get_db)):
    show = await db.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    await db.delete(show)
    await db.commit()

    return {"message": "Show deleted successfully"}
