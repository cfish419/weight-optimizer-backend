from datetime import datetime
from typing import Any, Dict, List, Optional


class OfflineRepository:
    """Repository for offline operations data"""

    def __init__(self):
        # In-memory storage for Phase 2
        self.queued_changes: Dict[str, Dict[str, Any]] = {}
        self.agent_queues: Dict[str, List[str]] = {}
        self.agent_heartbeats: Dict[str, str] = {}
        self.agent_sync_times: Dict[str, str] = {}
        self.offline_snapshots: Dict[str, Dict[str, Any]] = {}

    def save_queued_change(self, change_id: str, change_data: Dict[str, Any]) -> bool:
        """Save queued change"""
        try:
            self.queued_changes[change_id] = change_data

            # Add to agent queue
            agent_id = change_data["agent_id"]
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = []

            self.agent_queues[agent_id].append(change_id)
            return True
        except Exception:
            return False

    def get_agent_queued_changes(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all queued changes for agent"""
        change_ids = self.agent_queues.get(agent_id, [])

        queued_changes = []
        for change_id in change_ids:
            change = self.queued_changes.get(change_id)
            if change and change.get("status") == "queued":
                queued_changes.append(change)

        return queued_changes

    def mark_change_applied(self, change_id: str) -> bool:
        """Mark change as successfully applied"""
        try:
            if change_id in self.queued_changes:
                self.queued_changes[change_id]["status"] = "applied"
                self.queued_changes[change_id][
                    "applied_at"
                ] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception:
            return False

    def mark_change_failed(self, change_id: str, error_message: str) -> bool:
        """Mark change as failed"""
        try:
            if change_id in self.queued_changes:
                self.queued_changes[change_id]["status"] = "failed"
                self.queued_changes[change_id]["error"] = error_message
                self.queued_changes[change_id][
                    "failed_at"
                ] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception:
            return False

    def mark_change_invalid(self, change_id: str) -> bool:
        """Mark change as invalid/stale"""
        try:
            if change_id in self.queued_changes:
                self.queued_changes[change_id]["status"] = "invalid"
                self.queued_changes[change_id][
                    "invalidated_at"
                ] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception:
            return False

    def increment_retry_count(self, change_id: str) -> bool:
        """Increment retry count for failed change"""
        try:
            if change_id in self.queued_changes:
                current_count = self.queued_changes[change_id].get("retry_count", 0)
                self.queued_changes[change_id]["retry_count"] = current_count + 1
                self.queued_changes[change_id][
                    "last_retry"
                ] = datetime.utcnow().isoformat()
                return True
            return False
        except Exception:
            return False

    def get_conflicting_changes(
        self, resource_id: str, after_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """Get changes that conflict with a queued change"""
        conflicting = []

        for change in self.queued_changes.values():
            change_data = change.get("change_data", {})

            # Check if change affects same resource
            if (
                change_data.get("baggage_id") == resource_id
                and change.get("status") == "applied"
            ):

                applied_time = change.get("applied_at")
                if applied_time:
                    applied_datetime = datetime.fromisoformat(applied_time)
                    if applied_datetime > after_timestamp:
                        conflicting.append(change)

        return conflicting

    def update_heartbeat(self, agent_id: str, timestamp: str) -> bool:
        """Update agent heartbeat"""
        try:
            self.agent_heartbeats[agent_id] = timestamp
            return True
        except Exception:
            return False

    def get_last_heartbeat(self, agent_id: str) -> Optional[str]:
        """Get last heartbeat for agent"""
        return self.agent_heartbeats.get(agent_id)

    def update_last_sync_time(self, agent_id: str, timestamp: str) -> bool:
        """Update last sync time for agent"""
        try:
            self.agent_sync_times[agent_id] = timestamp
            return True
        except Exception:
            return False

    def get_last_sync_time(self, agent_id: str) -> Optional[str]:
        """Get last sync time for agent"""
        return self.agent_sync_times.get(agent_id)

    def get_pending_count(self, agent_id: str) -> int:
        """Get count of pending changes for agent"""
        change_ids = self.agent_queues.get(agent_id, [])

        pending_count = 0
        for change_id in change_ids:
            change = self.queued_changes.get(change_id)
            if change and change.get("status") == "queued":
                pending_count += 1

        return pending_count

    def save_offline_snapshot(
        self, snapshot_id: str, snapshot_data: Dict[str, Any]
    ) -> bool:
        """Save offline data snapshot"""
        try:
            self.offline_snapshots[snapshot_id] = snapshot_data
            return True
        except Exception:
            return False

    def get_offline_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get offline snapshot by ID"""
        return self.offline_snapshots.get(snapshot_id)

    def cleanup_old_changes(self, older_than_hours: int = 24) -> int:
        """Clean up old processed changes"""
        cutoff_time = datetime.utcnow().timestamp() - (older_than_hours * 3600)
        cleaned_count = 0

        changes_to_remove = []

        for change_id, change in self.queued_changes.items():
            if change.get("status") in ["applied", "failed", "invalid"]:
                change_time = datetime.fromisoformat(change["timestamp"]).timestamp()
                if change_time < cutoff_time:
                    changes_to_remove.append(change_id)

        for change_id in changes_to_remove:
            # Remove from queued changes
            del self.queued_changes[change_id]

            # Remove from agent queues
            for agent_id, queue in self.agent_queues.items():
                if change_id in queue:
                    queue.remove(change_id)

            cleaned_count += 1

        return cleaned_count
