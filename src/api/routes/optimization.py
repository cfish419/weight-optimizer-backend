from fastapi import APIRouter, HTTPException
from src.models.optimization import LoadingPlan
from src.services.optimization_service import OptimizationService

router = APIRouter()
optimization_service = OptimizationService()

@router.post("/calculate-loading-plan/{flight_id}", response_model=LoadingPlan)
async def calculate_loading_plan(flight_id: str):
    """Calculate optimal loading plan for a flight"""
    try:
        return await optimization_service.calculate_loading_plan(flight_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/loading-plan/{flight_id}", response_model=LoadingPlan)
async def get_loading_plan(flight_id: str):
    """Get the current loading plan for a flight"""
    plan = await optimization_service.get_loading_plan(flight_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Loading plan not found")
    return plan