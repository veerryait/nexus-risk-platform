"""
GNN Inference Service
Runs predictions using the trained Graph Neural Network
"""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from .gnn_model import SupplyChainGNN, SupplyChainGraph, get_pretrained_model, HAS_TORCH, HAS_PYGEOMETRIC


class GNNInferenceService:
    """
    Service for running GNN predictions on supply chain data
    """
    
    def __init__(self):
        self.model = get_pretrained_model()
        self.last_prediction_time: Optional[datetime] = None
        self.cached_predictions: Optional[Dict] = None
        self.cache_ttl_seconds = 30  # Cache predictions for 30 seconds
    
    def predict_network_risk(self, dashboard_data: Dict) -> Dict:
        """
        Predict risk scores for all nodes in the supply chain network
        
        Args:
            dashboard_data: Response from /api/v1/dashboard/live
            
        Returns:
            Dictionary with node risks, cascade probabilities, and network metrics
        """
        # Build graph from dashboard data
        graph = SupplyChainGraph.from_dashboard_data(dashboard_data)
        
        if len(graph.ports) == 0:
            return {"error": "No ports in graph", "node_risks": []}
        
        # Convert to data format
        data = graph.to_pyg_data()
        
        # Run inference
        if HAS_TORCH:
            import torch
            with torch.no_grad():
                if HAS_PYGEOMETRIC:
                    node_risks, graph_risk = self.model(
                        data.x, data.edge_index, data.edge_attr
                    )
                else:
                    node_risks, graph_risk = self.model(
                        data['x'], data['edge_index'], data['edge_attr']
                    )
        else:
            # Numpy fallback
            node_risks, graph_risk = self.model(
                data['x'], data['edge_index'], data['edge_attr']
            )
        
        # Build response
        node_results = []
        for i, port in enumerate(graph.ports):
            # Handle both torch tensor and numpy array
            if HAS_TORCH and hasattr(node_risks[i], 'item'):
                risk_score = float(node_risks[i].item())
            else:
                risk_score = float(node_risks[i][0]) if hasattr(node_risks[i], '__len__') else float(node_risks[i])
            
            # Determine risk level
            if risk_score > 0.75:
                risk_level = "critical"
            elif risk_score > 0.55:
                risk_level = "high"
            elif risk_score > 0.35:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            node_results.append({
                "port_code": port['code'],
                "gnn_risk_score": round(risk_score * 100, 1),
                "risk_level": risk_level,
                "congestion_input": round(port['congestion'] * 100, 1),
                "is_origin_port": port['is_origin']
            })
        
        # Sort by risk score descending
        node_results.sort(key=lambda x: x['gnn_risk_score'], reverse=True)
        
        # Get graph risk value
        if HAS_TORCH and hasattr(graph_risk, 'item'):
            graph_risk_val = float(graph_risk.item())
        else:
            graph_risk_val = float(graph_risk[0][0]) if hasattr(graph_risk[0], '__len__') else float(graph_risk[0])
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "model_version": "1.0.0-gat" if HAS_PYGEOMETRIC else "1.0.0-numpy",
            "network_risk_score": round(graph_risk_val * 100, 1),
            "total_nodes": len(graph.ports),
            "total_edges": len(graph.routes),
            "high_risk_nodes": len([n for n in node_results if n['risk_level'] in ['high', 'critical']]),
            "node_predictions": node_results,
            "model_info": {
                "architecture": "Graph Attention Network (GAT)" if HAS_PYGEOMETRIC else "Graph Propagation (Numpy)",
                "layers": 3,
                "hidden_dim": 64,
                "uses_pytorch": HAS_TORCH,
                "uses_pyg": HAS_PYGEOMETRIC
            }
        }
    
    def simulate_cascade(self, dashboard_data: Dict, source_port: str) -> Dict:
        """
        Simulate cascading failure from a specific port
        
        Args:
            dashboard_data: Response from /api/v1/dashboard/live
            source_port: Port code where cascade originates
            
        Returns:
            Cascade simulation results
        """
        # Build graph
        graph = SupplyChainGraph.from_dashboard_data(dashboard_data)
        
        if source_port not in graph.port_to_idx:
            return {"error": f"Port {source_port} not found in network"}
        
        source_idx = graph.port_to_idx[source_port]
        
        # Convert to data format
        data = graph.to_pyg_data()
        
        # Run cascade simulation
        if HAS_TORCH and HAS_PYGEOMETRIC:
            import torch
            with torch.no_grad():
                # Get intermediate embeddings
                h = self.model.node_encoder(data.x)
                e = self.model.edge_encoder(data.edge_attr)
                for conv in self.model.convs:
                    h = torch.relu(conv(h, data.edge_index, e))
                
                # Predict cascade
                cascade_risks = self.model.predict_cascade(h, data.edge_index, source_idx)
        else:
            # Fallback: simple distance-based cascade
            cascade_risks = self._simple_cascade(graph, source_idx)
        
        # Build response
        cascade_results = []
        for i, port in enumerate(graph.ports):
            # Handle both tensor and numpy
            if HAS_TORCH and hasattr(cascade_risks[i], 'item'):
                cascade_risk = float(cascade_risks[i].item())
            elif hasattr(cascade_risks[i], '__len__'):
                cascade_risk = float(cascade_risks[i][0])
            else:
                cascade_risk = float(cascade_risks[i])
            
            cascade_results.append({
                "port_code": port['code'],
                "cascade_risk_increase": round(cascade_risk * 100, 1),
                "is_source": i == source_idx,
                "original_congestion": round(port['congestion'] * 100, 1),
                "projected_congestion": min(100, round((port['congestion'] + cascade_risk * 0.3) * 100, 1))
            })
        
        # Sort by cascade impact
        cascade_results.sort(key=lambda x: x['cascade_risk_increase'], reverse=True)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source_port": source_port,
            "cascade_simulation": cascade_results,
            "total_impact_score": sum(r['cascade_risk_increase'] for r in cascade_results),
            "affected_ports": len([r for r in cascade_results if r['cascade_risk_increase'] > 10]),
            "propagation_depth": self._calculate_propagation_depth(graph, source_idx)
        }
    
    def _simple_cascade(self, graph: SupplyChainGraph, source_idx: int) -> List[float]:
        """Simple cascade simulation without PyG"""
        num_nodes = len(graph.ports)
        cascade_risks = [0.0] * num_nodes
        cascade_risks[source_idx] = 1.0
        
        # Build adjacency
        adj = {i: [] for i in range(num_nodes)}
        for route in graph.routes:
            src = graph.port_to_idx.get(route['origin'])
            dst = graph.port_to_idx.get(route['dest'])
            if src is not None and dst is not None:
                adj[src].append(dst)
                adj[dst].append(src)
        
        # BFS to propagate cascade
        visited = {source_idx}
        queue = [(source_idx, 1.0)]
        
        while queue:
            node, decay = queue.pop(0)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor_risk = decay * 0.6  # 40% decay per hop
                    cascade_risks[neighbor] = neighbor_risk
                    if neighbor_risk > 0.1:
                        queue.append((neighbor, neighbor_risk))
        
        return cascade_risks
    
    def _calculate_propagation_depth(self, graph: SupplyChainGraph, source_idx: int) -> int:
        """Calculate how many hops the cascade can propagate"""
        # Build adjacency
        adj = {i: [] for i in range(len(graph.ports))}
        for route in graph.routes:
            src = graph.port_to_idx.get(route['origin'])
            dst = graph.port_to_idx.get(route['dest'])
            if src is not None and dst is not None:
                adj[src].append(dst)
                adj[dst].append(src)
        
        # BFS to find max depth
        visited = {source_idx}
        queue = [(source_idx, 0)]
        max_depth = 0
        
        while queue:
            node, depth = queue.pop(0)
            max_depth = max(max_depth, depth)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return max_depth
    
    def get_network_structure(self, dashboard_data: Dict) -> Dict:
        """
        Get network structure for visualization
        
        Returns nodes and edges suitable for frontend graph visualization
        """
        graph = SupplyChainGraph.from_dashboard_data(dashboard_data)
        
        nodes = []
        for i, port in enumerate(graph.ports):
            nodes.append({
                "id": port['code'],
                "label": port['code'],
                "x": port['lng'] + 180,  # Normalize for visualization
                "y": 90 - port['lat'],   # Flip Y axis
                "congestion": port['congestion'],
                "is_origin": port['is_origin'],
                "size": 10 + port['congestion'] * 20
            })
        
        edges = []
        for route in graph.routes:
            edges.append({
                "source": route['origin'],
                "target": route['dest'],
                "weight": route['distance'] / 1000,
                "transit_time": route['transit_time'],
                "weather_risk": route['weather_risk']
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }


# Singleton instance
_gnn_service: Optional[GNNInferenceService] = None

def get_gnn_service() -> GNNInferenceService:
    global _gnn_service
    if _gnn_service is None:
        _gnn_service = GNNInferenceService()
    return _gnn_service
