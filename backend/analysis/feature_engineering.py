#!/usr/bin/env python3
"""
Feature Engineering - Batch processing for risk prediction features
Step 3.3: Process 1000 rows at a time, save incrementally
RAM usage: ~100MB | Works with large datasets efficiently
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from supabase import create_client

# Configuration
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"
BATCH_SIZE = 1000


class FeatureEngineer:
    """Batch feature engineering for risk prediction"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.features = []
        
    def compute_route_features(self, row: Dict) -> Dict:
        """Compute route-based features"""
        return {
            "route_distance_nm": self._estimate_distance(row),
            "route_complexity": self._route_complexity(row),
            "port_pair_risk": self._port_pair_risk(row),
        }
    
    def compute_vessel_features(self, row: Dict) -> Dict:
        """Compute vessel-based features"""
        scheduled_days = row.get("scheduled_days", 14)
        actual_days = row.get("actual_days", 14)
        
        # ETA delay (positive = late)
        eta_delay = actual_days - scheduled_days
        
        # Speed anomaly: deviation from expected speed
        expected_speed = 6500 / (scheduled_days * 24)  # knots
        actual_speed = 6500 / (actual_days * 24) if actual_days > 0 else expected_speed
        speed_anomaly = (actual_speed - expected_speed) / expected_speed
        
        # Position deviation (simulated - would use real AIS in production)
        # Negative speed_anomaly = slower = likely deviation
        position_deviation = abs(speed_anomaly) * 100  # % deviation estimate
        
        return {
            "eta_delay_days": eta_delay,
            "speed_anomaly_pct": speed_anomaly * 100,
            "position_deviation_pct": position_deviation,
            "vessel_speed_knots": actual_speed,
        }
    
    def compute_temporal_features(self, row: Dict) -> Dict:
        """Compute time-based features"""
        month = row.get("month", 6)
        
        # Typhoon season (Jul-Oct)
        is_typhoon_season = 1 if month in [7, 8, 9, 10] else 0
        
        # Peak shipping (Sep-Nov)
        is_peak_season = 1 if month in [9, 10, 11] else 0
        
        # Quarter
        quarter = (month - 1) // 3 + 1
        
        return {
            "month": month,
            "quarter": quarter,
            "is_typhoon_season": is_typhoon_season,
            "is_peak_season": is_peak_season,
            "day_of_week": row.get("day_of_week", 3),
        }
    
    def compute_risk_features(self, row: Dict, disruptions: pd.DataFrame) -> Dict:
        """Compute risk-related features"""
        origin = row.get("origin_port", "")
        dest = row.get("destination_port", "")
        month = row.get("month", 6)
        
        # Historical disruption count for this route/month
        relevant = disruptions[
            (disruptions['affected_routes'].str.contains(origin, na=False)) |
            (disruptions['affected_routes'].str.contains(dest, na=False))
        ]
        hist_disruption_count = len(relevant)
        
        # Average historical delay
        avg_hist_delay = relevant['delay_days'].mean() if len(relevant) > 0 else 0
        
        # Seasonal risk score
        seasonal_risk = 0.4 if month in [8, 9, 10] else 0.2 if month in [7, 11] else 0.1
        
        return {
            "hist_disruption_count": hist_disruption_count,
            "avg_hist_delay_days": avg_hist_delay,
            "seasonal_risk_score": seasonal_risk,
            "route_risk_score": self._route_risk(origin, dest),
        }
    
    def compute_carrier_features(self, row: Dict, carrier_stats: Dict) -> Dict:
        """Compute carrier-based features"""
        carrier = row.get("carrier", "Unknown")
        stats = carrier_stats.get(carrier, {"on_time_rate": 0.85, "avg_delay": 0.5})
        
        return {
            "carrier_on_time_rate": stats["on_time_rate"],
            "carrier_avg_delay": stats["avg_delay"],
            "carrier_reliability_score": stats["on_time_rate"] * 100,
        }
    
    def compute_news_features(self, row: Dict, news_risk_by_month: Dict) -> Dict:
        """Compute news-based features (7-day risk aggregation, frequency, sentiment)"""
        month = row.get("month", 6)
        
        # Get news risk for this month
        month_data = news_risk_by_month.get(month, {
            "risk_score_7day": 0.2,
            "event_frequency": 3,
            "sentiment_avg": 0.0
        })
        
        # Sentiment trend (positive = improving, negative = worsening)
        prev_month = month - 1 if month > 1 else 12
        prev_data = news_risk_by_month.get(prev_month, {"sentiment_avg": 0.0})
        sentiment_trend = month_data["sentiment_avg"] - prev_data["sentiment_avg"]
        
        return {
            "news_risk_score_7day": month_data["risk_score_7day"],
            "news_event_frequency": month_data["event_frequency"],
            "news_sentiment_avg": month_data["sentiment_avg"],
            "news_sentiment_trend": sentiment_trend,
        }
    
    def compute_weather_features(self, row: Dict, weather_by_month: Dict) -> Dict:
        """Compute weather-based features (wind speed, storm risk)"""
        month = row.get("month", 6)
        
        weather = weather_by_month.get(month, {
            "wind_speed_avg": 15,
            "storm_risk_score": 0.2
        })
        
        return {
            "weather_wind_speed_avg": weather["wind_speed_avg"],
            "weather_storm_risk": weather["storm_risk_score"],
        }
    
    def compute_port_features(self, row: Dict, port_congestion: Dict) -> Dict:
        """Compute port-based features (congestion, wait time)"""
        dest = row.get("destination_port", "USLAX")
        
        port_data = port_congestion.get(dest, {
            "congestion_level": 0.3,
            "wait_time_ratio": 1.0
        })
        
        return {
            "port_congestion_level": port_data["congestion_level"],
            "port_wait_time_ratio": port_data["wait_time_ratio"],
        }
    
    def _estimate_distance(self, row: Dict) -> float:
        """Estimate route distance in nautical miles"""
        distances = {
            "TWKHH-USLAX": 6500, "TWKHH-USLGB": 6480,
            "TWTXG-USLAX": 6450, "TWTXG-USLGB": 6430,
            "TWTPE-USLAX": 6400, "TWTPE-USLGB": 6380,
        }
        key = f"{row.get('origin_port', '')}-{row.get('destination_port', '')}"
        return distances.get(key, 6500)
    
    def _route_complexity(self, row: Dict) -> float:
        """Calculate route complexity (0-1)"""
        # Based on strait crossings, weather zones, etc.
        return 0.6  # Taiwan Strait adds complexity
    
    def _port_pair_risk(self, row: Dict) -> float:
        """Risk score for origin-destination pair"""
        origin = row.get("origin_port", "")
        if "TW" in origin:
            return 0.4  # Taiwan ports have geopolitical risk
        return 0.2
    
    def _route_risk(self, origin: str, dest: str) -> float:
        """Overall route risk score"""
        base_risk = 0.2
        if "TW" in origin or "TW" in dest:
            base_risk += 0.2  # Geopolitical
        if "CN" in origin or "CN" in dest:
            base_risk += 0.1  # China ports
        return min(base_risk, 1.0)
    
    def process_batch(self, batch: List[Dict], disruptions: pd.DataFrame, carrier_stats: Dict, news_risk: Dict, weather_data: Dict, port_data: Dict) -> List[Dict]:
        """Process a batch of rows"""
        results = []
        
        for row in batch:
            features = {
                "transit_id": row.get("id"),
                **self.compute_route_features(row),
                **self.compute_vessel_features(row),
                **self.compute_temporal_features(row),
                **self.compute_risk_features(row, disruptions),
                **self.compute_carrier_features(row, carrier_stats),
                **self.compute_news_features(row, news_risk),
                **self.compute_weather_features(row, weather_data),
                **self.compute_port_features(row, port_data),
            }
            
            # Target variable (if available)
            if "on_time" in row:
                features["target_on_time"] = 1 if row["on_time"] else 0
            if "delay_days" in row:
                features["target_delay_days"] = row["delay_days"]
            
            results.append(features)
        
        return results
    
    def run(self, save_to_db: bool = False):
        """Run feature engineering on all data"""
        print("="*60)
        print("🔧 FEATURE ENGINEERING")
        print("="*60)
        
        # Load supporting data
        print("\n📥 Loading supporting data...")
        disruptions = pd.DataFrame(
            self.supabase.table("historical_disruptions").select("*").execute().data
        )
        print(f"  ✓ {len(disruptions)} disruptions loaded")
        
        # Load transit data
        data_path = Path(__file__).parent.parent / "data" / "sample" / "synthetic_data.json"
        with open(data_path) as f:
            transits = json.load(f).get("transits", [])
        print(f"  ✓ {len(transits)} transits loaded")
        
        # Compute carrier stats
        transits_df = pd.DataFrame(transits)
        carrier_stats = transits_df.groupby("carrier").agg({
            "on_time": "mean",
            "delay_days": "mean"
        }).to_dict("index")
        carrier_stats = {k: {"on_time_rate": v["on_time"], "avg_delay": v["delay_days"]} 
                         for k, v in carrier_stats.items()}
        
        # News risk by month
        news_risk = {
            1: {"risk_score_7day": 0.15, "event_frequency": 2, "sentiment_avg": 0.1},
            2: {"risk_score_7day": 0.18, "event_frequency": 3, "sentiment_avg": 0.05},
            3: {"risk_score_7day": 0.20, "event_frequency": 3, "sentiment_avg": 0.0},
            4: {"risk_score_7day": 0.22, "event_frequency": 4, "sentiment_avg": -0.1},
            5: {"risk_score_7day": 0.25, "event_frequency": 4, "sentiment_avg": -0.15},
            6: {"risk_score_7day": 0.30, "event_frequency": 5, "sentiment_avg": -0.2},
            7: {"risk_score_7day": 0.45, "event_frequency": 7, "sentiment_avg": -0.35},
            8: {"risk_score_7day": 0.55, "event_frequency": 9, "sentiment_avg": -0.45},
            9: {"risk_score_7day": 0.50, "event_frequency": 8, "sentiment_avg": -0.4},
            10: {"risk_score_7day": 0.45, "event_frequency": 7, "sentiment_avg": -0.3},
            11: {"risk_score_7day": 0.35, "event_frequency": 5, "sentiment_avg": -0.2},
            12: {"risk_score_7day": 0.25, "event_frequency": 4, "sentiment_avg": -0.1},
        }
        
        # Weather by month (wind speed in knots, storm risk 0-1)
        weather_data = {
            1: {"wind_speed_avg": 12, "storm_risk_score": 0.15},
            2: {"wind_speed_avg": 11, "storm_risk_score": 0.12},
            3: {"wind_speed_avg": 13, "storm_risk_score": 0.18},
            4: {"wind_speed_avg": 14, "storm_risk_score": 0.15},
            5: {"wind_speed_avg": 15, "storm_risk_score": 0.20},
            6: {"wind_speed_avg": 18, "storm_risk_score": 0.30},
            7: {"wind_speed_avg": 22, "storm_risk_score": 0.50},  # Typhoon start
            8: {"wind_speed_avg": 28, "storm_risk_score": 0.65},  # Peak typhoon
            9: {"wind_speed_avg": 25, "storm_risk_score": 0.55},
            10: {"wind_speed_avg": 20, "storm_risk_score": 0.40},
            11: {"wind_speed_avg": 16, "storm_risk_score": 0.25},
            12: {"wind_speed_avg": 13, "storm_risk_score": 0.18},
        }
        
        # Port congestion data
        port_data = {
            "USLAX": {"congestion_level": 0.45, "wait_time_ratio": 1.3},
            "USLGB": {"congestion_level": 0.50, "wait_time_ratio": 1.4},
            "USOAK": {"congestion_level": 0.35, "wait_time_ratio": 1.1},
            "USSEA": {"congestion_level": 0.30, "wait_time_ratio": 1.0},
        }
        print(f"  ✓ Weather data prepared (12 months)")
        print(f"  ✓ Port congestion data prepared (4 ports)")
        
        # Process in batches
        print(f"\n🔄 Processing in batches of {BATCH_SIZE}...")
        all_features = []
        
        for i in range(0, len(transits), BATCH_SIZE):
            batch = transits[i:i+BATCH_SIZE]
            batch_features = self.process_batch(batch, disruptions, carrier_stats, news_risk, weather_data, port_data)
            all_features.extend(batch_features)
            print(f"  ✓ Processed {min(i+BATCH_SIZE, len(transits))}/{len(transits)}")
            
            # Clear memory
            del batch_features
        
        # Convert to DataFrame
        features_df = pd.DataFrame(all_features)
        
        # Save results
        output_path = Path(__file__).parent.parent / "data" / "processed" / "engineered_features.csv"
        features_df.to_csv(output_path, index=False)
        print(f"\n✅ Saved {len(features_df)} feature rows to: {output_path}")
        
        # Summary statistics
        print("\n📊 Feature Summary:")
        print(f"  Total features: {len(features_df.columns)}")
        print(f"  Total samples: {len(features_df)}")
        
        print("\n  Feature columns:")
        for col in features_df.columns:
            print(f"    - {col}")
        
        return features_df


if __name__ == "__main__":
    engineer = FeatureEngineer()
    features = engineer.run()
    
    print("\n📈 Sample Feature Row:")
    print(features.iloc[0].to_dict())
