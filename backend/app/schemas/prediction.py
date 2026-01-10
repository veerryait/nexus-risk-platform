"""
Prediction Schemas
"""

from typing import List
from pydantic import BaseModel
from datetime import datetime


class PredictionFactor(BaseModel):
    name: str
    contribution: float


class PredictionResponse(BaseModel):
    id: int
    route_id: int
    route_name: str
    predicted_delay_hours: int
    confidence: float
    risk_score: float
    factors: List[PredictionFactor]
    created_at: str
    
    class Config:
        from_attributes = True


class TopRiskFactor(BaseModel):
    factor: str
    occurrences: int


class RiskSummary(BaseModel):
    overall_risk: float
    routes_at_risk: int
    total_routes: int
    average_delay_hours: int
    top_risk_factors: List[TopRiskFactor]
    last_updated: str
