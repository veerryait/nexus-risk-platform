"""
Vessel Anomaly Detection - ML Inference Service (v2.0)
Uses trained Random Forest Classifier with optimized threshold
"""

import os
import numpy as np
import joblib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# Model paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
ISO_FOREST_PATH = os.path.join(MODEL_DIR, 'anomaly_isolation_forest.joblib')
CLASSIFIER_PATH = os.path.join(MODEL_DIR, 'anomaly_classifier.joblib')
SCALER_PATH = os.path.join(MODEL_DIR, 'anomaly_scaler.joblib')
METADATA_PATH = os.path.join(MODEL_DIR, 'model_metadata.json')


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyPrediction:
    is_anomaly: bool
    anomaly_score: float
    severity: AnomalySeverity
    confidence: float
    contributing_factors: List[str]


class MLAnomalyDetector:
    """ML-based anomaly detector using trained Random Forest + Isolation Forest"""
    
    def __init__(self):
        self.classifier = None
        self.iso_forest = None
        self.scaler = None
        self.metadata = None
        self.is_loaded = False
        self.threshold = 0.5
        self.feature_cols = [
            'speed', 'heading_change', 'distance_from_route', 'time_since_update',
            'acceleration', 'latitude', 'longitude', 'vessel_type', 'hour_of_day',
            'port_proximity', 'traffic_density', 'weather_severity',
            'historical_deviation', 'course_over_ground_diff'
        ]
        self._load_model()
    
    def _load_model(self):
        """Load trained models from disk"""
        try:
            if os.path.exists(CLASSIFIER_PATH) and os.path.exists(SCALER_PATH):
                self.classifier = joblib.load(CLASSIFIER_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                
                if os.path.exists(ISO_FOREST_PATH):
                    self.iso_forest = joblib.load(ISO_FOREST_PATH)
                
                if os.path.exists(METADATA_PATH):
                    with open(METADATA_PATH, 'r') as f:
                        self.metadata = json.load(f)
                    self.threshold = self.metadata.get('optimal_threshold', 0.5)
                
                self.is_loaded = True
                logger.info("✓ ML Anomaly Detection v2.0 models loaded successfully")
            else:
                logger.warning("ML models not found. Run training script first.")
                self.is_loaded = False
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}")
            self.is_loaded = False
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        if not self.is_loaded:
            return {
                "status": "not_loaded",
                "message": "Model not trained yet. Run: python -m app.ml.train_anomaly_model"
            }
        
        return {
            "status": "loaded",
            "model_type": self.metadata.get("model_type", "RandomForest + IsolationForest"),
            "version": self.metadata.get("version", "2.0.0"),
            "trained_at": self.metadata.get("trained_at", "unknown"),
            "optimal_threshold": self.threshold,
            "metrics": self.metadata.get("metrics", {}),
            "features": self.feature_cols,
            "improvements": self.metadata.get("improvements", [])
        }
    
    def prepare_features(
        self,
        speed: float,
        heading: float,
        lat: float,
        lng: float,
        distance_from_route: float = 0,
        time_since_update: float = 5,
        prev_heading: float = None,
        prev_speed: float = None,
        vessel_type: int = 0,
        hour_of_day: int = 12,
        port_proximity: float = 200,
        traffic_density: float = 0.2,
        weather_severity: float = 0.1,
        historical_deviation: float = 0.1
    ) -> np.ndarray:
        """Prepare 14-feature vector for prediction"""
        # Calculate heading change
        heading_change = 0
        if prev_heading is not None:
            heading_change = abs(heading - prev_heading)
            if heading_change > 180:
                heading_change = 360 - heading_change
        
        # Calculate acceleration
        acceleration = 0
        if prev_speed is not None:
            acceleration = speed - prev_speed
        
        # Course over ground difference (estimated)
        cog_diff = abs(heading_change) * 0.5
        
        features = np.array([
            speed,
            heading_change,
            distance_from_route,
            time_since_update,
            acceleration,
            lat,
            lng,
            vessel_type,
            hour_of_day,
            port_proximity,
            traffic_density,
            weather_severity,
            historical_deviation,
            cog_diff
        ]).reshape(1, -1)
        
        return features
    
    def predict(
        self,
        speed: float,
        heading: float,
        lat: float,
        lng: float,
        distance_from_route: float = 0,
        time_since_update: float = 5,
        prev_heading: float = None,
        prev_speed: float = None,
        vessel_type: int = 0,
        port_proximity: float = 200
    ) -> AnomalyPrediction:
        """Predict if vessel behavior is anomalous using trained classifier"""
        if not self.is_loaded:
            return self._rule_based_prediction(speed, heading, lat, lng, distance_from_route)
        
        try:
            from datetime import datetime
            hour_of_day = datetime.now().hour
            
            features = self.prepare_features(
                speed=speed,
                heading=heading,
                lat=lat,
                lng=lng,
                distance_from_route=distance_from_route,
                time_since_update=time_since_update,
                prev_heading=prev_heading,
                prev_speed=prev_speed,
                vessel_type=vessel_type,
                hour_of_day=hour_of_day,
                port_proximity=port_proximity
            )
            
            features_scaled = self.scaler.transform(features)
            
            # Get probability from classifier
            proba = self.classifier.predict_proba(features_scaled)[0][1]
            
            # Apply optimized threshold
            is_anomaly = proba >= self.threshold
            
            # Determine severity based on probability
            if proba >= 0.98:
                severity = AnomalySeverity.CRITICAL
            elif proba >= 0.95:
                severity = AnomalySeverity.HIGH
            elif proba >= 0.90:
                severity = AnomalySeverity.MEDIUM
            else:
                severity = AnomalySeverity.LOW
            
            factors = self._identify_factors(speed, heading, distance_from_route, time_since_update)
            
            # Confidence from model metrics
            confidence = self.metadata.get("metrics", {}).get("precision", 0.95)
            
            return AnomalyPrediction(
                is_anomaly=bool(is_anomaly),
                anomaly_score=round(float(proba), 3),
                severity=severity,
                confidence=round(float(confidence), 3),
                contributing_factors=factors
            )
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._rule_based_prediction(speed, heading, lat, lng, distance_from_route)
    
    def _identify_factors(
        self,
        speed: float,
        heading: float,
        distance_from_route: float,
        time_since_update: float
    ) -> List[str]:
        """Identify contributing factors to anomaly"""
        factors = []
        
        if speed < 3:
            factors.append("Vessel stopped/drifting")
        elif speed < 8:
            factors.append("Unusually slow speed")
        elif speed > 25:
            factors.append("Excessive speed")
        
        if distance_from_route > 300:
            factors.append("Major route deviation (>300nm)")
        elif distance_from_route > 150:
            factors.append("Significant route deviation")
        elif distance_from_route > 80:
            factors.append("Moderate route deviation")
        
        if time_since_update > 60:
            factors.append("Long AIS signal gap (>1hr)")
        elif time_since_update > 30:
            factors.append("AIS signal gap detected")
        
        return factors if factors else ["Normal behavior patterns"]
    
    def _rule_based_prediction(
        self,
        speed: float,
        heading: float,
        lat: float,
        lng: float,
        distance_from_route: float
    ) -> AnomalyPrediction:
        """Fallback rule-based detection"""
        factors = []
        score = 0
        
        if speed < 3:
            score += 0.4
            factors.append("Vessel stationary")
        elif speed > 26:
            score += 0.3
            factors.append("Excessive speed")
        
        if distance_from_route > 250:
            score += 0.5
            factors.append("Major route deviation")
        elif distance_from_route > 120:
            score += 0.25
            factors.append("Route deviation")
        
        score = min(score, 1.0)
        is_anomaly = score > 0.4
        
        if score >= 0.8:
            severity = AnomalySeverity.CRITICAL
        elif score >= 0.6:
            severity = AnomalySeverity.HIGH
        elif score >= 0.4:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW
        
        return AnomalyPrediction(
            is_anomaly=is_anomaly,
            anomaly_score=round(score, 3),
            severity=severity,
            confidence=0.7,
            contributing_factors=factors if factors else ["Normal behavior"]
        )
    
    def batch_predict(self, vessels: List[Dict]) -> List[Dict]:
        """Predict anomalies for multiple vessels"""
        results = []
        
        for vessel in vessels:
            pos = vessel.get("position", {})
            prediction = self.predict(
                speed=float(vessel.get("speed", 0)),
                heading=float(vessel.get("heading", 0)),
                lat=float(pos.get("lat", 0)),
                lng=float(pos.get("lng", 0)),
                distance_from_route=0,
                time_since_update=5
            )
            
            results.append({
                "vessel_id": str(vessel.get("id")),
                "vessel_name": vessel.get("name"),
                "is_anomaly": bool(prediction.is_anomaly),
                "anomaly_score": float(prediction.anomaly_score),
                "severity": prediction.severity.value,
                "confidence": float(prediction.confidence),
                "factors": prediction.contributing_factors
            })
        
        return results


# Singleton instance
_detector = None

def get_detector() -> MLAnomalyDetector:
    """Get or create singleton detector instance"""
    global _detector
    if _detector is None:
        _detector = MLAnomalyDetector()
    return _detector
