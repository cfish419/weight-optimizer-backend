from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from pydantic import BaseModel
from services.scenario_service import ScenarioService
from services.weather_service import WeatherService
from src.models.operational_scenarios import PassengerChange, CargoChange, AircraftSwap, EmergencyScenario
from src.models.aircraft_variants import Boeing737Variant

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

class PassengerNoShowRequest(BaseModel):
    flight_id: str
    passenger_id: str
    seat_number: str
    weight: float = 84.0
    baggage_count: int = 0
    baggage_weight: float = 0.0

class GateCheckRequest(BaseModel):
    flight_id: str
    baggage_weight: float
    compartment: str = "forward"
    passenger_count: int = 1

class AircraftSwapRequest(BaseModel):
    flight_id: str
    original_aircraft: str
    new_aircraft: str
    original_variant: str
    new_variant: str
    reason: str

class EmergencyReductionRequest(BaseModel):
    flight_id: str
    scenario_type: str
    weight_reduction_required: float
    time_constraint: int
    priority_items: List[str]

class WeatherUpdateRequest(BaseModel):
    flight_id: str
    departure_airport: str
    arrival_airport: str
    route_airports: List[str] = []

@router.post("/passenger-noshow")
async def handle_passenger_noshow(
    request: PassengerNoShowRequest,
    scenario_service: ScenarioService = Depends()
):
    """Handle passenger no-show scenario"""
    try:
        passenger_change = PassengerChange(
            passenger_id=request.passenger_id,
            action="remove",
            from_seat=request.seat_number,
            weight=request.weight,
            baggage_count=request.baggage_count,
            baggage_weight=request.baggage_weight
        )
        
        result = await scenario_service.handle_passenger_noshow(
            request.flight_id, passenger_change
        )
        
        return {
            "success": True,
            "message": f"Processed no-show for passenger {request.passenger_id}",
            "weight_reduction": request.weight + request.baggage_weight,
            "calculations": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gate-check")
async def handle_gate_check(
    request: GateCheckRequest,
    scenario_service: ScenarioService = Depends()
):
    """Handle last-minute gate check baggage"""
    try:
        result = await scenario_service.handle_gate_check_baggage(
            request.flight_id, request.baggage_weight, request.compartment
        )
        
        return {
            "success": True,
            "message": f"Added {request.baggage_weight}kg gate check baggage",
            "compartment": request.compartment,
            "calculations": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/aircraft-swap")
async def handle_aircraft_swap(
    request: AircraftSwapRequest,
    scenario_service: ScenarioService = Depends()
):
    """Handle aircraft substitution"""
    try:
        swap_data = AircraftSwap(
            original_aircraft=request.original_aircraft,
            new_aircraft=request.new_aircraft,
            original_variant=request.original_variant,
            new_variant=request.new_variant,
            reason=request.reason,
            impact_assessment={}
        )
        
        result = await scenario_service.handle_aircraft_swap(
            request.flight_id, swap_data
        )
        
        return {
            "success": True,
            "message": f"Aircraft swapped: {request.original_aircraft} -> {request.new_aircraft}",
            "variant_change": f"{request.original_variant} -> {request.new_variant}",
            "calculations": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emergency-reduction")
async def handle_emergency_reduction(
    request: EmergencyReductionRequest,
    scenario_service: ScenarioService = Depends()
):
    """Handle emergency weight reduction"""
    try:
        scenario = EmergencyScenario(
            scenario_type=request.scenario_type,
            weight_reduction_required=request.weight_reduction_required,
            time_constraint=request.time_constraint,
            priority_items=request.priority_items
        )
        
        result = await scenario_service.handle_emergency_weight_reduction(
            request.flight_id, scenario
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/weather-update")
async def handle_weather_update(
    request: WeatherUpdateRequest,
    weather_service: WeatherService = Depends()
):
    """Handle weather-driven operational changes"""
    try:
        # Get weather for departure airport
        departure_weather = await weather_service.get_weather_data(request.departure_airport)
        arrival_weather = await weather_service.get_weather_data(request.arrival_airport)
        
        if not departure_weather:
            raise HTTPException(status_code=404, detail="Weather data not available")
            
        # Calculate performance impacts
        performance_limits = weather_service.get_performance_limitations(departure_weather)
        
        # Calculate fuel adjustments
        base_fuel = 18000  # kg - would come from flight plan
        adjusted_fuel = weather_service.calculate_fuel_adjustment(departure_weather, base_fuel)
        fuel_difference = adjusted_fuel - base_fuel
        
        return {
            "success": True,
            "departure_weather": {
                "airport": request.departure_airport,
                "temperature": departure_weather.temperature,
                "wind_speed": departure_weather.wind_speed,
                "condition": departure_weather.condition.value,
                "performance_factor": departure_weather.get_performance_factor()
            },
            "performance_impacts": performance_limits,
            "fuel_adjustment": {
                "original_fuel": base_fuel,
                "adjusted_fuel": adjusted_fuel,
                "difference": fuel_difference,
                "reason": "Weather conditions"
            },
            "deicing_weight": departure_weather.get_deicing_weight()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active/{flight_id}")
async def get_active_scenarios(
    flight_id: str,
    scenario_service: ScenarioService = Depends()
):
    """Get all active scenarios for a flight"""
    try:
        scenarios = scenario_service.get_active_scenarios(flight_id)
        return {
            "flight_id": flight_id,
            "active_scenarios": scenarios,
            "count": len(scenarios)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aircraft-variants")
async def get_aircraft_variants():
    """Get available Boeing 737 variants and their specifications"""
    from src.models.aircraft_variants import AIRCRAFT_SPECS
    
    variants = {}
    for variant, specs in AIRCRAFT_SPECS.items():
        variants[variant.value] = {
            "empty_weight": specs.empty_weight,
            "max_takeoff_weight": specs.max_takeoff_weight,
            "passenger_capacity": specs.passenger_capacity,
            "cargo_capacity": {
                "forward": specs.forward_cargo_capacity,
                "aft": specs.aft_cargo_capacity
            },
            "cg_limits": {
                "forward": specs.cg_forward_limit,
                "aft": specs.cg_aft_limit,
                "optimal": specs.optimal_cg
            }
        }
    
    return {
        "variants": variants,
        "count": len(variants)
    }