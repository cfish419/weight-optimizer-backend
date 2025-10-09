"""
Enhanced Calculation Service
Integrates core calculations with optional advanced features
"""

from typing import Any, Dict

from config.features import FeatureFlags, plugin_manager
from services.observability_service import observability
from src.core.weight_balance import WeightBalanceCalculator


class EnhancedCalculationService:
    """Enhanced calculation service with optional ML optimization"""

    def __init__(self):
        self.core_calculator = WeightBalanceCalculator()

    @observability.track_performance("EnhancedCalculation")
    def calculate_with_enhancements(self, config) -> Dict[str, Any]:
        """Calculate with optional ML enhancements"""
        # Always perform core calculation
        core_result = {
            "center_of_gravity": self.core_calculator.calculate_center_of_gravity(
                config
            ),
            "weight_limits": self.core_calculator.validate_weight_limits(config),
            "cg_valid": self.core_calculator.validate_cg_limits(config),
            "calculation_method": "core",
        }

        # Enhance with ML if available
        ml_plugin = plugin_manager.get_plugin("ML_OPTIMIZATION")
        if ml_plugin and ml_plugin.is_healthy():
            try:
                enhanced_result = ml_plugin.optimize_loading(core_result)
                enhanced_result["calculation_method"] = "ml_enhanced"

                # Track ML usage
                observability.put_metric("MLOptimizationUsed", 1)

                return enhanced_result
            except Exception:
                # Fall back to core result if ML fails
                observability.put_metric("MLOptimizationFailed", 1)

        return core_result

    def get_fuel_prediction(self, config) -> Dict[str, Any]:
        """Get fuel savings prediction if ML is available"""
        ml_plugin = plugin_manager.get_plugin("ML_OPTIMIZATION")

        if ml_plugin and ml_plugin.is_healthy():
            prediction = ml_plugin.predict_fuel_savings(config)
            if prediction:
                return {
                    "fuel_savings_percent": prediction,
                    "prediction_available": True,
                    "source": "ml_model",
                }

        # Fallback to basic estimation
        return {
            "fuel_savings_percent": 2.0,  # Conservative estimate
            "prediction_available": False,
            "source": "baseline_estimate",
        }

    def is_ml_available(self) -> bool:
        """Check if ML optimization is available"""
        return FeatureFlags.is_enabled(
            FeatureFlags.ML_OPTIMIZATION
        ) and plugin_manager.is_plugin_available("ML_OPTIMIZATION")
