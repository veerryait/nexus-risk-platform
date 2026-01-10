"""
AI Service - Gemini Integration for Risk Explanation
Provides natural language risk analysis and scenario simulation
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class AIService:
    """Gemini AI integration for intelligent risk analysis"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            # Use gemini-pro for better compatibility
            self.model = genai.GenerativeModel('gemini-pro')
            self.available = True
        else:
            self.model = None
            self.available = False
            print("⚠️ Gemini API key not configured")
    
    async def explain_risk(self, risk_data: Dict) -> Dict:
        """
        Generate natural language explanation of risk assessment
        
        Args:
            risk_data: Current risk scores and factors from risk_calculator
        
        Returns:
            Natural language explanation with actionable insights
        """
        if not self.available:
            return self._mock_explanation(risk_data)
        
        prompt = f"""You are a supply chain risk analyst for Taiwan-US West Coast semiconductor shipping routes.

Analyze this risk assessment data and provide a clear, actionable explanation:

CURRENT RISK DATA:
- Overall Risk Score: {risk_data.get('overall_risk', 0):.2f} (0=low, 1=critical)
- Weather Risk: {risk_data.get('weather_risk', 0):.2f}
- Geopolitical Risk: {risk_data.get('geopolitical_risk', 0):.2f}
- Port Congestion Risk: {risk_data.get('port_risk', 0):.2f}
- Economic Risk: {risk_data.get('economic_risk', 0):.2f}
- Predicted Delay: {risk_data.get('predicted_delay_hours', 0)} hours

TOP FACTORS:
{self._format_factors(risk_data.get('factors', []))}

Provide a response in this JSON format:
{{
  "summary": "One paragraph executive summary of current risk state",
  "risk_level": "low/medium/high/critical",
  "key_concerns": ["Concern 1", "Concern 2", "Concern 3"],
  "recommendations": ["Action 1", "Action 2", "Action 3"],
  "confidence": "high/medium/low",
  "outlook_7_days": "Brief outlook for next week"
}}

Be specific about Taiwan-US shipping routes. Focus on actionable intelligence."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            # Parse JSON from response
            import json
            # Find JSON in response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                result = json.loads(text[start:end])
                result["generated_at"] = datetime.utcnow().isoformat()
                result["model"] = "gemini-1.5-flash"
                return result
            
            return {
                "summary": text,
                "generated_at": datetime.utcnow().isoformat(),
                "model": "gemini-1.5-flash",
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "fallback": self._mock_explanation(risk_data),
            }
    
    async def simulate_scenario(self, scenario: str, current_risk: Dict) -> Dict:
        """
        Simulate a "what if" scenario and predict impact
        
        Args:
            scenario: Description of the scenario (e.g., "Taiwan Strait closes")
            current_risk: Current risk baseline
        
        Returns:
            Predicted impact and recommendations
        """
        if not self.available:
            return self._mock_scenario(scenario)
        
        prompt = f"""You are a supply chain risk analyst. Simulate this scenario for Taiwan-US shipping:

SCENARIO: "{scenario}"

CURRENT BASELINE:
- Risk Score: {current_risk.get('overall_risk', 0.25):.2f}
- Predicted Delay: {current_risk.get('predicted_delay_hours', 32)} hours
- Routes: Kaohsiung → Los Angeles, Long Beach, Oakland

Analyze this scenario and provide response in JSON:
{{
  "scenario_summary": "Brief description of what would happen",
  "impact_level": "minimal/moderate/severe/catastrophic",
  "risk_change": "+0.XX or -0.XX change from baseline",
  "delay_impact_hours": "Additional delay in hours",
  "affected_routes": ["List of most affected routes"],
  "timeline": "How quickly impacts would be felt",
  "mitigation_strategies": ["Strategy 1", "Strategy 2", "Strategy 3"],
  "probability": "low/medium/high likelihood this scenario occurs"
}}

Be realistic and specific to semiconductor supply chain impacts."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            import json
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                result = json.loads(text[start:end])
                result["scenario_input"] = scenario
                result["generated_at"] = datetime.utcnow().isoformat()
                return result
            
            return {"summary": text, "scenario_input": scenario}
            
        except Exception as e:
            return {"error": str(e), "scenario": scenario}
    
    async def generate_recommendations(self, risk_data: Dict, context: str = "") -> List[Dict]:
        """Generate actionable recommendations based on current risk"""
        if not self.available:
            return self._mock_recommendations()
        
        prompt = f"""You are a supply chain strategist for Taiwan-US semiconductor shipping.

Based on current conditions, generate specific recommendations:

CURRENT RISK: {risk_data.get('overall_risk', 0.25):.2f}
KEY FACTORS: {', '.join([f['name'] for f in risk_data.get('factors', [])])}
ADDITIONAL CONTEXT: {context or 'None provided'}

Provide 5 actionable recommendations in JSON array format:
[
  {{
    "priority": "high/medium/low",
    "category": "routing/timing/inventory/communication/contingency",
    "action": "Specific action to take",
    "rationale": "Why this is recommended",
    "timeline": "When to implement"
  }}
]

Focus on practical, implementable actions for supply chain managers."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            import json
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            
            return self._mock_recommendations()
            
        except Exception as e:
            return self._mock_recommendations()
    
    async def analyze_trends(self, historical_data: Dict) -> Dict:
        """Analyze trends and provide narrative summary"""
        if not self.available:
            return {"summary": "AI analysis not available", "trends": []}
        
        prompt = f"""Analyze these supply chain trends for Taiwan-US shipping:

DATA:
- Average Delay: {historical_data.get('avg_delay', 0.5)} days
- On-Time Rate: {historical_data.get('on_time_rate', 0.85) * 100:.1f}%
- Peak Season Factor: {historical_data.get('peak_factor', 1.5)}x
- Total Transits Analyzed: {historical_data.get('total_transits', 3000)}

Provide a brief trend analysis in JSON:
{{
  "trend_summary": "Overall trend description",
  "seasonal_insight": "Seasonal pattern observation",
  "anomalies": ["Any unusual patterns"],
  "forecast": "Expected trend for next quarter"
}}"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            
            import json
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            
            return {"summary": text}
            
        except Exception as e:
            return {"error": str(e)}
    
    def _format_factors(self, factors: List[Dict]) -> str:
        """Format risk factors for prompt"""
        if not factors:
            return "No specific factors available"
        
        lines = []
        for f in factors[:5]:
            lines.append(f"- {f.get('name', 'Unknown')}: {f.get('score', 0):.2f}")
        return "\n".join(lines)
    
    def _mock_explanation(self, risk_data: Dict) -> Dict:
        """Fallback explanation when API unavailable"""
        risk = risk_data.get('overall_risk', 0.25)
        level = "low" if risk < 0.3 else "medium" if risk < 0.6 else "high"
        
        return {
            "summary": f"Current supply chain risk for Taiwan-US routes is {level}. "
                      f"Risk score of {risk:.2f} indicates normal operations with standard monitoring recommended.",
            "risk_level": level,
            "key_concerns": [
                "Weather conditions in Pacific",
                "Port congestion levels",
                "Geopolitical stability",
            ],
            "recommendations": [
                "Maintain standard shipping schedules",
                "Monitor weather forecasts for Pacific region",
                "Ensure buffer inventory for critical components",
            ],
            "confidence": "medium",
            "outlook_7_days": "Stable conditions expected with minor fluctuations",
            "generated_at": datetime.utcnow().isoformat(),
            "model": "fallback",
        }
    
    def _mock_scenario(self, scenario: str) -> Dict:
        """Fallback scenario simulation"""
        return {
            "scenario_summary": f"Analysis of '{scenario}' scenario indicates potential disruptions.",
            "impact_level": "moderate",
            "risk_change": "+0.20",
            "delay_impact_hours": 48,
            "affected_routes": ["Kaohsiung → Los Angeles", "Kaohsiung → Long Beach"],
            "timeline": "1-2 weeks for initial impact",
            "mitigation_strategies": [
                "Diversify shipping routes",
                "Increase safety stock",
                "Establish backup suppliers",
            ],
            "probability": "medium",
            "scenario_input": scenario,
            "model": "fallback",
        }
    
    def _mock_recommendations(self) -> List[Dict]:
        """Fallback recommendations"""
        return [
            {
                "priority": "high",
                "category": "inventory",
                "action": "Increase safety stock for critical semiconductors by 15%",
                "rationale": "Buffer against potential delays",
                "timeline": "Immediate",
            },
            {
                "priority": "medium",
                "category": "routing",
                "action": "Confirm alternate port arrangements with Oakland",
                "rationale": "Contingency if LA/Long Beach congested",
                "timeline": "Within 1 week",
            },
            {
                "priority": "medium",
                "category": "communication",
                "action": "Schedule weekly calls with Taiwan suppliers",
                "rationale": "Early warning of disruptions",
                "timeline": "Ongoing",
            },
        ]


# Singleton instance
ai_service = AIService()
