"""
Vessels API Endpoints - With AISStream.io for real vessel tracking
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import random
import math

from supabase import create_client

router = APIRouter()

# Supabase connection
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"

# AISStream.io API key
AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY", "")


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def is_aisstream_configured():
    return bool(AISSTREAM_API_KEY) and AISSTREAM_API_KEY != "your_aisstream_api_key_here"


@router.get("/")
async def get_vessels(
    limit: int = Query(20, ge=1, le=100),
    carrier: Optional[str] = None,
    route: Optional[str] = None
):
    """Get list of tracked vessels with current positions"""
    try:
        # Try AISStream for real positions first
        if is_aisstream_configured():
            try:
                from app.services.aisstream_service import get_real_vessel_positions
                real_positions = await get_real_vessel_positions()
                if real_positions:
                    return {
                        "vessels": real_positions[:limit],
                        "count": len(real_positions[:limit]),
                        "source": "aisstream",
                        "note": "Real-time AIS data from AISStream.io"
                    }
            except Exception as e:
                print(f"AISStream error: {e}")
        
        # Try database
        supabase = get_supabase()
        query = supabase.table("vessels").select("*").limit(limit)
        if carrier:
            query = query.ilike("carrier", f"%{carrier}%")
        result = query.execute()
        
        if result.data and len(result.data) > 0:
            vessels = []
            for v in result.data:
                vessels.append(enrich_vessel_data(v))
            return {
                "vessels": vessels,
                "count": len(vessels),
                "source": "database",
                "aisstream_configured": is_aisstream_configured()
            }
        
        # Fallback to simulated
        return generate_realistic_vessels(limit, carrier, route)
        
    except Exception as e:
        return generate_realistic_vessels(limit, carrier, route)


@router.get("/realtime")
async def get_realtime_vessels():
    """Get real-time vessel positions from AISStream (if configured)"""
    if not is_aisstream_configured():
        return {
            "error": "AISStream not configured",
            "configured": False,
            "instructions": "Add AISSTREAM_API_KEY to .env file"
        }
    
    try:
        from app.services.aisstream_service import get_real_vessel_positions
        positions = await get_real_vessel_positions()
        return {
            "vessels": positions,
            "count": len(positions),
            "source": "aisstream_realtime",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "configured": True}


def generate_realistic_vessels(limit: int, carrier: Optional[str], route: Optional[str]):
    """Generate realistic vessel positions for tracked vessels"""
    now = datetime.utcnow()
    vessels = []
    
    TRACKED_VESSELS = [
        {"imo": "9893890", "name": "Ever Ace", "carrier": "Evergreen", "route": "TWKHH-USLAX"},
        {"imo": "9811000", "name": "Ever Given", "carrier": "Evergreen", "route": "TWKHH-USLGB"},
        {"imo": "9708451", "name": "YM Wish", "carrier": "Yang Ming", "route": "TWKHH-USOAK"},
        {"imo": "9708463", "name": "YM Wind", "carrier": "Yang Ming", "route": "TWTPE-USLAX"},
        {"imo": "9458089", "name": "Maersk Elba", "carrier": "Maersk", "route": "TWKHH-USSEA"},
        {"imo": "9795610", "name": "COSCO Shipping Universe", "carrier": "COSCO", "route": "TWKHH-USLAX"},
        {"imo": "9939137", "name": "ONE Innovation", "carrier": "ONE", "route": "TWKHH-USLGB"},
        {"imo": "9929429", "name": "MSC Irina", "carrier": "MSC", "route": "TWKHH-USOAK"},
    ]
    
    filtered = TRACKED_VESSELS
    if carrier:
        filtered = [v for v in filtered if carrier.lower() in v["carrier"].lower()]
    if route:
        filtered = [v for v in filtered if route in v["route"]]
    
    for i, v in enumerate(filtered[:limit]):
        progress = random.uniform(0.1, 0.9)
        start_lat, start_lng = 22.6163, 120.3133
        end_lat, end_lng = 33.7406, -118.26
        
        lat = start_lat + (end_lat - start_lat) * progress
        lat += math.sin(progress * math.pi) * 8
        
        if progress < 0.5:
            lng = start_lng + 60 * progress
        else:
            lng = 180 - (180 + end_lng) * (progress - 0.5) * 2
            if lng > 180:
                lng -= 360
        
        status = "underway" if 0.05 < progress < 0.95 else ("departing" if progress < 0.05 else "arriving")
        speed = random.uniform(16, 22) if status == "underway" else random.uniform(5, 12)
        
        remaining_days = (1 - progress) * 14
        eta = now + timedelta(days=remaining_days)
        
        vessels.append({
            "id": f"v{i+1}",
            "imo": v["imo"],
            "name": v["name"],
            "carrier": v["carrier"],
            "route_id": v["route"],
            "position": {"lat": round(lat, 4), "lng": round(lng, 4)},
            "status": status,
            "speed": round(speed, 1),
            "heading": round(85 + random.uniform(-10, 10)),
            "destination": v["route"].split("-")[1],
            "eta": eta.isoformat(),
            "last_updated": now.isoformat()
        })
    
    return {
        "vessels": vessels,
        "count": len(vessels),
        "source": "simulated",
        "aisstream_configured": is_aisstream_configured(),
        "note": "Simulated positions. AISStream will provide real data when vessels are in Pacific."
    }


def enrich_vessel_data(vessel: dict) -> dict:
    """Enrich database vessel with computed fields"""
    now = datetime.utcnow()
    status = vessel.get("status", "underway")
    progress = random.uniform(0.1, 0.9) if status == "underway" else 0.05
    
    start_lat, start_lng = 22.6163, 120.3133
    end_lat, end_lng = 33.7406, -118.26
    
    lat = start_lat + (end_lat - start_lat) * progress
    lat += math.sin(progress * math.pi) * 8
    
    if progress < 0.5:
        lng = start_lng + 60 * progress
    else:
        lng = 180 - (180 + end_lng) * (progress - 0.5) * 2
        if lng > 180:
            lng -= 360
    
    vessel["position"] = {"lat": round(lat, 4), "lng": round(lng, 4)}
    
    if status == "underway":
        vessel["speed"] = round(random.uniform(16, 22), 1)
    elif status == "at_port":
        vessel["speed"] = 0
    else:
        vessel["speed"] = round(random.uniform(10, 18), 1)
    
    vessel["heading"] = round(85 + random.uniform(-15, 15))
    
    destinations = ["Los Angeles", "Long Beach", "Oakland", "Seattle"]
    vessel["destination"] = random.choice(destinations)
    
    if not vessel.get("eta"):
        remaining_days = (1 - progress) * 14
        vessel["eta"] = (now + timedelta(days=remaining_days)).isoformat()
    
    return vessel


@router.get("/{vessel_id}")
async def get_vessel(vessel_id: str):
    """Get vessel by ID"""
    try:
        supabase = get_supabase()
        result = supabase.table("vessels").select("*").eq("id", vessel_id).execute()
        if result.data:
            return enrich_vessel_data(result.data[0])
        raise HTTPException(status_code=404, detail="Vessel not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/aisstream")
async def get_aisstream_status():
    """Check AISStream configuration status"""
    return {
        "configured": is_aisstream_configured(),
        "api_key_set": bool(AISSTREAM_API_KEY),
        "provider": "aisstream.io"
    }
