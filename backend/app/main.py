"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, vessels, routes, predictions
from app.core.config import settings

app = FastAPI(
    title="Nexus Risk Platform API",
    description="Supply Chain Resilience Predictor - Taiwan to US West Coast Semiconductor Routes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(vessels.router, prefix="/api/v1/vessels", tags=["Vessels"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])


@app.get("/")
async def root():
    return {
        "name": "Nexus Risk Platform API",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs"
    }
