from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class BaggageType(Enum):
    STANDARD = "standard"
    OVERSIZED = "oversized"
    SPECIAL = "special"
    GATE_CHECK = "gate_check"


class SpecialItemType(Enum):
    GOLF_CLUBS = "golf_clubs"
    SKIS = "skis"
    MUSICAL_INSTRUMENT = "musical_instrument"
    WHEELCHAIR = "wheelchair"
    SPORTING_EQUIPMENT = "sporting_equipment"


@dataclass
class BaggageItem:
    weight: float
    length: float
    width: float
    height: float
    baggage_type: BaggageType
    passenger_id: str
    flight_id: str
    special_item_type: Optional[SpecialItemType] = None
    fragile: bool = False
    hazardous: bool = False
    loading_instructions: Optional[str] = None
    compartment_preference: Optional[str] = None

    def calculate_volume(self) -> float:
        """Calculate baggage volume in cubic meters"""
        return (self.length * self.width * self.height) / 1000000  # Convert cm³ to m³

    def is_oversized(self) -> bool:
        """Check if baggage exceeds standard dimensions"""
        # 737 cargo door: 117cm x 165cm
        return (
            self.length > 150
            or self.width > 100
            or self.height > 80
            or self.weight > 32
        )

    def get_loading_priority(self) -> int:
        """Get loading priority (1=highest, 5=lowest)"""
        if self.baggage_type == BaggageType.GATE_CHECK:
            return 1
        elif self.special_item_type:
            return 2
        elif self.fragile:
            return 3
        elif self.is_oversized():
            return 4
        else:
            return 5


@dataclass
class FlightBaggageManifest:
    flight_id: str
    baggage_items: list[BaggageItem]
    total_weight: float = 0.0
    total_volume: float = 0.0
    forward_compartment_weight: float = 0.0
    aft_compartment_weight: float = 0.0

    def __post_init__(self):
        self.calculate_totals()

    def calculate_totals(self):
        """Calculate total weight and volume"""
        self.total_weight = sum(item.weight for item in self.baggage_items)
        self.total_volume = sum(item.calculate_volume() for item in self.baggage_items)
