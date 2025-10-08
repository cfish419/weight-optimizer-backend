from fastapi import APIRouter, HTTPException
from src.models.flight import Flight, FlightCreate
from src.services.flight_service import FlightService

router = APIRouter()
flight_service = FlightService()

@router.post("/", response_model=Flight)
async def create_flight(flight: FlightCreate):
    """Create a new flight entry"""
    return await flight_service.create_flight(flight)

@router.get("/{flight_id}", response_model=Flight)
async def get_flight(flight_id: str):
    """Get flight details by ID"""
    flight = await flight_service.get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight

@router.get("/", response_model=list[Flight])
async def get_flights():
    """Get all active flights"""
    return await flight_service.get_active_flights()