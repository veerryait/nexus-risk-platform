"""
AI API - Gemini-powered Risk Analysis Endpoints
Natural language risk explanation, scenario simulation, and recommendations
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.services.ai_service import ai_service
from app.services.risk_calculator import risk_calculator

router = APIRouter()


# ==================== Request Models ====================

class ExplainRiskRequest(BaseModel):
    route_id: Optional[str] = "kaohsiung_losangeles"
    include_context: Optional[bool] = True


class SimulateScenarioRequest(BaseModel):
    scenario: str  # e.g., "Taiwan Strait closes for 2 weeks"
    route_id: Optional[str] = "kaohsiung_losangeles"


class RecommendationsRequest(BaseModel):
    context: Optional[str] = ""
    max_recommendations: Optional[int] = 5


# ==================== Endpoints ====================

@router.get("/status")
async def ai_status():
    """Check AI service status"""
    return {
        "available": ai_service.available,
        "model": "gemini-1.5-flash" if ai_service.available else None,
        "features": [
            "risk_explanation",
            "scenario_simulation",
            "recommendations",
            "trend_analysis",
        ] if ai_service.available else [],
    }


@router.post("/explain-risk")
async def explain_risk(request: ExplainRiskRequest = None):
    """
    Get AI-powered natural language explanation of current risk
    
    Returns plain English summary with key concerns and recommendations
    """
    try:
        # Get current risk data
        risk_data = await risk_calculator.calculate_route_risk(
            request.route_id if request else "kaohsiung_losangeles"
        )
        
        # Get AI explanation
        explanation = await ai_service.explain_risk(risk_data)
        
        return {
            "route_id": request.route_id if request else "kaohsiung_losangeles",
            "current_risk_score": risk_data.get("risk_score", 0),
            "explanation": explanation,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate_scenario(request: SimulateScenarioRequest):
    """
    Simulate a "what if" scenario and predict supply chain impact
    
    Examples:
    - "Taiwan Strait closes for 2 weeks"
    - "Category 5 typhoon hits Pacific shipping lanes"
    - "Port of Los Angeles shutdown due to strike"
    - "China imposes semiconductor export restrictions"
    """
    try:
        # Get current risk as baseline
        current_risk = await risk_calculator.calculate_route_risk(request.route_id)
        
        # Simulate scenario
        simulation = await ai_service.simulate_scenario(
            scenario=request.scenario,
            current_risk=current_risk
        )
        
        return {
            "scenario": request.scenario,
            "route_id": request.route_id,
            "baseline_risk": current_risk.get("risk_score", 0),
            "simulation": simulation,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations")
async def get_recommendations(context: str = ""):
    """
    Get AI-powered actionable recommendations based on current conditions
    """
    try:
        # Get current overall risk
        risk_summary = await risk_calculator.get_overall_risk()
        
        # Generate recommendations
        recommendations = await ai_service.generate_recommendations(
            risk_data=risk_summary,
            context=context
        )
        
        return {
            "current_risk": risk_summary.get("overall_risk", 0),
            "risk_level": risk_summary.get("risk_level", "low"),
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def analyze_trends():
    """
    Get AI analysis of historical trends and patterns
    """
    try:
        from app.services.historical_service import historical_service
        
        # Get historical baseline
        baseline = await historical_service.get_historical_baseline()
        
        # Get AI trend analysis
        analysis = await ai_service.analyze_trends({
            "avg_delay": baseline.get("baseline_delay_days", 0.5),
            "on_time_rate": baseline.get("on_time_rate", 0.85),
            "peak_factor": baseline.get("peak_season_factor", 1.5),
            "total_transits": baseline.get("total_transits_analyzed", 3000),
        })
        
        return {
            "baseline_data": baseline,
            "trend_analysis": analysis,
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def ask_question(question: str):
    """
    Ask a free-form question about supply chain risk
    
    Examples:
    - "What's the biggest risk to Taiwan shipping right now?"
    - "Should I increase inventory for Q4?"
    - "How reliable are Evergreen shipments?"
    """
    if not ai_service.available:
        raise HTTPException(status_code=503, detail="AI service not available")
    
    try:
        # Get current context
        risk_summary = await risk_calculator.get_overall_risk()
        
        prompt = f"""You are a supply chain risk analyst for Taiwan-US semiconductor shipping.

User question: "{question}"

CURRENT CONTEXT:
- Overall Risk: {risk_summary.get('overall_risk', 0.25):.2f}
- Risk Level: {risk_summary.get('risk_level', 'low')}
- Routes at risk: {risk_summary.get('routes_at_risk', 0)} of {risk_summary.get('total_routes', 3)}
- Average delay: {risk_summary.get('average_delay_hours', 30)} hours

Provide a helpful, specific answer focused on actionable intelligence.
Keep your response concise but informative (2-3 paragraphs max)."""

        response = ai_service.model.generate_content(prompt)
        
        return {
            "question": question,
            "answer": response.text,
            "context": {
                "risk_level": risk_summary.get("risk_level"),
                "overall_risk": risk_summary.get("overall_risk"),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
