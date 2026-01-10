"""
Historical Data Service
Provides analysis of historical shipping patterns for ML predictions
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class HistoricalService:
    """Service for analyzing historical maritime data"""
    
    def __init__(self):
        self._data = None
        self._load_data()
    
    def _load_data(self):
        """Load historical data from JSON file"""
        # Go up from app/services/ to backend/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        json_path = os.path.join(base_dir, "data", "sample", "synthetic_data.json")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                self._data = json.load(f)
            print(f"Loaded historical data from {json_path}")
        else:
            print(f"No historical data found at {json_path}")
            # Use empty defaults if no data
            self._data = {
                "transits": [],
                "port_congestion": [],
                "statistics": {},
            }
    
    async def get_route_statistics(self, origin_port: str = None, dest_port: str = None) -> Dict:
        """Get statistical summary for routes"""
        transits = self._data.get("transits", [])
        
        # Filter by route if specified
        if origin_port:
            transits = [t for t in transits if t["origin_port"] == origin_port]
        if dest_port:
            transits = [t for t in transits if t["destination_port"] == dest_port]
        
        if not transits:
            return {"error": "No data for specified route"}
        
        delays = [t["delay_days"] for t in transits]
        actual_days = [t["actual_days"] for t in transits]
        
        return {
            "total_transits": len(transits),
            "delay_statistics": {
                "mean_days": round(statistics.mean(delays), 2),
                "median_days": round(statistics.median(delays), 2),
                "std_dev": round(statistics.stdev(delays), 2) if len(delays) > 1 else 0,
                "min_days": round(min(delays), 2),
                "max_days": round(max(delays), 2),
                "percentile_95": round(sorted(delays)[int(len(delays) * 0.95)], 2),
            },
            "transit_time": {
                "mean_days": round(statistics.mean(actual_days), 2),
                "median_days": round(statistics.median(actual_days), 2),
            },
            "on_time_rate": round(sum(1 for t in transits if t["on_time"]) / len(transits), 3),
            "route_filter": {
                "origin": origin_port,
                "destination": dest_port,
            }
        }
    
    async def get_seasonal_patterns(self, route_origin: str = None) -> List[Dict]:
        """Get monthly delay patterns showing seasonality"""
        transits = self._data.get("transits", [])
        
        if route_origin:
            transits = [t for t in transits if t["origin_port"] == route_origin]
        
        # Group by month
        monthly_data = defaultdict(list)
        for transit in transits:
            month = transit["month"]
            monthly_data[month].append(transit["delay_days"])
        
        patterns = []
        for month in range(1, 13):
            delays = monthly_data.get(month, [0])
            avg_delay = statistics.mean(delays) if delays else 0
            on_time = sum(1 for d in delays if d < 1) / len(delays) if delays else 0
            
            # Determine risk level
            if avg_delay > 2:
                risk_level = "high"
            elif avg_delay > 1:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            patterns.append({
                "month": month,
                "month_name": datetime(2024, month, 1).strftime("%B"),
                "avg_delay_days": round(avg_delay, 2),
                "on_time_rate": round(on_time, 3),
                "transit_count": len(delays),
                "risk_level": risk_level,
            })
        
        return patterns
    
    async def get_delay_distribution(self) -> Dict:
        """Get delay distribution for histogram visualization"""
        transits = self._data.get("transits", [])
        delays = [t["delay_days"] for t in transits]
        
        if not delays:
            return {"error": "No delay data available"}
        
        # Create histogram bins
        bins = [0, 0.5, 1, 2, 3, 5, 7, 10, 15]
        histogram = []
        
        for i in range(len(bins) - 1):
            low, high = bins[i], bins[i + 1]
            count = sum(1 for d in delays if low <= d < high)
            histogram.append({
                "range": f"{low}-{high} days",
                "count": count,
                "percentage": round(count / len(delays) * 100, 1),
            })
        
        # 15+ days
        count_15plus = sum(1 for d in delays if d >= 15)
        histogram.append({
            "range": "15+ days",
            "count": count_15plus,
            "percentage": round(count_15plus / len(delays) * 100, 1),
        })
        
        return {
            "total_transits": len(delays),
            "histogram": histogram,
            "summary": {
                "on_time_pct": round(sum(1 for d in delays if d < 1) / len(delays) * 100, 1),
                "minor_delay_pct": round(sum(1 for d in delays if 1 <= d < 3) / len(delays) * 100, 1),
                "major_delay_pct": round(sum(1 for d in delays if d >= 3) / len(delays) * 100, 1),
            }
        }
    
    async def get_historical_baseline(self) -> Dict:
        """Get baseline metrics for risk calculations"""
        stats = self._data.get("statistics", {})
        transits = self._data.get("transits", [])
        
        if not transits:
            # Return sensible defaults
            return {
                "baseline_delay_days": 1.5,
                "delay_std_dev": 2.0,
                "on_time_rate": 0.7,
                "peak_season_factor": 1.5,
                "data_source": "defaults",
            }
        
        delays = [t["delay_days"] for t in transits]
        
        # Calculate peak season factor (Aug-Nov avg / rest of year avg)
        peak_delays = [t["delay_days"] for t in transits if t["month"] in [8, 9, 10, 11]]
        off_peak_delays = [t["delay_days"] for t in transits if t["month"] not in [8, 9, 10, 11]]
        
        peak_avg = statistics.mean(peak_delays) if peak_delays else 2
        off_peak_avg = statistics.mean(off_peak_delays) if off_peak_delays else 1
        peak_factor = peak_avg / off_peak_avg if off_peak_avg > 0 else 1.5
        
        return {
            "baseline_delay_days": round(statistics.mean(delays), 2),
            "delay_std_dev": round(statistics.stdev(delays), 2) if len(delays) > 1 else 1.5,
            "on_time_rate": round(sum(1 for d in delays if d < 1) / len(delays), 3),
            "peak_season_factor": round(peak_factor, 2),
            "data_source": "historical_analysis",
            "data_range": self._data.get("metadata", {}).get("date_range", {}),
            "total_transits_analyzed": len(transits),
        }
    
    async def get_carrier_performance(self) -> List[Dict]:
        """Get performance by carrier"""
        transits = self._data.get("transits", [])
        
        carrier_data = defaultdict(list)
        for transit in transits:
            carrier_data[transit["carrier"]].append(transit)
        
        performance = []
        for carrier, carrier_transits in carrier_data.items():
            delays = [t["delay_days"] for t in carrier_transits]
            on_time = sum(1 for t in carrier_transits if t["on_time"])
            
            performance.append({
                "carrier": carrier,
                "transit_count": len(carrier_transits),
                "avg_delay_days": round(statistics.mean(delays), 2),
                "on_time_rate": round(on_time / len(carrier_transits), 3),
                "reliability_score": round(1 - (statistics.mean(delays) / 10), 2),  # 0-1 score
            })
        
        # Sort by on-time rate
        performance.sort(key=lambda x: x["on_time_rate"], reverse=True)
        return performance
    
    async def get_port_congestion_history(self, port_code: str = None) -> Dict:
        """Get historical port congestion trends"""
        congestion = self._data.get("port_congestion", [])
        
        if port_code:
            congestion = [c for c in congestion if c["port_code"] == port_code]
        
        if not congestion:
            return {"error": "No congestion data available"}
        
        # Group by port
        port_data = defaultdict(list)
        for record in congestion:
            port_data[record["port_code"]].append(record)
        
        summary = {}
        for port_code, records in port_data.items():
            utilizations = [r["berth_utilization"] for r in records]
            wait_times = [r["wait_time_hours"] for r in records]
            
            summary[port_code] = {
                "port_name": records[0]["port_name"],
                "avg_utilization": round(statistics.mean(utilizations), 3),
                "max_utilization": round(max(utilizations), 3),
                "avg_wait_hours": round(statistics.mean(wait_times), 1),
                "max_wait_hours": round(max(wait_times), 1),
                "records_count": len(records),
            }
        
        return {
            "ports": summary,
            "overall_avg_utilization": round(
                statistics.mean([s["avg_utilization"] for s in summary.values()]), 3
            ),
        }
    
    async def get_summary(self) -> Dict:
        """Get overall historical data summary"""
        metadata = self._data.get("metadata", {})
        stats = self._data.get("statistics", {})
        
        return {
            "data_available": bool(self._data.get("transits")),
            "date_range": metadata.get("date_range", {}),
            "total_transits": metadata.get("total_transits", 0),
            "total_congestion_records": metadata.get("total_congestion_records", 0),
            "statistics": stats,
            "generated_at": metadata.get("generated_at"),
        }


# Singleton instance
historical_service = HistoricalService()
