# Nexus Risk Platform

> **Supply Chain Resilience Predictor** - Track and predict disruptions in semiconductor chip supply chains from Taiwan to US West Coast.

## 🎯 MVP Focus
- **Routes**: 5 key shipping lanes (Taiwan → US West Coast)
- **Vessels**: 10-15 container ships
- **Predictions**: Delay risk with >70% accuracy

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, SQLAlchemy |
| Frontend | React, Recharts, Mapbox |
| Database | PostgreSQL (Supabase) |
| ML/Training | Google Colab, scikit-learn |
| Deployment | Railway (backend), Vercel (frontend) |

## 📁 Project Structure

```
Nexus Risk Platform/
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Config, security
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── services/     # Business logic
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── utils/
├── data/
│   ├── raw/              # Raw data files
│   └── processed/        # Cleaned data
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## 🚀 Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📊 Data Sources

- **Vessel Tracking**: MarineTraffic, VesselFinder
- **Weather**: OpenWeather API, NOAA
- **Geopolitical**: GDELT, NewsAPI
- **Economic**: FRED, World Bank

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.
