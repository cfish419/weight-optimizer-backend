from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from api.routes import baggage, weight_balance, devices, scenarios, auth
from services.baggage_tracking.baggage_service import BaggageService
from services.sync_engine.sync_service import SyncService
from services.offline_manager.offline_service import OfflineService
from services.scenario_service import ScenarioService
from services.weather_service import WeatherService
from data.database import get_database

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

# Session middleware for OAuth state management
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-key")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://demo.dev.balanceiq.com",
        "http://localhost:3000",  # Development
        "http://localhost:8000"   # API docs
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
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
    # Test database connection
    db_status = "healthy"
    try:
        db = get_database()
        # Simple connectivity test
        await db.get_flight("health-check")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "weight-optimizer-api",
        "version": "2.0.0",
        "database": db_status
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )