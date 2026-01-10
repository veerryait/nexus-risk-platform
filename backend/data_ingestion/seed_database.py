"""
Database Seeding Script
Seeds the database with ports, routes, and historical transit data
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.models import Port, Route, Vessel, RouteTransit, PortCongestion


# Port definitions
PORTS = [
    # Taiwan ports
    {"code": "TWKHH", "name": "Kaohsiung", "country": "Taiwan", "lat": 22.6163, "lng": 120.3133, "timezone": "Asia/Taipei"},
    {"code": "TWTPE", "name": "Taipei (Keelung)", "country": "Taiwan", "lat": 25.1276, "lng": 121.7392, "timezone": "Asia/Taipei"},
    {"code": "TWTXG", "name": "Taichung", "country": "Taiwan", "lat": 24.2693, "lng": 120.5145, "timezone": "Asia/Taipei"},
    # US West Coast ports
    {"code": "USLAX", "name": "Los Angeles", "country": "USA", "lat": 33.7406, "lng": -118.2600, "timezone": "America/Los_Angeles"},
    {"code": "USLGB", "name": "Long Beach", "country": "USA", "lat": 33.7701, "lng": -118.1937, "timezone": "America/Los_Angeles"},
    {"code": "USOAK", "name": "Oakland", "country": "USA", "lat": 37.7955, "lng": -122.2789, "timezone": "America/Los_Angeles"},
    {"code": "USSEA", "name": "Seattle", "country": "USA", "lat": 47.5802, "lng": -122.3353, "timezone": "America/Los_Angeles"},
]

# Route definitions (Taiwan → US)
ROUTES = [
    {"origin": "TWKHH", "destination": "USLAX", "distance_nm": 6150, "avg_days": 14},
    {"origin": "TWKHH", "destination": "USLGB", "distance_nm": 6150, "avg_days": 14},
    {"origin": "TWKHH", "destination": "USOAK", "distance_nm": 5950, "avg_days": 13},
    {"origin": "TWKHH", "destination": "USSEA", "distance_nm": 5200, "avg_days": 12},
    {"origin": "TWTPE", "destination": "USLAX", "distance_nm": 6300, "avg_days": 15},
    {"origin": "TWTPE", "destination": "USLGB", "distance_nm": 6300, "avg_days": 15},
    {"origin": "TWTXG", "destination": "USLAX", "distance_nm": 6100, "avg_days": 14},
]

# Sample vessels
VESSELS = [
    {"name": "Ever Ace", "imo": "9893890", "carrier": "Evergreen Marine", "capacity_teu": 23992},
    {"name": "Ever Given", "imo": "9811000", "carrier": "Evergreen Marine", "capacity_teu": 20124},
    {"name": "Ever Glory", "imo": "9893802", "carrier": "Evergreen Marine", "capacity_teu": 23992},
    {"name": "YM Triumph", "imo": "9871927", "carrier": "Yang Ming", "capacity_teu": 12000},
    {"name": "YM Wellness", "imo": "9871915", "carrier": "Yang Ming", "capacity_teu": 12000},
    {"name": "Wan Hai 501", "imo": "9929305", "carrier": "Wan Hai Lines", "capacity_teu": 3055},
    {"name": "COSCO Pride", "imo": "9783538", "carrier": "COSCO Shipping", "capacity_teu": 21237},
    {"name": "MSC Oscar", "imo": "9703291", "carrier": "MSC", "capacity_teu": 19224},
]


def seed_ports(db: Session):
    """Seed ports table"""
    print("Seeding ports...")
    for port_data in PORTS:
        existing = db.query(Port).filter(Port.code == port_data["code"]).first()
        if not existing:
            port = Port(
                name=port_data["name"],
                code=port_data["code"],
                country=port_data["country"],
                lat=port_data["lat"],
                lng=port_data["lng"],
                timezone=port_data["timezone"],
            )
            db.add(port)
            print(f"  Added port: {port_data['name']} ({port_data['code']})")
        else:
            print(f"  Port exists: {port_data['name']}")
    db.commit()


def seed_routes(db: Session):
    """Seed routes table"""
    print("\nSeeding routes...")
    for route_data in ROUTES:
        origin = db.query(Port).filter(Port.code == route_data["origin"]).first()
        dest = db.query(Port).filter(Port.code == route_data["destination"]).first()
        
        if origin and dest:
            existing = db.query(Route).filter(
                Route.origin_port_id == origin.id,
                Route.destination_port_id == dest.id
            ).first()
            
            if not existing:
                route = Route(
                    origin_port_id=origin.id,
                    destination_port_id=dest.id,
                    origin_name=origin.name,
                    destination_name=dest.name,
                    distance_nm=route_data["distance_nm"],
                    avg_transit_days=route_data["avg_days"],
                    is_active=True,
                )
                db.add(route)
                print(f"  Added route: {origin.name} → {dest.name}")
            else:
                print(f"  Route exists: {origin.name} → {dest.name}")
    db.commit()


def seed_vessels(db: Session):
    """Seed vessels table"""
    print("\nSeeding vessels...")
    for vessel_data in VESSELS:
        existing = db.query(Vessel).filter(Vessel.imo == vessel_data["imo"]).first()
        if not existing:
            vessel = Vessel(
                name=vessel_data["name"],
                imo=vessel_data["imo"],
                carrier=vessel_data["carrier"],
                capacity_teu=vessel_data["capacity_teu"],
                status="underway",
            )
            db.add(vessel)
            print(f"  Added vessel: {vessel_data['name']}")
        else:
            print(f"  Vessel exists: {vessel_data['name']}")
    db.commit()


def seed_historical_transits(db: Session, json_path: str = None):
    """Seed historical transit data from synthetic data JSON"""
    print("\nSeeding historical transits...")
    
    if json_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, "data", "sample", "synthetic_data.json")
    
    if not os.path.exists(json_path):
        print(f"  No synthetic data found at {json_path}")
        print("  Run: python data_ingestion/synthetic_data.py first")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    transits = data.get("transits", [])
    print(f"  Found {len(transits)} transit records")
    
    # Get all vessels and routes for mapping
    vessels = {v.name: v for v in db.query(Vessel).all()}
    routes_by_ports = {}
    for route in db.query(Route).all():
        origin_port = db.query(Port).filter(Port.id == route.origin_port_id).first()
        dest_port = db.query(Port).filter(Port.id == route.destination_port_id).first()
        if origin_port and dest_port:
            routes_by_ports[(origin_port.code, dest_port.code)] = route
    
    added = 0
    for transit in transits[:500]:  # Limit to 500 for initial seed
        route_key = (transit["origin_port"], transit["destination_port"])
        route = routes_by_ports.get(route_key)
        
        if route:
            # Try to find matching vessel or use first one
            vessel = vessels.get(transit.get("vessel_name"))
            if not vessel and vessels:
                vessel = list(vessels.values())[0]
            
            if vessel:
                departure = datetime.strptime(transit["departure_date"], "%Y-%m-%d")
                arrival = datetime.strptime(transit["actual_arrival"], "%Y-%m-%d")
                eta = datetime.strptime(transit["scheduled_arrival"], "%Y-%m-%d")
                
                route_transit = RouteTransit(
                    vessel_id=vessel.id,
                    route_id=route.id,
                    departure_time=departure,
                    eta=eta,
                    actual_arrival=arrival,
                    status="arrived",
                    delay_hours=int(transit["delay_days"] * 24),
                )
                db.add(route_transit)
                added += 1
    
    db.commit()
    print(f"  Added {added} historical transit records")


def seed_port_congestion(db: Session, json_path: str = None):
    """Seed port congestion history"""
    print("\nSeeding port congestion history...")
    
    if json_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_path = os.path.join(base_dir, "data", "sample", "synthetic_data.json")
    
    if not os.path.exists(json_path):
        print(f"  No synthetic data found at {json_path}")
        return
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    congestion_records = data.get("port_congestion", [])
    print(f"  Found {len(congestion_records)} congestion records")
    
    # Get ports for mapping
    ports = {p.code: p for p in db.query(Port).all()}
    
    added = 0
    for record in congestion_records[:1000]:  # Limit to 1000 records
        port = ports.get(record["port_code"])
        if port:
            congestion = PortCongestion(
                port_id=port.id,
                wait_time_hours=record["wait_time_hours"],
                berth_utilization=record["berth_utilization"],
                vessels_waiting=record["vessels_waiting"],
                timestamp=datetime.strptime(record["date"], "%Y-%m-%d"),
            )
            db.add(congestion)
            added += 1
    
    db.commit()
    print(f"  Added {added} port congestion records")


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def seed_all():
    """Run all seed functions"""
    print("=" * 50)
    print("NEXUS RISK PLATFORM - DATABASE SEEDING")
    print("=" * 50)
    
    create_tables()
    
    db = SessionLocal()
    try:
        seed_ports(db)
        seed_routes(db)
        seed_vessels(db)
        seed_historical_transits(db)
        seed_port_congestion(db)
        
        print("\n" + "=" * 50)
        print("SEEDING COMPLETE!")
        print("=" * 50)
        
        # Print summary
        print(f"\nDatabase summary:")
        print(f"  Ports: {db.query(Port).count()}")
        print(f"  Routes: {db.query(Route).count()}")
        print(f"  Vessels: {db.query(Vessel).count()}")
        print(f"  Historical Transits: {db.query(RouteTransit).count()}")
        print(f"  Port Congestion Records: {db.query(PortCongestion).count()}")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
