from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from api.routes import baggage, weight_balance, devices, scenarios
from services.baggage_tracking.baggage_service import BaggageService
from services.sync_engine.sync_service import SyncService
from services.offline_manager.offline_service import OfflineService
from services.scenario_service import ScenarioService
from services.weather_service import WeatherService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Boeing 737 Weight & Balance Optimizer API...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Boeing 737 Weight & Balance Optimizer",
    description="Comprehensive cargo loading optimization system delivering $545K annual value per aircraft",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(baggage.router)
app.include_router(weight_balance.router)
app.include_router(devices.router)
app.include_router(scenarios.router)

@app.get("/")
async def root():
    return {
        "message": "Boeing 737 Weight & Balance Optimizer API",
        "version": "2.0.0",
        "features": [
            "Real-time weight/balance calculations",
            "Multi-agent coordination",
            "Offline resilience",
            "Special baggage handling",
            "FAA compliance automation",
            "IoT device integration",
            "Weather impact analysis",
            "Operational scenario handling"
        ],
        "endpoints": {
            "baggage": "/baggage",
            "weight_balance": "/weight-balance", 
            "devices": "/devices",
            "scenarios": "/scenarios",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "weight-optimizer-api",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )