from typing import Tuple, Dict
from ..models.aircraft import FlightConfiguration, LoadItem


class WeightBalanceCalculator:
    
    @staticmethod
    def calculate_total_weight(config: FlightConfiguration) -> float:
        """Calculate total aircraft weight"""
        passenger_weight = config.passenger_count * config.passenger_weight_avg
        carry_on_weight = config.passenger_count * config.carry_on_weight_avg
        checked_baggage_weight = config.passenger_count * config.checked_baggage_weight_avg
        crew_weight = config.crew_count * config.crew_weight_avg
        cargo_weight = sum(item.weight for item in config.cargo_items)
        
        return (config.aircraft.empty_weight + passenger_weight + 
                carry_on_weight + checked_baggage_weight + crew_weight + 
                config.fuel_weight + cargo_weight)
    
    @staticmethod
    def calculate_center_of_gravity(config: FlightConfiguration) -> float:
        """Calculate aircraft center of gravity as percentage of MAC"""
        # Simplified calculation - would need actual arm data for precise results
        total_moment = 0.0
        total_weight = 0.0
        
        # Aircraft empty weight moment (assumed at 25% MAC)
        empty_moment = config.aircraft.empty_weight * 0.25
        total_moment += empty_moment
        total_weight += config.aircraft.empty_weight
        
        # Passenger moments (distributed across cabin)
        passenger_weight = config.passenger_count * config.passenger_weight_avg
        passenger_moment = passenger_weight * 0.28  # Approximate passenger arm
        total_moment += passenger_moment
        total_weight += passenger_weight
        
        # Baggage moments
        carry_on_weight = config.passenger_count * config.carry_on_weight_avg
        carry_on_moment = carry_on_weight * 0.28  # Same as passengers
        total_moment += carry_on_moment
        total_weight += carry_on_weight
        
        checked_weight = config.passenger_count * config.checked_baggage_weight_avg
        checked_moment = checked_weight * 0.20  # Forward cargo hold
        total_moment += checked_moment
        total_weight += checked_weight
        
        # Crew moment
        crew_weight = config.crew_count * config.crew_weight_avg
        crew_moment = crew_weight * 0.15  # Forward position
        total_moment += crew_moment
        total_weight += crew_weight
        
        # Fuel moment (wing tanks, approximately at CG)
        fuel_moment = config.fuel_weight * 0.25
        total_moment += fuel_moment
        total_weight += config.fuel_weight
        
        # Cargo moments
        for item in config.cargo_items:
            total_moment += item.weight * (item.arm / 100)  # Convert to MAC %
            total_weight += item.weight
        
        return total_moment / total_weight if total_weight > 0 else 0.0
    
    @staticmethod
    def validate_weight_limits(config: FlightConfiguration) -> Dict[str, bool]:
        """Validate aircraft weight limits"""
        total_weight = WeightBalanceCalculator.calculate_total_weight(config)
        
        return {
            "mtow_valid": total_weight <= config.aircraft.max_takeoff_weight,
            "mlw_valid": total_weight <= config.aircraft.max_landing_weight,
            "mzfw_valid": (total_weight - config.fuel_weight) <= config.aircraft.max_zero_fuel_weight
        }
    
    @staticmethod
    def validate_cg_limits(config: FlightConfiguration) -> bool:
        """Validate center of gravity is within limits"""
        cg = WeightBalanceCalculator.calculate_center_of_gravity(config)
        return (config.aircraft.forward_cg_limit <= cg <= config.aircraft.aft_cg_limit)