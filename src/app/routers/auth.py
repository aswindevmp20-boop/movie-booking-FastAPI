from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.db import AsyncSessionLocal
from src.app.models import User
from src.app.schemas import UserCreate, UserRead, Token, UserLogin
from src.app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    query = await db.execute(
        select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
    )
    exist = query.scalars().first()
    if exist:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(user_in.password)

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).where(User.email == user_in.email))
    user = query.scalars().first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    return Token(access_token=access, refresh_token=refresh)
