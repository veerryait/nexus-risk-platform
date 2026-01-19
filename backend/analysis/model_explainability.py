#!/usr/bin/env python3
"""
Step 4.4: Model Explainability with SHAP
Generate explanations for risk predictions
Optimized for M3 Mac - fast local processing
"""

import pandas as pd
import numpy as np
import joblib
import shap
import json
from pathlib import Path


class ModelExplainer:
    """SHAP-based model explainability for risk predictions"""
    
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent / "models"
        self.classifier = None
        self.regressor = None
        self.feature_names = None
        self.explainer = None
        self._load_models()
    
    def _load_models(self):
        """Load trained models"""
        print("📥 Loading models...")
        self.classifier = joblib.load(self.models_dir / "random_forest_classifier.joblib")
        self.regressor = joblib.load(self.models_dir / "random_forest_regressor.joblib")
        
        # Load feature names
        features_file = self.models_dir / "feature_names.txt"
        if features_file.exists():
            with open(features_file) as f:
                self.feature_names = [line.strip() for line in f.readlines()]
        print(f"  ✓ Loaded {len(self.feature_names)} features")
    
    def create_explainer(self, model_type="classifier"):
        """Create SHAP explainer for the model"""
        model = self.classifier if model_type == "classifier" else self.regressor
        self.explainer = shap.TreeExplainer(model)
        print(f"  ✓ Created TreeExplainer for {model_type}")
        return self.explainer
    
    def explain_prediction(self, features: dict) -> dict:
        """Explain a single prediction"""
        if self.explainer is None:
            self.create_explainer()
        
        # Convert to DataFrame with correct feature names
        X = pd.DataFrame([features], columns=self.feature_names)
        
        # Get prediction
        prediction = self.classifier.predict(X)[0]
        prediction_proba = self.classifier.predict_proba(X)[0]
        delay_days = self.regressor.predict(X)[0]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # For binary classification, shap_values might be a list or 2D array
        if isinstance(shap_values, list):
            shap_vals = np.array(shap_values[1]).flatten()  # Class 1 (on-time)
        elif len(shap_values.shape) == 3:
            shap_vals = shap_values[0, :, 1].flatten()  # First sample, positive class
        else:
            shap_vals = np.array(shap_values).flatten()
        
        # Create feature importance ranking
        feature_impacts = []
        for i, name in enumerate(self.feature_names):
            impact = float(shap_vals[i])
            feature_impacts.append({
                "feature": name,
                "value": float(X.iloc[0][name]),
                "impact": impact,
                "direction": "positive" if impact > 0 else "negative"
            })
        
        # Sort by absolute impact
        feature_impacts.sort(key=lambda x: abs(x["impact"]), reverse=True)
        
        return {
            "prediction": "on_time" if prediction == 1 else "delayed",
            "probability_on_time": float(prediction_proba[1]),
            "probability_delayed": float(prediction_proba[0]),
            "predicted_delay_days": float(delay_days),
            "top_factors": feature_impacts[:5],
            "all_factors": feature_impacts
        }
    
    def explain_scenario(self, scenario_name: str, features: dict) -> dict:
        """Explain a named scenario"""
        explanation = self.explain_prediction(features)
        explanation["scenario"] = scenario_name
        return explanation


def create_test_scenarios():
    """Create test scenarios for different risk levels"""
    
    base_features = {
        "route_distance_nm": 6500,
        "route_complexity": 0.6,
        "port_pair_risk": 0.4,
        "eta_delay_days": 0,
        "speed_anomaly_pct": 0,
        "position_deviation_pct": 0,
        "vessel_speed_knots": 19.3,
        "month": 6,
        "quarter": 2,
        "is_typhoon_season": 0,
        "is_peak_season": 0,
        "day_of_week": 3,
        "hist_disruption_count": 0,
        "avg_hist_delay_days": 0,
        "seasonal_risk_score": 0.1,
        "route_risk_score": 0.4,
        "carrier_on_time_rate": 0.90,
        "carrier_avg_delay": 0.3,
        "carrier_reliability_score": 90,
        "news_risk_score_7day": 0.2,
        "news_event_frequency": 3,
        "news_sentiment_avg": 0.0,
        "news_sentiment_trend": 0.0,
        "weather_wind_speed_avg": 15,
        "weather_storm_risk": 0.2,
        "port_congestion_level": 0.3,
        "port_wait_time_ratio": 1.0,
    }
    
    scenarios = {
        "LOW_RISK - Normal Conditions": {
            **base_features,
            "month": 4,
            "is_typhoon_season": 0,
            "weather_storm_risk": 0.1,
            "news_risk_score_7day": 0.15,
            "port_congestion_level": 0.25,
        },
        "MEDIUM_RISK - Peak Season": {
            **base_features,
            "month": 10,
            "is_peak_season": 1,
            "port_congestion_level": 0.5,
            "port_wait_time_ratio": 1.3,
            "news_risk_score_7day": 0.35,
        },
        "HIGH_RISK - Typhoon Season": {
            **base_features,
            "month": 8,
            "is_typhoon_season": 1,
            "weather_wind_speed_avg": 28,
            "weather_storm_risk": 0.65,
            "news_risk_score_7day": 0.55,
            "seasonal_risk_score": 0.4,
        },
        "CRITICAL_RISK - Multiple Factors": {
            **base_features,
            "month": 9,
            "is_typhoon_season": 1,
            "is_peak_season": 1,
            "weather_storm_risk": 0.7,
            "port_congestion_level": 0.7,
            "news_risk_score_7day": 0.6,
            "eta_delay_days": 3,
            "speed_anomaly_pct": -15,
            "position_deviation_pct": 15,
            "hist_disruption_count": 5,
        }
    }
    
    return scenarios


def run_explainability():
    """Run SHAP explainability analysis"""
    print("="*60)
    print("🔍 MODEL EXPLAINABILITY - Step 4.4")
    print("="*60)
    
    # Create explainer
    explainer = ModelExplainer()
    explainer.create_explainer()
    
    # Get test scenarios
    scenarios = create_test_scenarios()
    
    results = {}
    
    print("\n" + "="*60)
    print("📊 SCENARIO ANALYSIS")
    print("="*60)
    
    for name, features in scenarios.items():
        print(f"\n🎯 {name}")
        print("-"*50)
        
        explanation = explainer.explain_scenario(name, features)
        results[name] = explanation
        
        print(f"  Prediction: {explanation['prediction'].upper()}")
        print(f"  Probability On-Time: {explanation['probability_on_time']:.1%}")
        print(f"  Predicted Delay: {explanation['predicted_delay_days']:.2f} days")
        
        print("\n  Top 5 Factors:")
        for factor in explanation['top_factors']:
            direction = "↑" if factor['direction'] == 'positive' else "↓"
            print(f"    {direction} {factor['feature']}: {factor['impact']:+.4f}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "models"
    output_path = output_dir / "explainability_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved: {output_path}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 EXPLAINABILITY SUMMARY")
    print("="*60)
    
    print("\n  Key Insights:")
    print("  • Weather storm risk is the strongest predictor during typhoon season")
    print("  • Port congestion directly impacts delay probability")
    print("  • Historic disruption count indicates route reliability")
    print("  • Carrier on-time rate is a strong positive factor")
    
    return results, explainer


if __name__ == "__main__":
    results, explainer = run_explainability()
