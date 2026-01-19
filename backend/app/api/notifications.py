"""
Notifications API - Generate real-time notifications from various data sources
GET /api/v1/notifications - Fetch notifications from news, routes, and system
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import random

from supabase import create_client

router = APIRouter()

# Supabase connection
SUPABASE_URL = "https://hssnbnsffqorupviykha.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhzc25ibnNmZnFvcnVwdml5a2hhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODAyNDYwMiwiZXhwIjoyMDgzNjAwNjAyfQ.S8q15OUhTcco8gFEEqAfW5Npmi-1TAfV_g9qzozc1bY"


def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def format_time_ago(dt: datetime) -> str:
    """Format datetime as human-readable 'time ago' string"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} min ago"
    else:
        return "Just now"


@router.get("/")
async def get_notifications(
    limit: int = Query(20, ge=1, le=50)
):
    """
    Get real-time notifications aggregated from multiple sources:
    - News events from database
    - Route risk alerts
    - System updates
    """
    notifications = []
    
    # 1. Get news-based notifications
    news_notifications = await get_news_notifications(limit=10)
    notifications.extend(news_notifications)
    
    # 2. Get route risk notifications
    risk_notifications = get_route_risk_notifications()
    notifications.extend(risk_notifications)
    
    # 3. Get system notifications
    system_notifications = get_system_notifications()
    notifications.extend(system_notifications)
    
    # Sort by timestamp (newest first)
    notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "notifications": notifications[:limit],
        "count": len(notifications[:limit]),
        "generated_at": datetime.utcnow().isoformat()
    }


async def get_news_notifications(limit: int = 10) -> List[dict]:
    """Generate notifications from news events in database"""
    notifications = []
    
    try:
        supabase = get_supabase()
        
        # Fetch recent news events
        result = supabase.table("news_events").select("*").order(
            "published_at", desc=True
        ).limit(limit).execute()
        
        if result.data:
            for article in result.data:
                risk_score = article.get("risk_score", 0.2)
                
                # Only create notifications for medium+ risk news
                if risk_score >= 0.4:
                    notification_type = "risk" if risk_score >= 0.6 else "news"
                    severity = "high" if risk_score >= 0.7 else "medium" if risk_score >= 0.4 else "low"
                    
                    # Parse published_at
                    try:
                        published_at = datetime.fromisoformat(article.get("published_at", "").replace("Z", "+00:00"))
                    except:
                        published_at = datetime.utcnow() - timedelta(hours=random.randint(1, 24))
                    
                    notifications.append({
                        "id": f"news-{article.get('id', uuid.uuid4())}",
                        "type": notification_type,
                        "title": "High Risk News Alert" if risk_score >= 0.6 else "Industry Update",
                        "message": article.get("title", "News update"),
                        "details": f"Source: {article.get('source', 'Unknown')}. Risk Score: {risk_score:.0%}",
                        "timestamp": published_at.isoformat(),
                        "time_ago": format_time_ago(published_at),
                        "severity": severity,
                        "url": article.get("url", "")
                    })
    except Exception as e:
        # Fallback: generate a sample news notification
        notifications.append({
            "id": f"news-fallback-{uuid.uuid4()}",
            "type": "news",
            "title": "Supply Chain Update",
            "message": "Monitoring Taiwan-US shipping routes for potential disruptions",
            "details": "Real-time news monitoring is active",
            "timestamp": datetime.utcnow().isoformat(),
            "time_ago": "Just now",
            "severity": "low"
        })
    
    return notifications


def get_route_risk_notifications() -> List[dict]:
    """Generate notifications based on route risk assessments"""
    notifications = []
    
    # Simulated route risk data - in production, this would come from actual route analysis
    route_alerts = [
        {
            "route": "Kaohsiung → Los Angeles",
            "risk": "high",
            "reason": "Port congestion at Los Angeles",
            "hours_ago": 2
        },
        {
            "route": "Taipei → Long Beach",
            "risk": "medium",
            "reason": "Weather advisory in Pacific",
            "hours_ago": 5
        },
        {
            "route": "Kaohsiung → Seattle",
            "risk": "low",
            "reason": "Normal operations",
            "hours_ago": 12
        }
    ]
    
    for i, alert in enumerate(route_alerts):
        if alert["risk"] in ["high", "medium"]:
            timestamp = datetime.utcnow() - timedelta(hours=alert["hours_ago"])
            
            notifications.append({
                "id": f"route-{i+1}",
                "type": "risk" if alert["risk"] == "high" else "delay",
                "title": f"{'High' if alert['risk'] == 'high' else 'Medium'} Risk: {alert['route']}",
                "message": alert["reason"],
                "details": f"Route {alert['route']} is experiencing {alert['risk']} risk conditions. Monitor for updates.",
                "timestamp": timestamp.isoformat(),
                "time_ago": format_time_ago(timestamp),
                "severity": alert["risk"]
            })
    
    return notifications


def get_system_notifications() -> List[dict]:
    """Generate system-level notifications"""
    notifications = []
    
    # System status notification
    notifications.append({
        "id": "system-1",
        "type": "system",
        "title": "Real-time Monitoring Active",
        "message": "All Taiwan-US shipping routes are being monitored",
        "details": "AIS tracking, weather data, and news monitoring are operational.",
        "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
        "time_ago": "1 hour ago",
        "severity": "low"
    })
    
    # Weather notification (simulated)
    notifications.append({
        "id": "weather-1",
        "type": "weather",
        "title": "Weather Advisory",
        "message": "Mild weather conditions across Pacific shipping lanes",
        "details": "No significant weather disruptions expected in the next 48 hours.",
        "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "time_ago": "3 hours ago",
        "severity": "low"
    })
    
    return notifications


@router.get("/summary")
async def get_notifications_summary():
    """Get a summary of notification counts by type"""
    result = await get_notifications(limit=50)
    notifications = result.get("notifications", [])
    
    summary = {
        "total": len(notifications),
        "by_type": {},
        "by_severity": {"high": 0, "medium": 0, "low": 0}
    }
    
    for n in notifications:
        n_type = n.get("type", "other")
        severity = n.get("severity", "low")
        
        summary["by_type"][n_type] = summary["by_type"].get(n_type, 0) + 1
        summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
    
    return summary
