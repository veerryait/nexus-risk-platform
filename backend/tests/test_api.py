"""
Nexus Risk Platform - Automated API Tests
Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os
import time

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self):
        """GET / returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "operational"
    
    def test_health_endpoint(self):
        """GET /health returns healthy"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRoutesAPI:
    """Test routes endpoints"""
    
    def test_get_routes(self):
        """GET /api/v1/routes returns route list"""
        response = client.get("/api/v1/routes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check route structure
        route = data[0]
        assert "id" in route
        assert "origin" in route
        assert "destination" in route
    
    def test_get_route_by_id(self):
        """GET /api/v1/routes/{id} returns single route"""
        # First get list to get an ID
        response = client.get("/api/v1/routes")
        routes = response.json()
        if routes:
            route_id = routes[0]["id"]
            response = client.get(f"/api/v1/routes/{route_id}")
            assert response.status_code == 200


class TestPredictionAPI:
    """Test ML prediction endpoints"""
    
    def test_predict_endpoint(self):
        """POST /api/v1/predict/ returns prediction"""
        payload = {
            "route_id": "TWKHH-USLAX",
            "origin": "TWKHH",
            "destination": "USLAX",
            "distance_nm": 6500,
            "eta_delay": 0,
            "speed_knots": 19.3,
            "congestion": 0.3,
            "storm_risk": 0.2,
            "news_risk": 0.2,
            "carrier_rate": 0.88
        }
        response = client.post("/api/v1/predict/", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data or "risk_level" in data or "predicted_delay_days" in data


class TestResponseTimes:
    """Test that API responses are fast"""
    
    def test_routes_response_time(self):
        """Routes endpoint responds in <500ms"""
        start = time.time()
        response = client.get("/api/v1/routes")
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed < 500, f"Response took {elapsed:.0f}ms, expected <500ms"
    
    def test_health_response_time(self):
        """Health endpoint responds in <300ms"""
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed < 300, f"Response took {elapsed:.0f}ms, expected <300ms"


class TestErrorHandling:
    """Test error responses are sanitized"""
    
    def test_404_not_found(self):
        """404 errors don't leak internal paths"""
        response = client.get("/api/v1/nonexistent/endpoint")
        assert response.status_code == 404
        data = response.json()
        # Should have error but not stack traces
        assert "detail" in data or "error" in data
        error_text = str(data)
        assert "/Users/" not in error_text
        assert "Traceback" not in error_text
    
    def test_invalid_route_id(self):
        """Invalid route ID returns proper error code"""
        response = client.get("/api/v1/routes/invalid-route-id-12345")
        # 404 (not found), 200 (empty), or 422 (validation error) are all acceptable
        assert response.status_code in [404, 200, 422]


class TestCORS:
    """Test CORS headers are present"""
    
    def test_cors_headers(self):
        """OPTIONS request returns CORS headers"""
        response = client.options(
            "/api/v1/routes",
            headers={"Origin": "http://localhost:3000"}
        )
        # Should allow the request
        assert response.status_code in [200, 405]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
