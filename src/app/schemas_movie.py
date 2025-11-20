from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MovieBase(BaseModel):
    title: str
    description: Optional[str] = None
    duration: int
    release_date: Optional[datetime] = None
    rating: Optional[str] = None


class MovieCreate(MovieBase):
    pass


class MovieUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    release_date: Optional[datetime] = None
    rating: Optional[str] = None


class MovieRead(MovieBase):
    id: int

    class Config:
        orm_mode = True
