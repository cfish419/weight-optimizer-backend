from typing import List, Dict, Tuple
from ..models.aircraft import FlightConfiguration, LoadItem
from .weight_balance import WeightBalanceCalculator


class LoadOptimizer:
    
    @staticmethod
    def optimize_baggage_distribution(config: FlightConfiguration) -> Dict[str, float]:
        """Optimize baggage distribution between forward and aft cargo holds"""
        total_checked_weight = config.passenger_count * config.checked_baggage_weight_avg
        
        # Start with even distribution
        forward_weight = total_checked_weight * 0.6  # Prefer forward for stability
        aft_weight = total_checked_weight * 0.4
        
        # Check compartment limits
        max_forward = config.aircraft.cargo_compartments["forward"]["max_weight"]
        max_aft = config.aircraft.cargo_compartments["aft"]["max_weight"]
        
        # Redistribute if limits exceeded
        if forward_weight > max_forward:
            overflow = forward_weight - max_forward
            forward_weight = max_forward
            aft_weight += overflow
            
        if aft_weight > max_aft:
            overflow = aft_weight - max_aft
            aft_weight = max_aft
            forward_weight += overflow
            
        return {
            "forward_cargo": forward_weight,
            "aft_cargo": aft_weight,
            "total_cargo": forward_weight + aft_weight
        }
    
    @staticmethod
    def calculate_optimal_cg(config: FlightConfiguration) -> float:
        """Calculate optimal CG position for fuel efficiency"""
        # Optimal CG is typically around 27-30% MAC for fuel efficiency
        return 0.28
    
    @staticmethod
    def suggest_ballast(config: FlightConfiguration) -> Dict[str, float]:
        """Suggest ballast placement to achieve optimal CG"""
        current_cg = WeightBalanceCalculator.calculate_center_of_gravity(config)
        optimal_cg = LoadOptimizer.calculate_optimal_cg(config)
        
        ballast_needed = 0.0
        ballast_location = "none"
        
        cg_difference = current_cg - optimal_cg
        
        if abs(cg_difference) > 0.02:  # 2% MAC tolerance
            total_weight = WeightBalanceCalculator.calculate_total_weight(config)
            
            if cg_difference > 0:  # CG too far aft
                ballast_needed = abs(cg_difference) * total_weight * 2
                ballast_location = "forward"
            else:  # CG too far forward
                ballast_needed = abs(cg_difference) * total_weight * 2
                ballast_location = "aft"
        
        return {
            "ballast_weight": ballast_needed,
            "ballast_location": ballast_location,
            "current_cg": current_cg,
            "optimal_cg": optimal_cg
        }