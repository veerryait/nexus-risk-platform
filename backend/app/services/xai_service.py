"""
Explainable AI (XAI) Service
Generates plain English explanations for all model predictions
Makes AI decisions transparent and understandable
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import random

# Try to use Gemini for enhanced explanations
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class ExplainableAI:
    """
    Generates human-readable explanations for AI predictions
    Uses rule-based explanations + optional LLM enhancement
    """
    
    def __init__(self):
        self.gemini_model = None
        if HAS_GEMINI:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            except Exception:
                pass
    
    def explain_delay_prediction(
        self,
        route_id: str,
        origin: str,
        destination: str,
        predicted_delay: float,
        risk_level: str,
        features: Dict[str, Any]
    ) -> Dict:
        """
        Explain why a specific delay was predicted for a route
        
        Args:
            route_id: Route identifier
            origin/destination: Port names
            predicted_delay: Predicted delay in days
            risk_level: low/medium/high/critical
            features: Input features used for prediction
            
        Returns:
            Explanation with causes, factors, and recommendations
        """
        # Analyze features to determine primary causes
        causes = []
        contributing_factors = []
        recommendations = []
        
        # Weather analysis
        weather_risk = features.get('weather_risk', 0)
        if weather_risk > 0.7:
            causes.append({
                "type": "weather",
                "icon": "🌀",
                "title": "Severe Weather Alert",
                "description": f"Active weather system detected along route with {int(weather_risk * 100)}% risk impact",
                "impact": "high"
            })
            recommendations.append("Consider delaying departure by 24-48 hours until weather clears")
        elif weather_risk > 0.4:
            contributing_factors.append({
                "type": "weather",
                "icon": "🌧️",
                "description": f"Moderate weather conditions ({int(weather_risk * 100)}% risk)",
                "impact": "medium"
            })
        
        # Port congestion
        origin_congestion = features.get('origin_congestion', 0)
        dest_congestion = features.get('dest_congestion', 0)
        
        if dest_congestion > 0.8:
            causes.append({
                "type": "congestion",
                "icon": "🚢",
                "title": "Destination Port Congested",
                "description": f"{destination} operating at {int(dest_congestion * 100)}% capacity - expect berthing delays",
                "impact": "high"
            })
            recommendations.append(f"Book berthing slot in advance at {destination}")
        elif dest_congestion > 0.6:
            contributing_factors.append({
                "type": "congestion",
                "icon": "⚓",
                "description": f"{destination} at {int(dest_congestion * 100)}% capacity",
                "impact": "medium"
            })
        
        if origin_congestion > 0.7:
            contributing_factors.append({
                "type": "congestion",
                "icon": "⚓",
                "description": f"{origin} origin port congestion at {int(origin_congestion * 100)}%",
                "impact": "medium"
            })
        
        # Geopolitical risk
        geopolitical_risk = features.get('geopolitical_risk', 0)
        if geopolitical_risk > 0.6:
            causes.append({
                "type": "geopolitical",
                "icon": "⚠️",
                "title": "Geopolitical Risk Detected",
                "description": "Military exercises or political tensions detected along route corridor",
                "impact": "high"
            })
            recommendations.append("Monitor situation closely and prepare contingency routing")
        elif geopolitical_risk > 0.3:
            contributing_factors.append({
                "type": "geopolitical",
                "icon": "📰",
                "description": "Elevated regional tensions reported in news",
                "impact": "medium"
            })
        
        # Distance/transit time factor
        distance = features.get('distance_nm', 0)
        if distance > 5000:
            contributing_factors.append({
                "type": "distance",
                "icon": "📏",
                "description": f"Long-haul route ({int(distance):,} nautical miles) increases exposure to delays",
                "impact": "low"
            })
        
        # Season factor
        month = datetime.now().month
        if month in [7, 8, 9, 10]:  # Typhoon season
            contributing_factors.append({
                "type": "seasonal",
                "icon": "📅",
                "description": "Currently in Pacific typhoon season (higher storm probability)",
                "impact": "medium"
            })
        
        # If no major causes found, add default explanation
        if not causes:
            if predicted_delay > 0:
                causes.append({
                    "type": "baseline",
                    "icon": "📊",
                    "title": "Normal Transit Variance",
                    "description": "Minor delays expected due to typical operational factors",
                    "impact": "low"
                })
        
        # Default recommendation if none added
        if not recommendations:
            if risk_level in ['high', 'critical']:
                recommendations.append("Monitor route conditions and prepare backup plans")
            else:
                recommendations.append("No immediate action required - continue as planned")
        
        # Build summary sentence
        if causes:
            primary_cause = causes[0]['title']
            summary = f"Delay of {predicted_delay:.1f} days predicted primarily due to {primary_cause.lower()}."
        else:
            summary = f"Minor delay of {predicted_delay:.1f} days expected from normal transit variance."
        
        return {
            "route_id": route_id,
            "summary": summary,
            "predicted_delay_days": predicted_delay,
            "risk_level": risk_level,
            "confidence": self._calculate_confidence(features),
            "primary_causes": causes,
            "contributing_factors": contributing_factors,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
            "explanation_type": "rule_based"
        }
    
    def explain_risk_score(
        self,
        entity_type: str,  # "route", "port", "vessel"
        entity_name: str,
        risk_score: float,
        factors: Dict[str, float]
    ) -> Dict:
        """
        Explain why an entity has a certain risk score
        """
        # Sort factors by impact
        sorted_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)
        
        explanations = []
        for factor_name, factor_value in sorted_factors[:5]:
            impact = "increases" if factor_value > 0 else "decreases"
            impact_level = "significantly" if abs(factor_value) > 0.3 else "moderately" if abs(factor_value) > 0.15 else "slightly"
            
            # Human-readable factor names
            factor_display = {
                "weather_risk": "Weather conditions",
                "congestion_level": "Port congestion",
                "geopolitical_index": "Geopolitical tensions",
                "distance_factor": "Route distance",
                "seasonal_risk": "Seasonal patterns",
                "historical_delays": "Historical performance",
                "vessel_age": "Vessel reliability",
                "port_efficiency": "Port efficiency"
            }.get(factor_name, factor_name.replace("_", " ").title())
            
            explanations.append({
                "factor": factor_display,
                "impact": impact,
                "level": impact_level,
                "contribution": round(abs(factor_value) * 100, 1)
            })
        
        # Generate plain English summary
        if risk_score > 75:
            risk_word = "Critical"
            emoji = "🔴"
        elif risk_score > 55:
            risk_word = "Elevated"
            emoji = "🟠"
        elif risk_score > 35:
            risk_word = "Moderate"
            emoji = "🟡"
        else:
            risk_word = "Low"
            emoji = "🟢"
        
        top_factor = explanations[0] if explanations else None
        if top_factor:
            summary = f"{emoji} {risk_word} risk ({risk_score:.0f}%) - {top_factor['factor']} {top_factor['impact']} risk {top_factor['level']}"
        else:
            summary = f"{emoji} {risk_word} risk level at {risk_score:.0f}%"
        
        return {
            "entity_type": entity_type,
            "entity_name": entity_name,
            "risk_score": risk_score,
            "summary": summary,
            "factor_breakdown": explanations,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def explain_cascade_effect(
        self,
        source_port: str,
        affected_ports: List[Dict],
        propagation_depth: int,
        total_impact: float
    ) -> Dict:
        """
        Explain how a failure cascades through the network
        """
        # Categorize affected ports by severity
        critical = [p for p in affected_ports if p.get('cascade_risk_increase', 0) > 60]
        high = [p for p in affected_ports if 30 < p.get('cascade_risk_increase', 0) <= 60]
        moderate = [p for p in affected_ports if 10 < p.get('cascade_risk_increase', 0) <= 30]
        
        # Build narrative explanation
        narrative_parts = []
        
        narrative_parts.append(f"🚨 **Cascade Analysis for {source_port} Failure**")
        narrative_parts.append("")
        
        if critical:
            port_names = ", ".join([p['port_code'] for p in critical[:3]])
            narrative_parts.append(f"⛔ **Critical Impact**: {len(critical)} ports severely affected ({port_names})")
            narrative_parts.append("   These ports have direct shipping connections and will experience immediate disruption.")
        
        if high:
            port_names = ", ".join([p['port_code'] for p in high[:3]])
            narrative_parts.append(f"🟠 **High Impact**: {len(high)} ports significantly affected ({port_names})")
            narrative_parts.append("   Secondary connections will see cargo rerouting within 24-48 hours.")
        
        if moderate:
            narrative_parts.append(f"🟡 **Moderate Impact**: {len(moderate)} ports affected by ripple effects")
            narrative_parts.append("   These ports may see increased traffic from diverted vessels.")
        
        narrative_parts.append("")
        narrative_parts.append(f"📊 **Network Analysis**:")
        narrative_parts.append(f"   • Cascade spreads {propagation_depth} connections deep into the network")
        narrative_parts.append(f"   • Total impact score: {total_impact:.0f} (higher = more disruption)")
        narrative_parts.append(f"   • Estimated recovery time: {propagation_depth * 2}-{propagation_depth * 4} days")
        
        # Recommendations
        recommendations = []
        if critical:
            recommendations.append(f"Immediately reroute shipments away from {critical[0]['port_code']}")
        if len(affected_ports) > 5:
            recommendations.append("Alert all customers with shipments in the Pacific region")
        recommendations.append("Activate contingency routing through unaffected corridors")
        
        return {
            "source_port": source_port,
            "narrative": "\n".join(narrative_parts),
            "impact_summary": {
                "critical_ports": len(critical),
                "high_impact_ports": len(high),
                "moderate_impact_ports": len(moderate),
                "total_affected": len([p for p in affected_ports if p.get('cascade_risk_increase', 0) > 0])
            },
            "propagation_depth": propagation_depth,
            "recommendations": recommendations,
            "explanation_type": "cascade_analysis"
        }
    
    def explain_weather_impact(
        self,
        weather_system: Dict,
        affected_routes: List[str]
    ) -> Dict:
        """
        Explain how weather affects shipping routes
        """
        system_type = weather_system.get('type', 'storm')
        intensity = weather_system.get('intensity', 'moderate')
        name = weather_system.get('name', 'Weather System')
        
        # Impact descriptions by type
        type_impacts = {
            'typhoon': {
                'description': f"Typhoon {name} is generating dangerous sea conditions with high winds and heavy swells",
                'icon': '🌀',
                'actions': ["Vessels advised to alter course to avoid eye wall", "Expect 2-4 day delays for affected routes"]
            },
            'storm': {
                'description': f"Storm system {name} bringing reduced visibility and rough seas",
                'icon': '⛈️',
                'actions': ["Reduce vessel speed for safety", "Monitor weather updates every 6 hours"]
            },
            'fog': {
                'description': "Dense fog conditions reducing visibility to under 1 nautical mile",
                'icon': '🌫️',
                'actions': ["Vessels must reduce speed in fog zones", "Port operations may be suspended temporarily"]
            },
            'high_winds': {
                'description': f"High wind advisory with sustained winds over 40 knots",
                'icon': '💨',
                'actions': ["Container loading/unloading may be suspended", "Small craft warnings in effect"]
            }
        }
        
        impact_info = type_impacts.get(system_type, type_impacts['storm'])
        
        # Severity multiplier
        severity_text = {
            'severe': "This is a major weather event requiring immediate action.",
            'moderate': "Exercise caution and monitor for intensification.",
            'mild': "Minor impact expected, continue with awareness."
        }.get(intensity, "")
        
        return {
            "weather_system": name,
            "type": system_type,
            "icon": impact_info['icon'],
            "summary": impact_info['description'],
            "severity_note": severity_text,
            "affected_routes": affected_routes,
            "recommended_actions": impact_info['actions'],
            "explanation_type": "weather_impact"
        }
    
    def generate_ai_summary(
        self,
        context: str,
        data: Dict
    ) -> Optional[str]:
        """
        Use Gemini to generate a natural language summary
        Falls back to rule-based if unavailable
        """
        if not self.gemini_model:
            return None
        
        try:
            prompt = f"""You are an AI assistant explaining supply chain predictions to business users.
Generate a brief, clear explanation in 2-3 sentences. Use simple language a non-expert can understand.
Avoid technical jargon. Be specific about causes and actionable in recommendations.

Context: {context}
Data: {data}

Generate a plain English explanation:"""

            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return None
    
    def _calculate_confidence(self, features: Dict) -> float:
        """Calculate prediction confidence based on data quality"""
        # More complete data = higher confidence
        filled_features = sum(1 for v in features.values() if v is not None and v != 0)
        total_features = len(features) if features else 1
        
        base_confidence = filled_features / total_features
        
        # Historical data availability boost
        if features.get('historical_data_points', 0) > 100:
            base_confidence += 0.1
        
        return min(0.95, max(0.5, base_confidence))
    
    def get_feature_importance_explanation(
        self,
        features: Dict[str, float],
        prediction: float
    ) -> Dict:
        """
        Explain which features most influenced the prediction
        Like a simplified SHAP explanation
        """
        # Normalize features
        total = sum(abs(v) for v in features.values()) or 1
        
        importance_list = []
        for name, value in sorted(features.items(), key=lambda x: abs(x[1]), reverse=True):
            normalized = abs(value) / total * 100
            
            # Human-readable names and icons
            display_info = {
                "weather_risk": ("Weather Conditions", "🌤️"),
                "port_congestion": ("Port Congestion", "🚢"),
                "geopolitical_risk": ("Geopolitical Factors", "🌍"),
                "distance_nm": ("Route Distance", "📏"),
                "historical_delay": ("Historical Performance", "📊"),
                "vessel_speed": ("Vessel Speed", "⚡"),
                "seasonal_factor": ("Seasonal Patterns", "📅"),
                "fuel_price": ("Fuel Costs", "⛽")
            }.get(name, (name.replace("_", " ").title(), "📈"))
            
            importance_list.append({
                "feature": display_info[0],
                "icon": display_info[1],
                "importance_pct": round(normalized, 1),
                "raw_value": value,
                "direction": "increases" if value > 0 else "decreases"
            })
        
        return {
            "prediction_value": prediction,
            "feature_contributions": importance_list[:6],  # Top 6 features
            "interpretation": f"Prediction of {prediction:.1f} is most influenced by {importance_list[0]['feature']} ({importance_list[0]['importance_pct']:.0f}%)"
        }


# Singleton instance
_xai_service: Optional[ExplainableAI] = None

def get_xai_service() -> ExplainableAI:
    global _xai_service
    if _xai_service is None:
        _xai_service = ExplainableAI()
    return _xai_service
