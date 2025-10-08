from typing import List, Optional
import numpy as np
from datetime import datetime
import uuid

from src.db.database import SessionLocal
from src.db.models import BaggageModel
from src.models.baggage import Baggage, BaggageCreate, LabelColor

class BaggageService:
    def __init__(self):
        self.db = SessionLocal()

    async def create_baggage(self, baggage: BaggageCreate) -> Baggage:
        """Create a new baggage entry with measurements"""
        density = baggage.mass / baggage.volume
        db_baggage = BaggageModel(
            id=str(uuid.uuid4()),
            flight_id=baggage.flight_id,
            mass=baggage.mass,
            volume=baggage.volume,
            density=density,
            image_url=baggage.image_url
        )
        
        self.db.add(db_baggage)
        await self.db.commit()
        await self.db.refresh(db_baggage)
        return db_baggage

    async def get_baggage(self, baggage_id: str) -> Optional[Baggage]:
        """Retrieve baggage by ID"""
        return await self.db.query(BaggageModel).filter(BaggageModel.id == baggage_id).first()

    async def get_flight_baggage(self, flight_id: str) -> List[Baggage]:
        """Get all baggage for a specific flight"""
        return await self.db.query(BaggageModel).filter(BaggageModel.flight_id == flight_id).all()

    async def update_loading_order(self, baggage_id: str, order: int, color: LabelColor) -> Baggage:
        """Update the loading order and color label for a baggage item"""
        baggage = await self.get_baggage(baggage_id)
        if not baggage:
            return None
        
        baggage.loading_order = order
        baggage.label_color = color
        baggage.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(baggage)
        return baggage