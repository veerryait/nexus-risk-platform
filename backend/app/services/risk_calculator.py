"""
Risk Calculator Service - Aggregates all data sources into risk predictions
"""

from typing import Dict, List, Optional
from datetime import datetime

from app.services.weather_service import weather_service
from app.services.gdelt_service import gdelt_service
from app.services.fred_service import fred_service
from app.services.port_congestion_service import port_congestion_service


class RiskCalculator:
    """
    Aggregates risk scores from all data sources to produce
    overall supply chain risk predictions
    """
    
    # Risk factor weights (sum to 1.0)
    WEIGHTS = {
        "weather": 0.25,
        "port_congestion": 0.30,
        "geopolitical": 0.25,
        "economic": 0.20,
    }
    
    # Route-specific adjustments
    ROUTE_MODIFIERS = {
        "kaohsiung_losangeles": {
            "weather": 1.1,  # Long Pacific crossing = more weather exposure
            "port_congestion": 1.2,  # LA is often congested
            "geopolitical": 1.3,  # Taiwan Strait tensions
            "economic": 1.0,
        },
        "kaohsiung_longbeach": {
            "weather": 1.1,
            "port_congestion": 1.0,  # Long Beach slightly better
            "geopolitical": 1.3,
            "economic": 1.0,
        },
        "kaohsiung_oakland": {
            "weather": 1.15,  # Longer route
            "port_congestion": 0.9,  # Less congested
            "geopolitical": 1.3,
            "economic": 1.0,
        },
    }
    
    # Delay estimation factors (hours per risk unit)
    DELAY_FACTORS = {
        "weather": 24,  # 1.0 weather risk = up to 24 hours delay
        "port_congestion": 48,  # 1.0 congestion = up to 48 hours
        "geopolitical": 72,  # 1.0 geopolitical = up to 72 hours
        "economic": 12,  # 1.0 economic = up to 12 hours
    }
    
    async def calculate_route_risk(
        self, 
        route_id: Optional[str] = None
    ) -> Dict:
        """Calculate comprehensive risk score for a shipping route"""
        
        # Gather all risk scores
        weather_risk = await weather_service.get_weather_risk_score()
        congestion_risk = await port_congestion_service.get_congestion_risk_score()
        geopolitical_risk = await gdelt_service.get_geopolitical_risk_score()
        economic_risk = await fred_service.get_economic_risk_score()
        
        # Get route modifiers
        route_key = route_id or "kaohsiung_losangeles"
        modifiers = self.ROUTE_MODIFIERS.get(route_key, {
            "weather": 1.0, "port_congestion": 1.0, 
            "geopolitical": 1.0, "economic": 1.0
        })
        
        # Apply modifiers to individual risks
        adjusted_risks = {
            "weather": min(weather_risk * modifiers["weather"], 1.0),
            "port_congestion": min(congestion_risk * modifiers["port_congestion"], 1.0),
            "geopolitical": min(geopolitical_risk * modifiers["geopolitical"], 1.0),
            "economic": min(economic_risk * modifiers["economic"], 1.0),
        }
        
        # Calculate weighted overall risk
        overall_risk = sum(
            adjusted_risks[factor] * self.WEIGHTS[factor]
            for factor in self.WEIGHTS
        )
        
        # Calculate predicted delay
        predicted_delay = self._calculate_delay(adjusted_risks)
        
        # Determine confidence based on data freshness
        confidence = self._calculate_confidence()
        
        return {
            "route_id": route_id,
            "overall_risk_score": round(overall_risk, 3),
            "risk_level": self._get_risk_level(overall_risk),
            "predicted_delay_hours": predicted_delay,
            "confidence": confidence,
            "risk_factors": {
                "weather": {
                    "score": round(adjusted_risks["weather"], 3),
                    "weight": self.WEIGHTS["weather"],
                    "contribution": round(adjusted_risks["weather"] * self.WEIGHTS["weather"], 3),
                },
                "port_congestion": {
                    "score": round(adjusted_risks["port_congestion"], 3),
                    "weight": self.WEIGHTS["port_congestion"],
                    "contribution": round(adjusted_risks["port_congestion"] * self.WEIGHTS["port_congestion"], 3),
                },
                "geopolitical": {
                    "score": round(adjusted_risks["geopolitical"], 3),
                    "weight": self.WEIGHTS["geopolitical"],
                    "contribution": round(adjusted_risks["geopolitical"] * self.WEIGHTS["geopolitical"], 3),
                },
                "economic": {
                    "score": round(adjusted_risks["economic"], 3),
                    "weight": self.WEIGHTS["economic"],
                    "contribution": round(adjusted_risks["economic"] * self.WEIGHTS["economic"], 3),
                },
            },
            "top_risk_factor": self._get_top_risk_factor(adjusted_risks),
            "recommendations": self._get_recommendations(adjusted_risks, overall_risk),
            "calculated_at": datetime.utcnow().isoformat(),
        }
    
    async def get_risk_summary(self) -> Dict:
        """Get summary risk assessment across all routes"""
        routes = [
            ("kaohsiung_losangeles", "Kaohsiung → Los Angeles"),
            ("kaohsiung_longbeach", "Kaohsiung → Long Beach"),
            ("kaohsiung_oakland", "Kaohsiung → Oakland"),
        ]
        
        route_risks = []
        for route_id, route_name in routes:
            risk = await self.calculate_route_risk(route_id)
            route_risks.append({
                "route_id": route_id,
                "route_name": route_name,
                "risk_score": risk["overall_risk_score"],
                "risk_level": risk["risk_level"],
                "delay_hours": risk["predicted_delay_hours"],
            })
        
        # Calculate average risk
        avg_risk = sum(r["risk_score"] for r in route_risks) / len(route_risks)
        routes_at_risk = sum(1 for r in route_risks if r["risk_level"] in ["high", "critical"])
        avg_delay = sum(r["delay_hours"] for r in route_risks) / len(route_risks)
        
        return {
            "overall_risk": round(avg_risk, 3),
            "overall_level": self._get_risk_level(avg_risk),
            "routes": route_risks,
            "routes_at_risk": routes_at_risk,
            "total_routes": len(route_risks),
            "average_delay_hours": round(avg_delay, 1),
            "last_updated": datetime.utcnow().isoformat(),
        }
    
    def _calculate_delay(self, risks: Dict) -> int:
        """Estimate delay in hours based on risk factors"""
        total_delay = 0
        for factor, risk_score in risks.items():
            delay_factor = self.DELAY_FACTORS.get(factor, 12)
            total_delay += risk_score * delay_factor
        return round(total_delay)
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence score based on data availability"""
        # This would ideally check data freshness from each service
        # For now, return a reasonable default
        return 0.75
    
    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score >= 0.7:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.3:
            return "moderate"
        return "low"
    
    def _get_top_risk_factor(self, risks: Dict) -> Dict:
        """Identify the highest contributing risk factor"""
        top_factor = max(risks, key=lambda k: risks[k] * self.WEIGHTS[k])
        return {
            "factor": top_factor,
            "score": risks[top_factor],
            "contribution": risks[top_factor] * self.WEIGHTS[top_factor],
        }
    
    def _get_recommendations(self, risks: Dict, overall: float) -> List[str]:
        """Generate actionable recommendations based on risk profile"""
        recommendations = []
        
        if overall >= 0.7:
            recommendations.append("⚠️ High risk: Consider delaying shipments or using alternate routes")
        
        if risks["weather"] > 0.5:
            recommendations.append("🌊 Monitor Pacific weather conditions closely")
        
        if risks["port_congestion"] > 0.5:
            recommendations.append("🚢 Expect port delays; consider alternate ports")
        
        if risks["geopolitical"] > 0.5:
            recommendations.append("🌏 Geopolitical tensions elevated; monitor news")
        
        if risks["economic"] > 0.5:
            recommendations.append("📊 Economic headwinds may affect shipping rates")
        
        if not recommendations:
            recommendations.append("✅ Conditions favorable for normal operations")
        
        return recommendations


# Singleton instance
risk_calculator = RiskCalculator()
