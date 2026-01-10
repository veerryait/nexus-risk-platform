#!/usr/bin/env python3
"""
Port Status Collector - Web form for manual port congestion entry
Creates simple CLI for entering weekly port data
Stores to port_status table in Supabase
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Configuration
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY")

# 4 key ports to track
PORTS = [
    {"code": "USLAX", "name": "Port of Los Angeles"},
    {"code": "USLGB", "name": "Port of Long Beach"},
    {"code": "CNSHA", "name": "Port of Shanghai"},
    {"code": "TWKHH", "name": "Port of Kaohsiung"},
]


def get_congestion_level(score: float) -> str:
    """Convert score to level"""
    if score < 0.25: return "low"
    if score < 0.5: return "medium"
    if score < 0.75: return "high"
    return "severe"


def enter_port_data():
    """Interactive CLI for entering port data"""
    print("=" * 50)
    print("📦 Port Status Entry Tool")
    print("=" * 50)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    recorded_at = datetime.now(timezone.utc).isoformat()
    
    print("\nPorts to update:")
    for i, port in enumerate(PORTS, 1):
        print(f"  {i}. {port['name']} ({port['code']})")
    
    print("\n(Enter 'all' for all ports, or port number, or 'q' to quit)")
    
    while True:
        choice = input("\nSelect port: ").strip().lower()
        
        if choice == 'q':
            break
        
        if choice == 'all':
            ports_to_update = PORTS
        elif choice.isdigit() and 1 <= int(choice) <= len(PORTS):
            ports_to_update = [PORTS[int(choice) - 1]]
        else:
            print("Invalid choice. Try again.")
            continue
        
        for port in ports_to_update:
            print(f"\n--- {port['name']} ({port['code']}) ---")
            
            try:
                vessels_waiting = int(input("  Vessels waiting: ") or "0")
                avg_wait_days = float(input("  Avg wait (days): ") or "0")
                berth_util = float(input("  Berth utilization (0-1): ") or "0.5")
                
                congestion_score = (vessels_waiting / 50) * 0.4 + avg_wait_days / 10 * 0.4 + berth_util * 0.2
                congestion_score = min(congestion_score, 1.0)
                
                record = {
                    "recorded_at": recorded_at,
                    "port_code": port["code"],
                    "port_name": port["name"],
                    "vessels_waiting": vessels_waiting,
                    "avg_wait_days": avg_wait_days,
                    "berth_utilization": berth_util,
                    "congestion_level": get_congestion_level(congestion_score),
                    "congestion_score": congestion_score,
                    "data_source": "manual_entry",
                }
                
                supabase.table("port_status").insert(record).execute()
                print(f"  ✅ Saved: {port['code']} - {get_congestion_level(congestion_score)} congestion")
                
            except ValueError:
                print("  ❌ Invalid input, skipping...")
            except Exception as e:
                print(f"  ❌ Error: {e}")
        
        if choice != 'all':
            continue_choice = input("\nUpdate another port? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
    
    print("\n✅ Port status update complete!")


def quick_update(port_code: str, vessels_waiting: int, avg_wait_days: float, berth_util: float):
    """Quick programmatic update for a port"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    congestion_score = (vessels_waiting / 50) * 0.4 + avg_wait_days / 10 * 0.4 + berth_util * 0.2
    congestion_score = min(congestion_score, 1.0)
    
    port_name = next((p["name"] for p in PORTS if p["code"] == port_code), port_code)
    
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "port_code": port_code,
        "port_name": port_name,
        "vessels_waiting": vessels_waiting,
        "avg_wait_days": avg_wait_days,
        "berth_utilization": berth_util,
        "congestion_level": get_congestion_level(congestion_score),
        "congestion_score": congestion_score,
        "data_source": "quick_update",
    }
    
    supabase.table("port_status").insert(record).execute()
    print(f"✅ {port_code}: {get_congestion_level(congestion_score)} congestion (score: {congestion_score:.2f})")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode: python port_collector.py --quick USLAX 10 2.5 0.7
        if len(sys.argv) == 6:
            quick_update(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
        else:
            print("Usage: python port_collector.py --quick PORT_CODE VESSELS WAIT_DAYS BERTH_UTIL")
    else:
        enter_port_data()
