"""
Admin API - Manual Data Entry Endpoints
For weekly port congestion and shipping rate updates
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
import os

from supabase import create_client, Client

router = APIRouter()


# Pydantic models
class PortCongestionEntry(BaseModel):
    port_code: str
    port_name: Optional[str] = None
    week_start: date
    vessels_waiting: int
    avg_wait_days: float
    berth_utilization: float
    notes: Optional[str] = None
    entered_by: Optional[str] = "admin"


class ShippingRateEntry(BaseModel):
    week_start: date
    route: str
    container_rate_usd: float
    bulk_rate_usd: Optional[float] = None
    trend: Optional[str] = "stable"  # rising, falling, stable
    notes: Optional[str] = None
    entered_by: Optional[str] = "admin"


class TriggerCollectionRequest(BaseModel):
    sources: Optional[List[str]] = ["weather", "news", "economics"]


def get_supabase() -> Client:
    """Get Supabase client"""
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Ensure .env is loaded
    env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    url = os.getenv("SUPABASE_URL", "https://hssnbnsffqorupviykha.supabase.co")
    # Try multiple key names
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    
    if not key:
        # Hardcoded fallback for this project
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"
    
    return create_client(url, key)


# ==================== Port Congestion Endpoints ====================

@router.post("/port-congestion")
async def add_port_congestion(entry: PortCongestionEntry):
    """Add weekly port congestion data (manual entry)"""
    try:
        supabase = get_supabase()
        
        result = supabase.table("manual_port_congestion").insert({
            "port_code": entry.port_code,
            "port_name": entry.port_name,
            "week_start": entry.week_start.isoformat(),
            "vessels_waiting": entry.vessels_waiting,
            "avg_wait_days": entry.avg_wait_days,
            "berth_utilization": entry.berth_utilization,
            "notes": entry.notes,
            "entered_by": entry.entered_by,
        }).execute()
        
        return {
            "status": "success",
            "message": f"Port congestion data added for {entry.port_code}",
            "id": result.data[0]["id"] if result.data else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/port-congestion")
async def get_port_congestion_history(port_code: Optional[str] = None, limit: int = 20):
    """Get manual port congestion entries"""
    try:
        supabase = get_supabase()
        
        query = supabase.table("manual_port_congestion").select("*").order("week_start", desc=True).limit(limit)
        
        if port_code:
            query = query.eq("port_code", port_code)
        
        result = query.execute()
        return {"entries": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Shipping Rate Endpoints ====================

# Quick update model for 4 key ports
class QuickPortUpdate(BaseModel):
    port: str  # USLAX, USLGB, CNSHA, TWKHH
    vessels_waiting: int = 0
    avg_wait_days: float = 0.0
    congestion_level: str = "low"  # low, medium, high, severe


@router.post("/port-status/quick")
async def quick_port_update(update: QuickPortUpdate):
    """Quick update for 4 key ports - LA, Long Beach, Shanghai, Kaohsiung"""
    
    ports = {
        "USLAX": "Port of Los Angeles",
        "USLGB": "Port of Long Beach", 
        "CNSHA": "Port of Shanghai",
        "TWKHH": "Port of Kaohsiung"
    }
    
    if update.port not in ports:
        raise HTTPException(400, f"Invalid port. Use: {list(ports.keys())}")
    
    try:
        supabase = get_supabase()
        
        # Calculate congestion score
        score_map = {"low": 0.2, "medium": 0.5, "high": 0.75, "severe": 0.95}
        
        result = supabase.table("port_status").insert({
            "recorded_at": datetime.utcnow().isoformat(),
            "port_code": update.port,
            "port_name": ports[update.port],
            "vessels_waiting": update.vessels_waiting,
            "avg_wait_days": update.avg_wait_days,
            "congestion_level": update.congestion_level,
            "congestion_score": score_map.get(update.congestion_level, 0.3),
            "data_source": "web_form",
        }).execute()
        
        return {
            "status": "success",
            "port": ports[update.port],
            "congestion": update.congestion_level,
            "id": result.data[0]["id"] if result.data else None
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/port-status")
async def get_port_status():
    """Get current status of 4 key ports"""
    try:
        supabase = get_supabase()
        result = supabase.table("port_status").select("*").order("recorded_at", desc=True).limit(10).execute()
        return {"ports": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/shipping-rates")
async def add_shipping_rate(entry: ShippingRateEntry):
    """Add weekly shipping rate data (manual entry)"""
    try:
        supabase = get_supabase()
        
        result = supabase.table("manual_shipping_rates").insert({
            "week_start": entry.week_start.isoformat(),
            "route": entry.route,
            "container_rate_usd": entry.container_rate_usd,
            "bulk_rate_usd": entry.bulk_rate_usd,
            "trend": entry.trend,
            "notes": entry.notes,
            "entered_by": entry.entered_by,
        }).execute()
        
        return {
            "status": "success",
            "message": f"Shipping rate data added for {entry.route}",
            "id": result.data[0]["id"] if result.data else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shipping-rates")
async def get_shipping_rate_history(route: Optional[str] = None, limit: int = 20):
    """Get manual shipping rate entries"""
    try:
        supabase = get_supabase()
        
        query = supabase.table("manual_shipping_rates").select("*").order("week_start", desc=True).limit(limit)
        
        if route:
            query = query.eq("route", route)
        
        result = query.execute()
        return {"entries": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Data Collection Trigger ====================

@router.post("/collect")
async def trigger_data_collection(request: TriggerCollectionRequest):
    """Manually trigger data collection from APIs"""
    from data_ingestion.data_collector import DataCollector
    
    collector = DataCollector()
    results = {}
    
    if "weather" in request.sources:
        results["weather"] = await collector.collect_weather_data()
    
    if "news" in request.sources:
        results["news"] = await collector.collect_news_data()
    
    if "economics" in request.sources:
        results["economics"] = await collector.collect_economics_data()
    
    return {
        "status": "success",
        "collected_at": datetime.utcnow().isoformat(),
        "results": results
    }


@router.get("/collection-history")
async def get_collection_history(source: str = "weather", limit: int = 10):
    """Get history of automated data collection"""
    try:
        supabase = get_supabase()
        
        table_map = {
            "weather": "collected_weather",
            "news": "collected_news",
            "economics": "collected_economics",
        }
        
        table = table_map.get(source)
        if not table:
            raise HTTPException(status_code=400, detail=f"Invalid source: {source}")
        
        result = supabase.table(table).select("*").order("collected_at", desc=True).limit(limit).execute()
        
        return {"source": source, "entries": result.data, "count": len(result.data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
