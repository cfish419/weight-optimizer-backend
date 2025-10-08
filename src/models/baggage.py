from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class LabelColor(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    BLUE = "blue"

class BaggageCreate(BaseModel):
    flight_id: str
    mass: float = Field(..., gt=0)  # in kg
    volume: float = Field(..., gt=0)  # in cubic meters
    image_url: Optional[str] = None

class Baggage(BaggageCreate):
    id: str
    density: float  # calculated from mass and volume
    label_color: Optional[LabelColor] = None
    loading_order: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True