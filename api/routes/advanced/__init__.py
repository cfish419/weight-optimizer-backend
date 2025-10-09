"""
Advanced API Routes
Conditionally loaded based on feature flags
"""

from fastapi import APIRouter

from config.features import FeatureFlags

# Create routers for advanced features
advanced_router = APIRouter()

# Conditionally import and include advanced route modules
if FeatureFlags.is_enabled(FeatureFlags.ML_OPTIMIZATION):
    try:
        from .ml_routes import ml_router

        advanced_router.include_router(
            ml_router, prefix="/ml", tags=["ML Optimization"]
        )
    except ImportError:
        pass

if FeatureFlags.is_enabled(FeatureFlags.COMPLIANCE_REPORTING):
    try:
        from .compliance_routes import compliance_router

        advanced_router.include_router(
            compliance_router, prefix="/compliance", tags=["Compliance"]
        )
    except ImportError:
        pass

if FeatureFlags.is_enabled(FeatureFlags.PREDICTIVE_ANALYTICS):
    try:
        from .analytics_routes import analytics_router

        advanced_router.include_router(
            analytics_router, prefix="/analytics", tags=["Analytics"]
        )
    except ImportError:
        pass
