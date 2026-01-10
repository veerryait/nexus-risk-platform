"""
Database Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Vessel(Base):
    """Container vessel tracking"""
    __tablename__ = "vessels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    imo = Column(String(20), unique=True, index=True)
    carrier = Column(String(100))
    capacity_teu = Column(Integer)
    current_lat = Column(Float)
    current_lng = Column(Float)
    status = Column(String(50), default="unknown")
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    positions = relationship("VesselPosition", back_populates="vessel")
    transits = relationship("RouteTransit", back_populates="vessel")


class VesselPosition(Base):
    """Historical vessel positions"""
    __tablename__ = "vessel_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, ForeignKey("vessels.id"), index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    speed = Column(Float)
    heading = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    vessel = relationship("Vessel", back_populates="positions")


class Port(Base):
    """Port information"""
    __tablename__ = "ports"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(10), unique=True, index=True)
    country = Column(String(100))
    lat = Column(Float)
    lng = Column(Float)
    timezone = Column(String(50))


class Route(Base):
    """Shipping routes"""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    origin_port_id = Column(Integer, ForeignKey("ports.id"))
    destination_port_id = Column(Integer, ForeignKey("ports.id"))
    origin_name = Column(String(255))
    destination_name = Column(String(255))
    distance_nm = Column(Integer)
    avg_transit_days = Column(Integer)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    transits = relationship("RouteTransit", back_populates="route")
    predictions = relationship("RiskPrediction", back_populates="route")


class RouteTransit(Base):
    """Individual vessel transits on a route"""
    __tablename__ = "route_transits"
    
    id = Column(Integer, primary_key=True, index=True)
    vessel_id = Column(Integer, ForeignKey("vessels.id"), index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    departure_time = Column(DateTime)
    eta = Column(DateTime)
    actual_arrival = Column(DateTime)
    status = Column(String(50), default="scheduled")  # scheduled, underway, arrived, delayed
    delay_hours = Column(Integer, default=0)
    
    # Relationships
    vessel = relationship("Vessel", back_populates="transits")
    route = relationship("Route", back_populates="transits")


class WeatherEvent(Base):
    """Weather events affecting routes"""
    __tablename__ = "weather_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50))  # typhoon, storm, fog, etc.
    severity = Column(String(20))  # low, medium, high, extreme
    lat = Column(Float)
    lng = Column(Float)
    radius_nm = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    description = Column(Text)


class PortCongestion(Base):
    """Port congestion metrics"""
    __tablename__ = "port_congestion"
    
    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(Integer, ForeignKey("ports.id"), index=True)
    wait_time_hours = Column(Float)
    berth_utilization = Column(Float)
    vessels_waiting = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class GeopoliticalEvent(Base):
    """Geopolitical events affecting supply chain"""
    __tablename__ = "geopolitical_events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    source = Column(String(255))
    risk_score = Column(Float)  # 0-1
    region = Column(String(100))
    event_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskPrediction(Base):
    """ML-generated risk predictions"""
    __tablename__ = "risk_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), index=True)
    predicted_delay_hours = Column(Float)
    confidence = Column(Float)
    risk_score = Column(Float)
    weather_risk = Column(Float)
    congestion_risk = Column(Float)
    geopolitical_risk = Column(Float)
    factors_json = Column(Text)  # JSON encoded risk factors
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    valid_until = Column(DateTime)
    
    # Relationships
    route = relationship("Route", back_populates="predictions")
