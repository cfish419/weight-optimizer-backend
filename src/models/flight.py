from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FlightCreate(BaseModel):
    flight_number: str
    aircraft_type: str
    departure_time: datetime
    arrival_time: datetime
    max_cargo_weight: float  # in kg
    max_cargo_volume: float  # in cubic meters

class Flight(FlightCreate):
    id: str
    status: str
    current_weight: float = 0
    current_volume: float = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True