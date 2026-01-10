"""
Database initialization script
Creates all tables in Supabase PostgreSQL
"""

import sys
sys.path.insert(0, 'backend')

from app.core.database import engine, Base
from app.models.models import (
    Vessel, VesselPosition, Port, Route, 
    RouteTransit, WeatherEvent, PortCongestion,
    GeopoliticalEvent, RiskPrediction
)

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

def seed_initial_data():
    """Seed initial route data"""
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    
    # Check if routes already exist
    existing = db.query(Route).first()
    if existing:
        print("ℹ️  Routes already exist, skipping seed")
        db.close()
        return
    
    # Taiwan ports
    ports = [
        Port(name="Kaohsiung", code="TWKHH", country="Taiwan", lat=22.6155, lng=120.2863),
        Port(name="Keelung", code="TWKEL", country="Taiwan", lat=25.1276, lng=121.7392),
        Port(name="Taichung", code="TWTXG", country="Taiwan", lat=24.1477, lng=120.6827),
        # US West Coast ports
        Port(name="Los Angeles", code="USLAX", country="USA", lat=33.7405, lng=-118.2608),
        Port(name="Long Beach", code="USLGB", country="USA", lat=33.7540, lng=-118.2162),
        Port(name="Oakland", code="USOAK", country="USA", lat=37.7956, lng=-122.2789),
        Port(name="Seattle", code="USSEA", country="USA", lat=47.5799, lng=-122.3432),
        Port(name="San Francisco", code="USSFO", country="USA", lat=37.7749, lng=-122.4194),
    ]
    db.add_all(ports)
    db.commit()
    print(f"✅ Added {len(ports)} ports")
    
    # Routes
    routes = [
        Route(origin_name="Kaohsiung, Taiwan", destination_name="Los Angeles, CA", distance_nm=6500, avg_transit_days=16),
        Route(origin_name="Kaohsiung, Taiwan", destination_name="Long Beach, CA", distance_nm=6500, avg_transit_days=16),
        Route(origin_name="Keelung, Taiwan", destination_name="Oakland, CA", distance_nm=6200, avg_transit_days=15),
        Route(origin_name="Taichung, Taiwan", destination_name="Seattle, WA", distance_nm=5800, avg_transit_days=14),
        Route(origin_name="Kaohsiung, Taiwan", destination_name="San Francisco, CA", distance_nm=6400, avg_transit_days=16),
    ]
    db.add_all(routes)
    db.commit()
    print(f"✅ Added {len(routes)} routes")
    
    # Sample vessels
    vessels = [
        Vessel(name="Ever Ace", imo="9893890", carrier="Evergreen", capacity_teu=23992, status="underway"),
        Vessel(name="Ever Given", imo="9811000", carrier="Evergreen", capacity_teu=20124, status="underway"),
        Vessel(name="YM Wish", imo="9708451", carrier="Yang Ming", capacity_teu=14220, status="at_port"),
        Vessel(name="YM Wind", imo="9708463", carrier="Yang Ming", capacity_teu=14220, status="underway"),
        Vessel(name="Maersk Elba", imo="9458089", carrier="Maersk", capacity_teu=13092, status="underway"),
    ]
    db.add_all(vessels)
    db.commit()
    print(f"✅ Added {len(vessels)} sample vessels")
    
    db.close()

if __name__ == "__main__":
    create_tables()
    seed_initial_data()
    print("\n🚀 Database initialization complete!")
