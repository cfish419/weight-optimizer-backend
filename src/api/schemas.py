from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class BaggageBase(BaseModel):
    tag_number: str
    weight_kg: float = Field(..., gt=0, le=32)  # Southwest's weight limit
    length_cm: float
    width_cm: float
    height_cm: float
    passenger_name: str
    priority: str
    category: str
    status: str

class BaggageCreate(BaggageBase):
    flight_id: str

class BaggageResponse(BaggageBase):
    id: str
    flight_id: str

    class Config:
        from_attributes = True

class FlightBase(BaseModel):
    flight_number: str
    departure: str
    arrival: str
    aircraft_type: str
    departure_time: datetime
    estimated_passengers: int

class FlightCreate(FlightBase):
    pass

class FlightResponse(FlightBase):
    id: str
    baggage_items: List[BaggageResponse] = []

    class Config:
        from_attributes = True

class OptimizationRequest(BaseModel):
    flight_id: str

class BaggagePosition(BaseModel):
    tag_number: str
    position_x: float
    position_y: float
    position_z: float
    loading_order: int
    zone: str

class OptimizationResponse(BaseModel):
    flight_id: str
    total_weight: float
    center_of_gravity: dict
    fuel_efficiency_gain: float
    baggage_positions: List[BaggagePosition]
    loading_instructions: List[str]