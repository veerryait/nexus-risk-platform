"""
Routes API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.route import RouteResponse, RouteWithRisk

router = APIRouter()


# Taiwan to US West Coast routes
ROUTES = [
    {"id": 1, "origin": "Kaohsiung, Taiwan", "destination": "Los Angeles, CA", "distance_nm": 6500, "avg_transit_days": 16},
    {"id": 2, "origin": "Kaohsiung, Taiwan", "destination": "Long Beach, CA", "distance_nm": 6500, "avg_transit_days": 16},
    {"id": 3, "origin": "Keelung, Taiwan", "destination": "Oakland, CA", "distance_nm": 6200, "avg_transit_days": 15},
    {"id": 4, "origin": "Taichung, Taiwan", "destination": "Seattle, WA", "distance_nm": 5800, "avg_transit_days": 14},
    {"id": 5, "origin": "Kaohsiung, Taiwan", "destination": "San Francisco, CA", "distance_nm": 6400, "avg_transit_days": 16},
]


@router.get("/", response_model=List[RouteResponse])
async def get_routes(db: Session = Depends(get_db)):
    """Get all tracked routes"""
    return ROUTES


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get route by ID"""
    for route in ROUTES:
        if route["id"] == route_id:
            return route
    raise HTTPException(status_code=404, detail="Route not found")


@router.get("/{route_id}/risk", response_model=RouteWithRisk)
async def get_route_risk(route_id: int, db: Session = Depends(get_db)):
    """Get route with current risk assessment"""
    for route in ROUTES:
        if route["id"] == route_id:
            return {
                **route,
                "risk_score": 0.35,
                "risk_factors": [
                    {"factor": "weather", "impact": 0.15},
                    {"factor": "port_congestion", "impact": 0.20}
                ],
                "predicted_delay_hours": 12
            }
    raise HTTPException(status_code=404, detail="Route not found")
