"""
Live Data Service - Generates realistic, consistent data for integrated dashboard
with cross-references between weather, ports, routes, and vessels
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import math

# ==================== REALISTIC DATA SOURCES ====================

# Major Pacific shipping routes with realistic distances and transit times
ROUTES = [
    {"id": "TW-LA", "origin": "Kaohsiung, Taiwan", "origin_code": "TWKHH", "dest": "Los Angeles, USA", "dest_code": "USLAX", 
     "distance_nm": 6150, "typical_days": 14, "lat_mid": 32.0, "lng_mid": -150.0},
    {"id": "TW-LB", "origin": "Kaohsiung, Taiwan", "origin_code": "TWKHH", "dest": "Long Beach, USA", "dest_code": "USLGB",
     "distance_nm": 6150, "typical_days": 14, "lat_mid": 31.5, "lng_mid": -148.0},
    {"id": "TW-OAK", "origin": "Keelung, Taiwan", "origin_code": "TWTPE", "dest": "Oakland, USA", "dest_code": "USOAK",
     "distance_nm": 5950, "typical_days": 13, "lat_mid": 35.0, "lng_mid": -155.0},
    {"id": "TW-SEA", "origin": "Kaohsiung, Taiwan", "origin_code": "TWKHH", "dest": "Seattle, USA", "dest_code": "USSEA",
     "distance_nm": 5200, "typical_days": 12, "lat_mid": 40.0, "lng_mid": -160.0},
    {"id": "CN-LA", "origin": "Shanghai, China", "origin_code": "CNSHA", "dest": "Los Angeles, USA", "dest_code": "USLAX",
     "distance_nm": 5900, "typical_days": 13, "lat_mid": 33.0, "lng_mid": -152.0},
    {"id": "CN-LB", "origin": "Ningbo, China", "origin_code": "CNNGB", "dest": "Long Beach, USA", "dest_code": "USLGB",
     "distance_nm": 5850, "typical_days": 13, "lat_mid": 32.5, "lng_mid": -151.0},
    {"id": "HK-LA", "origin": "Hong Kong", "origin_code": "HKHKG", "dest": "Los Angeles, USA", "dest_code": "USLAX",
     "distance_nm": 6400, "typical_days": 14, "lat_mid": 30.0, "lng_mid": -145.0},
    {"id": "SG-LA", "origin": "Singapore", "origin_code": "SGSIN", "dest": "Los Angeles, USA", "dest_code": "USLAX",
     "distance_nm": 8000, "typical_days": 18, "lat_mid": 25.0, "lng_mid": -140.0},
]

# Major ports with base congestion levels (varies by time of day and day of week)
PORTS = {
    "TWKHH": {"name": "Kaohsiung", "country": "Taiwan", "lat": 22.62, "lng": 120.31, "base_congestion": 0.45, "capacity_teus": 10500000},
    "TWTPE": {"name": "Keelung", "country": "Taiwan", "lat": 25.13, "lng": 121.74, "base_congestion": 0.35, "capacity_teus": 2800000},
    "USLAX": {"name": "Los Angeles", "country": "USA", "lat": 33.74, "lng": -118.26, "base_congestion": 0.62, "capacity_teus": 9500000},
    "USLGB": {"name": "Long Beach", "country": "USA", "lat": 33.77, "lng": -118.19, "base_congestion": 0.58, "capacity_teus": 8600000},
    "USOAK": {"name": "Oakland", "country": "USA", "lat": 37.80, "lng": -122.28, "base_congestion": 0.48, "capacity_teus": 2500000},
    "USSEA": {"name": "Seattle", "country": "USA", "lat": 47.58, "lng": -122.35, "base_congestion": 0.42, "capacity_teus": 3800000},
    "CNSHA": {"name": "Shanghai", "country": "China", "lat": 31.23, "lng": 121.47, "base_congestion": 0.55, "capacity_teus": 47000000},
    "CNNGB": {"name": "Ningbo", "country": "China", "lat": 29.87, "lng": 121.55, "base_congestion": 0.52, "capacity_teus": 31000000},
    "HKHKG": {"name": "Hong Kong", "country": "Hong Kong", "lat": 22.30, "lng": 114.17, "base_congestion": 0.50, "capacity_teus": 18000000},
    "SGSIN": {"name": "Singapore", "country": "Singapore", "lat": 1.29, "lng": 103.85, "base_congestion": 0.40, "capacity_teus": 37000000},
}

# Vessel fleet (representative of actual trans-Pacific carriers)
VESSELS = [
    {"id": "V001", "name": "EVER GOLDEN", "imo": "9811000", "carrier": "Evergreen", "capacity_teu": 12000, "flag": "Panama"},
    {"id": "V002", "name": "YM UNITY", "imo": "9462706", "carrier": "Yang Ming", "capacity_teu": 8500, "flag": "Liberia"},
    {"id": "V003", "name": "WAN HAI 506", "imo": "9461401", "carrier": "Wan Hai", "capacity_teu": 4250, "flag": "Singapore"},
    {"id": "V004", "name": "EVER GENIUS", "imo": "9832034", "carrier": "Evergreen", "capacity_teu": 20000, "flag": "Panama"},
    {"id": "V005", "name": "APL LION CITY", "imo": "9631987", "carrier": "APL", "capacity_teu": 14000, "flag": "Singapore"},
    {"id": "V006", "name": "OOCL TOKYO", "imo": "9310277", "carrier": "OOCL", "capacity_teu": 8063, "flag": "Hong Kong"},
    {"id": "V007", "name": "COSCO SHIPPING ARIES", "imo": "9795024", "carrier": "COSCO", "capacity_teu": 13500, "flag": "China"},
    {"id": "V008", "name": "MSC FRANCESCA", "imo": "9401176", "carrier": "MSC", "capacity_teu": 11660, "flag": "Panama"},
]


def get_current_time_factor() -> float:
    """Get a time-based factor for variation (simulates time-of-day patterns)"""
    now = datetime.utcnow()
    hour = now.hour
    # Peak congestion during business hours (Pacific time = UTC-8)
    pacific_hour = (hour - 8) % 24
    if 8 <= pacific_hour <= 18:
        return 1.2  # Peak hours
    elif 6 <= pacific_hour <= 8 or 18 <= pacific_hour <= 20:
        return 1.0  # Transition hours
    else:
        return 0.8  # Off-peak hours


def get_seasonal_factor() -> float:
    """Get seasonal shipping factor (peak before holidays)"""
    now = datetime.utcnow()
    month = now.month
    # Peak season: Aug-Oct (holiday prep), Jan-Feb (Chinese New Year)
    if month in [8, 9, 10]:
        return 1.3
    elif month in [1, 2]:
        return 1.25
    elif month in [11, 12]:
        return 1.1
    else:
        return 1.0


def calculate_weather_impact(route: Dict, weather_systems: List[Dict]) -> Dict:
    """Calculate how weather systems affect a specific route"""
    total_impact = 0
    affecting_systems = []
    
    for system in weather_systems:
        # Simple distance check from route midpoint to weather system
        dist_lat = abs(route["lat_mid"] - system["lat"])
        dist_lng = abs(route["lng_mid"] - system["lng"])
        distance = math.sqrt(dist_lat**2 + dist_lng**2)
        
        # Check if within radius (convert nm to degrees roughly: 60nm = 1 degree)
        radius_degrees = system["radius_nm"] / 60
        
        if distance < radius_degrees * 2:  # Within extended impact zone
            # Impact decreases with distance
            proximity_factor = max(0, 1 - (distance / (radius_degrees * 2)))
            intensity_factor = {"low": 0.1, "medium": 0.25, "high": 0.5, "severe": 0.8}.get(system["intensity"], 0.25)
            impact = proximity_factor * intensity_factor
            total_impact += impact
            
            if proximity_factor > 0.3:
                affecting_systems.append({
                    "id": system["id"],
                    "name": system["name"],
                    "type": system["type"],
                    "impact_level": "high" if proximity_factor > 0.7 else "medium" if proximity_factor > 0.4 else "low"
                })
    
    return {
        "delay_factor": min(1.5, 1 + total_impact),  # Max 50% delay increase
        "risk_increase": min(40, total_impact * 50),  # Max 40% risk increase
        "affecting_systems": affecting_systems
    }


def calculate_port_delay(port_code: str, time_factor: float) -> Dict:
    """Calculate port-specific delay based on congestion"""
    port = PORTS.get(port_code, {})
    base = port.get("base_congestion", 0.5)
    
    seasonal = get_seasonal_factor()
    current_congestion = min(0.95, base * time_factor * seasonal)
    
    # Wait time in hours based on congestion
    wait_hours = current_congestion * 48  # Up to 48 hours at full congestion
    
    # Berth utilization
    berth_util = min(98, current_congestion * 100 + 5)
    
    return {
        "port_code": port_code,
        "port_name": port.get("name", port_code),
        "congestion_level": round(current_congestion, 2),
        "wait_time_hours": round(wait_hours, 1),
        "berth_utilization": round(berth_util, 1),
        "trend": "increasing" if seasonal > 1.1 else "stable" if seasonal > 0.95 else "decreasing"
    }


def generate_vessel_position(vessel: Dict, route: Dict, progress: float) -> Dict:
    """Generate realistic vessel position along a route"""
    # Linear interpolation along route (simplified great circle)
    origin_port = PORTS.get(route["origin_code"], {})
    dest_port = PORTS.get(route["dest_code"], {})
    
    lat = origin_port.get("lat", 25) + (dest_port.get("lat", 35) - origin_port.get("lat", 25)) * progress
    lng = origin_port.get("lng", 120) + (dest_port.get("lng", -120) - origin_port.get("lng", 120)) * progress
    
    # Speed varies based on weather and fuel optimization
    base_speed = 18  # knots
    speed = base_speed * (0.9 + progress * 0.2)  # Speed up as approaching port
    
    # Heading towards destination
    heading = math.degrees(math.atan2(
        dest_port.get("lng", -120) - lng,
        dest_port.get("lat", 35) - lat
    )) % 360
    
    # Calculate ETA
    remaining_distance = route["distance_nm"] * (1 - progress)
    remaining_hours = remaining_distance / speed
    eta = datetime.utcnow() + timedelta(hours=remaining_hours)
    
    return {
        "vessel_id": vessel["id"],
        "name": vessel["name"],
        "imo": vessel["imo"],
        "carrier": vessel["carrier"],
        "lat": round(lat, 4),
        "lng": round(lng, 4),
        "speed_knots": round(speed, 1),
        "heading": round(heading, 1),
        "route_id": route["id"],
        "origin": route["origin"],
        "destination": route["dest"],
        "progress_percent": round(progress * 100, 1),
        "eta": eta.isoformat(),
        "status": "underway" if 0.05 < progress < 0.95 else "arriving" if progress >= 0.95 else "departing"
    }


def generate_weather_systems() -> List[Dict]:
    """Generate realistic weather systems for current time"""
    now = datetime.utcnow()
    day_of_year = now.timetuple().tm_yday
    
    # Base systems - positions shift slightly based on time
    systems = []
    
    # Typhoon season: June-November (peak Aug-Sep)
    is_typhoon_season = 6 <= now.month <= 11
    
    if is_typhoon_season:
        # Active typhoon
        systems.append({
            "id": f"TY-{now.year}-{(day_of_year // 20) + 1:02d}",
            "type": "typhoon",
            "name": f"Typhoon {'ABCDEFGHIJ'[(day_of_year // 20) % 10]}{'NOPQRSTUVW'[(day_of_year // 7) % 10]}",
            "lat": 18 + (day_of_year % 10),
            "lng": 125 + (day_of_year % 15) - 7,
            "intensity": "severe" if now.month in [8, 9] else "high",
            "wind_speed_knots": 95 + (day_of_year % 40),
            "wave_height_m": 8 + (day_of_year % 6),
            "radius_nm": 150 + (day_of_year % 100),
            "direction": 315 + (day_of_year % 30) - 15,
            "speed_knots": 10 + (day_of_year % 8),
            "warning_level": "warning" if now.month in [8, 9] else "watch",
            "impact_description": "Tropical cyclone affecting Western Pacific shipping lanes"
        })
    
    # Pacific storm (year-round)
    systems.append({
        "id": f"ST-{now.year}-{(day_of_year // 15) % 20 + 1:02d}",
        "type": "storm",
        "name": f"Pacific Storm {'Alpha Beta Gamma Delta Epsilon'.split()[(day_of_year // 15) % 5]}",
        "lat": 35 + (day_of_year % 10) - 5,
        "lng": -150 + (day_of_year % 20) - 10,
        "intensity": "medium",
        "wind_speed_knots": 35 + (day_of_year % 20),
        "wave_height_m": 4 + (day_of_year % 3),
        "radius_nm": 100 + (day_of_year % 80),
        "direction": 60 + (day_of_year % 40) - 20,
        "speed_knots": 15 + (day_of_year % 10),
        "warning_level": "advisory",
        "impact_description": "Moderate storm system affecting trans-Pacific routes"
    })
    
    # Fog near US coast (common year-round, worse in summer)
    if now.month in [5, 6, 7, 8]:
        systems.append({
            "id": f"FG-{now.year}-{day_of_year // 5:03d}",
            "type": "fog",
            "name": "California Coastal Fog",
            "lat": 34 + (day_of_year % 3),
            "lng": -120 - (day_of_year % 3),
            "intensity": "medium",
            "wind_speed_knots": 8,
            "wave_height_m": 1.5,
            "radius_nm": 60 + (day_of_year % 40),
            "direction": 180,
            "speed_knots": 3,
            "warning_level": "advisory",
            "impact_description": "Marine fog reducing visibility at LA/LB approach"
        })
    
    # High winds in North Pacific (worse in winter)
    if now.month in [10, 11, 12, 1, 2, 3]:
        systems.append({
            "id": f"HW-{now.year}-{day_of_year // 7 % 52:02d}",
            "type": "high_winds",
            "name": "North Pacific Gale",
            "lat": 45 + (day_of_year % 10),
            "lng": -170 + (day_of_year % 20) - 10,
            "intensity": "high",
            "wind_speed_knots": 45 + (day_of_year % 20),
            "wave_height_m": 6 + (day_of_year % 4),
            "radius_nm": 120 + (day_of_year % 60),
            "direction": 225 + (day_of_year % 30) - 15,
            "speed_knots": 8 + (day_of_year % 6),
            "warning_level": "watch",
            "impact_description": "Gale force winds affecting North Pacific routing"
        })
    
    return systems


def generate_sea_conditions(weather_systems: List[Dict]) -> List[Dict]:
    """Generate sea conditions for key regions"""
    now = datetime.utcnow()
    day = now.day
    
    regions = [
        {"name": "Taiwan Strait", "lat": 24.0, "lng": 119.5, "base_state": 3},
        {"name": "Philippine Sea", "lat": 20.0, "lng": 125.0, "base_state": 4},
        {"name": "East China Sea", "lat": 28.0, "lng": 125.0, "base_state": 3},
        {"name": "North Pacific Central", "lat": 35.0, "lng": -160.0, "base_state": 4},
        {"name": "Mid-Pacific", "lat": 30.0, "lng": -140.0, "base_state": 3},
        {"name": "US West Coast", "lat": 35.0, "lng": -122.0, "base_state": 2},
        {"name": "South China Sea", "lat": 15.0, "lng": 115.0, "base_state": 3},
        {"name": "Western Pacific", "lat": 25.0, "lng": 135.0, "base_state": 4},
    ]
    
    conditions = []
    for region in regions:
        # Check weather impact on this region
        sea_state = region["base_state"]
        for system in weather_systems:
            dist = math.sqrt((region["lat"] - system["lat"])**2 + (region["lng"] - system["lng"])**2)
            if dist < 15:  # Within ~900nm
                sea_state = min(9, sea_state + ({"severe": 3, "high": 2, "medium": 1, "low": 0}.get(system["intensity"], 1)))
        
        # Add daily variation
        sea_state = max(1, min(9, sea_state + (day % 3) - 1))
        
        wave_height = sea_state * 0.8  # Rough conversion
        wind_speed = sea_state * 5 + 10
        
        condition_map = {1: "calm", 2: "calm", 3: "moderate", 4: "moderate", 5: "rough", 6: "rough", 7: "very_rough", 8: "high", 9: "high"}
        
        conditions.append({
            "region": region["name"],
            "lat": region["lat"],
            "lng": region["lng"],
            "sea_state": sea_state,
            "wave_height_m": round(wave_height, 1),
            "wind_direction": (day * 30) % 360,
            "wind_speed_knots": wind_speed,
            "visibility_nm": max(3, 20 - sea_state * 2),
            "condition": condition_map.get(sea_state, "moderate")
        })
    
    return conditions


def generate_analytics_data(routes_data: List[Dict]) -> Dict:
    """Generate analytics data based on current route status"""
    now = datetime.utcnow()
    
    # Risk distribution
    risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    total_delay = 0
    on_time_count = 0
    
    for route in routes_data:
        risk = route.get("risk_level", "medium")
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        delay = route.get("weather_impact", {}).get("delay_factor", 1) - 1
        total_delay += delay * route.get("typical_days", 14)
        
        if delay < 0.1:
            on_time_count += 1
    
    total_routes = len(routes_data)
    
    return {
        "risk_distribution": {
            "low": risk_counts["low"],
            "medium": risk_counts["medium"],
            "high": risk_counts["high"],
            "critical": risk_counts["critical"]
        },
        "avg_delay_days": round(total_delay / max(1, total_routes), 1),
        "on_time_rate": round((on_time_count / max(1, total_routes)) * 100, 1),
        "total_routes_monitored": total_routes,
        "last_updated": now.isoformat()
    }


def get_integrated_dashboard_data() -> Dict:
    """Main function to generate fully integrated dashboard data"""
    time_factor = get_current_time_factor()
    seasonal_factor = get_seasonal_factor()
    
    # Generate weather systems
    weather_systems = generate_weather_systems()
    
    # Generate sea conditions
    sea_conditions = generate_sea_conditions(weather_systems)
    
    # Process routes with weather impact
    routes_data = []
    for route in ROUTES:
        weather_impact = calculate_weather_impact(route, weather_systems)
        origin_delay = calculate_port_delay(route["origin_code"], time_factor)
        dest_delay = calculate_port_delay(route["dest_code"], time_factor)
        
        # Calculate total delay
        weather_delay = (weather_impact["delay_factor"] - 1) * route["typical_days"]
        port_delay = (origin_delay["wait_time_hours"] + dest_delay["wait_time_hours"]) / 24
        total_delay = weather_delay + port_delay
        
        # Risk score
        base_risk = 30
        risk_score = min(100, base_risk + weather_impact["risk_increase"] + (origin_delay["congestion_level"] * 20) + (dest_delay["congestion_level"] * 20))
        
        risk_level = "critical" if risk_score > 75 else "high" if risk_score > 55 else "medium" if risk_score > 35 else "low"
        
        routes_data.append({
            **route,
            "weather_impact": weather_impact,
            "origin_port_status": origin_delay,
            "dest_port_status": dest_delay,
            "predicted_delay_days": round(total_delay, 1),
            "adjusted_transit_days": route["typical_days"] + round(total_delay, 1),
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level,
            "last_updated": datetime.utcnow().isoformat()
        })
    
    # Generate vessels along routes
    vessels_data = []
    for i, vessel in enumerate(VESSELS):
        route = ROUTES[i % len(ROUTES)]
        # Progress based on current time (cycles every 14 days)
        base_progress = ((datetime.utcnow().timestamp() / 86400) % route["typical_days"]) / route["typical_days"]
        progress = (base_progress + (i * 0.12)) % 1.0  # Stagger vessels
        
        vessel_pos = generate_vessel_position(vessel, route, progress)
        vessels_data.append(vessel_pos)
    
    # Generate port congestion data
    ports_data = []
    for code, port in PORTS.items():
        delay_info = calculate_port_delay(code, time_factor)
        ports_data.append({
            "code": code,
            "name": port["name"],
            "country": port["country"],
            "lat": port["lat"],
            "lng": port["lng"],
            "capacity_teus": port["capacity_teus"],
            **delay_info
        })
    
    # Generate analytics
    analytics = generate_analytics_data(routes_data)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "time_factor": time_factor,
        "seasonal_factor": seasonal_factor,
        "routes": routes_data,
        "vessels": vessels_data,
        "weather_systems": weather_systems,
        "sea_conditions": sea_conditions,
        "ports": ports_data,
        "analytics": analytics,
        "summary": {
            "total_routes": len(routes_data),
            "total_vessels": len(vessels_data),
            "active_weather_systems": len(weather_systems),
            "ports_monitored": len(ports_data),
            "high_risk_routes": len([r for r in routes_data if r["risk_level"] in ["high", "critical"]]),
            "avg_delay": analytics["avg_delay_days"],
            "on_time_rate": analytics["on_time_rate"]
        }
    }
