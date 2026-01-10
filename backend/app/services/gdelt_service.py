"""
GDELT Service - Geopolitical News & Events Tracking
Uses GDELT Project for real-time global event monitoring
"""

import httpx
import feedparser
from typing import Dict, List
from datetime import datetime, timedelta
import re


class GDELTService:
    """GDELT Project integration for geopolitical event tracking"""
    
    # GDELT GKG (Global Knowledge Graph) API
    DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
    GEO_API = "https://api.gdeltproject.org/api/v2/geo/geo"
    
    # Keywords for maritime/Taiwan-related events
    TAIWAN_KEYWORDS = [
        "Taiwan Strait", "Taiwan military", "China Taiwan",
        "Taiwan blockade", "Taiwan shipping", "TSMC",
    ]
    
    SHIPPING_KEYWORDS = [
        "shipping disruption", "port strike", "maritime accident",
        "container shortage", "shipping delay", "freight rates",
        "port congestion", "supply chain disruption",
    ]
    
    TRADE_KEYWORDS = [
        "trade war", "tariff", "sanctions", "export ban",
        "semiconductor", "chip shortage",
    ]
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_taiwan_strait_events(self) -> List[Dict]:
        """Get recent events related to Taiwan Strait tensions"""
        return await self._search_events(self.TAIWAN_KEYWORDS, theme="taiwan_geopolitical")
    
    async def get_shipping_disruption_events(self) -> List[Dict]:
        """Get events related to shipping disruptions"""
        return await self._search_events(self.SHIPPING_KEYWORDS, theme="shipping")
    
    async def get_trade_events(self) -> List[Dict]:
        """Get trade-related events (tariffs, sanctions, etc.)"""
        return await self._search_events(self.TRADE_KEYWORDS, theme="trade")
    
    async def _search_events(self, keywords: List[str], theme: str) -> List[Dict]:
        """Search GDELT for events matching keywords"""
        events = []
        
        try:
            # Use GDELT DOC API with keyword search
            query = " OR ".join(f'"{kw}"' for kw in keywords[:3])  # Limit keywords
            
            response = await self.client.get(
                self.DOC_API,
                params={
                    "query": query,
                    "mode": "artlist",
                    "maxrecords": 10,
                    "format": "json",
                    "timespan": "7d",
                    "sort": "datedesc",
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                for article in articles[:10]:
                    events.append({
                        "title": article.get("title", ""),
                        "url": article.get("url", ""),
                        "source": article.get("domain", "unknown"),
                        "date": article.get("seendate", ""),
                        "theme": theme,
                        "sentiment": self._analyze_sentiment(article.get("title", "")),
                        "risk_contribution": self._calculate_event_risk(article, theme),
                    })
        except Exception as e:
            print(f"GDELT API error: {e}")
            # Return mock events on error
            events = self._mock_events(theme)
        
        return events
    
    async def get_geopolitical_risk_score(self) -> float:
        """Calculate overall geopolitical risk score (0-1)"""
        taiwan_events = await self.get_taiwan_strait_events()
        shipping_events = await self.get_shipping_disruption_events()
        trade_events = await self.get_trade_events()
        
        # Weight different event types
        taiwan_risk = sum(e["risk_contribution"] for e in taiwan_events) * 0.4
        shipping_risk = sum(e["risk_contribution"] for e in shipping_events) * 0.35
        trade_risk = sum(e["risk_contribution"] for e in trade_events) * 0.25
        
        total_risk = taiwan_risk + shipping_risk + trade_risk
        
        # Normalize to 0-1 scale
        return min(total_risk, 1.0)
    
    async def get_all_events_summary(self) -> Dict:
        """Get summary of all monitored events"""
        taiwan = await self.get_taiwan_strait_events()
        shipping = await self.get_shipping_disruption_events()
        trade = await self.get_trade_events()
        
        return {
            "taiwan_strait": {
                "event_count": len(taiwan),
                "events": taiwan[:5],
                "risk_level": "high" if len(taiwan) > 5 else "medium" if len(taiwan) > 2 else "low"
            },
            "shipping_disruptions": {
                "event_count": len(shipping),
                "events": shipping[:5],
                "risk_level": "high" if len(shipping) > 5 else "medium" if len(shipping) > 2 else "low"
            },
            "trade_tensions": {
                "event_count": len(trade),
                "events": trade[:5],
                "risk_level": "high" if len(trade) > 5 else "medium" if len(trade) > 2 else "low"
            },
            "last_updated": datetime.utcnow().isoformat(),
        }
    
    def _analyze_sentiment(self, title: str) -> str:
        """Simple sentiment analysis based on keywords"""
        negative_words = ["crisis", "war", "conflict", "disruption", "delay", "shortage", "block", "strike"]
        positive_words = ["resolve", "agreement", "improve", "ease", "recover"]
        
        title_lower = title.lower()
        neg_count = sum(1 for w in negative_words if w in title_lower)
        pos_count = sum(1 for w in positive_words if w in title_lower)
        
        if neg_count > pos_count:
            return "negative"
        elif pos_count > neg_count:
            return "positive"
        return "neutral"
    
    def _calculate_event_risk(self, article: Dict, theme: str) -> float:
        """Calculate risk contribution from a single event"""
        base_risk = 0.05
        title = article.get("title", "").lower()
        
        # High-risk keywords
        high_risk = ["military", "blockade", "war", "invasion", "missile", "strike action"]
        medium_risk = ["tension", "dispute", "delay", "shortage", "congestion"]
        
        for keyword in high_risk:
            if keyword in title:
                base_risk += 0.15
                break
        
        for keyword in medium_risk:
            if keyword in title:
                base_risk += 0.08
                break
        
        # Theme-specific adjustments
        if theme == "taiwan_geopolitical":
            base_risk *= 1.2
        
        return min(base_risk, 0.3)
    
    def _mock_events(self, theme: str) -> List[Dict]:
        """Return mock events when API fails"""
        mock_data = {
            "taiwan_geopolitical": [
                {"title": "Taiwan monitors Chinese military activity in strait", "risk_contribution": 0.1},
            ],
            "shipping": [
                {"title": "Port of LA reports moderate congestion levels", "risk_contribution": 0.08},
            ],
            "trade": [
                {"title": "Semiconductor supply chain shows signs of stabilization", "risk_contribution": 0.05},
            ],
        }
        
        events = mock_data.get(theme, [])
        for event in events:
            event.update({
                "url": "#",
                "source": "mock_data",
                "date": datetime.utcnow().isoformat(),
                "theme": theme,
                "sentiment": "neutral",
            })
        return events
    
    async def close(self):
        await self.client.aclose()


# Singleton instance
gdelt_service = GDELTService()
