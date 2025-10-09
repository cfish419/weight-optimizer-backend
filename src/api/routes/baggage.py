from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Baggage
from ..schemas import BaggageCreate, BaggageResponse

router = APIRouter()


@router.get("", response_model=List[BaggageResponse])
async def get_baggage_items(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Get all baggage items with pagination"""
    items = db.query(Baggage).offset(skip).limit(limit).all()
    return items


@router.get("/{tag_number}", response_model=BaggageResponse)
async def get_baggage(tag_number: str, db: Session = Depends(get_db)):
    """Get a specific baggage item by tag number"""
    baggage = db.query(Baggage).filter(Baggage.tag_number == tag_number).first()
    if baggage is None:
        raise HTTPException(status_code=404, detail="Baggage not found")
    return baggage


@router.post("", response_model=BaggageResponse)
async def create_baggage(baggage: BaggageCreate, db: Session = Depends(get_db)):
    """Create a new baggage item"""
    db_baggage = Baggage(**baggage.model_dump())
    db.add(db_baggage)
    db.commit()
    db.refresh(db_baggage)
    return db_baggage
