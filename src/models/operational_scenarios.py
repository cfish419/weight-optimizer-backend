from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ChangeType(Enum):
    PASSENGER_NOSHOW = "passenger_noshow"
    GATE_CHECK = "gate_check"
    AIRCRAFT_SWAP = "aircraft_swap"
    CREW_CHANGE = "crew_change"
    CARGO_ADDITION = "cargo_addition"
    CARGO_REMOVAL = "cargo_removal"
    FUEL_ADJUSTMENT = "fuel_adjustment"
    WEATHER_IMPACT = "weather_impact"
    ROUTE_CHANGE = "route_change"
    EMERGENCY_REDUCTION = "emergency_reduction"


@dataclass
class OperationalChange:
    change_id: str
    change_type: ChangeType
    timestamp: datetime
    description: str
    weight_impact: float  # kg (positive = addition, negative = removal)
    cg_impact: float  # impact on CG position
    priority: int  # 1=critical, 2=high, 3=normal
    requires_recalculation: bool = True


@dataclass
class PassengerChange:
    passenger_id: str
    action: str  # "add", "remove", "move"
    from_seat: Optional[str] = None
    to_seat: Optional[str] = None
    weight: float = 84.0  # kg (average passenger weight)
    baggage_count: int = 0
    baggage_weight: float = 0.0


@dataclass
class CargoChange:
    cargo_id: str
    cargo_type: str  # "baggage", "mail", "freight", "catering", "supplies"
    action: str  # "add", "remove", "move"
    weight: float
    from_compartment: Optional[str] = None
    to_compartment: Optional[str] = None
    special_handling: bool = False
    hazmat: bool = False


@dataclass
class AircraftSwap:
    original_aircraft: str
    new_aircraft: str
    original_variant: str
    new_variant: str
    reason: str
    impact_assessment: Dict[str, float]


@dataclass
class EmergencyScenario:
    scenario_type: str  # "medical", "security", "mechanical", "weather"
    weight_reduction_required: float  # kg
    time_constraint: int  # minutes
    priority_items: List[str]  # items to remove first


class ScenarioHandler:
    def __init__(self):
        self.active_changes: List[OperationalChange] = []

    def add_change(self, change: OperationalChange):
        """Add operational change and trigger recalculation if needed"""
        self.active_changes.append(change)
        if change.requires_recalculation:
            return self._trigger_recalculation(change)
        return True

    def handle_passenger_noshow(self, passenger: PassengerChange) -> OperationalChange:
        """Handle passenger no-show scenario"""
        weight_impact = -(passenger.weight + passenger.baggage_weight)
        return OperationalChange(
            change_id=f"noshow_{passenger.passenger_id}",
            change_type=ChangeType.PASSENGER_NOSHOW,
            timestamp=datetime.now(),
            description=f"Passenger {passenger.passenger_id} no-show",
            weight_impact=weight_impact,
            cg_impact=0.0,  # Calculate based on seat position
            priority=2,
        )

    def handle_gate_check(self, baggage_weight: float) -> OperationalChange:
        """Handle last-minute gate check baggage"""
        return OperationalChange(
            change_id=f"gatecheck_{datetime.now().timestamp()}",
            change_type=ChangeType.GATE_CHECK,
            timestamp=datetime.now(),
            description=f"Gate check baggage: {baggage_weight}kg",
            weight_impact=baggage_weight,
            cg_impact=0.0,  # Calculate based on compartment
            priority=1,
        )

    def handle_aircraft_swap(self, swap: AircraftSwap) -> OperationalChange:
        """Handle aircraft substitution"""
        return OperationalChange(
            change_id=f"swap_{swap.new_aircraft}",
            change_type=ChangeType.AIRCRAFT_SWAP,
            timestamp=datetime.now(),
            description=f"Aircraft swap: {swap.original_aircraft} -> {swap.new_aircraft}",
            weight_impact=0.0,  # Handled by new aircraft specs
            cg_impact=0.0,
            priority=1,
        )

    def handle_emergency_reduction(
        self, scenario: EmergencyScenario
    ) -> List[OperationalChange]:
        """Handle emergency weight reduction scenarios"""
        changes = []
        remaining_reduction = scenario.weight_reduction_required

        # Priority order: cargo, baggage, fuel, passengers
        for item in scenario.priority_items:
            if remaining_reduction <= 0:
                break

            change = OperationalChange(
                change_id=f"emergency_{item}_{datetime.now().timestamp()}",
                change_type=ChangeType.EMERGENCY_REDUCTION,
                timestamp=datetime.now(),
                description=f"Emergency removal: {item}",
                weight_impact=-min(remaining_reduction, 100),  # Estimate
                cg_impact=0.0,
                priority=1,
            )
            changes.append(change)
            remaining_reduction -= abs(change.weight_impact)

        return changes

    def _trigger_recalculation(self, change: OperationalChange) -> bool:
        """Trigger weight/balance recalculation"""
        # This would integrate with the main calculation engine
        import logging

        logging.info(f"Triggering recalculation for change: {change.description}")
        return True
