from typing import List, Dict, Any
from datetime import datetime
import asyncio
import json

from services.device_manager import DeviceManager
from services.baggage_tracking.baggage_service import BaggageService
from src.core.weight_balance import WeightBalanceCalculator

class DataIngestionService:
    def __init__(self):
        self.device_manager = DeviceManager()
        self.baggage_service = BaggageService()
        self.calculator = WeightBalanceCalculator()
        self.readings_buffer = []  # In-memory storage for Phase 3
        
    async def process_readings(self, readings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process incoming sensor readings"""
        processed_count = 0
        errors = []
        
        for reading in readings:
            try:
                await self._process_single_reading(reading)
                processed_count += 1
            except Exception as e:
                errors.append(f"Reading {reading.get('device_id')}: {str(e)}")
        
        return {
            "processed": processed_count,
            "total": len(readings),
            "errors": errors,
            "timestamp": datetime.now()
        }
    
    async def _process_single_reading(self, reading: Dict[str, Any]):
        """Process a single sensor reading"""
        device_id = reading["device_id"]
        device_type = await self._get_device_type(device_id)
        
        # Store reading
        self.readings_buffer.append({
            **reading,
            "processed_at": datetime.now()
        })
        
        # Update device status
        await self.device_manager.update_device_status(
            device_id, "online", {"last_reading": reading["value"]}
        )
        
        # Process based on device type
        if device_type == "load_cell":
            await self._process_weight_reading(reading)
        elif device_type == "rfid_scanner":
            await self._process_baggage_scan(reading)
    
    async def get_device_readings(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent readings for a device"""
        device_readings = [
            r for r in self.readings_buffer 
            if r["device_id"] == device_id
        ]
        
        # Sort by timestamp and limit
        device_readings.sort(key=lambda x: x["timestamp"], reverse=True)
        return device_readings[:limit]
    
    async def _get_device_type(self, device_id: str) -> str:
        """Get device type from device manager"""
        device = self.device_manager.devices.get(device_id)
        return device.get("device_type", "unknown") if device else "unknown"
    
    async def _process_weight_reading(self, reading: Dict[str, Any]):
        """Process weight sensor reading from cargo compartment"""
        pass
    
    async def _process_baggage_scan(self, reading: Dict[str, Any]):
        """Process RFID/barcode scan for baggage tracking"""
        pass