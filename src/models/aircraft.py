from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Boeing737Specs:
    empty_weight: float = 41000.0  # kg
    max_takeoff_weight: float = 79000.0  # kg
    max_landing_weight: float = 66000.0  # kg
    max_zero_fuel_weight: float = 62730.0  # kg
    forward_cg_limit: float = 0.15  # MAC percentage
    aft_cg_limit: float = 0.35  # MAC percentage
    cargo_compartments: Dict[str, Dict] = None

    def __post_init__(self):
        if self.cargo_compartments is None:
            self.cargo_compartments = {
                "forward": {"max_weight": 3400.0, "arm": 8.5},
                "aft": {"max_weight": 2300.0, "arm": 25.8},
            }


@dataclass
class LoadItem:
    weight: float
    arm: float  # distance from datum
    zone: str


@dataclass
class FlightConfiguration:
    aircraft: Boeing737Specs
    passenger_count: int
    passenger_weight_avg: float = 75.6  # kg
    carry_on_weight_avg: float = 7.6  # kg
    checked_baggage_weight_avg: float = 15.9  # kg
    crew_count: int = 5
    crew_weight_avg: float = 85.0  # kg
    fuel_weight: float = 0.0
    cargo_items: List[LoadItem] = None

    def __post_init__(self):
        if self.cargo_items is None:
            self.cargo_items = []
