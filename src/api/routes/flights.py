from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...db.database import get_db
from ...db.models import Flight, Baggage
from ..schemas import FlightResponse, FlightCreate

router = APIRouter()

@router.get("", response_model=List[FlightResponse])
async def get_flights(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Get all flights with pagination"""
    flights = db.query(Flight).offset(skip).limit(limit).all()
    return flights

@router.get("/{flight_id}", response_model=FlightResponse)
async def get_flight(flight_id: str, db: Session = Depends(get_db)):
    """Get a specific flight by ID"""
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if flight is None:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight

@router.post("", response_model=FlightResponse)
async def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    """Create a new flight"""
    db_flight = Flight(**flight.model_dump())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight