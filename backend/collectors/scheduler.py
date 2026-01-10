#!/usr/bin/env python3
"""
Scheduler - Background scheduler for data collection
Weather: Every 12 hours
News: Every 6 hours
Runs as background daemon
"""

import asyncio
import schedule
import time
from datetime import datetime
import threading

# Import collectors
from weather_collector import collect_weather
from news_collector import collect_news


def run_async(coro):
    """Wrapper to run async function from sync scheduler"""
    asyncio.run(coro())


def weather_job():
    """Weather collection job"""
    print(f"\n{'='*50}")
    print(f"⏰ Scheduled Weather Collection - {datetime.now()}")
    print(f"{'='*50}")
    run_async(collect_weather)


def news_job():
    """News collection job"""
    print(f"\n{'='*50}")
    print(f"⏰ Scheduled News Collection - {datetime.now()}")
    print(f"{'='*50}")
    run_async(collect_news)


def main():
    print("=" * 60)
    print("🚀 Data Collection Scheduler Started")
    print("=" * 60)
    print("\nSchedule:")
    print("  🌤️  Weather: Every 12 hours (00:00, 12:00 UTC)")
    print("  📰 News: Every 6 hours (00:00, 06:00, 12:00, 18:00 UTC)")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Schedule jobs
    schedule.every(12).hours.do(weather_job)
    schedule.every(6).hours.do(news_job)
    
    # Run immediately on start
    print("\n🔄 Running initial collection...")
    weather_job()
    news_job()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()
