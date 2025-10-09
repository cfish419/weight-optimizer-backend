from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.schemas.baggage_schemas import BaggageItem, BaggageType, SpecialItemType
from data.repositories.baggage_repository import BaggageRepository


class BaggageService:
    """Service for managing baggage tracking and optimization"""

    def __init__(self):
        self.repository = BaggageRepository()

    def add_baggage(self, baggage_data: Dict[str, Any]) -> str:
        """Add new baggage item with validation"""
        baggage_id = str(uuid4())

        # Create baggage item from data
        baggage_item = BaggageItem(
            weight=baggage_data["weight"],
            length=baggage_data["length"],
            width=baggage_data["width"],
            height=baggage_data["height"],
            baggage_type=BaggageType(baggage_data.get("baggage_type", "standard")),
            passenger_id=baggage_data["passenger_id"],
            flight_id=baggage_data["flight_id"],
            special_item_type=(
                SpecialItemType(baggage_data["special_item_type"])
                if baggage_data.get("special_item_type")
                else None
            ),
            fragile=baggage_data.get("fragile", False),
            hazardous=baggage_data.get("hazardous", False),
            loading_instructions=baggage_data.get("loading_instructions"),
            compartment_preference=baggage_data.get("compartment_preference"),
        )

        # Validate baggage constraints
        validation_result = self.validate_baggage(baggage_item)
        if not validation_result["valid"]:
            raise ValueError(
                f"Baggage validation failed: {validation_result['errors']}"
            )

        # Store in repository
        self.repository.save_baggage(baggage_id, baggage_item)

        return baggage_id

    def update_baggage(self, baggage_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing baggage item"""
        existing_baggage = self.repository.get_baggage(baggage_id)
        if not existing_baggage:
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(existing_baggage, key):
                setattr(existing_baggage, key, value)

        # Re-validate
        validation_result = self.validate_baggage(existing_baggage)
        if not validation_result["valid"]:
            return False

        self.repository.save_baggage(baggage_id, existing_baggage)
        return True

    def get_flight_baggage(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all baggage for a specific flight"""
        return self.repository.get_flight_baggage(flight_id)

    def validate_baggage(self, baggage_item: BaggageItem) -> Dict[str, Any]:
        """Validate baggage against 737 constraints"""
        errors = []

        # Weight limits
        if baggage_item.weight > 50:  # kg
            errors.append("Exceeds maximum weight limit (50kg)")

        # Dimension limits (737 cargo door constraints)
        if baggage_item.length > 200:  # cm
            errors.append("Length exceeds cargo door limit (200cm)")
        if baggage_item.width > 150:  # cm
            errors.append("Width exceeds cargo door limit (150cm)")
        if baggage_item.height > 120:  # cm
            errors.append("Height exceeds cargo door limit (120cm)")

        # Special item validations
        if baggage_item.special_item_type == SpecialItemType.GOLF_CLUBS:
            if baggage_item.length < 100:
                errors.append("Golf clubs must be at least 100cm long")

        return {"valid": len(errors) == 0, "errors": errors}

    def optimize_compartment_loading(self, flight_id: str) -> Dict[str, Any]:
        """Optimize baggage distribution across compartments"""
        baggage_items = self.get_flight_baggage(flight_id)

        # Sort by loading priority
        sorted_items = sorted(
            baggage_items, key=lambda x: BaggageItem(**x).get_loading_priority()
        )

        forward_items = []
        aft_items = []
        forward_weight = 0.0
        aft_weight = 0.0

        # Distribute based on weight balance and constraints
        for item_data in sorted_items:
            item = BaggageItem(**item_data)

            # Prefer forward compartment for heavy items (stability)
            if forward_weight < 3400 and (
                item.weight > 20 or forward_weight <= aft_weight
            ):
                forward_items.append(item_data)
                forward_weight += item.weight
            elif aft_weight < 2300:
                aft_items.append(item_data)
                aft_weight += item.weight
            else:
                # Overflow handling
                if forward_weight < aft_weight and forward_weight < 3400:
                    forward_items.append(item_data)
                    forward_weight += item.weight
                else:
                    aft_items.append(item_data)
                    aft_weight += item.weight

        return {
            "forward_compartment": {
                "items": forward_items,
                "total_weight": forward_weight,
                "item_count": len(forward_items),
            },
            "aft_compartment": {
                "items": aft_items,
                "total_weight": aft_weight,
                "item_count": len(aft_items),
            },
        }
