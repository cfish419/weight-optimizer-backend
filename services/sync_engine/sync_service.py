from typing import Dict, Any, List, Set
from datetime import datetime
from data.repositories.sync_repository import SyncRepository


class SyncService:
    """Service for real-time data synchronization across agents"""
    
    def __init__(self):
        self.repository = SyncRepository()
        self.connected_agents: Set[str] = set()
        self.websocket_connections: Dict[str, Any] = {}
    
    def register_agent(self, agent_id: str, connection=None) -> bool:
        """Register agent for real-time updates"""
        self.connected_agents.add(agent_id)
        if connection:
            self.websocket_connections[agent_id] = connection
        
        # Send pending updates to newly connected agent
        pending_updates = self.repository.get_pending_updates(agent_id)
        for update in pending_updates:
            self.send_to_agent(agent_id, update)
        
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from real-time updates"""
        self.connected_agents.discard(agent_id)
        self.websocket_connections.pop(agent_id, None)
        return True
    
    def broadcast_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Broadcast update to all connected agents"""
        update_id = self.repository.create_update(update_data)
        
        successful_sends = 0
        failed_sends = 0
        
        for agent_id in self.connected_agents:
            try:
                success = self.send_to_agent(agent_id, update_data)
                if success:
                    successful_sends += 1
                else:
                    failed_sends += 1
                    # Queue for offline delivery
                    self.repository.queue_update_for_agent(agent_id, update_id)
            except Exception:
                failed_sends += 1
                self.repository.queue_update_for_agent(agent_id, update_id)
        
        return {
            "update_id": update_id,
            "successful_sends": successful_sends,
            "failed_sends": failed_sends,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def send_to_agent(self, agent_id: str, update_data: Dict[str, Any]) -> bool:
        """Send update to specific agent"""
        connection = self.websocket_connections.get(agent_id)
        
        if connection:
            try:
                # WebSocket send (implementation depends on framework)
                # connection.send(json.dumps(update_data))
                return True
            except Exception:
                return False
        else:
            # Agent not connected, queue for later
            return False
    
    def handle_agent_update(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update from agent with conflict resolution"""
        
        # Check for conflicts
        conflicts = self.detect_conflicts(update_data)
        
        if conflicts:
            return {
                "status": "conflict",
                "conflicts": conflicts,
                "requires_resolution": True
            }
        
        # Apply update
        update_id = self.repository.create_update({
            **update_data,
            "source_agent": agent_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Broadcast to other agents
        broadcast_result = self.broadcast_update({
            **update_data,
            "source_agent": agent_id,
            "update_id": update_id
        })
        
        return {
            "status": "applied",
            "update_id": update_id,
            "broadcast_result": broadcast_result
        }
    
    def detect_conflicts(self, update_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts with existing data"""
        conflicts = []
        
        # Check timestamp conflicts
        if 'baggage_id' in update_data:
            last_update = self.repository.get_last_update(update_data['baggage_id'])
            if last_update and 'timestamp' in update_data:
                update_time = datetime.fromisoformat(update_data['timestamp'])
                last_time = datetime.fromisoformat(last_update['timestamp'])
                
                if update_time < last_time:
                    conflicts.append({
                        "type": "timestamp_conflict",
                        "message": "Update is older than existing data",
                        "existing_timestamp": last_update['timestamp'],
                        "update_timestamp": update_data['timestamp']
                    })
        
        return conflicts
    
    def resolve_conflict(self, conflict_id: str, resolution: str) -> bool:
        """Resolve data conflict"""
        # Implementation depends on conflict resolution strategy
        # Options: last-write-wins, manual resolution, merge strategies
        return self.repository.resolve_conflict(conflict_id, resolution)
    
    def get_sync_status(self, agent_id: str) -> Dict[str, Any]:
        """Get synchronization status for agent"""
        return {
            "agent_id": agent_id,
            "connected": agent_id in self.connected_agents,
            "last_sync": self.repository.get_last_sync_time(agent_id),
            "pending_updates": self.repository.get_pending_count(agent_id),
            "conflicts": self.repository.get_unresolved_conflicts(agent_id)
        }