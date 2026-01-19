"""
ML Prediction Service - Load models and make predictions
Used by the predict API endpoint
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List
import json


class RiskPredictionService:
    """ML-based risk prediction service with model loading"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to load models only once"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not RiskPredictionService._initialized:
            self.models_dir = Path(__file__).parent.parent.parent / "models"
            self.classifier = None
            self.regressor = None
            self.scaler = None
            self.feature_names = None
            self._load_models()
            RiskPredictionService._initialized = True
    
    def _load_models(self):
        """Load trained ML models from disk"""
        try:
            self.classifier = joblib.load(self.models_dir / "random_forest_classifier.joblib")
            self.regressor = joblib.load(self.models_dir / "random_forest_regressor.joblib")
            self.scaler = joblib.load(self.models_dir / "scaler.joblib")
            
            # Load feature names
            features_file = self.models_dir / "feature_names.txt"
            if features_file.exists():
                with open(features_file) as f:
                    self.feature_names = [line.strip() for line in f.readlines()]
            
            # Log model loading status (safe info)
            import logging
            logging.getLogger(__name__).info(f"ML models loaded: {len(self.feature_names)} features")
        except Exception as e:
            # Log error type only, not full details or paths
            import logging
            logging.getLogger("nexus.security").warning(f"Model load fallback: {type(e).__name__}")
            self.feature_names = self._get_default_features()
    
    def _get_default_features(self) -> List[str]:
        """Default feature names if model not loaded"""
        return [
            "route_distance_nm", "route_complexity", "port_pair_risk",
            "eta_delay_days", "speed_anomaly_pct", "position_deviation_pct", "vessel_speed_knots",
            "month", "quarter", "is_typhoon_season", "is_peak_season", "day_of_week",
            "hist_disruption_count", "avg_hist_delay_days", "seasonal_risk_score", "route_risk_score",
            "carrier_on_time_rate", "carrier_avg_delay", "carrier_reliability_score",
            "news_risk_score_7day", "news_event_frequency", "news_sentiment_avg", "news_sentiment_trend",
            "weather_wind_speed_avg", "weather_storm_risk",
            "port_congestion_level", "port_wait_time_ratio"
        ]
    
    def predict(self, route_data: Dict) -> Dict:
        """Make risk prediction for a route"""
        try:
            # Build feature vector
            features = self._build_features(route_data)
            X = pd.DataFrame([features], columns=self.feature_names)
            
            if self.classifier is None:
                # Return mock prediction if model not loaded
                return self._mock_prediction(route_data)
            
            # Get predictions
            on_time_prob = self.classifier.predict_proba(X)[0]
            delay_days = self.regressor.predict(X)[0]
            
            # Determine risk level
            delay_prob = float(on_time_prob[0])
            if delay_prob >= 0.7:
                risk_level = "critical"
            elif delay_prob >= 0.4:
                risk_level = "high"
            elif delay_prob >= 0.2:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            return {
                "route_id": route_data.get("route_id", "TWKHH-USLAX"),
                "prediction": {
                    "on_time_probability": float(on_time_prob[1]),
                    "delay_probability": float(on_time_prob[0]),
                    "predicted_delay_days": max(0, float(delay_days)),
                    "risk_level": risk_level,
                    "confidence": float(max(on_time_prob))
                },
                "factors": self._get_risk_factors(route_data),
                "recommendations": self._get_recommendations(risk_level, route_data)
            }
        except Exception as e:
            return self._mock_prediction(route_data, error=str(e))
    
    def _build_features(self, route_data: Dict) -> Dict:
        """Build feature dictionary from route data"""
        from datetime import datetime
        
        month = route_data.get("month", datetime.now().month)
        
        return {
            "route_distance_nm": route_data.get("distance_nm", 6500),
            "route_complexity": 0.6,
            "port_pair_risk": 0.4 if "TW" in route_data.get("origin", "TWKHH") else 0.2,
            "eta_delay_days": route_data.get("eta_delay", 0),
            "speed_anomaly_pct": route_data.get("speed_anomaly", 0),
            "position_deviation_pct": route_data.get("position_deviation", 0),
            "vessel_speed_knots": route_data.get("speed_knots", 19.3),
            "month": month,
            "quarter": (month - 1) // 3 + 1,
            "is_typhoon_season": 1 if month in [7, 8, 9, 10] else 0,
            "is_peak_season": 1 if month in [9, 10, 11] else 0,
            "day_of_week": route_data.get("day_of_week", 3),
            "hist_disruption_count": route_data.get("disruption_count", 0),
            "avg_hist_delay_days": route_data.get("avg_delay", 0),
            "seasonal_risk_score": 0.4 if month in [8, 9, 10] else 0.1,
            "route_risk_score": 0.4,
            "carrier_on_time_rate": route_data.get("carrier_rate", 0.88),
            "carrier_avg_delay": route_data.get("carrier_delay", 0.4),
            "carrier_reliability_score": route_data.get("carrier_rate", 0.88) * 100,
            "news_risk_score_7day": route_data.get("news_risk", 0.2),
            "news_event_frequency": route_data.get("news_frequency", 3),
            "news_sentiment_avg": route_data.get("sentiment", 0),
            "news_sentiment_trend": 0,
            "weather_wind_speed_avg": route_data.get("wind_speed", 15),
            "weather_storm_risk": route_data.get("storm_risk", 0.2),
            "port_congestion_level": route_data.get("congestion", 0.3),
            "port_wait_time_ratio": route_data.get("wait_ratio", 1.0),
        }
    
    def _get_risk_factors(self, route_data: Dict) -> List[Dict]:
        """Get contributing risk factors"""
        factors = []
        
        if route_data.get("storm_risk", 0) > 0.5:
            factors.append({"factor": "weather", "impact": "high", "description": "Storm conditions detected"})
        
        if route_data.get("congestion", 0) > 0.5:
            factors.append({"factor": "port_congestion", "impact": "high", "description": "Port congestion above normal"})
        
        if route_data.get("news_risk", 0) > 0.4:
            factors.append({"factor": "geopolitical", "impact": "medium", "description": "Elevated regional risk in news"})
        
        month = route_data.get("month", 6)
        if month in [8, 9, 10]:
            factors.append({"factor": "seasonal", "impact": "medium", "description": "Typhoon season"})
        
        return factors if factors else [{"factor": "none", "impact": "low", "description": "Normal conditions"}]
    
    def _get_recommendations(self, risk_level: str, route_data: Dict) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = []
        
        if risk_level == "critical":
            recommendations = [
                "Consider alternative routing",
                "Increase safety stock at destination",
                "Notify customers of potential delays",
                "Activate contingency plans"
            ]
        elif risk_level == "high":
            recommendations = [
                "Monitor conditions closely",
                "Prepare backup shipping options",
                "Review insurance coverage"
            ]
        elif risk_level == "medium":
            recommendations = [
                "Standard monitoring recommended",
                "No immediate action required"
            ]
        else:
            recommendations = [
                "Conditions favorable for transit",
                "Routine monitoring sufficient"
            ]
        
        return recommendations
    
    def _mock_prediction(self, route_data: Dict, error: str = None) -> Dict:
        """Return mock prediction when model unavailable"""
        return {
            "route_id": route_data.get("route_id", "TWKHH-USLAX"),
            "prediction": {
                "on_time_probability": 0.85,
                "delay_probability": 0.15,
                "predicted_delay_days": 0.5,
                "risk_level": "low",
                "confidence": 0.85
            },
            "factors": [{"factor": "mock", "impact": "low", "description": "Using fallback prediction"}],
            "recommendations": ["Model prediction service initializing"],
            "note": "Using fallback prediction" + (f": {error}" if error else "")
        }


# Singleton instance
prediction_service = RiskPredictionService()
