# Nexus Risk Platform - API Documentation

## Base URL
- **Local**: `http://localhost:8000`
- **Production**: `https://your-app.railway.app`

## Authentication
Currently no authentication required. Add API keys for production use.

---

## Endpoints

### Health & Status

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

---

### Vessels

#### `GET /api/v1/vessels/`
List tracked vessels.

**Response:**
```json
{
  "vessels": [...],
  "count": 10
}
```

---

### Routes

#### `GET /api/v1/routes/`
List shipping routes.

#### `GET /api/v1/routes/{route_id}`
Get specific route details.

---

### News

#### `GET /api/v1/news/`
Get recent supply chain news.

**Query Params:**
- `limit`: Number of articles (default: 20)
- `min_risk`: Minimum risk score filter

#### `GET /api/v1/news/risk-summary`
Get aggregated news risk summary.

---

### ML Predictions

#### `GET /api/v1/predict/health`
Check ML model status.

**Response:**
```json
{
  "status": "healthy",
  "classifier_loaded": true,
  "regressor_loaded": true,
  "feature_count": 27
}
```

#### `POST /api/v1/predict/`
Make risk prediction for a route.

**Request Body:**
```json
{
  "route_id": "TWKHH-USLAX",
  "origin": "TWKHH",
  "destination": "USLAX",
  "storm_risk": 0.3,
  "congestion": 0.4,
  "eta_delay": 0
}
```

**Response:**
```json
{
  "route_id": "TWKHH-USLAX",
  "prediction": {
    "on_time_probability": 0.95,
    "delay_probability": 0.05,
    "predicted_delay_days": 0.5,
    "risk_level": "low",
    "confidence": 0.95
  },
  "factors": [...],
  "recommendations": [...]
}
```

#### `POST /api/v1/predict/batch`
Batch predictions (max 50 routes).

---

### Data Sources

#### `GET /api/v1/data/weather`
Get weather conditions for route waypoints.

#### `GET /api/v1/data/economics`
Get economic indicators (imports, exports, shipping rates).

---

### Admin

#### `GET /api/v1/admin/port-status`
Get current port congestion status.

#### `POST /api/v1/admin/port-status/quick`
Add port congestion data.

**Request Body:**
```json
{
  "port": "USLAX",
  "vessels_waiting": 15,
  "avg_wait_days": 3.5,
  "congestion_level": "high"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

---

## Rate Limits
- External APIs (weather, news): Cached for 5 minutes
- ML predictions: No limit

---

## Interactive Docs
- Swagger UI: `/docs`
- ReDoc: `/redoc`
