from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
 
app = FastAPI(title="Weight Optimizer API", version="1.0.0")
 
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)