"""
ML Optimization API Routes
Advanced machine learning endpoints
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from config.features import plugin_manager
from plugins.ml_optimization import MLOptimizationPlugin

ml_router = APIRouter()

# Initialize ML plugin
ml_plugin = MLOptimizationPlugin()
if ml_plugin.initialize():
    plugin_manager.register_plugin("ML_OPTIMIZATION", ml_plugin)


@ml_router.get("/status")
async def ml_status():
    """Get ML optimization status"""
    plugin = plugin_manager.get_plugin("ML_OPTIMIZATION")
    return {
        "enabled": plugin is not None,
        "healthy": plugin.is_healthy() if plugin else False,
        "features": ["load_optimization", "fuel_prediction"],
    }


@ml_router.post("/optimize")
async def ml_optimize_loading(calculation_data: Dict[str, Any]):
    """Enhance weight calculation with ML optimization"""
    plugin = plugin_manager.get_plugin("ML_OPTIMIZATION")

    if not plugin:
        raise HTTPException(status_code=503, detail="ML optimization not available")

    try:
        optimized_result = plugin.optimize_loading(calculation_data)
        return {"status": "success", "data": optimized_result, "ml_enhanced": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML optimization failed: {str(e)}")


@ml_router.post("/predict-fuel-savings")
async def predict_fuel_savings(config: Dict[str, Any]):
    """Predict fuel savings using ML model"""
    plugin = plugin_manager.get_plugin("ML_OPTIMIZATION")

    if not plugin:
        raise HTTPException(status_code=503, detail="ML prediction not available")

    prediction = plugin.predict_fuel_savings(config)

    if prediction is None:
        raise HTTPException(status_code=500, detail="Prediction failed")

    return {
        "predicted_fuel_savings_percent": prediction,
        "confidence": "high",
        "model_version": "1.0",
    }
