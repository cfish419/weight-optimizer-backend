from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json

class DeviceManager:
    def __init__(self):
        self.devices = {}  # In-memory storage for Phase 3
        self.device_status = {}
        
    async def register_device(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new IoT device"""
        device_id = device_data["device_id"]
        
        self.devices[device_id] = {
            **device_data,
            "registered_at": datetime.now(),
            "last_seen": None,
            "status": "registered"
        }
        
        return {
            "device_id": device_id,
            "status": "registered",
            "message": f"Device {device_id} registered successfully"
        }
    
    async def update_device_status(self, device_id: str, status: str, metadata: Dict = None):
        """Update device status and last seen timestamp"""
        if device_id in self.devices:
            self.devices[device_id]["status"] = status
            self.devices[device_id]["last_seen"] = datetime.now()
            if metadata:
                self.devices[device_id]["metadata"] = metadata
    
    async def get_aircraft_devices(self, aircraft_id: str) -> List[Dict[str, Any]]:
        """Get all devices for a specific aircraft"""
        aircraft_devices = []
        
        for device_id, device_data in self.devices.items():
            if device_data.get("aircraft_id") == aircraft_id:
                # Check if device is online (last seen within 5 minutes)
                is_online = False
                if device_data.get("last_seen"):
                    time_diff = datetime.now() - device_data["last_seen"]
                    is_online = time_diff < timedelta(minutes=5)
                
                aircraft_devices.append({
                    **device_data,
                    "is_online": is_online
                })
        
        return aircraft_devices