from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class FlightStatus(Enum):
    PLANNING = "planning"
    BOARDING = "boarding"
    LOADING = "loading"
    READY = "ready"
    DEPARTED = "departed"
    COMPLETED = "completed"

class BaggageStatus(Enum):
    CHECKED = "checked"
    LOADED = "loaded"
    TRANSFERRED = "transferred"
    REMOVED = "removed"

@dataclass
class Flight:
    flight_id: str
    flight_number: str
    aircraft_id: str
    departure_airport: str
    arrival_airport: str
    departure_date: str
    passenger_count: int = 0
    fuel_weight: float = 0.0
    total_weight: float = 0.0
    cg_position: float = 0.0
    status: FlightStatus = FlightStatus.PLANNING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        if not data['created_at']:
            data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Flight':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = FlightStatus(data['status'])
        return cls(**data)

@dataclass
class Baggage:
    baggage_id: str
    flight_id: str
    passenger_id: str
    weight: float
    compartment: Optional[str] = None
    special_handling: bool = False
    baggage_type: str = "standard"
    status: BaggageStatus = BaggageStatus.CHECKED
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        if not data['created_at']:
            data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Baggage':
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = BaggageStatus(data['status'])
        return cls(**data)

@dataclass
class AircraftConfig:
    aircraft_id: str
    aircraft_type: str
    variant: str
    empty_weight: float
    max_takeoff_weight: float
    max_landing_weight: float
    max_fuel_capacity: float
    passenger_capacity: int
    forward_cargo_capacity: float
    aft_cargo_capacity: float
    cg_forward_limit: float
    cg_aft_limit: float
    optimal_cg: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if not data['created_at']:
            data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AircraftConfig':
        return cls(**data)

@dataclass
class CalculationResult:
    calculation_id: str
    flight_id: str
    calculation_type: str
    total_weight: float
    cg_position: float
    mac_percentage: float
    compartment_weights: Dict[str, float]
    ballast_required: float
    ballast_location: str
    fuel_optimization: Dict[str, Any]
    compliance_status: bool
    warnings: List[str]
    timestamp: Optional[str] = None
    expires_at: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if not data['timestamp']:
            data['timestamp'] = datetime.utcnow().isoformat()
        # Set expiration to 24 hours from now (for DynamoDB TTL)
        if not data['expires_at']:
            data['expires_at'] = int(datetime.utcnow().timestamp()) + 86400
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalculationResult':
        return cls(**data)