"""
Data Sources API - External data endpoints
"""

from fastapi import APIRouter
from typing import Optional

from app.services.weather_service import weather_service
from app.services.gdelt_service import gdelt_service
from app.services.fred_service import fred_service
from app.services.port_congestion_service import port_congestion_service
from app.services.risk_calculator import risk_calculator
from app.services.historical_service import historical_service

router = APIRouter()


# ----- Weather Endpoints -----

@router.get("/weather")
async def get_weather_data():
    """Get current weather conditions along shipping routes"""
    route_weather = await weather_service.get_route_weather()
    storm_alerts = await weather_service.get_storm_alerts()
    risk_score = await weather_service.get_weather_risk_score()
    
    return {
        "route_conditions": route_weather,
        "storm_alerts": storm_alerts,
        "risk_score": round(risk_score, 3),
        "risk_level": "high" if risk_score > 0.5 else "moderate" if risk_score > 0.25 else "low",
    }


@router.get("/weather/storms")
async def get_storm_alerts():
    """Get active storm/typhoon alerts in shipping zones"""
    return await weather_service.get_storm_alerts()


# ----- Geopolitical/News Endpoints -----

@router.get("/news")
async def get_news_events():
    """Get geopolitical events affecting supply chains"""
    return await gdelt_service.get_all_events_summary()


@router.get("/news/taiwan")
async def get_taiwan_events():
    """Get Taiwan Strait related events"""
    return await gdelt_service.get_taiwan_strait_events()


@router.get("/news/shipping")
async def get_shipping_events():
    """Get shipping disruption events"""
    return await gdelt_service.get_shipping_disruption_events()


@router.get("/news/trade")
async def get_trade_events():
    """Get trade-related events (tariffs, sanctions)"""
    return await gdelt_service.get_trade_events()


# ----- Economic Indicators Endpoints -----

@router.get("/economics")
async def get_economic_data():
    """Get economic indicators summary"""
    return await fred_service.get_economic_summary()


@router.get("/economics/trade")
async def get_trade_indicators():
    """Get trade-specific economic indicators"""
    return await fred_service.get_trade_indicators()


@router.get("/economics/shipping-rates")
async def get_shipping_rates():
    """Get shipping rate proxy from freight PPI"""
    return await fred_service.get_shipping_rate_proxy()


# ----- Port Congestion Endpoints -----

@router.get("/ports")
async def get_ports_summary():
    """Get summary of all port conditions"""
    return await port_congestion_service.get_port_summary()


@router.get("/ports/{port_id}")
async def get_port_congestion(port_id: str):
    """Get congestion data for a specific port
    
    Port IDs: los_angeles, long_beach, oakland
    """
    return await port_congestion_service.get_port_congestion(port_id)


@router.get("/ports/list/all")
async def get_all_ports():
    """Get congestion data for all monitored ports"""
    return await port_congestion_service.get_all_ports_congestion()


# ----- Risk Assessment Endpoints -----

@router.get("/risk")
async def get_risk_summary():
    """Get overall risk summary across all routes"""
    return await risk_calculator.get_risk_summary()


@router.get("/risk/route/{route_id}")
async def get_route_risk(route_id: Optional[str] = None):
    """Get detailed risk assessment for a specific route
    
    Route IDs: kaohsiung_losangeles, kaohsiung_longbeach, kaohsiung_oakland
    """
    return await risk_calculator.calculate_route_risk(route_id)


# ----- Historical Data Endpoints -----

@router.get("/historical")
async def get_historical_summary():
    """Get historical data summary"""
    return await historical_service.get_summary()


@router.get("/historical/statistics")
async def get_historical_statistics(
    origin: Optional[str] = None,
    destination: Optional[str] = None
):
    """Get route statistics from historical data
    
    Port codes: TWKHH (Kaohsiung), USLAX (Los Angeles), USLGB (Long Beach), etc.
    """
    return await historical_service.get_route_statistics(origin, destination)


@router.get("/historical/seasonal")
async def get_seasonal_patterns(origin: Optional[str] = None):
    """Get monthly seasonal patterns for delays"""
    return await historical_service.get_seasonal_patterns(origin)


@router.get("/historical/delays")
async def get_delay_distribution():
    """Get delay distribution histogram"""
    return await historical_service.get_delay_distribution()


@router.get("/historical/baseline")
async def get_historical_baseline():
    """Get historical baseline metrics for predictions"""
    return await historical_service.get_historical_baseline()


@router.get("/historical/carriers")
async def get_carrier_performance():
    """Get carrier performance rankings"""
    return await historical_service.get_carrier_performance()


@router.get("/historical/congestion")
async def get_congestion_history(port: Optional[str] = None):
    """Get historical port congestion data"""
    return await historical_service.get_port_congestion_history(port)
