"""
Synthetic Data Generator for Historical Maritime Data
Generates realistic transit history for Taiwan → US West Coast routes
"""

import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import os


class SyntheticDataGenerator:
    """Generates realistic maritime transit data"""
    
    # Taiwan ports
    TAIWAN_PORTS = [
        {"code": "TWKHH", "name": "Kaohsiung", "lat": 22.6163, "lng": 120.3133},
        {"code": "TWTPE", "name": "Taipei (Keelung)", "lat": 25.1276, "lng": 121.7392},
        {"code": "TWTXG", "name": "Taichung", "lat": 24.2693, "lng": 120.5145},
    ]
    
    # US West Coast ports
    US_PORTS = [
        {"code": "USLAX", "name": "Los Angeles", "lat": 33.7406, "lng": -118.2600},
        {"code": "USLGB", "name": "Long Beach", "lat": 33.7701, "lng": -118.1937},
        {"code": "USOAK", "name": "Oakland", "lat": 37.7955, "lng": -122.2789},
        {"code": "USSEA", "name": "Seattle", "lat": 47.5802, "lng": -122.3353},
    ]
    
    # Carriers operating on these routes
    CARRIERS = [
        "Evergreen Marine", "Yang Ming", "Wan Hai Lines",
        "COSCO Shipping", "Maersk Line", "MSC",
        "ONE (Ocean Network Express)", "HMM"
    ]
    
    # Route-specific typical transit times (days)
    ROUTE_TRANSIT_TIMES = {
        ("TWKHH", "USLAX"): 14,
        ("TWKHH", "USLGB"): 14,
        ("TWKHH", "USOAK"): 13,
        ("TWKHH", "USSEA"): 12,
        ("TWTPE", "USLAX"): 15,
        ("TWTPE", "USLGB"): 15,
        ("TWTXG", "USLAX"): 14,
    }
    
    # Seasonal delay factors (higher in Q4, typhoon season)
    SEASONAL_FACTORS = {
        1: 1.0,   # January - post-holiday slowdown
        2: 0.9,   # February - Chinese New Year
        3: 1.0,
        4: 1.0,
        5: 1.1,
        6: 1.2,   # Starting typhoon season
        7: 1.3,   # Peak typhoon
        8: 1.4,   # Peak typhoon
        9: 1.5,   # Peak typhoon + pre-holiday rush
        10: 1.6,  # Holiday rush
        11: 1.5,  # Holiday rush
        12: 1.3,  # Holiday peak
    }
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
    
    def generate_transit(
        self,
        origin: Dict,
        destination: Dict,
        departure_date: datetime,
    ) -> Dict:
        """Generate a single transit record with realistic delays"""
        
        route_key = (origin["code"], destination["code"])
        base_days = self.ROUTE_TRANSIT_TIMES.get(route_key, 14)
        
        # Get seasonal factor
        month = departure_date.month
        seasonal = self.SEASONAL_FACTORS.get(month, 1.0)
        
        # Generate delay using lognormal distribution (most are on-time, few very late)
        # Mean delay of ~0.5 days, but with occasional long delays
        delay_factor = np.random.lognormal(mean=-0.5, sigma=0.8)
        delay_days = max(0, delay_factor * seasonal - 1)  # Subtract 1 to center around 0
        
        # Cap extreme delays
        delay_days = min(delay_days, 15)
        
        # Actual transit time
        actual_days = base_days + delay_days
        
        # Calculate dates
        scheduled_arrival = departure_date + timedelta(days=base_days)
        actual_arrival = departure_date + timedelta(days=actual_days)
        
        return {
            "origin_port": origin["code"],
            "origin_name": origin["name"],
            "destination_port": destination["code"],
            "destination_name": destination["name"],
            "carrier": random.choice(self.CARRIERS),
            "vessel_name": self._generate_vessel_name(),
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "scheduled_arrival": scheduled_arrival.strftime("%Y-%m-%d"),
            "actual_arrival": actual_arrival.strftime("%Y-%m-%d"),
            "scheduled_days": base_days,
            "actual_days": round(actual_days, 1),
            "delay_days": round(delay_days, 1),
            "year": departure_date.year,
            "month": departure_date.month,
            "on_time": delay_days < 1,  # Within 1 day is "on time"
        }
    
    def generate_port_congestion(
        self,
        port: Dict,
        date: datetime,
    ) -> Dict:
        """Generate port congestion record for a specific date"""
        
        month = date.month
        seasonal = self.SEASONAL_FACTORS.get(month, 1.0)
        
        # Base congestion varies by port
        base_congestion = {
            "USLAX": 0.75,
            "USLGB": 0.70,
            "USOAK": 0.60,
            "USSEA": 0.55,
        }.get(port["code"], 0.65)
        
        # Add seasonal and random variation
        utilization = base_congestion * seasonal * random.uniform(0.85, 1.15)
        utilization = min(utilization, 0.98)  # Cap at 98%
        
        wait_hours = (utilization - 0.5) * 100 * random.uniform(0.8, 1.2)
        wait_hours = max(0, wait_hours)
        
        vessels_waiting = int(utilization * 40 * random.uniform(0.8, 1.2))
        
        return {
            "port_code": port["code"],
            "port_name": port["name"],
            "date": date.strftime("%Y-%m-%d"),
            "berth_utilization": round(utilization, 3),
            "wait_time_hours": round(wait_hours, 1),
            "vessels_waiting": vessels_waiting,
            "congestion_level": "high" if utilization > 0.85 else "medium" if utilization > 0.7 else "low",
        }
    
    def generate_dataset(
        self,
        start_date: datetime,
        end_date: datetime,
        transits_per_week: int = 15,
    ) -> Dict:
        """Generate complete historical dataset"""
        
        transits = []
        congestion_records = []
        
        current_date = start_date
        transit_id = 1
        
        while current_date < end_date:
            # Generate transits for this week
            for _ in range(transits_per_week):
                origin = random.choice(self.TAIWAN_PORTS)
                destination = random.choice(self.US_PORTS)
                
                # Random day within the week
                departure = current_date + timedelta(days=random.randint(0, 6))
                
                transit = self.generate_transit(origin, destination, departure)
                transit["id"] = transit_id
                transits.append(transit)
                transit_id += 1
            
            # Generate daily congestion for US ports
            for day_offset in range(7):
                day = current_date + timedelta(days=day_offset)
                for port in self.US_PORTS:
                    congestion = self.generate_port_congestion(port, day)
                    congestion_records.append(congestion)
            
            current_date += timedelta(weeks=1)
        
        # Calculate statistics
        total_transits = len(transits)
        delays = [t["delay_days"] for t in transits]
        on_time_rate = sum(1 for t in transits if t["on_time"]) / total_transits
        
        return {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                "total_transits": total_transits,
                "total_congestion_records": len(congestion_records),
            },
            "statistics": {
                "avg_delay_days": round(np.mean(delays), 2),
                "median_delay_days": round(np.median(delays), 2),
                "max_delay_days": round(max(delays), 2),
                "on_time_rate": round(on_time_rate, 3),
                "delay_std": round(np.std(delays), 2),
            },
            "transits": transits,
            "port_congestion": congestion_records,
        }
    
    def _generate_vessel_name(self) -> str:
        """Generate realistic vessel names"""
        prefixes = ["Ever", "Yang Ming", "Wan Hai", "COSCO", "Maersk", "MSC", "ONE"]
        suffixes = [
            "Fortune", "Glory", "Triumph", "Champion", "Leader",
            "Excellence", "Pioneer", "Progress", "Success", "Unity",
            "Ace", "Star", "Crown", "Pearl", "Diamond"
        ]
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"
    
    def save_to_json(self, data: Dict, filepath: str):
        """Save generated data to JSON file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {filepath}")
    
    def save_to_csv(self, data: Dict, output_dir: str):
        """Save generated data to CSV files"""
        import csv
        os.makedirs(output_dir, exist_ok=True)
        
        # Save transits
        transits_file = os.path.join(output_dir, "historical_transits.csv")
        with open(transits_file, 'w', newline='') as f:
            if data["transits"]:
                writer = csv.DictWriter(f, fieldnames=data["transits"][0].keys())
                writer.writeheader()
                writer.writerows(data["transits"])
        print(f"Saved {transits_file}")
        
        # Save congestion
        congestion_file = os.path.join(output_dir, "port_congestion_history.csv")
        with open(congestion_file, 'w', newline='') as f:
            if data["port_congestion"]:
                writer = csv.DictWriter(f, fieldnames=data["port_congestion"][0].keys())
                writer.writeheader()
                writer.writerows(data["port_congestion"])
        print(f"Saved {congestion_file}")


def generate_sample_data():
    """Generate 3 years of sample historical data"""
    generator = SyntheticDataGenerator(seed=42)
    
    # Generate 3 years of data (2022-2024)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2025, 1, 1)
    
    print("Generating 3 years of historical data...")
    data = generator.generate_dataset(
        start_date=start_date,
        end_date=end_date,
        transits_per_week=20,  # ~20 transits per week
    )
    
    print(f"\nGenerated:")
    print(f"  - {data['metadata']['total_transits']} transit records")
    print(f"  - {data['metadata']['total_congestion_records']} congestion records")
    print(f"\nStatistics:")
    print(f"  - Avg delay: {data['statistics']['avg_delay_days']} days")
    print(f"  - On-time rate: {data['statistics']['on_time_rate']*100:.1f}%")
    
    # Save data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    
    generator.save_to_json(data, os.path.join(data_dir, "sample", "synthetic_data.json"))
    generator.save_to_csv(data, os.path.join(data_dir, "processed"))
    
    return data


if __name__ == "__main__":
    generate_sample_data()
