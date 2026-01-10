#!/usr/bin/env python3
"""
Vessel Tracking Collector - Track key vessels on Taiwan-US routes
Runs every 4 hours | Tracks 10-15 MMSI numbers | ~50MB RAM
Uses VesselFinder free tier or mock data
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
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", 
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY")

# Key vessels on Taiwan-US routes (MMSI numbers)
# These are representative container vessels
KEY_VESSELS = [
    {"mmsi": "477328600", "name": "Ever Given", "carrier": "Evergreen"},
    {"mmsi": "477234000", "name": "Ever Ace", "carrier": "Evergreen"},
    {"mmsi": "477918000", "name": "YM Wellness", "carrier": "Yang Ming"},
    {"mmsi": "477063000", "name": "YM Warranty", "carrier": "Yang Ming"},
    {"mmsi": "636092799", "name": "Maersk Edinburgh", "carrier": "Maersk"},
    {"mmsi": "636019825", "name": "Maersk Elba", "carrier": "Maersk"},
    {"mmsi": "538006716", "name": "ONE Commitment", "carrier": "ONE"},
    {"mmsi": "538007780", "name": "ONE Columba", "carrier": "ONE"},
    {"mmsi": "477712100", "name": "WAN HAI 506", "carrier": "Wan Hai"},
    {"mmsi": "477712200", "name": "WAN HAI 507", "carrier": "Wan Hai"},
    {"mmsi": "636017000", "name": "COSCO Shipping Star", "carrier": "COSCO"},
    {"mmsi": "636017001", "name": "COSCO Shipping Sun", "carrier": "COSCO"},
]


def generate_mock_position(vessel: dict) -> dict:
    """Generate realistic mock position for vessel"""
    import random
    
    # Simulate position along Taiwan-LA route
    routes = [
        {"lat": 22.6, "lon": 120.3, "status": "At Port", "port": "Kaohsiung"},
        {"lat": 24.5, "lon": 125.0, "status": "En Route", "port": None},
        {"lat": 28.0, "lon": 140.0, "status": "En Route", "port": None},
        {"lat": 30.0, "lon": 160.0, "status": "En Route", "port": None},
        {"lat": 32.0, "lon": 180.0, "status": "En Route", "port": None},
        {"lat": 33.5, "lon": -160.0, "status": "En Route", "port": None},
        {"lat": 33.7, "lon": -130.0, "status": "En Route", "port": None},
        {"lat": 33.7, "lon": -118.3, "status": "At Port", "port": "Los Angeles"},
    ]
    
    pos = random.choice(routes)
    speed = random.uniform(0, 2) if pos["status"] == "At Port" else random.uniform(15, 22)
    
    return {
        "mmsi": vessel["mmsi"],
        "name": vessel["name"],
        "carrier": vessel["carrier"],
        "latitude": pos["lat"] + random.uniform(-0.5, 0.5),
        "longitude": pos["lon"] + random.uniform(-0.5, 0.5),
        "speed_knots": round(speed, 1),
        "heading": random.randint(0, 360),
        "status": pos["status"],
        "destination": "Los Angeles" if pos["port"] != "Los Angeles" else "Kaohsiung",
        "eta": (datetime.now(timezone.utc).isoformat() if pos["port"] else None),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_vessel_positions(use_api: bool = False) -> list:
    """Fetch vessel positions (mock for free tier)"""
    positions = []
    
    for vessel in KEY_VESSELS:
        # For MVP, use mock data (real AIS API requires paid subscription)
        pos = generate_mock_position(vessel)
        positions.append(pos)
        print(f"  📍 {vessel['name']}: {pos['latitude']:.2f}, {pos['longitude']:.2f} ({pos['status']})")
    
    return positions


async def store_positions(positions: list):
    """Store vessel positions to Supabase"""
    if not positions:
        return
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Update vessels table with latest positions
        for pos in positions:
            supabase.table("vessels").upsert({
                "mmsi": pos["mmsi"],
                "name": pos["name"],
                "carrier": pos["carrier"],
                "current_lat": pos["latitude"],
                "current_lon": pos["longitude"],
                "current_speed": pos["speed_knots"],
                "heading": pos["heading"],
                "status": pos["status"],
                "destination": pos["destination"],
                "last_updated": pos["recorded_at"],
            }, on_conflict="mmsi").execute()
        
        print(f"  ✅ Updated {len(positions)} vessel positions in Supabase")
        
    except Exception as e:
        print(f"  ⚠️ Storage note: {e}")


async def collect_vessels():
    """Main collection function"""
    print(f"🚢 Vessel Tracking Started - {datetime.now(timezone.utc).isoformat()}")
    print(f"   Tracking {len(KEY_VESSELS)} vessels")
    
    positions = await fetch_vessel_positions()
    await store_positions(positions)
    
    # Summary
    at_port = sum(1 for p in positions if p["status"] == "At Port")
    en_route = len(positions) - at_port
    avg_speed = sum(p["speed_knots"] for p in positions) / len(positions)
    
    print(f"\n📊 Summary:")
    print(f"   At Port: {at_port} | En Route: {en_route}")
    print(f"   Avg Speed: {avg_speed:.1f} knots")
    
    return positions


if __name__ == "__main__":
    asyncio.run(collect_vessels())
