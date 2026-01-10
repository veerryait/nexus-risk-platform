"""
Shipping Routes API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


# Route definitions for Taiwan to US West Coast
SHIPPING_ROUTES = [
    {
        "id": 1,
        "name": "Kaohsiung → Los Angeles",
        "origin": {"port": "Kaohsiung", "country": "Taiwan", "code": "TWKHH"},
        "destination": {"port": "Los Angeles", "country": "USA", "code": "USLAX"},
        "distance_nm": 6150,
        "typical_days": 14,
        "transit_points": ["Pacific Ocean"],
    },
    {
        "id": 2,
        "name": "Kaohsiung → Long Beach",
        "origin": {"port": "Kaohsiung", "country": "Taiwan", "code": "TWKHH"},
        "destination": {"port": "Long Beach", "country": "USA", "code": "USLGB"},
        "distance_nm": 6150,
        "typical_days": 14,
        "transit_points": ["Pacific Ocean"],
    },
    {
        "id": 3,
        "name": "Kaohsiung → Oakland",
        "origin": {"port": "Kaohsiung", "country": "Taiwan", "code": "TWKHH"},
        "destination": {"port": "Oakland", "country": "USA", "code": "USOAK"},
        "distance_nm": 5950,
        "typical_days": 13,
        "transit_points": ["Pacific Ocean"],
    },
    {
        "id": 4,
        "name": "Taipei → Los Angeles",
        "origin": {"port": "Taipei", "country": "Taiwan", "code": "TWTPE"},
        "destination": {"port": "Los Angeles", "country": "USA", "code": "USLAX"},
        "distance_nm": 6300,
        "typical_days": 15,
        "transit_points": ["Pacific Ocean"],
    },
    {
        "id": 5,
        "name": "Kaohsiung → Seattle",
        "origin": {"port": "Kaohsiung", "country": "Taiwan", "code": "TWKHH"},
        "destination": {"port": "Seattle", "country": "USA", "code": "USSEA"},
        "distance_nm": 5200,
        "typical_days": 12,
        "transit_points": ["Pacific Ocean"],
    },
]


@router.get("/")
async def get_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get list of monitored shipping routes"""
    return SHIPPING_ROUTES[skip:skip + limit]


@router.get("/{route_id}")
async def get_route(route_id: int, db: Session = Depends(get_db)):
    """Get a specific route by ID"""
    for route in SHIPPING_ROUTES:
        if route["id"] == route_id:
            return route
    return {"error": f"Route {route_id} not found"}


@router.get("/{route_id}/details")
async def get_route_details(route_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a shipping route"""
    for route in SHIPPING_ROUTES:
        if route["id"] == route_id:
            return {
                **route,
                "details": {
                    "carriers": ["Evergreen", "Yang Ming", "Wan Hai"],
                    "cargo_types": ["Semiconductors", "Electronics", "Manufacturing"],
                    "frequency": "Daily departures",
                    "last_updated": datetime.utcnow().isoformat(),
                }
            }
    return {"error": f"Route {route_id} not found"}
