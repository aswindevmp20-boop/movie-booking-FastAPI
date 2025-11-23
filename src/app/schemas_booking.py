from pydantic import BaseModel
from typing import List

class SeatReserveRequest(BaseModel):
    seat_ids: List[int]
