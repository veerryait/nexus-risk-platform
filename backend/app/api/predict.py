"""
Predict API - ML-based Risk Prediction Endpoint
POST /api/v1/predict - Make risk predictions for routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from app.services.prediction_service import prediction_service

router = APIRouter()


class RouteInput(BaseModel):
    """Input schema for route prediction"""
    route_id: str = Field(default="TWKHH-USLAX", description="Route identifier")
    origin: str = Field(default="TWKHH", description="Origin port code")
    destination: str = Field(default="USLAX", description="Destination port code")
    distance_nm: float = Field(default=6500, description="Distance in nautical miles")
    
    # Optional real-time data
    eta_delay: float = Field(default=0, description="Current ETA delay in days")
    speed_knots: float = Field(default=19.3, description="Current vessel speed")
    speed_anomaly: float = Field(default=0, description="Speed deviation %")
    position_deviation: float = Field(default=0, description="Position deviation %")
    
    # Weather conditions
    wind_speed: float = Field(default=15, description="Wind speed m/s")
    storm_risk: float = Field(default=0.2, ge=0, le=1, description="Storm risk 0-1")
    
    # Port conditions
    congestion: float = Field(default=0.3, ge=0, le=1, description="Port congestion 0-1")
    wait_ratio: float = Field(default=1.0, description="Wait time ratio")
    
    # News/sentiment
    news_risk: float = Field(default=0.2, ge=0, le=1, description="News risk score")
    
    # Carrier performance
    carrier_rate: float = Field(default=0.88, ge=0, le=1, description="Carrier on-time rate")
    
    # Optional date override
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month for prediction")

    class Config:
        json_schema_extra = {
            "example": {
                "route_id": "TWKHH-USLAX",
                "origin": "TWKHH",
                "destination": "USLAX",
                "distance_nm": 6500,
                "storm_risk": 0.3,
                "congestion": 0.4
            }
        }


class PredictionResult(BaseModel):
    """Output schema for prediction"""
    route_id: str
    prediction: Dict
    factors: List[Dict]
    recommendations: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


@router.post("/", response_model=PredictionResult)
async def predict_risk(route: RouteInput):
    """
    Predict delay risk for a shipping route
    
    Uses trained ML models (Random Forest) to predict:
    - Probability of on-time arrival
    - Expected delay in days
    - Risk level (low/medium/high/critical)
    """
    try:
        # Build route data dict
        route_data = route.model_dump()
        if route_data.get("month") is None:
            route_data["month"] = datetime.now().month
        
        # Get prediction from ML service
        result = prediction_service.predict(route_data)
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/batch")
async def predict_batch(routes: List[RouteInput]):
    """Predict risk for multiple routes"""
    if len(routes) > 50:
        raise HTTPException(400, "Maximum 50 routes per batch")
    
    results = []
    for route in routes:
        route_data = route.model_dump()
        if route_data.get("month") is None:
            route_data["month"] = datetime.now().month
        results.append(prediction_service.predict(route_data))
    
    return {"predictions": results, "count": len(results)}


@router.get("/health")
async def model_health():
    """Check if ML models are loaded"""
    service = prediction_service
    
    return {
        "status": "healthy" if service.classifier is not None else "degraded",
        "classifier_loaded": service.classifier is not None,
        "regressor_loaded": service.regressor is not None,
        "feature_count": len(service.feature_names) if service.feature_names else 0
    }
