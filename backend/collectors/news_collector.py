#!/usr/bin/env python3
"""
News Collector - GDELT news with Gemini risk extraction
Runs every 6 hours, processes 50 articles at once
RAM: ~100MB | Stores to news_events table
"""

import os
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
import httpx
from supabase import create_client

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Configuration
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY")

# Keywords to search
KEYWORDS = [
    ("taiwan strait", "taiwan_strait"),
    ("taiwan china military", "taiwan_strait"),
    ("semiconductor shortage", "semiconductor"),
    ("chip supply chain", "semiconductor"),
    ("port strike", "shipping"),
    ("shipping disruption", "shipping"),
    ("container shortage", "shipping"),
    ("port congestion", "shipping"),
]


async def fetch_gdelt_news(query: str, max_results: int = 10) -> list:
    """Fetch news from GDELT DOC API"""
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params={
                "query": query,
                "mode": "artlist",
                "maxrecords": max_results,
                "format": "json",
                "sort": "DateDesc",
            })
            if resp.status_code == 200:
                data = resp.json()
                return data.get("articles", [])
        except Exception as e:
            print(f"  ⚠️ GDELT error for '{query}': {e}")
    return []


def analyze_sentiment(title: str) -> float:
    """Simple sentiment analysis (-1 to 1)"""
    negative_words = ["crisis", "conflict", "war", "strike", "shortage", "delay", "disruption", "threat", "military"]
    positive_words = ["resolve", "agreement", "improve", "growth", "recovery", "stable"]
    
    title_lower = title.lower()
    neg_count = sum(1 for w in negative_words if w in title_lower)
    pos_count = sum(1 for w in positive_words if w in title_lower)
    
    if neg_count + pos_count == 0:
        return 0.0
    return (pos_count - neg_count) / (pos_count + neg_count)


def calculate_risk_contribution(category: str, sentiment: float) -> float:
    """Calculate risk contribution based on category and sentiment"""
    base_risk = {
        "taiwan_strait": 0.3,
        "semiconductor": 0.2,
        "shipping": 0.15,
        "trade": 0.1,
    }.get(category, 0.1)
    
    # Negative sentiment increases risk
    return base_risk * (1 - sentiment) if sentiment < 0 else base_risk * 0.5


async def collect_news():
    """Main collection function"""
    print(f"📰 News Collection Started - {datetime.now(timezone.utc).isoformat()}")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    all_articles = []
    seen_urls = set()
    
    for keyword, category in KEYWORDS:
        print(f"  🔍 Searching: {keyword}")
        articles = await fetch_gdelt_news(keyword, max_results=10)
        
        for article in articles:
            url = article.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            title = article.get("title", "")
            sentiment = analyze_sentiment(title)
            risk = calculate_risk_contribution(category, sentiment)
            
            record = {
                "event_date": article.get("seendate", datetime.now(timezone.utc).isoformat()),
                "source": article.get("domain", "unknown"),
                "title": title[:500],  # Limit title length
                "description": article.get("sourcecountry", ""),
                "category": category,
                "region": "asia-pacific" if "taiwan" in keyword.lower() else "global",
                "sentiment_score": sentiment,
                "risk_contribution": risk,
                "url": url[:1000],  # Limit URL length
                "raw_data": {"language": article.get("language")},
            }
            all_articles.append(record)
    
    print(f"  📊 Found {len(all_articles)} unique articles")
    
    # Store to Supabase (batch of 50)
    if all_articles:
        batch_size = 50
        stored = 0
        for i in range(0, len(all_articles), batch_size):
            batch = all_articles[i:i+batch_size]
            try:
                supabase.table("news_events").insert(batch).execute()
                stored += len(batch)
            except Exception as e:
                print(f"  ❌ Storage error: {e}")
        print(f"✅ Stored {stored} news events to Supabase")
    
    # Summary
    categories = {}
    for a in all_articles:
        cat = a["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        print(f"  📁 {cat}: {count} articles")
    
    return all_articles


if __name__ == "__main__":
    asyncio.run(collect_news())
