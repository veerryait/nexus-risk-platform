"""
Model Performance API Endpoints

Provides endpoints for:
- Current model metrics
- Historical accuracy trends
- Calibration data
- Drift analysis
- Data quality reports
- Prediction vs actual comparison
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from app.services.model_metrics_service import get_performance_tracker

router = APIRouter()


@router.get("/summary")
async def get_performance_summary():
    """
    Get comprehensive model performance summary.
    
    Returns overall health, current metrics, trends, calibration,
    drift analysis, and data quality information.
    """
    tracker = get_performance_tracker()
    return tracker.get_performance_summary()


@router.get("/current")
async def get_current_metrics():
    """
    Get the most recent model performance metrics.
    
    Returns MAE, RMSE, Precision, Recall, F1, etc.
    """
    tracker = get_performance_tracker()
    return tracker.get_current_metrics()


@router.get("/trends")
async def get_accuracy_trends(days: int = 30):
    """
    Get historical accuracy trends for visualization.
    
    Args:
        days: Number of days of history to return (default 30)
    
    Returns time series data for various metrics.
    """
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
    
    tracker = get_performance_tracker()
    return tracker.get_accuracy_trends()


@router.get("/calibration")
async def get_calibration_data():
    """
    Get calibration data showing predicted confidence vs actual accuracy.
    
    Returns calibration curve data and Expected Calibration Error (ECE).
    A well-calibrated model has low ECE (< 0.1).
    """
    tracker = get_performance_tracker()
    return tracker.get_calibration_data()


@router.get("/predictions-vs-actual")
async def get_prediction_vs_actual(limit: int = 50):
    """
    Get recent predictions compared to actual outcomes.
    
    Args:
        limit: Maximum number of predictions to return (default 50)
    
    Returns predictions with their actual outcomes for scatter plot.
    """
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 200")
    
    tracker = get_performance_tracker()
    return tracker.get_prediction_vs_actual(limit)


@router.get("/drift")
async def get_drift_analysis():
    """
    Analyze model and data drift.
    
    Compares recent metrics to previous period to detect:
    - Feature drift (input distribution changes)
    - Prediction drift (output distribution changes)
    - Accuracy drift (performance degradation)
    """
    tracker = get_performance_tracker()
    return tracker.get_drift_analysis()


@router.get("/data-quality")
async def get_data_quality_report():
    """
    Get data quality metrics for model inputs.
    
    Returns completeness, freshness, and quality scores
    for each data source used by the model.
    """
    tracker = get_performance_tracker()
    return tracker.get_data_quality_report()


@router.get("/health")
async def get_model_health():
    """
    Get overall model health score and status.
    
    Returns a 0-100 health score based on accuracy,
    calibration, drift, and data quality.
    """
    tracker = get_performance_tracker()
    summary = tracker.get_performance_summary()
    return summary["overall_health"]


@router.get("/history")
async def get_metrics_history(days: int = 30):
    """
    Get raw historical metrics data.
    
    Args:
        days: Number of days of history (default 30)
    """
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
    
    tracker = get_performance_tracker()
    return {
        "days": days,
        "metrics": tracker.get_metrics_history(days)
    }
