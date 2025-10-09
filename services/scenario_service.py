from datetime import datetime
from typing import Dict, List, Optional

from services.sync_service import SyncService
from services.weight_balance_service import WeightBalanceService
from src.models.aircraft_variants import AIRCRAFT_SPECS, Boeing737Variant
from src.models.operational_scenarios import (
    AircraftSwap,
    CargoChange,
    ChangeType,
    EmergencyScenario,
    OperationalChange,
    PassengerChange,
    ScenarioHandler,
)


class ScenarioService:
    def __init__(
        self, weight_balance_service: WeightBalanceService, sync_service: SyncService
    ):
        self.weight_balance_service = weight_balance_service
        self.sync_service = sync_service
        self.scenario_handler = ScenarioHandler()

    async def handle_passenger_noshow(
        self, flight_id: str, passenger_data: PassengerChange
    ) -> Dict:
        """Handle passenger no-show scenario"""
        change = self.scenario_handler.handle_passenger_noshow(passenger_data)

        # Update flight data
        result = await self._apply_change(flight_id, change)

        # Broadcast to all agents
        await self.sync_service.broadcast_change(
            {
                "type": "passenger_noshow",
                "flight_id": flight_id,
                "passenger_id": passenger_data.passenger_id,
                "weight_impact": change.weight_impact,
                "new_calculations": result,
            }
        )

        return result

    async def handle_gate_check_baggage(
        self, flight_id: str, baggage_weight: float, compartment: str
    ) -> Dict:
        """Handle last-minute gate check baggage"""
        change = self.scenario_handler.handle_gate_check(baggage_weight)

        # Add baggage to specified compartment
        cargo_change = CargoChange(
            cargo_id=f"gatecheck_{datetime.now().timestamp()}",
            cargo_type="baggage",
            action="add",
            weight=baggage_weight,
            to_compartment=compartment,
        )

        result = await self._apply_cargo_change(flight_id, cargo_change)

        # Broadcast urgent update
        await self.sync_service.broadcast_change(
            {
                "type": "gate_check",
                "flight_id": flight_id,
                "baggage_weight": baggage_weight,
                "compartment": compartment,
                "priority": "urgent",
                "new_calculations": result,
            }
        )

        return result

    async def handle_aircraft_swap(
        self, flight_id: str, swap_data: AircraftSwap
    ) -> Dict:
        """Handle aircraft substitution"""
        # Get new aircraft specifications
        new_variant = Boeing737Variant(swap_data.new_variant)
        new_specs = AIRCRAFT_SPECS[new_variant]

        # Recalculate everything with new aircraft
        result = await self.weight_balance_service.recalculate_with_new_aircraft(
            flight_id, new_specs
        )

        change = self.scenario_handler.handle_aircraft_swap(swap_data)
        self.scenario_handler.add_change(change)

        # Critical broadcast - affects all operations
        await self.sync_service.broadcast_change(
            {
                "type": "aircraft_swap",
                "flight_id": flight_id,
                "original_aircraft": swap_data.original_aircraft,
                "new_aircraft": swap_data.new_aircraft,
                "new_specs": {
                    "variant": new_specs.variant.value,
                    "max_takeoff_weight": new_specs.max_takeoff_weight,
                    "cargo_capacity": {
                        "forward": new_specs.forward_cargo_capacity,
                        "aft": new_specs.aft_cargo_capacity,
                    },
                },
                "priority": "critical",
                "new_calculations": result,
            }
        )

        return result

    async def handle_emergency_weight_reduction(
        self, flight_id: str, scenario: EmergencyScenario
    ) -> Dict:
        """Handle emergency weight reduction scenarios"""
        changes = self.scenario_handler.handle_emergency_reduction(scenario)

        # Apply all emergency changes
        total_reduction = 0.0
        removal_plan = []

        for change in changes:
            total_reduction += abs(change.weight_impact)
            removal_plan.append(
                {
                    "item": change.description,
                    "weight_reduction": abs(change.weight_impact),
                    "priority": change.priority,
                }
            )

        # Recalculate with reduced weight
        result = await self.weight_balance_service.apply_weight_reduction(
            flight_id, total_reduction
        )

        # Emergency broadcast
        await self.sync_service.broadcast_change(
            {
                "type": "emergency_reduction",
                "flight_id": flight_id,
                "scenario_type": scenario.scenario_type,
                "total_reduction": total_reduction,
                "removal_plan": removal_plan,
                "time_constraint": scenario.time_constraint,
                "priority": "emergency",
                "new_calculations": result,
            }
        )

        return {
            "success": True,
            "total_reduction": total_reduction,
            "removal_plan": removal_plan,
            "new_calculations": result,
        }

    async def handle_connecting_baggage(
        self, flight_id: str, connecting_bags: List[Dict]
    ) -> Dict:
        """Handle connecting baggage transfers"""
        total_weight = sum(bag["weight"] for bag in connecting_bags)

        cargo_change = CargoChange(
            cargo_id=f"connecting_{datetime.now().timestamp()}",
            cargo_type="baggage",
            action="add",
            weight=total_weight,
            to_compartment="forward",  # Default compartment
        )

        result = await self._apply_cargo_change(flight_id, cargo_change)

        await self.sync_service.broadcast_change(
            {
                "type": "connecting_baggage",
                "flight_id": flight_id,
                "bag_count": len(connecting_bags),
                "total_weight": total_weight,
                "new_calculations": result,
            }
        )

        return result

    async def handle_crew_change(
        self, flight_id: str, crew_changes: List[Dict]
    ) -> Dict:
        """Handle crew substitutions"""
        weight_impact = sum(
            change.get("weight_difference", 0) for change in crew_changes
        )

        if weight_impact != 0:
            change = OperationalChange(
                change_id=f"crew_{datetime.now().timestamp()}",
                change_type=ChangeType.CREW_CHANGE,
                timestamp=datetime.now(),
                description=f"Crew change: {len(crew_changes)} members",
                weight_impact=weight_impact,
                cg_impact=0.0,
                priority=2,
            )

            result = await self._apply_change(flight_id, change)

            await self.sync_service.broadcast_change(
                {
                    "type": "crew_change",
                    "flight_id": flight_id,
                    "crew_changes": crew_changes,
                    "weight_impact": weight_impact,
                    "new_calculations": result,
                }
            )

            return result

        return {"success": True, "message": "No weight impact from crew change"}

    async def _apply_change(self, flight_id: str, change: OperationalChange) -> Dict:
        """Apply operational change and recalculate"""
        # This would integrate with the main weight/balance calculation
        result = await self.weight_balance_service.apply_weight_change(
            flight_id, change.weight_impact
        )

        self.scenario_handler.add_change(change)
        return result

    async def _apply_cargo_change(
        self, flight_id: str, cargo_change: CargoChange
    ) -> Dict:
        """Apply cargo change and recalculate"""
        result = await self.weight_balance_service.apply_cargo_change(
            flight_id, cargo_change
        )
        return result

    def get_active_scenarios(self, flight_id: str) -> List[Dict]:
        """Get all active scenarios for a flight"""
        return [
            {
                "change_id": change.change_id,
                "type": change.change_type.value,
                "timestamp": change.timestamp.isoformat(),
                "description": change.description,
                "weight_impact": change.weight_impact,
                "priority": change.priority,
            }
            for change in self.scenario_handler.active_changes
        ]
