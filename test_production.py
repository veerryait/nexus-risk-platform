
import httpx
import asyncio
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "https://nexus-risk-platform-production.up.railway.app"
FRONTEND_URL = "https://nexus-risk-platform-vedq.vercel.app"

async def test_endpoint(client, name, url, method="GET", json_data=None, expected_status=200):
    print(f"Testing {name}...", end=" ", flush=True)
    try:
        if method == "GET":
            response = await client.get(url, timeout=30.0)
        else:
            response = await client.post(url, json=json_data, timeout=30.0)
        
        if response.status_code == expected_status:
            print(f"✅ OK ({response.elapsed.total_seconds():.2f}s)")
            return True, response.json() if response.content else None
        else:
            print(f"❌ FAILED (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False, None

async def main():
    print(f"Starting Production Verification at {datetime.now().isoformat()}")
    print(f"Backend: {API_BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("-" * 50)

    stats = {"passed": 0, "failed": 0}
    
    async with httpx.AsyncClient(base_url=API_BASE_URL) as client:
        # 1. Health Check
        success, _ = await test_endpoint(client, "Health Check", "/health")
        if success: 
            stats["passed"] += 1
        else: 
            stats["failed"] += 1

        # 2. Routes (Live Data)
        success, data = await test_endpoint(client, "Live Routes", "/api/v1/routes/")
        if success:
            stats["passed"] += 1
            if data and len(data) > 0:
                print(f"   Found {len(data)} routes.")
                first_route_id = data[0].get('id')
            else:
                print("   ⚠️ No routes found.")
                first_route_id = "1" # Fallback
        else:
            stats["failed"] += 1
            first_route_id = "1"

        # 3. GNN Analysis
        success, _ = await test_endpoint(client, "GNN Analysis", "/api/v1/gnn/predict")
        if success: 
            stats["passed"] += 1
        else: 
            stats["failed"] += 1

        # 4. Predict Risk (using a route ID)
        # Test with string ID
        payload = {
            "route_id": str(first_route_id), 
            "specific_features": {
                "weather_impact": 0.5,
                "port_congestion": 0.3
            }
        }
        success, _ = await test_endpoint(client, "Risk Prediction", "/api/v1/predict/", method="POST", json_data=payload)
        if success: 
            stats["passed"] += 1
        else: 
            stats["failed"] += 1

        # 5. Dashboard Summary (XAI)
        success, _ = await test_endpoint(client, "Dashboard Summary", "/api/v1/xai/dashboard-summary")
        if success: 
            stats["passed"] += 1
        else: 
            stats["failed"] += 1

    print("-" * 50)
    print(f"Verification Complete: {stats['passed']} Passed, {stats['failed']} Failed")
    
    if stats["failed"] > 0:
        sys.exit(1)
    
if __name__ == "__main__":
    asyncio.run(main())
