from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from data.repositories.offline_repository import OfflineRepository


class OfflineService:
    """Service for managing offline agent operations"""
    
    def __init__(self):
        self.repository = OfflineRepository()
        self.sync_timeout = timedelta(minutes=5)  # Consider agent offline after 5 min
    
    def queue_change(self, agent_id: str, change_data: Dict[str, Any]) -> bool:
        """Queue change for offline agent"""
        change_id = str(uuid4())
        
        queued_change = {
            "id": change_id,
            "agent_id": agent_id,
            "change_data": change_data,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "queued",
            "retry_count": 0
        }
        
        return self.repository.save_queued_change(change_id, queued_change)
    
    def get_queued_changes(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all queued changes for agent"""
        return self.repository.get_agent_queued_changes(agent_id)
    
    def apply_change(self, change: Dict[str, Any]) -> bool:
        """Apply queued change when agent comes online"""
        try:
            # Validate change is still applicable
            if not self.validate_change_applicability(change):
                self.repository.mark_change_invalid(change["id"])
                return False
            
            # Apply the change (implementation depends on change type)
            success = self.execute_change(change["change_data"])
            
            if success:
                self.repository.mark_change_applied(change["id"])
            else:
                self.repository.increment_retry_count(change["id"])
            
            return success
            
        except Exception as e:
            self.repository.mark_change_failed(change["id"], str(e))
            return False
    
    def validate_change_applicability(self, change: Dict[str, Any]) -> bool:
        """Validate if queued change is still applicable"""
        change_time = datetime.fromisoformat(change["timestamp"])
        
        # Changes older than 24 hours are considered stale
        if datetime.utcnow() - change_time > timedelta(hours=24):
            return False
        
        # Check if conflicting changes have been applied
        conflicting_changes = self.repository.get_conflicting_changes(
            change["change_data"].get("baggage_id"),
            change_time
        )
        
        return len(conflicting_changes) == 0
    
    def execute_change(self, change_data: Dict[str, Any]) -> bool:
        """Execute the actual change operation"""
        change_type = change_data.get("type")
        
        if change_type == "add_baggage":
            from services.baggage_tracking.baggage_service import BaggageService
            service = BaggageService()
            try:
                service.add_baggage(change_data["baggage_data"])
                return True
            except Exception:
                return False
                
        elif change_type == "update_baggage":
            from services.baggage_tracking.baggage_service import BaggageService
            service = BaggageService()
            return service.update_baggage(
                change_data["baggage_id"], 
                change_data["updates"]
            )
        
        return False
    
    def is_agent_online(self, agent_id: str) -> bool:
        """Check if agent is currently online"""
        last_heartbeat = self.repository.get_last_heartbeat(agent_id)
        if not last_heartbeat:
            return False
        
        last_time = datetime.fromisoformat(last_heartbeat)
        return datetime.utcnow() - last_time < self.sync_timeout
    
    def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp"""
        return self.repository.update_heartbeat(agent_id, datetime.utcnow().isoformat())
    
    def get_last_sync_time(self, agent_id: str) -> Optional[str]:
        """Get last successful sync time for agent"""
        return self.repository.get_last_sync_time(agent_id)
    
    def get_pending_count(self, agent_id: str) -> int:
        """Get count of pending changes for agent"""
        return self.repository.get_pending_count(agent_id)
    
    def create_offline_snapshot(self, agent_id: str, flight_id: str) -> Dict[str, Any]:
        """Create offline data snapshot for agent"""
        from services.baggage_tracking.baggage_service import BaggageService
        
        baggage_service = BaggageService()
        flight_baggage = baggage_service.get_flight_baggage(flight_id)
        
        snapshot = {
            "snapshot_id": str(uuid4()),
            "agent_id": agent_id,
            "flight_id": flight_id,
            "timestamp": datetime.utcnow().isoformat(),
            "baggage_data": flight_baggage,
            "expires_at": (datetime.utcnow() + timedelta(hours=12)).isoformat()
        }
        
        self.repository.save_offline_snapshot(snapshot["snapshot_id"], snapshot)
        
        return snapshot
    
    def sync_offline_changes(self, agent_id: str, offline_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sync changes made while agent was offline"""
        results = {
            "applied": 0,
            "failed": 0,
            "conflicts": []
        }
        
        for change in offline_changes:
            # Add metadata
            change["agent_id"] = agent_id
            change["sync_timestamp"] = datetime.utcnow().isoformat()
            
            # Queue for processing
            if self.queue_change(agent_id, change):
                # Try to apply immediately
                if self.apply_change({"id": str(uuid4()), "change_data": change}):
                    results["applied"] += 1
                else:
                    results["failed"] += 1
            else:
                results["failed"] += 1
        
        # Update last sync time
        self.repository.update_last_sync_time(agent_id, datetime.utcnow().isoformat())
        
        return results