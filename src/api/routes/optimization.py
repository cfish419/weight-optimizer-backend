import random  # For demo purposes

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import Baggage, Flight
from ..schemas import OptimizationRequest, OptimizationResponse

router = APIRouter()


@router.post("/calculate-loading-plan", response_model=OptimizationResponse)
async def calculate_loading_plan(
    request: OptimizationRequest, db: Session = Depends(get_db)
):
    """Calculate optimal loading plan for a flight"""
    # Get flight and its baggage
    flight = db.query(Flight).filter(Flight.id == request.flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    baggage_items = (
        db.query(Baggage).filter(Baggage.flight_id == request.flight_id).all()
    )
    if not baggage_items:
        raise HTTPException(
            status_code=400, detail="No baggage items found for this flight"
        )

    # For demo purposes, generate a simple loading plan
    # In reality, this would use your optimization algorithm
    total_weight = sum(bag.weight_kg for bag in baggage_items)
    positions = []
    instructions = []

    for idx, bag in enumerate(baggage_items):
        # Simple demo positioning - replace with actual optimization
        pos = {
            "tag_number": bag.tag_number,
            "position_x": random.uniform(0, 30),  # Length of aircraft
            "position_y": random.uniform(0, 3.5),  # Width of aircraft
            "position_z": random.uniform(0, 2),  # Height of cargo hold
            "loading_order": idx + 1,
            "zone": f"Zone {(idx % 3) + 1}",
        }
        positions.append(pos)
        instructions.append(
            f"Load bag {bag.tag_number} in {pos['zone']} at position {idx + 1}"
        )

    return OptimizationResponse(
        flight_id=request.flight_id,
        total_weight=total_weight,
        center_of_gravity={
            "x": 15.0,  # Demo values - replace with actual calculations
            "y": 1.75,
            "z": 1.0,
        },
        fuel_efficiency_gain=1.5,  # Demo value
        baggage_positions=positions,
        loading_instructions=instructions,
    )
