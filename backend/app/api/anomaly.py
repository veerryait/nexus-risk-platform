"""
Vessel Anomaly Detection API
ML-based detection for route deviations, speed anomalies, and unusual behavior
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime, timedelta
import math
import numpy as np
from dataclasses import dataclass
from enum import Enum

router = APIRouter()


class AnomalyType(str, Enum):
    ROUTE_DEVIATION = "route_deviation"
    SPEED_ANOMALY = "speed_anomaly"
    STATIONARY_ALERT = "stationary_alert"
    HEADING_ANOMALY = "heading_anomaly"
    AIS_GAP = "ais_gap"
    ZONE_ENTRY = "zone_entry"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Expected route waypoints for Taiwan to US West Coast
EXPECTED_ROUTES = {
    "TWKHH-USLAX": {
        "name": "Kaohsiung to Los Angeles",
        "waypoints": [
            {"lat": 22.62, "lng": 120.31, "name": "Kaohsiung"},
            {"lat": 25.0, "lng": 125.0, "name": "East China Sea"},
            {"lat": 30.0, "lng": 140.0, "name": "Pacific Entry"},
            {"lat": 35.0, "lng": 160.0, "name": "North Pacific"},
            {"lat": 35.0, "lng": 180.0, "name": "International Date Line"},
            {"lat": 35.0, "lng": -160.0, "name": "Mid Pacific"},
            {"lat": 34.0, "lng": -140.0, "name": "Approaching US"},
            {"lat": 33.74, "lng": -118.26, "name": "Los Angeles"},
        ],
        "expected_speed_range": (14, 24),  # knots
        "corridor_width_nm": 200,  # nautical miles
    }
}

# Risk zones to monitor
RISK_ZONES = [
    {"name": "Taiwan Strait", "center": {"lat": 24.0, "lng": 119.0}, "radius_nm": 150, "risk": "high"},
    {"name": "South China Sea", "center": {"lat": 15.0, "lng": 115.0}, "radius_nm": 300, "risk": "medium"},
    {"name": "Piracy Risk Zone", "center": {"lat": 5.0, "lng": 110.0}, "radius_nm": 200, "risk": "high"},
]


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in nautical miles"""
    R = 3440.065  # Earth radius in nautical miles
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def calculate_route_deviation(lat: float, lng: float, route_id: str = "TWKHH-USLAX") -> dict:
    """Calculate how far a vessel is from expected route corridor"""
    route = EXPECTED_ROUTES.get(route_id, EXPECTED_ROUTES["TWKHH-USLAX"])
    waypoints = route["waypoints"]
    
    # Find minimum distance to route line
    min_distance = float('inf')
    nearest_waypoint = None
    
    for i, wp in enumerate(waypoints):
        dist = haversine_distance(lat, lng, wp["lat"], wp["lng"])
        if dist < min_distance:
            min_distance = dist
            nearest_waypoint = wp
    
    # Check if outside corridor
    corridor_width = route["corridor_width_nm"]
    is_deviated = min_distance > corridor_width
    
    return {
        "distance_from_route_nm": round(min_distance, 1),
        "corridor_width_nm": corridor_width,
        "is_deviated": is_deviated,
        "nearest_waypoint": nearest_waypoint,
        "deviation_percentage": round((min_distance / corridor_width) * 100, 1)
    }


def detect_speed_anomaly(speed: float, route_id: str = "TWKHH-USLAX") -> dict:
    """Detect if speed is outside normal range"""
    route = EXPECTED_ROUTES.get(route_id, EXPECTED_ROUTES["TWKHH-USLAX"])
    min_speed, max_speed = route["expected_speed_range"]
    
    # Calculate z-score assuming normal distribution
    expected_mean = (min_speed + max_speed) / 2
    expected_std = (max_speed - min_speed) / 4  # Approximate
    z_score = (speed - expected_mean) / expected_std if expected_std > 0 else 0
    
    is_anomaly = speed < min_speed * 0.7 or speed > max_speed * 1.2
    
    severity = SeverityLevel.LOW
    if abs(z_score) > 3:
        severity = SeverityLevel.CRITICAL
    elif abs(z_score) > 2:
        severity = SeverityLevel.HIGH
    elif abs(z_score) > 1.5:
        severity = SeverityLevel.MEDIUM
    
    return {
        "current_speed": speed,
        "expected_range": route["expected_speed_range"],
        "z_score": round(z_score, 2),
        "is_anomaly": is_anomaly,
        "severity": severity.value,
        "description": "Too slow" if speed < min_speed else ("Too fast" if speed > max_speed else "Normal")
    }


def check_zone_entry(lat: float, lng: float) -> List[dict]:
    """Check if vessel has entered any risk zones"""
    alerts = []
    
    for zone in RISK_ZONES:
        dist = haversine_distance(lat, lng, zone["center"]["lat"], zone["center"]["lng"])
        if dist <= zone["radius_nm"]:
            alerts.append({
                "zone_name": zone["name"],
                "risk_level": zone["risk"],
                "distance_to_center_nm": round(dist, 1),
                "in_zone": True
            })
    
    return alerts


def detect_vessel_anomalies(
    vessel_id: str,
    name: str,
    lat: float,
    lng: float,
    speed: float,
    heading: float,
    status: str,
    last_update: Optional[str] = None
) -> dict:
    """Comprehensive anomaly detection for a single vessel"""
    anomalies = []
    risk_score = 0
    
    # 1. Route deviation check
    route_check = calculate_route_deviation(lat, lng)
    if route_check["is_deviated"]:
        severity = SeverityLevel.HIGH if route_check["distance_from_route_nm"] > 500 else SeverityLevel.MEDIUM
        anomalies.append({
            "type": AnomalyType.ROUTE_DEVIATION.value,
            "severity": severity.value,
            "title": "Route Deviation Detected",
            "description": f"Vessel is {route_check['distance_from_route_nm']} nm from expected route corridor",
            "details": route_check
        })
        risk_score += 30 if severity == SeverityLevel.HIGH else 15
    
    # 2. Speed anomaly check
    speed_check = detect_speed_anomaly(speed)
    if speed_check["is_anomaly"]:
        anomalies.append({
            "type": AnomalyType.SPEED_ANOMALY.value,
            "severity": speed_check["severity"],
            "title": f"Unusual Speed: {speed_check['description']}",
            "description": f"Current speed {speed} kts is outside normal range {speed_check['expected_range']}",
            "details": speed_check
        })
        risk_score += {"low": 5, "medium": 15, "high": 25, "critical": 40}.get(speed_check["severity"], 10)
    
    # 3. Stationary check (vessel stopped unexpectedly)
    if status == "underway" and speed < 1:
        anomalies.append({
            "type": AnomalyType.STATIONARY_ALERT.value,
            "severity": SeverityLevel.MEDIUM.value,
            "title": "Vessel Stopped While Underway",
            "description": f"Vessel status is 'underway' but speed is only {speed} knots",
            "details": {"speed": speed, "status": status}
        })
        risk_score += 20
    
    # 4. Zone entry alerts
    zone_alerts = check_zone_entry(lat, lng)
    for zone in zone_alerts:
        severity = SeverityLevel.HIGH if zone["risk_level"] == "high" else SeverityLevel.MEDIUM
        anomalies.append({
            "type": AnomalyType.ZONE_ENTRY.value,
            "severity": severity.value,
            "title": f"Entered {zone['zone_name']}",
            "description": f"Vessel is in {zone['risk_level']} risk zone",
            "details": zone
        })
        risk_score += 25 if zone["risk_level"] == "high" else 10
    
    # Calculate overall risk level
    overall_risk = SeverityLevel.LOW
    if risk_score >= 50:
        overall_risk = SeverityLevel.CRITICAL
    elif risk_score >= 30:
        overall_risk = SeverityLevel.HIGH
    elif risk_score >= 15:
        overall_risk = SeverityLevel.MEDIUM
    
    return {
        "vessel_id": vessel_id,
        "vessel_name": name,
        "position": {"lat": lat, "lng": lng},
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "risk_score": min(risk_score, 100),
        "overall_risk": overall_risk.value,
        "analyzed_at": datetime.utcnow().isoformat(),
        "has_anomalies": len(anomalies) > 0
    }


@router.get("/")
async def get_anomaly_detection_info():
    """Get anomaly detection system info"""
    # Get ML model status
    try:
        from app.ml.anomaly_detector import get_detector
        detector = get_detector()
        ml_info = detector.get_model_info()
    except Exception as e:
        ml_info = {"status": "not_loaded", "error": str(e)}
    
    return {
        "name": "Vessel Anomaly Detection System",
        "version": "2.0.0",
        "detection_types": [t.value for t in AnomalyType],
        "severity_levels": [s.value for s in SeverityLevel],
        "risk_zones_monitored": len(RISK_ZONES),
        "routes_configured": len(EXPECTED_ROUTES),
        "ml_model": ml_info
    }


@router.get("/ml/predict")
async def ml_predict(
    speed: float = Query(..., description="Speed in knots"),
    heading: float = Query(0, description="Heading in degrees"),
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    distance_from_route: float = Query(0, description="Distance from expected route in nm"),
    name: str = Query("Unknown", description="Vessel name")
):
    """ML-based anomaly prediction using trained Isolation Forest model"""
    try:
        from app.ml.anomaly_detector import get_detector
        detector = get_detector()
        
        prediction = detector.predict(
            speed=speed,
            heading=heading,
            lat=lat,
            lng=lng,
            distance_from_route=distance_from_route
        )
        
        return {
            "vessel_name": name,
            "position": {"lat": lat, "lng": lng},
            "speed": speed,
            "prediction": {
                "is_anomaly": prediction.is_anomaly,
                "anomaly_score": prediction.anomaly_score,
                "severity": prediction.severity.value,
                "confidence": prediction.confidence,
                "contributing_factors": prediction.contributing_factors
            },
            "model_type": "IsolationForest",
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "prediction": None}


@router.get("/ml/fleet")
async def ml_analyze_fleet():
    """Analyze entire fleet using ML model"""
    from app.api.vessels import get_vessels
    
    try:
        from app.ml.anomaly_detector import get_detector
        detector = get_detector()
        
        vessels_response = await get_vessels()
        vessels = vessels_response.get("vessels", [])
        
        results = detector.batch_predict(vessels)
        
        anomalies = [r for r in results if r["is_anomaly"]]
        
        return {
            "fleet_size": len(vessels),
            "vessels_with_anomalies": len(anomalies),
            "anomaly_rate": round(len(anomalies) / len(vessels) * 100, 1) if vessels else 0,
            "model_info": detector.get_model_info(),
            "predictions": results,
            "high_severity": [r for r in anomalies if r["severity"] in ["high", "critical"]],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "fleet_size": 0}


@router.get("/analyze/{vessel_id}")
async def analyze_vessel(
    vessel_id: str,
    lat: float = Query(..., description="Vessel latitude"),
    lng: float = Query(..., description="Vessel longitude"),
    speed: float = Query(..., description="Speed in knots"),
    heading: float = Query(0, description="Heading in degrees"),
    name: str = Query("Unknown", description="Vessel name"),
    status: str = Query("underway", description="Vessel status")
):
    """Analyze a single vessel for anomalies"""
    return detect_vessel_anomalies(vessel_id, name, lat, lng, speed, heading, status)


@router.get("/fleet")
async def analyze_fleet():
    """Analyze all vessels in fleet for anomalies"""
    from app.api.vessels import get_vessels
    
    try:
        # Get current vessel data
        vessels_response = await get_vessels()
        vessels = vessels_response.get("vessels", [])
        
        fleet_anomalies = []
        total_risk_score = 0
        vessels_with_anomalies = 0
        
        for vessel in vessels:
            pos = vessel.get("position", {})
            analysis = detect_vessel_anomalies(
                vessel_id=vessel.get("id", "unknown"),
                name=vessel.get("name", "Unknown"),
                lat=pos.get("lat", 0),
                lng=pos.get("lng", 0),
                speed=vessel.get("speed", 0),
                heading=vessel.get("heading", 0),
                status=vessel.get("status", "unknown")
            )
            
            if analysis["has_anomalies"]:
                fleet_anomalies.append(analysis)
                vessels_with_anomalies += 1
            
            total_risk_score += analysis["risk_score"]
        
        avg_risk = total_risk_score / len(vessels) if vessels else 0
        
        return {
            "fleet_size": len(vessels),
            "vessels_with_anomalies": vessels_with_anomalies,
            "total_anomalies": sum(a["anomaly_count"] for a in fleet_anomalies),
            "average_risk_score": round(avg_risk, 1),
            "high_risk_vessels": [a for a in fleet_anomalies if a["overall_risk"] in ["high", "critical"]],
            "all_anomalies": fleet_anomalies,
            "analyzed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "fleet_size": 0, "vessels_with_anomalies": 0}


@router.get("/alerts")
async def get_active_alerts(
    min_severity: str = Query("medium", description="Minimum severity: low, medium, high, critical")
):
    """Get all active anomaly alerts sorted by severity"""
    fleet_analysis = await analyze_fleet()
    
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    min_level = severity_order.get(min_severity, 2)
    
    all_alerts = []
    for vessel in fleet_analysis.get("all_anomalies", []):
        for anomaly in vessel.get("anomalies", []):
            if severity_order.get(anomaly["severity"], 3) <= min_level:
                all_alerts.append({
                    "vessel_id": vessel["vessel_id"],
                    "vessel_name": vessel["vessel_name"],
                    **anomaly,
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    # Sort by severity
    all_alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
    
    return {
        "alerts": all_alerts,
        "count": len(all_alerts),
        "min_severity_filter": min_severity
    }
