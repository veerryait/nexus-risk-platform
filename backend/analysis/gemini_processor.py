#!/usr/bin/env python3
"""
Gemini News Processor - Batch process news articles for risk extraction
Step 3.2: Extract risk signals using Gemini API
Rate limit: 60 req/min | Batch size: 50 articles
"""

import os
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
from supabase import create_client
import httpx

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", 
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY")

BATCH_SIZE = 50
RATE_LIMIT_RPM = 60
DELAY_BETWEEN_REQUESTS = 1.1  # seconds (to stay under 60/min)


class GeminiNewsProcessor:
    """Process news articles with Gemini for risk extraction"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        self.api_key = GEMINI_API_KEY
        self.processed_count = 0
        self.errors = []
        
    async def extract_risk_signals(self, article: Dict) -> Dict:
        """Send article to Gemini and extract risk signals"""
        
        prompt = f"""Analyze this supply chain news article and extract risk signals.

ARTICLE TITLE: {article.get('title', 'No title')}
SOURCE: {article.get('source', 'Unknown')}
CATEGORY: {article.get('category', 'General')}

Extract and return ONLY a JSON object with these fields:
{{
    "risk_level": "low/medium/high/critical",
    "affected_regions": ["list of affected regions"],
    "event_type": "typhoon/strike/port_closure/geopolitical/supply_shortage/congestion/other",
    "severity": 1-10,
    "shipping_impact": "none/minor/moderate/major/severe",
    "delay_likelihood_days": 0-30,
    "key_entities": ["companies/ports/countries mentioned"],
    "summary": "One sentence risk summary"
}}

Return ONLY valid JSON, no other text."""

        if not self.api_key:
            # Fallback: Simple heuristic-based extraction
            return self._heuristic_extraction(article)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.2,
                            "maxOutputTokens": 500
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
                    
                    # Parse JSON from response
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    if start >= 0 and end > start:
                        return json.loads(text[start:end])
                    
                elif response.status_code == 429:
                    print(f"  ⚠️ Rate limited, waiting...")
                    await asyncio.sleep(10)
                    return await self.extract_risk_signals(article)
                    
                else:
                    print(f"  ⚠️ API error: {response.status_code}")
                    
        except Exception as e:
            self.errors.append(str(e))
            
        return self._heuristic_extraction(article)
    
    def _heuristic_extraction(self, article: Dict) -> Dict:
        """Fallback: Extract risk signals using keyword heuristics"""
        title = article.get('title', '').lower()
        category = article.get('category', '').lower()
        
        # Risk level detection
        high_risk_words = ['crisis', 'war', 'military', 'blockade', 'shutdown', 'catastrophic']
        medium_risk_words = ['delay', 'congestion', 'strike', 'typhoon', 'shortage']
        
        risk_level = "low"
        if any(w in title for w in high_risk_words):
            risk_level = "high"
        elif any(w in title for w in medium_risk_words):
            risk_level = "medium"
        
        # Event type detection
        event_type = "other"
        if "typhoon" in title or "storm" in title:
            event_type = "typhoon"
        elif "strike" in title:
            event_type = "strike"
        elif "port" in title and ("close" in title or "shut" in title):
            event_type = "port_closure"
        elif "taiwan" in title or "china" in title or "military" in title:
            event_type = "geopolitical"
        elif "shortage" in title or "supply" in title:
            event_type = "supply_shortage"
        elif "congestion" in title:
            event_type = "congestion"
        
        # Regions
        regions = []
        if "taiwan" in title: regions.append("Taiwan")
        if "china" in title: regions.append("China")
        if "japan" in title: regions.append("Japan")
        if "korea" in title: regions.append("Korea")
        if "us" in title or "america" in title: regions.append("USA")
        if not regions:
            regions = ["Asia-Pacific"]
        
        # Severity
        severity_map = {"low": 3, "medium": 5, "high": 8, "critical": 10}
        severity = severity_map.get(risk_level, 3)
        
        return {
            "risk_level": risk_level,
            "affected_regions": regions,
            "event_type": event_type,
            "severity": severity,
            "shipping_impact": "minor" if risk_level == "low" else "moderate" if risk_level == "medium" else "major",
            "delay_likelihood_days": 0 if risk_level == "low" else 3 if risk_level == "medium" else 7,
            "key_entities": regions,
            "summary": f"Detected {event_type} event affecting {', '.join(regions)}",
            "extraction_method": "heuristic"
        }
    
    async def fetch_articles_from_gdelt(self, max_articles: int = 50) -> List[Dict]:
        """Fetch fresh articles from GDELT"""
        keywords = [
            "taiwan strait shipping",
            "semiconductor supply chain",
            "port congestion asia",
            "container shipping delay"
        ]
        
        all_articles = []
        seen_urls = set()
        
        async with httpx.AsyncClient(timeout=30) as client:
            for keyword in keywords:
                try:
                    resp = await client.get(
                        "https://api.gdeltproject.org/api/v2/doc/doc",
                        params={
                            "query": keyword,
                            "mode": "artlist",
                            "maxrecords": 15,
                            "format": "json",
                            "sort": "DateDesc"
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        for article in data.get("articles", []):
                            url = article.get("url", "")
                            if url not in seen_urls:
                                seen_urls.add(url)
                                all_articles.append({
                                    "title": article.get("title", ""),
                                    "source": article.get("domain", ""),
                                    "url": url,
                                    "date": article.get("seendate", ""),
                                    "category": keyword.split()[0]
                                })
                except Exception as e:
                    print(f"  ⚠️ GDELT error for '{keyword}': {e}")
        
        return all_articles[:max_articles]
    
    async def process_batch(self, articles: List[Dict]) -> List[Dict]:
        """Process a batch of articles"""
        results = []
        
        for i, article in enumerate(articles):
            print(f"  Processing {i+1}/{len(articles)}: {article.get('title', '')[:50]}...")
            
            # Extract risk signals
            signals = await self.extract_risk_signals(article)
            
            # Combine article with extracted signals
            enriched = {
                **article,
                "risk_signals": signals,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }
            results.append(enriched)
            self.processed_count += 1
            
            # Rate limiting
            if i < len(articles) - 1:
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        
        return results
    
    async def store_enriched_articles(self, articles: List[Dict]):
        """Store enriched articles in Supabase"""
        records = []
        for article in articles:
            signals = article.get("risk_signals", {})
            records.append({
                "event_date": article.get("date", datetime.now(timezone.utc).isoformat()),
                "source": article.get("source", ""),
                "title": article.get("title", "")[:500],
                "description": signals.get("summary", ""),
                "category": signals.get("event_type", "other"),
                "region": ", ".join(signals.get("affected_regions", [])),
                "sentiment_score": -0.5 if signals.get("risk_level") == "high" else -0.2 if signals.get("risk_level") == "medium" else 0.1,
                "risk_contribution": signals.get("severity", 3) / 10,
                "url": article.get("url", "")[:1000],
                "raw_data": signals
            })
        
        if records:
            try:
                self.supabase.table("news_events").insert(records).execute()
                print(f"  ✅ Stored {len(records)} enriched articles")
            except Exception as e:
                print(f"  ⚠️ Storage error: {e}")
    
    async def run(self, max_articles: int = 50):
        """Main processing pipeline"""
        print("="*60)
        print("🤖 GEMINI NEWS PROCESSOR")
        print(f"   Processing up to {max_articles} articles")
        print(f"   Rate limit: {RATE_LIMIT_RPM} req/min")
        print("="*60)
        
        # Fetch articles
        print("\n📥 Fetching articles from GDELT...")
        articles = await self.fetch_articles_from_gdelt(max_articles)
        print(f"   Found {len(articles)} articles")
        
        if not articles:
            print("   No articles found")
            return
        
        # Process in batches
        print(f"\n🔄 Processing with {'Gemini API' if self.api_key else 'heuristics'}...")
        enriched = await self.process_batch(articles)
        
        # Store results
        print("\n💾 Storing enriched data...")
        await self.store_enriched_articles(enriched)
        
        # Summary
        risk_counts = {}
        for article in enriched:
            level = article.get("risk_signals", {}).get("risk_level", "unknown")
            risk_counts[level] = risk_counts.get(level, 0) + 1
        
        print("\n" + "="*60)
        print("✅ PROCESSING COMPLETE")
        print("="*60)
        print(f"   Total processed: {self.processed_count}")
        print(f"   Errors: {len(self.errors)}")
        print(f"\n   Risk Distribution:")
        for level, count in sorted(risk_counts.items()):
            print(f"     {level}: {count}")
        
        return enriched


async def main():
    processor = GeminiNewsProcessor()
    results = await processor.run(max_articles=50)
    return results


if __name__ == "__main__":
    asyncio.run(main())
