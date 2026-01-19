"""
Explainable AI (XAI) API Endpoints
Provides plain English explanations for all predictions
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.services.xai_service import get_xai_service
from app.services.live_data_service import get_integrated_dashboard_data

router = APIRouter()


class DelayExplanationRequest(BaseModel):
    route_id: str
    origin: str
    destination: str
    predicted_delay: float
    risk_level: str = "medium"
    features: Dict[str, Any] = {}


class RiskExplanationRequest(BaseModel):
    entity_type: str  # route, port, vessel
    entity_name: str
    risk_score: float
    factors: Dict[str, float] = {}


@router.get("/delay/{route_id}")
async def explain_route_delay(route_id: str):
    """
    Get AI explanation for a route's predicted delay
    
    Returns plain English explanation of:
    - Primary cause of delay
    - Contributing factors
    - Actionable recommendations
    """
    xai = get_xai_service()
    dashboard_data = get_integrated_dashboard_data()
    
    # Find route in data
    route = None
    for r in dashboard_data.get('routes', []):
        if r['id'] == route_id:
            route = r
            break
    
    if not route:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")
    
    # Build features from route data
    features = {
        "weather_risk": route.get('weather_impact', {}).get('risk_increase', 0) / 100,
        "origin_congestion": 0.5,  # Would come from port data
        "dest_congestion": 0.6,
        "geopolitical_risk": 0.2,
        "distance_nm": route.get('distance_nm', 5000),
        "historical_delay": route.get('predicted_delay_days', 0)
    }
    
    # Get port congestion
    for port in dashboard_data.get('ports', []):
        if port['code'] == route.get('origin_code'):
            features['origin_congestion'] = port['congestion_level']
        if port['code'] == route.get('dest_code'):
            features['dest_congestion'] = port['congestion_level']
    
    explanation = xai.explain_delay_prediction(
        route_id=route_id,
        origin=route.get('origin', route.get('origin_code', 'Origin')),
        destination=route.get('destination', route.get('dest_code', 'Destination')),
        predicted_delay=route.get('predicted_delay_days', 0),
        risk_level=route.get('risk_level', 'medium'),
        features=features
    )
    
    return explanation


@router.post("/delay")
async def explain_delay_custom(request: DelayExplanationRequest):
    """
    Get AI explanation for a custom delay prediction
    """
    xai = get_xai_service()
    
    return xai.explain_delay_prediction(
        route_id=request.route_id,
        origin=request.origin,
        destination=request.destination,
        predicted_delay=request.predicted_delay,
        risk_level=request.risk_level,
        features=request.features
    )


@router.get("/risk/{entity_type}/{entity_name}")
async def explain_risk_score(entity_type: str, entity_name: str):
    """
    Explain why an entity (route/port/vessel) has its current risk score
    """
    xai = get_xai_service()
    dashboard_data = get_integrated_dashboard_data()
    
    risk_score = 50.0
    factors = {}
    
    if entity_type == "port":
        for port in dashboard_data.get('ports', []):
            if port['code'] == entity_name.upper():
                risk_score = port['congestion_level'] * 100
                factors = {
                    "congestion_level": port['congestion_level'],
                    "wait_time": port['wait_time_hours'] / 48,
                    "seasonal_factor": 0.1
                }
                break
    elif entity_type == "route":
        for route in dashboard_data.get('routes', []):
            if route['id'] == entity_name:
                risk_score = route.get('risk_score', 50)
                weather_impact = route.get('weather_impact', {})
                factors = {
                    "weather_risk": weather_impact.get('risk_increase', 0) / 100,
                    "distance_factor": route.get('distance_nm', 5000) / 10000,
                    "historical_delays": route.get('predicted_delay_days', 0) / 10
                }
                break
    
    return xai.explain_risk_score(
        entity_type=entity_type,
        entity_name=entity_name,
        risk_score=risk_score,
        factors=factors
    )


@router.get("/cascade/{port_code}")
async def explain_cascade(port_code: str):
    """
    Get narrative explanation of cascade effects from a port failure
    """
    from app.ml.gnn_inference import get_gnn_service
    
    xai = get_xai_service()
    gnn = get_gnn_service()
    dashboard_data = get_integrated_dashboard_data()
    
    # Run cascade simulation
    cascade_result = gnn.simulate_cascade(dashboard_data, port_code.upper())
    
    if "error" in cascade_result:
        raise HTTPException(status_code=404, detail=cascade_result["error"])
    
    # Generate explanation
    explanation = xai.explain_cascade_effect(
        source_port=port_code.upper(),
        affected_ports=cascade_result.get('cascade_simulation', []),
        propagation_depth=cascade_result.get('propagation_depth', 0),
        total_impact=cascade_result.get('total_impact_score', 0)
    )
    
    return {
        **cascade_result,
        "explanation": explanation
    }


@router.get("/weather")
async def explain_weather_impacts():
    """
    Get explanations for current weather impacts on routes
    """
    xai = get_xai_service()
    dashboard_data = get_integrated_dashboard_data()
    
    weather_explanations = []
    
    for weather in dashboard_data.get('weather_systems', []):
        # Find affected routes
        affected_routes = []
        for route in dashboard_data.get('routes', []):
            weather_impact = route.get('weather_impact', {})
            if weather_impact.get('current_weather'):
                affected_routes.append(route['id'])
        
        explanation = xai.explain_weather_impact(
            weather_system=weather,
            affected_routes=affected_routes[:5]
        )
        weather_explanations.append(explanation)
    
    return {
        "weather_count": len(weather_explanations),
        "explanations": weather_explanations
    }


@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """
    Get a complete XAI summary for the entire dashboard
    Returns plain English explanations for all major metrics
    """
    xai = get_xai_service()
    dashboard_data = get_integrated_dashboard_data()
    
    # Analyze routes
    routes = dashboard_data.get('routes', [])
    high_risk_routes = [r for r in routes if r.get('risk_score', 0) > 70]
    delayed_routes = [r for r in routes if r.get('predicted_delay_days', 0) > 2]
    
    # Analyze ports
    ports = dashboard_data.get('ports', [])
    congested_ports = [p for p in ports if p.get('congestion_level', 0) > 0.7]
    
    # Analyze weather
    weather_systems = dashboard_data.get('weather_systems', [])
    severe_weather = [w for w in weather_systems if w.get('intensity') == 'severe']
    
    # Build summary insights
    insights = []
    
    # Route insight
    if high_risk_routes:
        route_names = ", ".join([r['id'][:10] for r in high_risk_routes[:2]])
        insights.append({
            "category": "Routes",
            "icon": "🛳️",
            "title": f"{len(high_risk_routes)} High-Risk Routes",
            "description": f"Routes {route_names} are experiencing elevated risk due to weather and congestion factors.",
            "severity": "high",
            "action": "Review alternative routing options"
        })
    else:
        insights.append({
            "category": "Routes",
            "icon": "✅",
            "title": "Routes Operating Normally",
            "description": "All shipping routes are within acceptable risk parameters.",
            "severity": "low",
            "action": "Continue monitoring"
        })
    
    # Weather insight
    if severe_weather:
        weather_names = ", ".join([w.get('name', 'Storm') for w in severe_weather])
        insights.append({
            "category": "Weather",
            "icon": "🌀",
            "title": f"Severe Weather Alert",
            "description": f"{weather_names} may cause delays of 2-4 days on affected routes.",
            "severity": "high",
            "action": "Vessels should alter course to avoid storm paths"
        })
    elif weather_systems:
        insights.append({
            "category": "Weather",
            "icon": "🌤️",
            "title": f"{len(weather_systems)} Weather Systems Tracked",
            "description": "Moderate conditions detected but no severe impact expected.",
            "severity": "medium",
            "action": "Monitor weather updates"
        })
    else:
        insights.append({
            "category": "Weather",
            "icon": "☀️",
            "title": "Favorable Weather",
            "description": "Clear conditions across major shipping lanes.",
            "severity": "low",
            "action": "No weather-related actions needed"
        })
    
    # Port insight
    if congested_ports:
        port_names = ", ".join([p['code'] for p in congested_ports[:2]])
        insights.append({
            "category": "Ports",
            "icon": "🚢",
            "title": f"{len(congested_ports)} Congested Ports",
            "description": f"{port_names} operating above 70% capacity. Expect berthing delays.",
            "severity": "high" if len(congested_ports) > 2 else "medium",
            "action": "Pre-book berthing slots and consider timing adjustments"
        })
    else:
        insights.append({
            "category": "Ports",
            "icon": "⚓",
            "title": "Ports Operating Efficiently",
            "description": "All monitored ports have adequate capacity.",
            "severity": "low",
            "action": "No congestion-related delays expected"
        })
    
    # Calculate overall status
    high_severity_count = len([i for i in insights if i['severity'] == 'high'])
    if high_severity_count >= 2:
        overall_status = "critical"
        overall_message = "Multiple high-severity issues require immediate attention"
    elif high_severity_count == 1:
        overall_status = "warning"
        overall_message = "One area requires monitoring but operations can continue"
    else:
        overall_status = "healthy"
        overall_message = "Supply chain operating within normal parameters"
    
    return {
        "generated_at": dashboard_data.get('generated_at'),
        "overall_status": overall_status,
        "overall_message": overall_message,
        "insights": insights,
        "quick_stats": {
            "total_routes": len(routes),
            "high_risk_routes": len(high_risk_routes),
            "delayed_routes": len(delayed_routes),
            "congested_ports": len(congested_ports),
            "active_weather": len(weather_systems)
        }
    }


@router.get("/feature-importance/{prediction_type}")
async def get_feature_importance(prediction_type: str):
    """
    Show which features most influence predictions
    Like a simplified SHAP explanation
    """
    xai = get_xai_service()
    
    # Example feature importances (in production, would come from model)
    if prediction_type == "delay":
        features = {
            "weather_risk": 0.35,
            "port_congestion": 0.25,
            "distance_nm": 0.15,
            "geopolitical_risk": 0.12,
            "seasonal_factor": 0.08,
            "vessel_speed": 0.05
        }
        prediction = 3.5
    elif prediction_type == "risk":
        features = {
            "port_congestion": 0.30,
            "weather_risk": 0.28,
            "historical_delay": 0.18,
            "geopolitical_risk": 0.14,
            "fuel_price": 0.10
        }
        prediction = 65.0
    else:
        features = {
            "network_connectivity": 0.25,
            "port_congestion": 0.22,
            "weather_exposure": 0.20,
            "distance_to_hub": 0.18,
            "historical_reliability": 0.15
        }
        prediction = 54.0
    
    return xai.get_feature_importance_explanation(features, prediction)
