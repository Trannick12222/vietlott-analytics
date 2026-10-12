from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import date
from src.config.settings import LotteryType

class DrawResponse(BaseModel):
    id: int
    lottery_type: str
    draw_number: int
    draw_date: date
    numbers: List[int]
    jackpot_2: Optional[int] = None
    source: str

class FetchRequest(BaseModel):
    lottery_type: LotteryType
    limit: int = 100

class CustomPoolRequest(BaseModel):
    lottery_type: LotteryType
    numbers: List[int]
    ticket_count: int = 8

class SuitabilityRequest(BaseModel):
    numbers: List[int]


