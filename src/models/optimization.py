from pydantic import BaseModel
from datetime import datetime
from typing import List
from .baggage import Baggage

class LoadingPlan(BaseModel):
    flight_id: str
    baggage_items: List[Baggage]
    total_weight: float
    total_volume: float
    center_of_gravity: dict
    fuel_efficiency_gain: float  # estimated fuel savings in percentage
    created_at: datetime
    
    class Config:
        from_attributes = True