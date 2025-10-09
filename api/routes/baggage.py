from typing import Any, Dict, List

from services.baggage_tracking.baggage_service import BaggageService
from services.sync_engine.sync_service import SyncService


class BaggageRoutes:
    """REST API routes for baggage management"""

    def __init__(self):
        self.baggage_service = BaggageService()
        self.sync_service = SyncService()

    def add_baggage(self, baggage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add new baggage item"""
        baggage_id = self.baggage_service.add_baggage(baggage_data)

        # Trigger real-time sync
        self.sync_service.broadcast_update(
            {
                "type": "baggage_added",
                "baggage_id": baggage_id,
                "flight_id": baggage_data.get("flight_id"),
            }
        )

        return {"baggage_id": baggage_id, "status": "added"}

    def update_baggage(
        self, baggage_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update existing baggage item"""
        success = self.baggage_service.update_baggage(baggage_id, updates)

        if success:
            self.sync_service.broadcast_update(
                {
                    "type": "baggage_updated",
                    "baggage_id": baggage_id,
                    "updates": updates,
                }
            )

        return {"baggage_id": baggage_id, "status": "updated" if success else "failed"}

    def get_flight_baggage(self, flight_id: str) -> List[Dict[str, Any]]:
        """Get all baggage for a flight"""
        return self.baggage_service.get_flight_baggage(flight_id)

    def handle_gate_check(self, gate_check_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle last-minute gate-checked baggage"""
        baggage_id = self.baggage_service.add_baggage(
            {**gate_check_data, "source": "gate_check", "priority": "high"}
        )

        # Immediate recalculation trigger
        self.sync_service.broadcast_update(
            {
                "type": "gate_check_added",
                "baggage_id": baggage_id,
                "flight_id": gate_check_data.get("flight_id"),
                "requires_recalculation": True,
            }
        )

        return {"baggage_id": baggage_id, "status": "gate_checked"}
