from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="IBL System API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from src.api.routes import baggage, flights, optimization

app.include_router(baggage.router, prefix="/api/v1/baggage", tags=["baggage"])
app.include_router(flights.router, prefix="/api/v1/flights", tags=["flights"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"])

@app.get("/")
async def root():
    return {"message": "Welcome to IBL System API"}