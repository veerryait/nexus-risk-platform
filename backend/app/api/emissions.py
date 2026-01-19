"""
Carbon Emissions API - Calculate CO2 emissions per voyage
Based on IMO MEPC guidelines and industry standards
"""

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime
import math

router = APIRouter()


# IMO standard emission factors (kg CO2 per ton of fuel)
EMISSION_FACTORS = {
    "HFO": 3.114,      # Heavy Fuel Oil
    "MDO": 3.206,      # Marine Diesel Oil  
    "LNG": 2.750,      # Liquefied Natural Gas
    "LSFO": 3.151,     # Low Sulfur Fuel Oil
}

# Average fuel consumption rates (tons per day at sea)
# Based on ship size and type
FUEL_CONSUMPTION_RATES = {
    "ultra_large": 250,    # ULCV 20,000+ TEU
    "very_large": 180,     # 14,000-20,000 TEU
    "large": 150,          # 10,000-14,000 TEU
    "medium": 100,         # 5,000-10,000 TEU
    "small": 60,           # Under 5,000 TEU
}


def estimate_vessel_size(name: str) -> str:
    """Estimate vessel size category from name"""
    large_vessels = ["Ever Ace", "Ever Given", "MSC Irina", "COSCO Shipping Universe", "ONE Innovation"]
    medium_vessels = ["YM Wish", "YM Wind", "Maersk Elba"]
    
    if any(v.lower() in name.lower() for v in large_vessels):
        return "ultra_large"
    elif any(v.lower() in name.lower() for v in medium_vessels):
        return "large"
    return "medium"


def calculate_voyage_emissions(
    distance_nm: float,
    speed_knots: float,
    vessel_name: str = "",
    fuel_type: str = "LSFO"
) -> dict:
    """
    Calculate CO2 emissions for a voyage
    
    Formula:
    - Sea days = Distance / (Speed × 24)
    - Fuel consumed = Sea days × Daily fuel consumption rate
    - CO2 emissions = Fuel consumed × Emission factor
    """
    if speed_knots <= 0:
        speed_knots = 18  # Default cruising speed
    
    # Calculate voyage duration in days
    sea_days = distance_nm / (speed_knots * 24)
    
    # Get fuel consumption rate based on vessel size
    vessel_size = estimate_vessel_size(vessel_name)
    daily_fuel_tons = FUEL_CONSUMPTION_RATES.get(vessel_size, 120)
    
    # Calculate total fuel consumed
    fuel_consumed_tons = sea_days * daily_fuel_tons
    
    # Calculate CO2 emissions
    emission_factor = EMISSION_FACTORS.get(fuel_type, EMISSION_FACTORS["LSFO"])
    co2_emissions_tons = fuel_consumed_tons * emission_factor
    
    # Calculate per-TEU emissions (assuming 80% capacity utilization)
    teu_capacity = {
        "ultra_large": 23000,
        "very_large": 16000,
        "large": 12000,
        "medium": 7000,
        "small": 3000,
    }
    capacity = teu_capacity.get(vessel_size, 10000)
    utilized_teu = capacity * 0.8
    co2_per_teu = co2_emissions_tons / utilized_teu * 1000  # kg per TEU
    
    return {
        "voyage_distance_nm": round(distance_nm, 1),
        "voyage_duration_days": round(sea_days, 2),
        "average_speed_knots": round(speed_knots, 1),
        "vessel_size_category": vessel_size,
        "fuel_type": fuel_type,
        "fuel_consumed_tons": round(fuel_consumed_tons, 1),
        "co2_emissions_tons": round(co2_emissions_tons, 1),
        "co2_per_teu_kg": round(co2_per_teu, 2),
        "emission_factor": emission_factor,
        "methodology": "IMO MEPC guidelines",
        "calculated_at": datetime.utcnow().isoformat()
    }


@router.get("/")
async def get_emissions_info():
    """Get emissions calculation methodology info"""
    return {
        "description": "Carbon emissions calculator based on IMO MEPC guidelines",
        "emission_factors": EMISSION_FACTORS,
        "fuel_consumption_rates": FUEL_CONSUMPTION_RATES,
        "note": "Emissions vary based on vessel size, speed, weather, and cargo load"
    }


@router.get("/calculate")
async def calculate_emissions(
    distance_nm: float = Query(6150, description="Voyage distance in nautical miles"),
    speed_knots: float = Query(18, description="Average speed in knots"),
    vessel_name: str = Query("", description="Vessel name for size estimation"),
    fuel_type: str = Query("LSFO", description="Fuel type: HFO, MDO, LNG, LSFO")
):
    """Calculate CO2 emissions for a voyage"""
    return calculate_voyage_emissions(distance_nm, speed_knots, vessel_name, fuel_type)


@router.get("/vessel/{vessel_id}")
async def get_vessel_emissions(vessel_id: str):
    """Get estimated emissions for a specific vessel's current voyage"""
    # Taiwan to US West Coast typical distance
    typical_distances = {
        "TWKHH-USLAX": 6150,
        "TWKHH-USLGB": 6150,
        "TWKHH-USOAK": 5950,
        "TWKHH-USSEA": 5200,
        "TWTPE-USLAX": 6300,
    }
    
    # Default to LA route
    distance = typical_distances.get("TWKHH-USLAX", 6150)
    
    return {
        "vessel_id": vessel_id,
        "route": "Taiwan → US West Coast",
        **calculate_voyage_emissions(distance, 18, vessel_id, "LSFO")
    }


@router.get("/routes/summary")
async def get_routes_emissions_summary():
    """Get emissions summary for all tracked routes"""
    routes = [
        {"route": "Kaohsiung → Los Angeles", "distance_nm": 6150},
        {"route": "Kaohsiung → Long Beach", "distance_nm": 6150},
        {"route": "Kaohsiung → Oakland", "distance_nm": 5950},
        {"route": "Kaohsiung → Seattle", "distance_nm": 5200},
        {"route": "Taipei → Los Angeles", "distance_nm": 6300},
    ]
    
    summary = []
    for r in routes:
        emissions = calculate_voyage_emissions(r["distance_nm"], 18, "", "LSFO")
        summary.append({
            "route": r["route"],
            "distance_nm": r["distance_nm"],
            "co2_emissions_tons": emissions["co2_emissions_tons"],
            "co2_per_teu_kg": emissions["co2_per_teu_kg"],
            "voyage_days": emissions["voyage_duration_days"]
        })
    
    return {
        "routes": summary,
        "total_tracked_routes": len(summary),
        "methodology": "IMO MEPC guidelines with LSFO fuel assumption"
    }
