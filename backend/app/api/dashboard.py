"""
Dashboard API - Unified endpoint for integrated live data
"""

from fastapi import APIRouter
from app.services.live_data_service import get_integrated_dashboard_data

router = APIRouter()


@router.get("/live")
async def get_live_dashboard():
    """
    Get fully integrated live dashboard data.
    
    Returns all data needed for the dashboard with cross-references:
    - Routes with weather impact and port delays
    - Vessels with positions and ETAs
    - Weather systems affecting routes
    - Sea conditions by region
    - Port congestion levels
    - Analytics summary
    
    Data updates based on current time and seasonal factors.
    """
    return get_integrated_dashboard_data()


@router.get("/summary")
async def get_dashboard_summary():
    """Get quick dashboard summary stats"""
    data = get_integrated_dashboard_data()
    return data.get("summary", {})


@router.get("/routes")
async def get_routes_with_impact():
    """Get routes with integrated weather and port impact"""
    data = get_integrated_dashboard_data()
    return {"routes": data.get("routes", []), "timestamp": data.get("timestamp")}


@router.get("/vessels")
async def get_vessels_positions():
    """Get vessel positions and ETAs"""
    data = get_integrated_dashboard_data()
    return {"vessels": data.get("vessels", []), "timestamp": data.get("timestamp")}


@router.get("/weather")
async def get_weather_integrated():
    """Get weather systems and sea conditions"""
    data = get_integrated_dashboard_data()
    return {
        "weather_systems": data.get("weather_systems", []),
        "sea_conditions": data.get("sea_conditions", []),
        "timestamp": data.get("timestamp")
    }


@router.get("/ports")
async def get_ports_congestion():
    """Get port congestion data"""
    data = get_integrated_dashboard_data()
    return {"ports": data.get("ports", []), "timestamp": data.get("timestamp")}


@router.get("/analytics")
async def get_analytics():
    """Get analytics data"""
    data = get_integrated_dashboard_data()
    return {**data.get("analytics", {}), "timestamp": data.get("timestamp")}
