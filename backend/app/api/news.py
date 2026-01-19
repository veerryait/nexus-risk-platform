"""
News API - Supply Chain News Events Endpoint
GET /api/v1/news - Fetch news events from GDELT and database
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import httpx

from supabase import create_client

router = APIRouter()

# Supabase connection
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@router.get("/")
async def get_news(
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_risk: Optional[float] = None
):
    """Get recent supply chain news events"""
    try:
        supabase = get_supabase()
        
        # Try to get from database first
        query = supabase.table("news_events").select("*").order("published_at", desc=True).limit(limit)
        
        if min_risk:
            query = query.gte("risk_score", min_risk)
        
        result = query.execute()
        
        if result.data:
            return {
                "news": result.data,
                "count": len(result.data),
                "source": "database"
            }
        
        # Fallback: fetch from GDELT
        return await fetch_gdelt_news(limit)
        
    except Exception as e:
        # Fallback to GDELT on any error
        return await fetch_gdelt_news(limit)


async def fetch_gdelt_news(limit: int = 20):
    """Fetch news from GDELT API"""
    keywords = ["Taiwan Strait", "semiconductor supply", "port congestion", "shipping delay"]
    all_articles = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for keyword in keywords[:2]:  # Limit to reduce API calls
            try:
                url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={keyword}&mode=artlist&maxrecords=10&format=json"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    
                    for article in articles[:5]:
                        all_articles.append({
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "source": article.get("domain", ""),
                            "published_at": article.get("seendate", ""),
                            "image_url": article.get("socialimage", ""),
                            "keyword": keyword,
                            "risk_score": estimate_risk_score(article.get("title", ""))
                        })
            except Exception:
                continue
    
    return {
        "news": all_articles[:limit],
        "count": len(all_articles[:limit]),
        "source": "gdelt"
    }


def estimate_risk_score(title: str) -> float:
    """Estimate risk score from title keywords"""
    title_lower = title.lower()
    
    high_risk = ["crisis", "block", "closure", "attack", "war", "suspend"]
    medium_risk = ["delay", "congestion", "storm", "strike", "disruption"]
    low_risk = ["concern", "monitor", "issue", "slow"]
    
    for word in high_risk:
        if word in title_lower:
            return 0.8
    
    for word in medium_risk:
        if word in title_lower:
            return 0.5
    
    for word in low_risk:
        if word in title_lower:
            return 0.3
    
    return 0.2


@router.get("/risk-summary")
async def get_risk_summary():
    """Get aggregated risk summary from recent news"""
    news = await get_news(limit=50)
    articles = news.get("news", [])
    
    if not articles:
        return {"overall_risk": 0.2, "risk_level": "low", "article_count": 0}
    
    avg_risk = sum(a.get("risk_score", 0.2) for a in articles) / len(articles)
    
    if avg_risk >= 0.6:
        risk_level = "high"
    elif avg_risk >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    return {
        "overall_risk": round(avg_risk, 2),
        "risk_level": risk_level,
        "article_count": len(articles),
        "high_risk_count": sum(1 for a in articles if a.get("risk_score", 0) >= 0.6),
        "updated_at": datetime.utcnow().isoformat()
    }
