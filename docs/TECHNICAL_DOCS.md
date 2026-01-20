# Technical Documentation 🛠️

## 1. System Architecture

Nexus Risk Platform is built on a modular, containerized architecture designed for scalability and maintainability.

### 1.1 High-Level Overview
-   **Frontend**: Next.js application served via Vercel Edge Network.
-   **Backend**: FastAPI service running in Docker on Railway.
-   **Database**: PostgreSQL managed by Supabase.
-   **Automation**: GitHub Actions for scheduled data ingestion.

---

## 2. Data Pipeline 📊

The data pipeline aggregates heterogeneous data sources into a unified risk model.

### 2.1 Data Sources
| Domain | Source | Frequency | Purpose |
|--------|--------|-----------|---------|
| **Vessels** | MarineTraffic / AIS | 4 Hours | Live position, speed, heading |
| **Weather** | OpenWeatherMap | 12 Hours | Typhoon tracking, wave height |
| **News** | NewsAPI / GDELT | 6 Hours | Port strikes, trade policy changes |
| **Ports** | Internal DB | Static | Port coordinates, capacity (TEUs) |

### 2.2 Ingestion Flow
1.  **Collectors**: Specialized Python scripts (`backend/collectors/`) run via GitHub Actions.
2.  **normalization**: Raw JSON/XML is parsed and normalized into Pydantic models.
3.  **Storage**: Cleaned data is upserted into Supabase tables (`vessel_positions`, `weather_alerts`).
4.  **Signal Generation**: `live_data_service.py` aggregates recent data to compute `Operational Risk`.

---

## 3. Machine Learning Models 🤖

Nexus uses a hybrid approach combining rule-based heuristics and Graph Neural Networks.

### 3.1 Random Forest Regressor (Route Risk)
-   **Goal**: Predict delay (in days) for individual routes.
-   **Features**:
    -   `distance_remaining` (Normalized)
    -   `average_speed` (vs design speed)
    -   `weather_severity_index` (0-1)
    -   `port_congestion_level` (0-1)
-   **Implementation**: Scikit-learn (`app/ml/predict.py`).

### 3.2 Graph Neural Network (Network Risk)
-   **Goal**: Identify cascading risks in the global port network.
-   **Architecture**:
    -   **Nodes**: Ports (Features: Capacity, Congestion, Weather)
    -   **Edges**: Shipping Routes (Features: Distance, Transit Time)
    -   **Model**: Graph Attention Network (GAT) or GCN.
-   **Inference**:
    -   **GPU Mode**: Uses PyTorch Geometric if CUDA/MPS is available.
    -   **Standard Mode**: Falls back to specialized NumPy matrix operations for CPU environments (like Railway).
-   **Output**: `Network Risk Score` (0-100) for the entire system and individual nodes.

### 3.3 Explainable AI (XAI)
-   **Mechanism**: Uses Integrated Gradients (conceptually) to attribute risk scores to specific feature inputs.
-   **Output**: Natural language explanations (e.g., "High risk due to Typhoon near Kaohsiung").

---

## 4. API Reference 🔌

The backend exposes a RESTful API via FastAPI.

### Base URL: `/api/v1`

### Key Endpoints

#### Routes
-   `GET /routes/`: List active shipping routes with current status.
-   `GET /routes/{id}`: Detailed telemetry for a specific route.

#### Predictions
-   `POST /predict/`: Get risk assessment for a hypothetical or real route.
    ```json
    {
      "route_id": "TW-US-001",
      "specific_features": { "weather_impact": 0.8 }
    }
    ```

#### GNN
-   `GET /gnn/predict`: Get structural network risk.
-   `GET /gnn/network`: Get graph topology for visualization.

---

## 5. Development & Deployment

### 5.1 Local Development
The project uses `dotenv` for configuration. API keys must be set in `.env`.

### 5.2 Deployment Strategy
-   **Backend**: Dockerfile builds a lightweight Python image. Deployed to Railway from the `main` branch.
-   **Frontend**: Next.js build pipeline on Vercel. Automagically deploys on push.
-   **Database**: Migrations managed by SQLAlchemy (currently using `Base.metadata.create_all`).

### 5.3 Monitoring
-   **Logs**: Application logs are routed to `stdout` (captured by Railway).
-   **Health Check**: `/health` endpoint serves as a heartbeat for uptime monitors.
