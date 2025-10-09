from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SyncRepository:
    """Repository for synchronization data"""

    def __init__(self):
        # In-memory storage for Phase 2
        self.updates_store: Dict[str, Dict[str, Any]] = {}
        self.agent_updates: Dict[str, List[str]] = {}
        self.pending_updates: Dict[str, List[str]] = {}
        self.conflicts: Dict[str, Dict[str, Any]] = {}

    def create_update(self, update_data: Dict[str, Any]) -> str:
        """Create new update record"""
        update_id = str(uuid4())

        update_record = {
            "id": update_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "created",
        }

        self.updates_store[update_id] = update_record
        return update_id

    def get_update(self, update_id: str) -> Optional[Dict[str, Any]]:
        """Get update by ID"""
        return self.updates_store.get(update_id)

    def queue_update_for_agent(self, agent_id: str, update_id: str) -> bool:
        """Queue update for specific agent"""
        try:
            if agent_id not in self.pending_updates:
                self.pending_updates[agent_id] = []

            if update_id not in self.pending_updates[agent_id]:
                self.pending_updates[agent_id].append(update_id)

            return True
        except Exception:
            return False

    def get_pending_updates(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get pending updates for agent"""
        pending_ids = self.pending_updates.get(agent_id, [])

        pending_updates = []
        for update_id in pending_ids:
            update = self.updates_store.get(update_id)
            if update:
                pending_updates.append(update["data"])

        return pending_updates

    def mark_update_delivered(self, agent_id: str, update_id: str) -> bool:
        """Mark update as delivered to agent"""
        try:
            if agent_id in self.pending_updates:
                if update_id in self.pending_updates[agent_id]:
                    self.pending_updates[agent_id].remove(update_id)

            # Add to agent's update history
            if agent_id not in self.agent_updates:
                self.agent_updates[agent_id] = []

            if update_id not in self.agent_updates[agent_id]:
                self.agent_updates[agent_id].append(update_id)

            return True
        except Exception:
            return False

    def get_last_update(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """Get last update for a specific resource"""
        # Find most recent update for resource
        latest_update = None
        latest_timestamp = None

        for update in self.updates_store.values():
            update_data = update["data"]

            # Check if update affects this resource
            if (
                update_data.get("baggage_id") == resource_id
                or update_data.get("flight_id") == resource_id
            ):

                update_time = datetime.fromisoformat(update["timestamp"])

                if latest_timestamp is None or update_time > latest_timestamp:
                    latest_timestamp = update_time
                    latest_update = update

        return latest_update

    def get_last_sync_time(self, agent_id: str) -> Optional[str]:
        """Get last sync time for agent"""
        agent_update_ids = self.agent_updates.get(agent_id, [])

        if not agent_update_ids:
            return None

        # Find most recent update timestamp
        latest_timestamp = None

        for update_id in agent_update_ids:
            update = self.updates_store.get(update_id)
            if update:
                update_time = datetime.fromisoformat(update["timestamp"])
                if latest_timestamp is None or update_time > latest_timestamp:
                    latest_timestamp = update_time

        return latest_timestamp.isoformat() if latest_timestamp else None

    def get_pending_count(self, agent_id: str) -> int:
        """Get count of pending updates for agent"""
        return len(self.pending_updates.get(agent_id, []))

    def create_conflict(self, conflict_data: Dict[str, Any]) -> str:
        """Create conflict record"""
        conflict_id = str(uuid4())

        conflict_record = {
            "id": conflict_id,
            "data": conflict_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unresolved",
        }

        self.conflicts[conflict_id] = conflict_record
        return conflict_id

    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve conflict"""
        try:
            if conflict_id in self.conflicts:
                self.conflicts[conflict_id]["status"] = "resolved"
                self.conflicts[conflict_id]["resolution"] = resolution
                self.conflicts[conflict_id][
                    "resolved_at"
                ] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception:
            return False

    def get_unresolved_conflicts(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get unresolved conflicts for agent"""
        agent_conflicts = []

        for conflict in self.conflicts.values():
            if (
                conflict["status"] == "unresolved"
                and conflict["data"].get("agent_id") == agent_id
            ):
                agent_conflicts.append(conflict)

        return agent_conflicts
