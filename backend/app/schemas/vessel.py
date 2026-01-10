"""
Vessel Schemas
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class VesselBase(BaseModel):
    name: str
    imo: str
    carrier: str
    capacity_teu: int


class VesselCreate(VesselBase):
    pass


class VesselResponse(VesselBase):
    id: int
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    status: str = "unknown"
    
    class Config:
        from_attributes = True


class VesselPositionResponse(BaseModel):
    id: int
    vessel_id: int
    lat: float
    lng: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True
