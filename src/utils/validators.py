from typing import Dict, List
from ..models.aircraft import FlightConfiguration


class FAA_Validator:
    
    @staticmethod
    def validate_weight_balance_compliance(config: FlightConfiguration) -> Dict[str, bool]:
        """Validate FAA weight and balance compliance"""
        from ..core.weight_balance import WeightBalanceCalculator
        
        weight_limits = WeightBalanceCalculator.validate_weight_limits(config)
        cg_valid = WeightBalanceCalculator.validate_cg_limits(config)
        
        return {
            "mtow_compliant": weight_limits["mtow_valid"],
            "mlw_compliant": weight_limits["mlw_valid"], 
            "mzfw_compliant": weight_limits["mzfw_valid"],
            "cg_compliant": cg_valid,
            "overall_compliant": all(weight_limits.values()) and cg_valid
        }
    
    @staticmethod
    def validate_cargo_compartment_limits(config: FlightConfiguration) -> Dict[str, bool]:
        """Validate individual cargo compartment weight limits"""
        from ..core.optimizer import LoadOptimizer
        
        distribution = LoadOptimizer.optimize_baggage_distribution(config)
        
        forward_limit = config.aircraft.cargo_compartments["forward"]["max_weight"]
        aft_limit = config.aircraft.cargo_compartments["aft"]["max_weight"]
        
        return {
            "forward_compliant": distribution["forward_cargo"] <= forward_limit,
            "aft_compliant": distribution["aft_cargo"] <= aft_limit,
            "total_within_limits": (distribution["forward_cargo"] <= forward_limit and 
                                  distribution["aft_cargo"] <= aft_limit)
        }