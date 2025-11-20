from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# ------- THEATRE --------
class TheatreBase(BaseModel):
    name: str
    location: str


class TheatreCreate(TheatreBase):
    pass


class TheatreUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None


class TheatreRead(TheatreBase):
    id: int

    class Config:
        orm_mode = True


# ------- SHOW --------
class ShowBase(BaseModel):
    movie_id: int
    theatre_id: int
    start_time: datetime
    end_time: datetime


class ShowCreate(ShowBase):
    pass


class ShowUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None


class ShowRead(ShowBase):
    id: int

    class Config:
        orm_mode = True
