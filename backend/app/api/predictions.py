"""
Predictions API Endpoints - Updated to use real risk calculator
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.services.risk_calculator import risk_calculator

router = APIRouter()


# Route ID mapping
ROUTE_MAP = {
    1: "kaohsiung_losangeles",
    2: "kaohsiung_longbeach",
    3: "kaohsiung_oakland",
}

ROUTE_NAMES = {
    1: "Kaohsiung → Los Angeles",
    2: "Kaohsiung → Long Beach",
    3: "Kaohsiung → Oakland",
}


@router.get("/")
async def get_predictions(
    route_id: Optional[int] = Query(None, description="Route ID (1=LA, 2=Long Beach, 3=Oakland)"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get real-time predictions using aggregated data sources"""
    
    # If specific route requested, calculate for that route
    if route_id and route_id in ROUTE_MAP:
        route_key = ROUTE_MAP[route_id]
        risk_data = await risk_calculator.calculate_route_risk(route_key)
        
        return [{
            "id": route_id,
            "route_id": route_id,
            "route_name": ROUTE_NAMES.get(route_id, "Unknown Route"),
            "predicted_delay_hours": risk_data["predicted_delay_hours"],
            "confidence": risk_data["confidence"],
            "risk_score": risk_data["overall_risk_score"],
            "risk_level": risk_data["risk_level"],
            "factors": [
                {
                    "name": factor,
                    "score": data["score"],
                    "contribution": data["contribution"]
                }
                for factor, data in risk_data["risk_factors"].items()
            ],
            "top_risk_factor": risk_data["top_risk_factor"]["factor"],
            "recommendations": risk_data["recommendations"],
            "created_at": risk_data["calculated_at"],
        }]
    
    # Otherwise, return predictions for all routes
    predictions = []
    for rid, route_key in ROUTE_MAP.items():
        risk_data = await risk_calculator.calculate_route_risk(route_key)
        predictions.append({
            "id": rid,
            "route_id": rid,
            "route_name": ROUTE_NAMES.get(rid, "Unknown Route"),
            "predicted_delay_hours": risk_data["predicted_delay_hours"],
            "confidence": risk_data["confidence"],
            "risk_score": risk_data["overall_risk_score"],
            "risk_level": risk_data["risk_level"],
            "factors": [
                {
                    "name": factor,
                    "score": data["score"],
                    "contribution": data["contribution"]
                }
                for factor, data in risk_data["risk_factors"].items()
            ],
            "top_risk_factor": risk_data["top_risk_factor"]["factor"],
            "recommendations": risk_data["recommendations"],
            "created_at": risk_data["calculated_at"],
        })
    
    return predictions[:limit]


@router.get("/summary")
async def get_risk_summary(db: Session = Depends(get_db)):
    """Get overall risk summary for all routes using real data"""
    summary = await risk_calculator.get_risk_summary()
    
    # Map to expected schema format
    return {
        "overall_risk": summary["overall_risk"],
        "overall_level": summary["overall_level"],
        "routes_at_risk": summary["routes_at_risk"],
        "total_routes": summary["total_routes"],
        "average_delay_hours": summary["average_delay_hours"],
        "routes": summary["routes"],
        "last_updated": summary["last_updated"],
    }


@router.post("/analyze/{route_id}")
async def trigger_analysis(route_id: int, db: Session = Depends(get_db)):
    """Trigger a new prediction analysis for a route"""
    if route_id not in ROUTE_MAP:
        return {
            "status": "error",
            "message": f"Unknown route_id: {route_id}. Valid IDs: 1 (LA), 2 (Long Beach), 3 (Oakland)"
        }
    
    route_key = ROUTE_MAP[route_id]
    
    # Actually perform the analysis
    risk_data = await risk_calculator.calculate_route_risk(route_key)
    
    return {
        "status": "completed",
        "route_id": route_id,
        "route_name": ROUTE_NAMES[route_id],
        "result": {
            "risk_score": risk_data["overall_risk_score"],
            "risk_level": risk_data["risk_level"],
            "predicted_delay_hours": risk_data["predicted_delay_hours"],
            "top_risk_factor": risk_data["top_risk_factor"],
            "recommendations": risk_data["recommendations"],
        },
        "calculated_at": risk_data["calculated_at"],
    }
