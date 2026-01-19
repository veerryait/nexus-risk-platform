"""
AISStream Service - Real-time vessel tracking via WebSocket
Free tier: https://aisstream.io
"""

import os
import json
import asyncio
import websockets
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY", "")


@dataclass
class VesselPosition:
    """Real-time vessel position from AIS"""
    mmsi: str
    imo: Optional[str]
    name: str
    latitude: float
    longitude: float
    speed: float  # knots
    heading: float  # degrees
    course: float  # degrees
    status: str
    destination: Optional[str]
    eta: Optional[str]
    timestamp: str


class AISStreamService:
    """Service to fetch real-time vessel data from AISStream.io"""
    
    def __init__(self):
        self.api_key = AISSTREAM_API_KEY
        self.vessel_cache: Dict[str, VesselPosition] = {}
        self.cache_ttl = timedelta(minutes=5)
        self.last_fetch = None
        
        # IMOs of vessels we want to track (Taiwan-US routes)
        self.tracked_imos = [
            "9893890",  # Ever Ace
            "9811000",  # Ever Given
            "9708451",  # YM Wish
            "9708463",  # YM Wind
            "9458089",  # Maersk Elba
            "9893905",  # Ever Act
            "9893917",  # Ever Aim
            "9893929",  # Ever Alp
            "9684653",  # YM World
            "9704611",  # YM Wholesome
            "9795610",  # COSCO Shipping Universe
            "9795622",  # COSCO Shipping Nebula
            "9939137",  # ONE Innovation
            "9933004",  # ONE Infinity
            "9929429",  # MSC Irina
        ]
    
    def is_configured(self) -> bool:
        """Check if API key is configured"""
        return bool(self.api_key) and self.api_key != "your_aisstream_api_key_here"
    
    async def fetch_vessel_positions(self) -> List[VesselPosition]:
        """Fetch current positions for tracked vessels via WebSocket"""
        if not self.is_configured():
            logger.warning("AISStream API key not configured")
            return []
        
        # Check cache
        if self.last_fetch and datetime.utcnow() - self.last_fetch < self.cache_ttl:
            return list(self.vessel_cache.values())
        
        positions = []
        
        try:
            # Connect to AISStream WebSocket
            uri = "wss://stream.aisstream.io/v0/stream"
            
            async with websockets.connect(uri) as ws:
                # Subscribe to our tracked vessels
                subscribe_msg = {
                    "APIKey": self.api_key,
                    "BoundingBoxes": [
                        # Expanded Pacific Ocean - Taiwan to US West Coast
                        [[0, 100], [60, -100]],
                        # East Asia shipping lanes
                        [[10, 100], [45, 145]],
                        # US West Coast ports
                        [[30, -130], [50, -115]],
                    ],
                    "FilterMessageTypes": ["PositionReport"]
                }
                
                await ws.send(json.dumps(subscribe_msg))
                
                # Collect messages for a longer period to catch more vessels
                start_time = asyncio.get_event_loop().time()
                timeout = 15  # increased from 5 seconds
                
                while asyncio.get_event_loop().time() - start_time < timeout:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=1)
                        data = json.loads(msg)
                        
                        if data.get("MessageType") == "PositionReport":
                            meta = data.get("MetaData", {})
                            pos = data.get("Message", {}).get("PositionReport", {})
                            
                            imo = meta.get("IMO", "")
                            if imo and str(imo) in self.tracked_imos:
                                vessel_pos = VesselPosition(
                                    mmsi=str(meta.get("MMSI", "")),
                                    imo=str(imo),
                                    name=meta.get("ShipName", "Unknown"),
                                    latitude=pos.get("Latitude", 0),
                                    longitude=pos.get("Longitude", 0),
                                    speed=pos.get("Sog", 0),  # Speed over ground
                                    heading=pos.get("TrueHeading", 0),
                                    course=pos.get("Cog", 0),  # Course over ground
                                    status=self._decode_nav_status(pos.get("NavigationalStatus", 15)),
                                    destination=meta.get("Destination", "Unknown"),
                                    eta=self._format_eta(meta.get("ETA", "")),
                                    timestamp=datetime.utcnow().isoformat()
                                )
                                positions.append(vessel_pos)
                                self.vessel_cache[vessel_pos.imo] = vessel_pos
                    except asyncio.TimeoutError:
                        continue
                
                self.last_fetch = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"AISStream connection error: {e}")
        
        return positions if positions else list(self.vessel_cache.values())
    
    def _decode_nav_status(self, status: int) -> str:
        """Decode AIS navigational status code"""
        statuses = {
            0: "underway",
            1: "anchored",
            2: "not_under_command",
            3: "restricted_manoeuvrability",
            4: "constrained_by_draught",
            5: "moored",
            6: "aground",
            7: "fishing",
            8: "underway_sailing",
            15: "unknown"
        }
        return statuses.get(status, "unknown")
    
    def _format_eta(self, eta_str: str) -> Optional[str]:
        """Format ETA string to ISO format"""
        if not eta_str:
            return None
        try:
            # ETA format varies, try to parse
            return eta_str
        except Exception:
            return None
    
    def get_cached_positions(self) -> List[Dict]:
        """Get cached vessel positions as dictionaries"""
        return [asdict(v) for v in self.vessel_cache.values()]


# Singleton instance
ais_service = AISStreamService()


async def get_real_vessel_positions() -> List[Dict]:
    """Helper function to get real vessel positions"""
    if not ais_service.is_configured():
        return []
    
    positions = await ais_service.fetch_vessel_positions()
    return [asdict(p) for p in positions]
