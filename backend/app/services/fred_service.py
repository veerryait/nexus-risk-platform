"""
FRED Service - Federal Reserve Economic Data Integration
Tracks economic indicators relevant to shipping and trade
"""

import httpx
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os


class FREDService:
    """FRED API integration for economic indicators"""
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    # Key economic series for supply chain analysis
    SERIES = {
        # Trade and shipping indicators
        "imports_goods": "IMPGS",  # Imports of Goods
        "exports_goods": "EXPGS",  # Exports of Goods
        "trade_balance": "BOPGSTB",  # Trade Balance: Goods
        
        # Manufacturing and production
        "industrial_production": "INDPRO",  # Industrial Production Index
        "manufacturing_pmi": "MANEMP",  # Manufacturing Employment
        
        # Container and freight
        "ppi_freight": "PCU4841214841212",  # PPI: General Freight Trucking
        
        # Economic health
        "gdp": "GDP",  # Gross Domestic Product
        "unemployment": "UNRATE",  # Unemployment Rate
    }
    
    # Shipping-specific series (proxy for maritime activity)
    SHIPPING_PROXIES = {
        "west_coast_imports": "IMPGS",
        "manufacturing_activity": "INDPRO",
    }
    
    def __init__(self):
        self.api_key = os.getenv("FRED_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
        self._cache = {}
        self._cache_time = {}
    
    async def get_series_data(
        self, 
        series_id: str, 
        limit: int = 12
    ) -> List[Dict]:
        """Get historical data for a FRED series"""
        
        # Check cache (1 hour expiry)
        cache_key = f"{series_id}_{limit}"
        if cache_key in self._cache:
            cache_age = datetime.now() - self._cache_time[cache_key]
            if cache_age < timedelta(hours=1):
                return self._cache[cache_key]
        
        if not self.api_key:
            return self._mock_series_data(series_id, limit)
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": limit,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            observations = []
            for obs in data.get("observations", []):
                if obs.get("value") != ".":
                    observations.append({
                        "date": obs["date"],
                        "value": float(obs["value"]),
                    })
            
            # Cache the result
            self._cache[cache_key] = observations
            self._cache_time[cache_key] = datetime.now()
            
            return observations
            
        except Exception as e:
            print(f"FRED API error: {e}")
            return self._mock_series_data(series_id, limit)
    
    async def get_trade_indicators(self) -> Dict:
        """Get key trade-related economic indicators"""
        imports_data = await self.get_series_data(self.SERIES["imports_goods"])
        exports_data = await self.get_series_data(self.SERIES["exports_goods"])
        production = await self.get_series_data(self.SERIES["industrial_production"])
        
        return {
            "imports": {
                "latest_value": imports_data[0]["value"] if imports_data else None,
                "latest_date": imports_data[0]["date"] if imports_data else None,
                "trend": self._calculate_trend(imports_data),
                "history": imports_data[:6],
            },
            "exports": {
                "latest_value": exports_data[0]["value"] if exports_data else None,
                "latest_date": exports_data[0]["date"] if exports_data else None,
                "trend": self._calculate_trend(exports_data),
                "history": exports_data[:6],
            },
            "industrial_production": {
                "latest_value": production[0]["value"] if production else None,
                "latest_date": production[0]["date"] if production else None,
                "trend": self._calculate_trend(production),
                "history": production[:6],
            },
            "last_updated": datetime.utcnow().isoformat(),
        }
    
    async def get_shipping_rate_proxy(self) -> Dict:
        """Get proxy for shipping rates from freight PPI"""
        freight_data = await self.get_series_data(self.SERIES["ppi_freight"])
        
        if not freight_data:
            return {
                "latest_index": 100.0,
                "trend": "stable",
                "risk_level": "low",
            }
        
        latest = freight_data[0]["value"]
        trend = self._calculate_trend(freight_data)
        
        # Determine risk level based on trend
        risk_level = "low"
        if trend == "rising" and latest > 150:
            risk_level = "high"
        elif trend == "rising" or latest > 130:
            risk_level = "medium"
        
        return {
            "latest_index": latest,
            "latest_date": freight_data[0]["date"],
            "trend": trend,
            "risk_level": risk_level,
            "history": freight_data[:6],
        }
    
    async def get_economic_risk_score(self) -> float:
        """Calculate economic risk score (0-1) based on indicators"""
        trade_data = await self.get_trade_indicators()
        shipping_data = await self.get_shipping_rate_proxy()
        
        risk_score = 0.0
        
        # Trade imbalance risk
        if trade_data["imports"]["trend"] == "rising" and trade_data["exports"]["trend"] == "falling":
            risk_score += 0.15
        
        # Industrial production decline risk
        if trade_data["industrial_production"]["trend"] == "falling":
            risk_score += 0.2
        
        # Shipping rate risk
        shipping_risk_map = {"low": 0.05, "medium": 0.15, "high": 0.3}
        risk_score += shipping_risk_map.get(shipping_data["risk_level"], 0.1)
        
        # Normalize
        return min(risk_score, 1.0)
    
    async def get_economic_summary(self) -> Dict:
        """Get comprehensive economic summary"""
        trade = await self.get_trade_indicators()
        shipping = await self.get_shipping_rate_proxy()
        risk_score = await self.get_economic_risk_score()
        
        return {
            "trade_indicators": trade,
            "shipping_rates": shipping,
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.5 else "medium" if risk_score > 0.25 else "low",
            "last_updated": datetime.utcnow().isoformat(),
        }
    
    def _calculate_trend(self, data: List[Dict]) -> str:
        """Calculate trend from historical data"""
        if len(data) < 2:
            return "stable"
        
        recent_avg = sum(d["value"] for d in data[:3]) / min(3, len(data))
        older_avg = sum(d["value"] for d in data[3:6]) / min(3, len(data[3:6])) if len(data) > 3 else recent_avg
        
        if recent_avg > older_avg * 1.02:
            return "rising"
        elif recent_avg < older_avg * 0.98:
            return "falling"
        return "stable"
    
    def _mock_series_data(self, series_id: str, limit: int) -> List[Dict]:
        """Return mock data when API key is not available"""
        import random
        base_date = datetime.now()
        base_value = random.uniform(80, 120)
        
        data = []
        for i in range(limit):
            date = base_date - timedelta(days=30 * i)
            value = base_value * (1 + random.uniform(-0.05, 0.05))
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": round(value, 2),
            })
        return data
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
fred_service = FREDService()
