from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.app.dependencies import get_current_user, require_role

from src.app.db import AsyncSessionLocal
from src.app.models import Movie
from src.app.schemas_movie import MovieCreate, MovieRead, MovieUpdate

router = APIRouter(prefix="/movies", tags=["Movies"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/", response_model=MovieRead, dependencies=[Depends(require_role("admin"))])
async def create_movie(movie_in: MovieCreate, db: AsyncSession = Depends(get_db)):

    movie = Movie(**movie_in.dict())
    db.add(movie)
    await db.commit()
    await db.refresh(movie)

    return movie


@router.get("/", response_model=list[MovieRead], dependencies=[Depends(require_role("admin"))])
async def list_movies(
    db: AsyncSession = Depends(get_db),
    search: str | None = None,
    skip: int = 0,
    limit: int =20,
    sort_by: str = Query("id", regex="^(id|title|duration|rating)$"),
    order: str = Query("asc", regex="^(asc|desc)$")
):
    query = select(Movie)

    if search:
        query = query.where(Movie.title.ilike(f"%{search}%"))

    if order == "asc":
        query = query.order_by(getattr(Movie, sort_by).asc()) 
    else:
        query = query.order_by(getattr(Movie, sort_by).desc())

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    movies = result.scalars().all()

    return movies


@router.get("/{movie_id}", response_model=MovieRead, dependencies=[Depends(require_role("admin"))])
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(Movie, movie_id)

    if not movie:
        raise HTTPException (status_code=404, detail = "Movie not found")

    return movie

@router.put("/{movie_id}", response_model=MovieRead, dependencies=[Depends(require_role("admin"))])
async def update_movie(movie_id: int, movie_in: MovieUpdate, db: AsyncSession = Depends(get_db)):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    update_data = movie_in.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)

    return movie


@router.delete("/{movie_id}", dependencies=[Depends(require_role("admin"))])
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detial="Movie not found")

    await db.delete(movie)
    await db.commit()

    return {"message":"Movie deleted successfully"}