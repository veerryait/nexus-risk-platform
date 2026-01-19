"""
Weather Service - OpenWeatherMap Integration
Tracks Pacific weather conditions along shipping routes
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime
import os


class WeatherService:
    """OpenWeatherMap API integration for maritime weather tracking"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    # Key shipping route waypoints (Taiwan → US West Coast)
    ROUTE_WAYPOINTS = [
        {"name": "Kaohsiung", "lat": 22.6163, "lon": 120.3133},
        {"name": "Pacific Mid-Point", "lat": 30.0, "lon": 170.0},
        {"name": "Pacific East", "lat": 35.0, "lon": -140.0},
        {"name": "Los Angeles", "lat": 33.7406, "lon": -118.2600},
        {"name": "Long Beach", "lat": 33.7701, "lon": -118.1937},
    ]
    
    # Typhoon-prone areas in Pacific
    STORM_ZONES = [
        {"name": "Western Pacific", "lat": 20.0, "lon": 140.0},
        {"name": "Philippine Sea", "lat": 18.0, "lon": 125.0},
        {"name": "Taiwan Strait", "lat": 24.0, "lon": 119.0},
    ]
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_weather_at_point(self, lat: float, lon: float) -> Dict:
        """Get current weather at a specific coordinate"""
        if not self.api_key:
            return self._mock_weather_data(lat, lon)
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": self.api_key,
                    "units": "metric"
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            # Log privately, don't expose API error details
            import logging
            logging.getLogger("nexus.security").error(f"Weather API error: {type(e).__name__}")
            return self._mock_weather_data(lat, lon)
    
    async def get_route_weather(self) -> List[Dict]:
        """Get weather conditions along the entire shipping route"""
        results = []
        for waypoint in self.ROUTE_WAYPOINTS:
            weather = await self.get_weather_at_point(waypoint["lat"], waypoint["lon"])
            results.append({
                "location": waypoint["name"],
                "coordinates": {"lat": waypoint["lat"], "lon": waypoint["lon"]},
                "conditions": weather.get("weather", [{}])[0].get("main", "Unknown"),
                "description": weather.get("weather", [{}])[0].get("description", ""),
                "wind_speed_ms": weather.get("wind", {}).get("speed", 0),
                "wave_risk": self._calculate_wave_risk(weather),
                "visibility_km": weather.get("visibility", 10000) / 1000,
                "temperature_c": weather.get("main", {}).get("temp", 20),
            })
        return results
    
    async def get_storm_alerts(self) -> List[Dict]:
        """Check for storms/typhoons in shipping zones"""
        alerts = []
        for zone in self.STORM_ZONES:
            weather = await self.get_weather_at_point(zone["lat"], zone["lon"])
            wind_speed = weather.get("wind", {}).get("speed", 0)
            conditions = weather.get("weather", [{}])[0].get("main", "").lower()
            
            severity = "low"
            if wind_speed > 20 or "storm" in conditions or "typhoon" in conditions:
                severity = "high"
            elif wind_speed > 10 or "rain" in conditions:
                severity = "medium"
            
            if severity != "low":
                alerts.append({
                    "zone": zone["name"],
                    "severity": severity,
                    "wind_speed_ms": wind_speed,
                    "conditions": conditions,
                    "recommendation": self._get_recommendation(severity),
                })
        return alerts
    
    async def get_weather_risk_score(self) -> float:
        """Calculate overall weather risk score (0-1)"""
        route_weather = await self.get_route_weather()
        storm_alerts = await self.get_storm_alerts()
        
        # Base risk from route conditions
        route_risk = 0.0
        for point in route_weather:
            route_risk += point["wave_risk"] * 0.5
            if point["visibility_km"] < 5:
                route_risk += 0.1
        route_risk = min(route_risk / len(route_weather), 0.5)
        
        # Additional risk from storm alerts
        storm_risk = 0.0
        for alert in storm_alerts:
            if alert["severity"] == "high":
                storm_risk += 0.3
            elif alert["severity"] == "medium":
                storm_risk += 0.15
        storm_risk = min(storm_risk, 0.5)
        
        return min(route_risk + storm_risk, 1.0)
    
    def _calculate_wave_risk(self, weather: Dict) -> float:
        """Estimate wave risk from wind speed"""
        wind_speed = weather.get("wind", {}).get("speed", 0)
        if wind_speed > 25:
            return 0.9
        elif wind_speed > 15:
            return 0.6
        elif wind_speed > 10:
            return 0.3
        return 0.1
    
    def _get_recommendation(self, severity: str) -> str:
        """Get routing recommendation based on severity"""
        if severity == "high":
            return "Consider alternate route or delay departure"
        elif severity == "medium":
            return "Monitor conditions, possible delays"
        return "Normal operations"
    
    def _mock_weather_data(self, lat: float, lon: float) -> Dict:
        """Return mock data when API key is not available"""
        import random
        conditions = ["Clear", "Clouds", "Rain", "Thunderstorm"]
        return {
            "weather": [{"main": random.choice(conditions[:3]), "description": "scattered clouds"}],
            "wind": {"speed": random.uniform(3, 15)},
            "visibility": random.randint(5000, 10000),
            "main": {"temp": random.uniform(15, 30)},
        }
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
weather_service = WeatherService()
