import json
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.data_ingestion import DataIngestionService
from services.device_manager import DeviceManager

router = APIRouter(prefix="/devices", tags=["devices"])


class DeviceRegistration(BaseModel):
    device_id: str
    device_type: str  # load_cell, rfid_scanner, weight_sensor, environmental
    location: str  # forward_cargo, aft_cargo, nose_gear, main_gear
    aircraft_id: str
    calibration_data: Dict[str, Any] = {}


class SensorReading(BaseModel):
    device_id: str
    timestamp: datetime
    value: float
    unit: str
    metadata: Dict[str, Any] = {}


@router.post("/register")
async def register_device(device: DeviceRegistration):
    """Register a new IoT device"""
    device_manager = DeviceManager()
    return await device_manager.register_device(device.dict())


@router.post("/readings")
async def ingest_sensor_data(readings: List[SensorReading]):
    """Ingest sensor readings from IoT devices"""
    ingestion_service = DataIngestionService()
    return await ingestion_service.process_readings([r.dict() for r in readings])


@router.get("/status/{aircraft_id}")
async def get_device_status(aircraft_id: str):
    """Get status of all devices for an aircraft"""
    device_manager = DeviceManager()
    return await device_manager.get_aircraft_devices(aircraft_id)


@router.get("/readings/{device_id}")
async def get_device_readings(device_id: str, limit: int = 100):
    """Get recent readings from a specific device"""
    ingestion_service = DataIngestionService()
    return await ingestion_service.get_device_readings(device_id, limit)
