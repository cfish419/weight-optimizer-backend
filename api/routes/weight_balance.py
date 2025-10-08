from typing import Dict, Any
from src.models.aircraft import Boeing737Specs, FlightConfiguration
from src.core.weight_balance import WeightBalanceCalculator
from src.core.optimizer import LoadOptimizer
from services.baggage_tracking.baggage_service import BaggageService


class WeightBalanceRoutes:
    """REST API routes for weight and balance calculations"""
    
    @staticmethod
    def calculate_weight_balance(flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weight and balance for a flight"""
        aircraft = Boeing737Specs()
        config = FlightConfiguration(
            aircraft=aircraft,
            passenger_count=flight_data.get('passenger_count', 0),
            fuel_weight=flight_data.get('fuel_weight', 0.0)
        )
        
        total_weight = WeightBalanceCalculator.calculate_total_weight(config)
        cg_position = WeightBalanceCalculator.calculate_center_of_gravity(config)
        weight_limits = WeightBalanceCalculator.validate_weight_limits(config)
        cg_valid = WeightBalanceCalculator.validate_cg_limits(config)
        
        return {
            "total_weight": total_weight,
            "center_of_gravity": cg_position,
            "weight_limits_valid": weight_limits,
            "cg_valid": cg_valid,
            "flight_id": flight_data.get('flight_id')
        }
    
    @staticmethod
    def optimize_loading(flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize baggage loading distribution"""
        aircraft = Boeing737Specs()
        config = FlightConfiguration(
            aircraft=aircraft,
            passenger_count=flight_data.get('passenger_count', 0),
            fuel_weight=flight_data.get('fuel_weight', 0.0)
        )
        
        baggage_dist = LoadOptimizer.optimize_baggage_distribution(config)
        ballast = LoadOptimizer.suggest_ballast(config)
        
        return {
            "baggage_distribution": baggage_dist,
            "ballast_recommendation": ballast,
            "flight_id": flight_data.get('flight_id')
        }