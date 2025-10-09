from dataclasses import dataclass
from enum import Enum
from typing import Dict

class Boeing737Variant(Enum):
    B737_700 = "737-700"
    B737_800 = "737-800"
    B737_900 = "737-900"
    B737_MAX7 = "737-MAX7"
    B737_MAX8 = "737-MAX8"
    B737_MAX9 = "737-MAX9"

@dataclass
class AircraftSpecs:
    variant: Boeing737Variant
    empty_weight: float  # kg
    max_takeoff_weight: float  # kg
    max_landing_weight: float  # kg
    max_fuel_capacity: float  # kg
    passenger_capacity: int
    forward_cargo_capacity: float  # kg
    aft_cargo_capacity: float  # kg
    cg_forward_limit: float  # % MAC
    cg_aft_limit: float  # % MAC
    optimal_cg: float  # % MAC

# Aircraft specifications database
AIRCRAFT_SPECS: Dict[Boeing737Variant, AircraftSpecs] = {
    Boeing737Variant.B737_700: AircraftSpecs(
        variant=Boeing737Variant.B737_700,
        empty_weight=37500,
        max_takeoff_weight=70080,
        max_landing_weight=60550,
        max_fuel_capacity=20894,
        passenger_capacity=149,
        forward_cargo_capacity=2900,
        aft_cargo_capacity=1900,
        cg_forward_limit=15.0,
        cg_aft_limit=35.0,
        optimal_cg=27.5
    ),
    Boeing737Variant.B737_800: AircraftSpecs(
        variant=Boeing737Variant.B737_800,
        empty_weight=41000,
        max_takeoff_weight=79016,
        max_landing_weight=66361,
        max_fuel_capacity=26020,
        passenger_capacity=175,
        forward_cargo_capacity=3400,
        aft_cargo_capacity=2300,
        cg_forward_limit=15.0,
        cg_aft_limit=35.0,
        optimal_cg=28.0
    ),
    Boeing737Variant.B737_900: AircraftSpecs(
        variant=Boeing737Variant.B737_900,
        empty_weight=44676,
        max_takeoff_weight=85139,
        max_landing_weight=71214,
        max_fuel_capacity=26020,
        passenger_capacity=189,
        forward_cargo_capacity=3800,
        aft_cargo_capacity=2500,
        cg_forward_limit=15.0,
        cg_aft_limit=35.0,
        optimal_cg=28.5
    ),
    Boeing737Variant.B737_MAX8: AircraftSpecs(
        variant=Boeing737Variant.B737_MAX8,
        empty_weight=45070,
        max_takeoff_weight=82191,
        max_landing_weight=71214,
        max_fuel_capacity=26020,
        passenger_capacity=178,
        forward_cargo_capacity=3400,
        aft_cargo_capacity=2300,
        cg_forward_limit=15.0,
        cg_aft_limit=35.0,
        optimal_cg=28.2
    )
}