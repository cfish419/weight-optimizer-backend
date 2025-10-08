from fastapi import APIRouter, HTTPException
from src.models.baggage import Baggage, BaggageCreate
from src.services.baggage_service import BaggageService

router = APIRouter()
baggage_service = BaggageService()

@router.post("/", response_model=Baggage)
async def create_baggage(baggage: BaggageCreate):
    """Create a new baggage entry with measurements"""
    return await baggage_service.create_baggage(baggage)

@router.get("/{baggage_id}", response_model=Baggage)
async def get_baggage(baggage_id: str):
    """Get baggage details by ID"""
    baggage = await baggage_service.get_baggage(baggage_id)
    if not baggage:
        raise HTTPException(status_code=404, detail="Baggage not found")
    return baggage

@router.get("/flight/{flight_id}", response_model=list[Baggage])
async def get_flight_baggage(flight_id: str):
    """Get all baggage for a specific flight"""
    return await baggage_service.get_flight_baggage(flight_id)