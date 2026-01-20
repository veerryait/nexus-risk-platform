"""
GNN API Endpoints
Graph Neural Network predictions for cascading supply chain risk
"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from app.ml.gnn_inference import get_gnn_service
from app.services.live_data_service import get_integrated_dashboard_data

router = APIRouter()


@router.get("/predict")
async def get_gnn_predictions():
    """
    Get GNN-based risk predictions for the entire supply chain network
    
    Uses Graph Attention Networks to predict cascading risk scores
    for each port based on current congestion, weather, and network topology.
    
    Returns:
        Network-wide risk predictions with per-node scores
    """
    try:
        # Get current dashboard data
        dashboard_data = get_integrated_dashboard_data()
        
        # Run GNN inference
        gnn_service = get_gnn_service()
        predictions = gnn_service.predict_network_risk(dashboard_data)
        
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GNN prediction failed: {str(e)}")


@router.get("/cascade/{port_code}")
async def simulate_cascade(port_code: str):
    """
    Simulate cascading failure from a specific port
    
    Models how congestion/failure at one port propagates through the network
    to affect other connected ports.
    
    Args:
        port_code: Port code (e.g., TWKHH, USLAX) where cascade originates
        
    Returns:
        Cascade impact on each connected port
    """
    try:
        # Get current dashboard data
        dashboard_data = get_integrated_dashboard_data()
        
        # Validate port exists
        valid_ports = [p['code'] for p in dashboard_data.get('ports', [])]
        if port_code.upper() not in valid_ports:
            raise HTTPException(
                status_code=404, 
                detail=f"Port {port_code} not found. Valid ports: {valid_ports}"
            )
        
        # Run cascade simulation
        gnn_service = get_gnn_service()
        cascade = gnn_service.simulate_cascade(dashboard_data, port_code.upper())
        
        return cascade
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cascade simulation failed: {str(e)}")


@router.get("/network")
async def get_network_structure():
    """
    Get network structure for graph visualization
    
    Returns nodes (ports) and edges (routes) formatted for
    frontend graph visualization libraries.
    
    Returns:
        Graph structure with nodes, edges, and their properties
    """
    try:
        # Get current dashboard data
        dashboard_data = get_integrated_dashboard_data()
        
        # Get network structure
        gnn_service = get_gnn_service()
        network = gnn_service.get_network_structure(dashboard_data)
        
        return network
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get network: {str(e)}")


@router.get("/compare")
async def compare_with_baseline():
    """
    Compare GNN predictions with rule-based baseline
    
    Shows how GNN captures network effects that simple rules miss.
    
    Returns:
        Side-by-side comparison of GNN vs baseline predictions
    """
    try:
        # Get current dashboard data
        dashboard_data = get_integrated_dashboard_data()
        
        # Get GNN predictions
        gnn_service = get_gnn_service()
        gnn_predictions = gnn_service.predict_network_risk(dashboard_data)
        
        # Get baseline (rule-based) predictions from routes
        comparison = []
        gnn_nodes = {n['port_code']: n for n in gnn_predictions['node_predictions']}
        
        for port in dashboard_data.get('ports', []):
            port_code = port['code']
            
            # Baseline: simple congestion-based risk
            baseline_risk = port['congestion_level'] * 100
            
            # GNN prediction
            gnn_risk = gnn_nodes.get(port_code, {}).get('gnn_risk_score', 0)
            
            # Difference shows network effects
            network_effect = gnn_risk - baseline_risk
            
            comparison.append({
                "port_code": port_code,
                "baseline_risk": round(baseline_risk, 1),
                "gnn_risk": round(gnn_risk, 1),
                "network_effect": round(network_effect, 1),
                "network_effect_direction": "increase" if network_effect > 5 else "decrease" if network_effect < -5 else "similar"
            })
        
        # Sort by absolute network effect
        comparison.sort(key=lambda x: abs(x['network_effect']), reverse=True)
        
        return {
            "timestamp": gnn_predictions['timestamp'],
            "comparison": comparison,
            "summary": {
                "avg_baseline_risk": round(sum(c['baseline_risk'] for c in comparison) / len(comparison), 1),
                "avg_gnn_risk": round(sum(c['gnn_risk'] for c in comparison) / len(comparison), 1),
                "max_network_effect": max(c['network_effect'] for c in comparison) if comparison else 0,
                "ports_with_significant_network_effects": len([c for c in comparison if abs(c['network_effect']) > 10])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/info")
async def get_model_info():
    """
    Get information about the GNN model
    
    Returns model architecture, training info, and capabilities.
    """
    from app.ml.gnn_model import HAS_PYGEOMETRIC
    
    return {
        "model_name": "SupplyChainGNN",
        "architecture": "Graph Attention Network (GAT)",
        "version": "1.0.0",
        "layers": 3,
        "hidden_dim": 64,
        "attention_heads": 4,
        "node_features": [
            "congestion_level",
            "wait_time_hours",
            "capacity_teus",
            "latitude",
            "longitude",
            "is_origin_port"
        ],
        "edge_features": [
            "distance_nm",
            "transit_time_days",
            "weather_risk",
            "current_delay"
        ],
        "capabilities": [
            "Network-wide risk prediction",
            "Cascading failure simulation",
            "Graph visualization data",
            "Comparison with rule-based baseline"
        ],
        "pytorch_geometric_available": HAS_PYGEOMETRIC,
        "inference_mode": "GPU" if HAS_PYGEOMETRIC else "Standard Mode"
    }
