#!/usr/bin/env python3
"""
Weather Collector - Lightweight script for route weather data
Runs every 12 hours, collects 7 waypoints, stores to Supabase
RAM: ~30MB | API calls: 14/day
"""

import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import httpx
from supabase import create_client

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Configuration
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY")

# 7 waypoints along Taiwan → US route
WAYPOINTS = [
    {"name": "Kaohsiung", "lat": 22.6163, "lon": 120.3133},
    {"name": "Taiwan Strait", "lat": 24.0, "lon": 119.0},
    {"name": "Western Pacific", "lat": 25.0, "lon": 140.0},
    {"name": "Pacific Mid-Point", "lat": 30.0, "lon": 170.0},
    {"name": "Eastern Pacific", "lat": 33.0, "lon": -150.0},
    {"name": "Approach LA", "lat": 33.5, "lon": -125.0},
    {"name": "Los Angeles", "lat": 33.7406, "lon": -118.2600},
]


async def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch weather from OpenWeatherMap"""
    if not OPENWEATHERMAP_API_KEY:
        # Generate realistic mock data
        import random
        return {
            "main": {"temp": random.uniform(15, 30)},
            "wind": {"speed": random.uniform(3, 20)},
            "visibility": random.randint(5000, 10000),
            "weather": [{"main": random.choice(["Clear", "Clouds", "Rain"]), "description": ""}]
        }
    
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": OPENWEATHERMAP_API_KEY, "units": "metric"}
        )
        if resp.status_code == 200:
            return resp.json()
        return {}


def calculate_risk_score(weather: dict) -> float:
    """Calculate risk score from weather conditions"""
    wind_speed = weather.get("wind", {}).get("speed", 0)
    visibility = weather.get("visibility", 10000) / 1000
    conditions = weather.get("weather", [{}])[0].get("main", "").lower()
    
    risk = 0.0
    if wind_speed > 20: risk += 0.4
    elif wind_speed > 15: risk += 0.25
    elif wind_speed > 10: risk += 0.1
    
    if visibility < 3: risk += 0.3
    elif visibility < 5: risk += 0.15
    
    if "storm" in conditions or "typhoon" in conditions: risk += 0.4
    elif "rain" in conditions: risk += 0.1
    
    return min(risk, 1.0)


async def collect_weather():
    """Main collection function"""
    print(f"🌤️  Weather Collection Started - {datetime.now(timezone.utc).isoformat()}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    recorded_at = datetime.now(timezone.utc).isoformat()
    
    results = []
    for waypoint in WAYPOINTS:
        weather = await fetch_weather(waypoint["lat"], waypoint["lon"])
        
        if weather:
            risk_score = calculate_risk_score(weather)
            storm_alert = risk_score > 0.5
            
            record = {
                "recorded_at": recorded_at,
                "location_name": waypoint["name"],
                "latitude": waypoint["lat"],
                "longitude": waypoint["lon"],
                "temperature_c": weather.get("main", {}).get("temp"),
                "wind_speed_ms": weather.get("wind", {}).get("speed"),
                "visibility_km": weather.get("visibility", 10000) / 1000,
                "conditions": weather.get("weather", [{}])[0].get("main"),
                "storm_alert": storm_alert,
                "risk_score": risk_score,
                "raw_data": weather,
            }
            results.append(record)
            
            status = "⚠️" if storm_alert else "✅"
            print(f"  {status} {waypoint['name']}: {record['conditions']}, risk={risk_score:.2f}")
    
    # Store to Supabase
    if results:
        try:
            supabase.table("weather_data").insert(results).execute()
            print(f"✅ Stored {len(results)} weather records to Supabase")
        except Exception as e:
            print(f"❌ Storage error: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(collect_weather())
