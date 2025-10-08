from typing import Dict, Any, List
from services.offline_manager.offline_service import OfflineService


class OfflineSyncMiddleware:
    """Middleware to handle offline data synchronization"""
    
    def __init__(self):
        self.offline_service = OfflineService()
    
    def process_offline_queue(self, agent_id: str) -> Dict[str, Any]:
        """Process queued offline changes when agent comes online"""
        queued_changes = self.offline_service.get_queued_changes(agent_id)
        
        results = {
            "processed": 0,
            "failed": 0,
            "conflicts": []
        }
        
        for change in queued_changes:
            try:
                success = self.offline_service.apply_change(change)
                if success:
                    results["processed"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                results["conflicts"].append({
                    "change_id": change.get("id"),
                    "error": str(e)
                })
        
        return results
    
    def queue_for_offline(self, agent_id: str, change_data: Dict[str, Any]) -> bool:
        """Queue change for offline agent"""
        return self.offline_service.queue_change(agent_id, change_data)
    
    def check_connectivity(self, agent_id: str) -> Dict[str, Any]:
        """Check agent connectivity status"""
        return {
            "agent_id": agent_id,
            "online": self.offline_service.is_agent_online(agent_id),
            "last_sync": self.offline_service.get_last_sync_time(agent_id),
            "pending_changes": self.offline_service.get_pending_count(agent_id)
        }