"""
Automated Data Collector
Runs daily to collect data from GDELT, OpenWeather, and FRED APIs
Stores results in Supabase for historical tracking
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, List

from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment
load_dotenv()


class DataCollector:
    """Automated data collection from all sources"""
    
    def __init__(self):
        # Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL", "https://hssnbnsffqorupviykha.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SUPABASE_SERVICE_KEY", ""))
        
        if self.supabase_key:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        else:
            self.supabase = None
            print("⚠️ Supabase not configured - data will not be saved")
    
    async def collect_weather_data(self) -> Dict:
        """Collect weather data from OpenWeatherMap"""
        from app.services.weather_service import weather_service
        
        print("📡 Collecting weather data...")
        try:
            route_weather = await weather_service.get_route_weather()
            storm_alerts = await weather_service.get_storm_alerts()
            risk_score = await weather_service.get_weather_risk_score()
            
            data = {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "route_conditions": route_weather,
                "storm_alerts": storm_alerts,
                "risk_score": risk_score,
                "source": "openweathermap"
            }
            
            # Store in Supabase
            if self.supabase:
                self.supabase.table("collected_weather").insert({
                    "collected_at": data["collected_at"],
                    "risk_score": risk_score,
                    "storm_count": len(storm_alerts),
                    "data": data
                }).execute()
            
            print(f"  ✅ Weather: {len(route_weather)} points, risk={risk_score:.2f}")
            return data
        except Exception as e:
            print(f"  ❌ Weather error: {e}")
            return {"error": str(e)}
    
    async def collect_news_data(self) -> Dict:
        """Collect geopolitical news from GDELT"""
        from app.services.gdelt_service import gdelt_service
        
        print("📡 Collecting GDELT news...")
        try:
            taiwan_events = await gdelt_service.get_taiwan_strait_events()
            shipping_events = await gdelt_service.get_shipping_disruption_events()
            risk_score = await gdelt_service.get_geopolitical_risk_score()
            
            data = {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "taiwan_events": taiwan_events[:10],  # Limit
                "shipping_events": shipping_events[:10],
                "risk_score": risk_score,
                "source": "gdelt"
            }
            
            # Store in Supabase
            if self.supabase:
                self.supabase.table("collected_news").insert({
                    "collected_at": data["collected_at"],
                    "risk_score": risk_score,
                    "taiwan_event_count": len(taiwan_events),
                    "shipping_event_count": len(shipping_events),
                    "data": data
                }).execute()
            
            print(f"  ✅ News: {len(taiwan_events)} Taiwan, {len(shipping_events)} shipping events")
            return data
        except Exception as e:
            print(f"  ❌ News error: {e}")
            return {"error": str(e)}
    
    async def collect_economics_data(self) -> Dict:
        """Collect economic data from FRED"""
        from app.services.fred_service import fred_service
        
        print("📡 Collecting FRED economic data...")
        try:
            trade_data = await fred_service.get_trade_indicators()
            shipping_rates = await fred_service.get_shipping_rate_proxy()
            risk_score = await fred_service.get_economic_risk_score()
            
            data = {
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "trade_indicators": trade_data,
                "shipping_rates": shipping_rates,
                "risk_score": risk_score,
                "source": "fred"
            }
            
            # Store in Supabase
            if self.supabase:
                imports_val = trade_data.get("imports", {}).get("latest_value")
                exports_val = trade_data.get("exports", {}).get("latest_value")
                
                self.supabase.table("collected_economics").insert({
                    "collected_at": data["collected_at"],
                    "risk_score": risk_score,
                    "imports_value": imports_val,
                    "exports_value": exports_val,
                    "data": data
                }).execute()
            
            print(f"  ✅ Economics: imports={trade_data.get('imports', {}).get('latest_value')}, risk={risk_score:.2f}")
            return data
        except Exception as e:
            print(f"  ❌ Economics error: {e}")
            return {"error": str(e)}
    
    async def collect_all(self) -> Dict:
        """Run all collectors"""
        print(f"\n{'='*50}")
        print(f"🚀 Starting Daily Data Collection")
        print(f"   Time: {datetime.now(timezone.utc).isoformat()}")
        print(f"{'='*50}\n")
        
        results = {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "weather": await self.collect_weather_data(),
            "news": await self.collect_news_data(),
            "economics": await self.collect_economics_data(),
        }
        
        # Calculate overall risk
        risks = []
        for key in ["weather", "news", "economics"]:
            if "risk_score" in results[key]:
                risks.append(results[key]["risk_score"])
        
        if risks:
            results["overall_risk"] = sum(risks) / len(risks)
        
        print(f"\n{'='*50}")
        print(f"✅ Collection Complete")
        print(f"   Overall Risk: {results.get('overall_risk', 'N/A'):.2f}")
        print(f"{'='*50}\n")
        
        return results


# Scheduler functions
def run_daily_collection():
    """Synchronous wrapper for scheduler"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    collector = DataCollector()
    asyncio.run(collector.collect_all())


def setup_scheduler():
    """Set up APScheduler for daily collection"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    
    scheduler = BackgroundScheduler()
    
    # Run daily at midnight UTC
    scheduler.add_job(
        run_daily_collection,
        CronTrigger(hour=0, minute=0),
        id="daily_data_collection",
        name="Daily Data Collection",
        replace_existing=True
    )
    
    scheduler.start()
    print("📅 Scheduler started - Daily collection at 00:00 UTC")
    return scheduler


async def main():
    """Manual collection run"""
    collector = DataCollector()
    results = await collector.collect_all()
    print(f"\nResults: {results.keys()}")


if __name__ == "__main__":
    asyncio.run(main())
