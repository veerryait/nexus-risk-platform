"""
FastAPI Application Entry Point
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, vessels, routes, predictions, data_sources, admin, ai, news, predict, analytics, notifications, emissions, anomaly, auth, scenarios, dashboard, gnn, xai, model_metrics
from app.core.config import settings
from app.core.error_handler import SecureErrorMiddleware, setup_exception_handlers

app = FastAPI(
    title="Nexus Risk Platform API",
    description="Supply Chain Resilience Predictor - Taiwan to US West Coast Semiconductor Routes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Secure error handling - prevents information leakage
app.add_middleware(SecureErrorMiddleware)
setup_exception_handlers(app)

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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(gnn.router, prefix="/api/v1/gnn", tags=["Graph Neural Network"])
app.include_router(xai.router, prefix="/api/v1/xai", tags=["Explainable AI"])
app.include_router(model_metrics.router, prefix="/api/v1/model-metrics", tags=["Model Performance"])
app.include_router(vessels.router, prefix="/api/v1/vessels", tags=["Vessels"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["Predictions"])
app.include_router(data_sources.router, prefix="/api/v1/data", tags=["Data Sources"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])
app.include_router(news.router, prefix="/api/v1/news", tags=["News"])
app.include_router(predict.router, prefix="/api/v1/predict", tags=["ML Predictions"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(emissions.router, prefix="/api/v1/emissions", tags=["Emissions"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(scenarios.router, prefix="/api/v1/scenarios", tags=["Scenario Simulation"])


@app.get("/")
async def root():
    return {
        "name": "Nexus Risk Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }
