from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import baggage, flights, optimization

app = FastAPI(
    title="Southwest Airlines Baggage Optimizer",
    description="API for optimizing aircraft baggage loading positions",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flights.router, prefix="/api/flights", tags=["Flights"])
app.include_router(baggage.router, prefix="/api/baggage", tags=["Baggage"])
app.include_router(
    optimization.router, prefix="/api/optimization", tags=["Optimization"]
)


@app.get("/")
async def root():
    return {
        "message": "Southwest Airlines Baggage Optimization API",
        "docs": "/docs",
        "redoc": "/redoc",
    }
