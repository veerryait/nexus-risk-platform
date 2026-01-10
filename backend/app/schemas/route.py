"""
Route Schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class RouteBase(BaseModel):
    origin: str
    destination: str
    distance_nm: int
    avg_transit_days: int


class RouteResponse(RouteBase):
    id: int
    
    class Config:
        from_attributes = True


class RiskFactor(BaseModel):
    factor: str
    impact: float


class RouteWithRisk(RouteResponse):
    risk_score: float
    risk_factors: List[RiskFactor]
    predicted_delay_hours: int
