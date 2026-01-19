"""
Model Performance & Accuracy Tracking Service

This service tracks ML model performance over time, including:
- Prediction accuracy metrics (MAE, RMSE, MAPE)
- Classification metrics (Precision, Recall, F1)
- Confidence calibration
- Model drift detection
- Data quality monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import random
from dataclasses import dataclass, asdict
from enum import Enum


class MetricType(str, Enum):
    MAE = "mae"           # Mean Absolute Error
    RMSE = "rmse"         # Root Mean Square Error
    MAPE = "mape"         # Mean Absolute Percentage Error
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
    ACCURACY = "accuracy"
    AUC_ROC = "auc_roc"


@dataclass
class PredictionRecord:
    """Records a single prediction for accuracy tracking"""
    prediction_id: str
    timestamp: datetime
    route_id: str
    predicted_delay: float
    actual_delay: Optional[float]  # None until outcome is known
    predicted_risk: str
    actual_risk: Optional[str]
    confidence: float
    features_used: Dict[str, float]


@dataclass
class ModelMetrics:
    """Point-in-time model performance metrics"""
    timestamp: datetime
    window_size_hours: int
    
    # Regression metrics (delay prediction)
    mae: float
    rmse: float
    mape: float
    
    # Classification metrics (risk prediction)
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    
    # Calibration
    calibration_error: float
    overconfidence_rate: float
    
    # Data quality
    data_completeness: float
    feature_staleness_hours: float
    
    # Drift indicators
    feature_drift_score: float
    prediction_drift_score: float
    
    sample_size: int


class ModelPerformanceTracker:
    """
    Tracks and analyzes ML model performance over time.
    
    In production, this would connect to a metrics database (e.g., MLflow, 
    Prometheus) and track actual predictions vs outcomes.
    """
    
    def __init__(self):
        self.predictions: List[PredictionRecord] = []
        self.metrics_history: List[ModelMetrics] = []
        self._initialize_synthetic_history()
    
    def _initialize_synthetic_history(self):
        """Generate realistic historical metrics for demo"""
        base_date = datetime.utcnow() - timedelta(days=30)
        
        # Simulate metrics over last 30 days
        for day in range(30):
            timestamp = base_date + timedelta(days=day)
            
            # Simulate gradual improvement with some variance
            improvement_factor = 1 - (day * 0.005)  # Slight improvement over time
            noise = random.uniform(-0.05, 0.05)
            
            # Base metrics with realistic values
            base_mae = 1.8 * improvement_factor + noise
            base_precision = min(0.92, 0.85 + day * 0.002 + noise * 0.5)
            
            metrics = ModelMetrics(
                timestamp=timestamp,
                window_size_hours=24,
                
                # Regression metrics
                mae=max(0.5, base_mae),
                rmse=max(0.7, base_mae * 1.3),
                mape=max(5, 15 * improvement_factor + noise * 5),
                
                # Classification metrics
                precision=min(0.98, max(0.75, base_precision)),
                recall=min(0.95, max(0.70, base_precision - 0.03)),
                f1_score=min(0.96, max(0.72, base_precision - 0.015)),
                accuracy=min(0.94, max(0.78, base_precision + 0.02)),
                
                # Calibration
                calibration_error=max(0.02, 0.08 * improvement_factor + abs(noise) * 0.3),
                overconfidence_rate=max(0.05, 0.15 * improvement_factor + noise * 0.1),
                
                # Data quality
                data_completeness=min(0.99, 0.92 + day * 0.002),
                feature_staleness_hours=max(0.5, 4 - day * 0.1),
                
                # Drift
                feature_drift_score=max(0.01, 0.05 + noise * 0.05),
                prediction_drift_score=max(0.01, 0.04 + noise * 0.04),
                
                sample_size=random.randint(150, 300)
            )
            
            self.metrics_history.append(metrics)
        
        # Generate some sample predictions with outcomes
        self._generate_sample_predictions()
    
    def _generate_sample_predictions(self):
        """Generate sample prediction records for demo"""
        routes = ["SHA-LAX", "SHA-LGB", "HKG-LAX", "SGP-SEA", "TPE-LAX", "NGB-OAK"]
        risk_levels = ["low", "medium", "high", "critical"]
        
        for i in range(100):
            timestamp = datetime.utcnow() - timedelta(hours=random.randint(1, 720))
            predicted_delay = random.uniform(0, 10)
            # Actual delay correlates with predicted but has noise
            actual_delay = predicted_delay + random.gauss(0, 1.5)
            actual_delay = max(0, actual_delay)
            
            predicted_risk = random.choice(risk_levels)
            # Actual risk often matches, sometimes doesn't
            actual_risk = predicted_risk if random.random() > 0.15 else random.choice(risk_levels)
            
            record = PredictionRecord(
                prediction_id=f"pred_{i:04d}",
                timestamp=timestamp,
                route_id=random.choice(routes),
                predicted_delay=round(predicted_delay, 2),
                actual_delay=round(actual_delay, 2),
                predicted_risk=predicted_risk,
                actual_risk=actual_risk,
                confidence=random.uniform(0.6, 0.95),
                features_used={
                    "weather_severity": random.uniform(0, 1),
                    "port_congestion": random.uniform(0.3, 0.9),
                    "historical_delay": random.uniform(0, 5)
                }
            )
            self.predictions.append(record)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get the most recent model performance metrics"""
        if self.metrics_history:
            latest = self.metrics_history[-1]
            return asdict(latest)
        return {}
    
    def get_metrics_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics for trend analysis"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        filtered = [m for m in self.metrics_history if m.timestamp >= cutoff]
        return [asdict(m) for m in filtered]
    
    def get_accuracy_trends(self) -> Dict[str, Any]:
        """Get accuracy trends over time for visualization"""
        history = self.metrics_history[-30:]  # Last 30 data points
        
        return {
            "timestamps": [m.timestamp.isoformat() for m in history],
            "mae": [round(m.mae, 3) for m in history],
            "rmse": [round(m.rmse, 3) for m in history],
            "precision": [round(m.precision, 3) for m in history],
            "recall": [round(m.recall, 3) for m in history],
            "f1_score": [round(m.f1_score, 3) for m in history],
            "accuracy": [round(m.accuracy, 3) for m in history],
        }
    
    def get_calibration_data(self) -> Dict[str, Any]:
        """
        Get data for calibration plot (predicted probability vs actual frequency).
        This shows if the model's confidence scores are well-calibrated.
        """
        # Bucket predictions by confidence level
        buckets = {i/10: {"count": 0, "correct": 0} for i in range(1, 11)}
        
        for pred in self.predictions:
            if pred.actual_risk is None:
                continue
            
            # Find bucket
            bucket_key = round(pred.confidence, 1)
            bucket_key = min(1.0, max(0.1, bucket_key))
            bucket_key = round(bucket_key, 1)
            
            if bucket_key in buckets:
                buckets[bucket_key]["count"] += 1
                if pred.predicted_risk == pred.actual_risk:
                    buckets[bucket_key]["correct"] += 1
        
        # Calculate actual accuracy per bucket
        calibration_points = []
        for conf, data in sorted(buckets.items()):
            if data["count"] > 0:
                actual_accuracy = data["correct"] / data["count"]
                calibration_points.append({
                    "predicted_confidence": conf,
                    "actual_accuracy": round(actual_accuracy, 3),
                    "sample_count": data["count"]
                })
        
        # Calculate Expected Calibration Error (ECE)
        ece = 0
        total_samples = sum(p["sample_count"] for p in calibration_points)
        for point in calibration_points:
            weight = point["sample_count"] / total_samples if total_samples > 0 else 0
            ece += weight * abs(point["predicted_confidence"] - point["actual_accuracy"])
        
        return {
            "calibration_curve": calibration_points,
            "expected_calibration_error": float(round(ece, 4)),
            "is_well_calibrated": bool(ece < 0.1),
            "interpretation": self._interpret_calibration(ece)
        }
    
    def _interpret_calibration(self, ece: float) -> str:
        if ece < 0.05:
            return "Excellent calibration - model confidence closely matches actual accuracy"
        elif ece < 0.10:
            return "Good calibration - model is reasonably well-calibrated"
        elif ece < 0.15:
            return "Fair calibration - some overconfidence or underconfidence detected"
        else:
            return "Poor calibration - model confidence does not reflect actual accuracy"
    
    def get_prediction_vs_actual(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent predictions vs actual outcomes for scatter plot"""
        # Filter predictions that have outcomes
        completed = [p for p in self.predictions if p.actual_delay is not None]
        # Sort by timestamp, most recent first
        completed.sort(key=lambda x: x.timestamp, reverse=True)
        
        recent = completed[:limit]
        
        return {
            "predictions": [{
                "id": p.prediction_id,
                "route": p.route_id,
                "predicted": p.predicted_delay,
                "actual": p.actual_delay,
                "error": round(abs(p.predicted_delay - p.actual_delay), 2),
                "within_1_day": bool(abs(p.predicted_delay - p.actual_delay) < 1),
                "confidence": float(p.confidence),
                "timestamp": p.timestamp.isoformat()
            } for p in recent],
            "summary": {
                "total": len(recent),
                "within_1_day": int(sum(1 for p in recent if abs(p.predicted_delay - p.actual_delay) < 1)),
                "within_2_days": int(sum(1 for p in recent if abs(p.predicted_delay - p.actual_delay) < 2)),
                "avg_error": float(round(np.mean([abs(p.predicted_delay - p.actual_delay) for p in recent]), 2)) if recent else 0.0
            }
        }
    
    def get_drift_analysis(self) -> Dict[str, Any]:
        """Analyze model and data drift"""
        history = self.metrics_history[-14:]  # Last 2 weeks
        
        if len(history) < 7:
            return {"status": "insufficient_data"}
        
        # Compare recent week to previous week
        recent = history[-7:]
        previous = history[-14:-7]
        
        # Calculate average metrics for each period
        def avg(metrics: List[ModelMetrics], attr: str) -> float:
            return np.mean([getattr(m, attr) for m in metrics])
        
        feature_drift_change = avg(recent, 'feature_drift_score') - avg(previous, 'feature_drift_score')
        pred_drift_change = avg(recent, 'prediction_drift_score') - avg(previous, 'prediction_drift_score')
        accuracy_change = avg(recent, 'accuracy') - avg(previous, 'accuracy')
        
        # Determine drift status
        drift_detected = bool(feature_drift_change > 0.05 or pred_drift_change > 0.05 or accuracy_change < -0.05)
        
        return {
            "status": "drift_detected" if drift_detected else "stable",
            "feature_drift": {
                "current": float(round(avg(recent, 'feature_drift_score'), 3)),
                "previous": float(round(avg(previous, 'feature_drift_score'), 3)),
                "change": float(round(feature_drift_change, 4)),
                "alert": bool(feature_drift_change > 0.05)
            },
            "prediction_drift": {
                "current": float(round(avg(recent, 'prediction_drift_score'), 3)),
                "previous": float(round(avg(previous, 'prediction_drift_score'), 3)),
                "change": float(round(pred_drift_change, 4)),
                "alert": bool(pred_drift_change > 0.05)
            },
            "accuracy_trend": {
                "current": float(round(avg(recent, 'accuracy'), 3)),
                "previous": float(round(avg(previous, 'accuracy'), 3)),
                "change": float(round(accuracy_change, 4)),
                "alert": bool(accuracy_change < -0.05)
            },
            "recommendation": self._get_drift_recommendation(
                feature_drift_change, pred_drift_change, accuracy_change
            )
        }
    
    def _get_drift_recommendation(self, feat_drift: float, pred_drift: float, acc_change: float) -> str:
        if feat_drift > 0.1:
            return "🚨 Significant feature drift detected. Recommend retraining with recent data."
        elif pred_drift > 0.1:
            return "⚠️ Prediction distribution has shifted. Investigate recent data patterns."
        elif acc_change < -0.1:
            return "📉 Model accuracy declining. Consider model refresh or feature engineering."
        elif feat_drift > 0.05 or pred_drift > 0.05:
            return "📊 Minor drift detected. Continue monitoring and prepare for potential retrain."
        else:
            return "✅ Model performance is stable. No immediate action required."
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """Get data quality metrics"""
        latest = self.metrics_history[-1] if self.metrics_history else None
        
        if not latest:
            return {"status": "no_data"}
        
        # Feature-level quality (simulated)
        features = {
            "weather_data": {
                "completeness": 0.98,
                "freshness_minutes": 15,
                "quality_score": 0.95
            },
            "port_congestion": {
                "completeness": 0.92,
                "freshness_minutes": 60,
                "quality_score": 0.88
            },
            "ais_vessel_data": {
                "completeness": 0.96,
                "freshness_minutes": 5,
                "quality_score": 0.94
            },
            "news_sentiment": {
                "completeness": 0.85,
                "freshness_minutes": 120,
                "quality_score": 0.82
            },
            "historical_delays": {
                "completeness": 0.99,
                "freshness_minutes": 1440,  # Daily update
                "quality_score": 0.97
            }
        }
        
        overall_quality = float(np.mean([f["quality_score"] for f in features.values()]))
        
        return {
            "overall_quality_score": float(round(overall_quality, 3)),
            "data_completeness": float(round(latest.data_completeness, 3)),
            "feature_staleness_hours": float(round(latest.feature_staleness_hours, 2)),
            "features": features,
            "quality_status": "good" if overall_quality > 0.9 else "fair" if overall_quality > 0.8 else "poor",
            "recommendations": self._get_quality_recommendations(features)
        }
    
    def _get_quality_recommendations(self, features: Dict) -> List[str]:
        recommendations = []
        for name, data in features.items():
            if data["completeness"] < 0.90:
                recommendations.append(f"Improve {name} data collection - currently {data['completeness']*100:.0f}% complete")
            if data["quality_score"] < 0.85:
                recommendations.append(f"Review {name} data pipeline - quality score below threshold")
        return recommendations if recommendations else ["All data sources meeting quality standards"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary"""
        current = self.get_current_metrics()
        trends = self.get_accuracy_trends()
        calibration = self.get_calibration_data()
        drift = self.get_drift_analysis()
        quality = self.get_data_quality_report()
        pred_actual = self.get_prediction_vs_actual(50)
        
        # Calculate overall health score
        health_score = self._calculate_health_score(current, calibration, drift, quality)
        
        return {
            "overall_health": {
                "score": health_score,
                "status": "excellent" if health_score > 90 else "good" if health_score > 75 else "fair" if health_score > 60 else "needs_attention",
                "last_updated": datetime.utcnow().isoformat()
            },
            "current_metrics": current,
            "trends": trends,
            "calibration": calibration,
            "drift_analysis": drift,
            "data_quality": quality,
            "prediction_vs_actual": pred_actual
        }
    
    def _calculate_health_score(self, metrics: Dict, calibration: Dict, drift: Dict, quality: Dict) -> int:
        """Calculate overall model health score (0-100)"""
        score = 100
        
        # Accuracy penalties
        if metrics.get('accuracy', 0) < 0.9:
            score -= (0.9 - metrics['accuracy']) * 100
        
        # Calibration penalties
        if calibration.get('expected_calibration_error', 0) > 0.1:
            score -= 10
        
        # Drift penalties
        if drift.get('status') == 'drift_detected':
            score -= 15
        
        # Data quality penalties
        if quality.get('overall_quality_score', 0) < 0.9:
            score -= 10
        
        return max(0, min(100, int(score)))


# Singleton instance
_tracker: Optional[ModelPerformanceTracker] = None

def get_performance_tracker() -> ModelPerformanceTracker:
    global _tracker
    if _tracker is None:
        _tracker = ModelPerformanceTracker()
    return _tracker
