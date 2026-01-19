"""
Supply Chain Graph Neural Network Model
Predicts cascading failures in supply chain networks using Graph Attention Networks

Falls back to numpy-based implementation when PyTorch is not available.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import math

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("PyTorch not installed. Using numpy fallback for GNN.")

# Try to import PyTorch Geometric
try:
    from torch_geometric.nn import GATConv, global_mean_pool
    from torch_geometric.data import Data, Batch
    HAS_PYGEOMETRIC = True
except ImportError:
    HAS_PYGEOMETRIC = False
    if HAS_TORCH:
        print("PyTorch Geometric not installed. Using PyTorch-only fallback.")


class SupplyChainGNN:
    """
    Graph Neural Network for Supply Chain Risk Prediction
    
    Uses Graph Attention Networks when PyTorch/PyG available,
    falls back to numpy-based graph propagation otherwise.
    
    Nodes: Ports/Facilities with features (congestion, capacity, location, etc.)
    Edges: Shipping routes with features (distance, transit time, weather risk)
    Output: Risk score for each node (0-1)
    """
    
    def __init__(
        self,
        node_features: int = 6,
        edge_features: int = 4,
        hidden_dim: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        self.node_features = node_features
        self.edge_features = edge_features
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        
        if HAS_TORCH and HAS_PYGEOMETRIC:
            self._init_pyg_model(node_features, edge_features, hidden_dim, num_heads, num_layers, dropout)
        elif HAS_TORCH:
            self._init_torch_model(node_features, hidden_dim, dropout)
        else:
            # Numpy fallback - use learned-like weights
            np.random.seed(42)
            self.weights = {
                'layer1': np.random.randn(node_features, hidden_dim) * 0.1,
                'layer2': np.random.randn(hidden_dim, hidden_dim) * 0.1,
                'output': np.random.randn(hidden_dim, 1) * 0.1
            }
    
    def _init_pyg_model(self, node_features, edge_features, hidden_dim, num_heads, num_layers, dropout):
        """Initialize PyTorch Geometric model"""
        import torch.nn as nn
        
        self.node_encoder = nn.Linear(node_features, hidden_dim)
        self.edge_encoder = nn.Linear(edge_features, hidden_dim)
        
        self.convs = nn.ModuleList()
        self.convs.append(GATConv(hidden_dim, hidden_dim // num_heads, 
                                   heads=num_heads, edge_dim=hidden_dim, dropout=dropout))
        for _ in range(num_layers - 1):
            self.convs.append(GATConv(hidden_dim, hidden_dim // num_heads,
                                      heads=num_heads, edge_dim=hidden_dim, dropout=dropout))
        
        self.risk_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
    
    def _init_torch_model(self, node_features, hidden_dim, dropout):
        """Initialize simple PyTorch MLP model"""
        import torch.nn as nn
        
        self.mlp = nn.Sequential(
            nn.Linear(node_features, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )
    
    def eval(self):
        """Set model to evaluation mode"""
        if HAS_TORCH:
            if hasattr(self, 'convs'):
                for conv in self.convs:
                    conv.eval()
            if hasattr(self, 'mlp'):
                self.mlp.eval()
        return self
    
    def __call__(self, x, edge_index, edge_attr, batch=None):
        """Make the model callable - delegates to forward"""
        return self.forward(x, edge_index, edge_attr, batch)
    
    def forward(
        self,
        x,
        edge_index,
        edge_attr,
        batch = None
    ):
        """
        Forward pass through the GNN
        
        Args:
            x: Node features [num_nodes, node_features]
            edge_index: Edge connectivity [2, num_edges]
            edge_attr: Edge features [num_edges, edge_features]
            batch: Batch assignment for multiple graphs
            
        Returns:
            node_risks: Risk score for each node [num_nodes, 1]
            graph_risk: Overall graph risk [batch_size, 1]
        """
        if not HAS_TORCH:
            # Numpy fallback: graph-aware risk propagation
            return self._numpy_forward(x, edge_index, edge_attr)
        
        if not HAS_PYGEOMETRIC:
            # PyTorch-only fallback: Simple MLP prediction
            node_risks = self.mlp(x)
            graph_risk = node_risks.mean(dim=0, keepdim=True)
            return node_risks, graph_risk
        
        # Full PyG forward pass
        h = self.node_encoder(x)
        e = self.edge_encoder(edge_attr)
        
        for conv in self.convs:
            h = F.relu(conv(h, edge_index, e))
        
        node_risks = self.risk_predictor(h)
        
        if batch is not None:
            graph_risk = global_mean_pool(node_risks, batch)
        else:
            graph_risk = node_risks.mean(dim=0, keepdim=True)
        
        return node_risks, graph_risk
    
    def _numpy_forward(self, x, edge_index, edge_attr):
        """
        Numpy-based forward pass using graph propagation
        Simulates GNN behavior without PyTorch
        """
        x = np.array(x) if not isinstance(x, np.ndarray) else x
        edge_index = np.array(edge_index) if not isinstance(edge_index, np.ndarray) else edge_index
        edge_attr = np.array(edge_attr) if not isinstance(edge_attr, np.ndarray) else edge_attr
        
        num_nodes = x.shape[0]
        
        # Build adjacency with edge weights
        adj = {i: [] for i in range(num_nodes)}
        for idx in range(edge_index.shape[1]):
            src, dst = int(edge_index[0, idx]), int(edge_index[1, idx])
            edge_weight = 1.0 - edge_attr[idx, 2]  # Inverse of weather risk
            adj[src].append((dst, edge_weight))
        
        # Initial node risk from congestion (feature 0)
        node_risks = x[:, 0].copy()  # Congestion level
        
        # Graph propagation for 3 iterations (simulating 3 GNN layers)
        for _ in range(self.num_layers):
            new_risks = node_risks.copy()
            for node in range(num_nodes):
                # Aggregate neighbor risks with attention-like weighting
                neighbor_contrib = 0.0
                total_weight = 0.0
                for neighbor, weight in adj[node]:
                    neighbor_contrib += node_risks[neighbor] * weight
                    total_weight += weight
                
                if total_weight > 0:
                    # Combine self and neighbor information
                    new_risks[node] = 0.6 * node_risks[node] + 0.4 * (neighbor_contrib / total_weight)
            
            node_risks = new_risks
        
        # Normalize to 0-1
        node_risks = np.clip(node_risks, 0, 1)
        
        # Graph-level risk
        graph_risk = np.mean(node_risks)
        
        return node_risks.reshape(-1, 1), np.array([[graph_risk]])
    
    def predict_cascade(
        self,
        h,
        edge_index,
        source_node: int
    ):
        """
        Predict risk cascade from a source node
        Works with both PyTorch and numpy
        """
        if HAS_TORCH and hasattr(h, 'size'):
            num_nodes = h.size(0)
            cascade_risks = torch.zeros(num_nodes, 1)
        else:
            num_nodes = h.shape[0] if hasattr(h, 'shape') else len(h)
            cascade_risks = np.zeros((num_nodes, 1))
        
        # BFS-based cascade propagation
        cascade_risks[source_node] = 1.0
        
        # Build adjacency
        edge_idx = np.array(edge_index) if HAS_TORCH and hasattr(edge_index, 'numpy') else edge_index
        if HAS_TORCH and hasattr(edge_idx, 'numpy'):
            edge_idx = edge_idx.numpy()
        
        adj = {i: [] for i in range(num_nodes)}
        if len(edge_idx.shape) == 2 and edge_idx.shape[0] == 2:
            for j in range(edge_idx.shape[1]):
                src, dst = int(edge_idx[0, j]), int(edge_idx[1, j])
                adj[src].append(dst)
        
        # Propagate cascade with decay
        visited = {source_node}
        queue = [(source_node, 1.0)]
        
        while queue:
            node, risk = queue.pop(0)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    neighbor_risk = risk * 0.65  # 35% decay per hop
                    cascade_risks[neighbor] = neighbor_risk
                    if neighbor_risk > 0.05:
                        queue.append((neighbor, neighbor_risk))
        
        return cascade_risks


class SupplyChainGraph:
    """
    Builder class for constructing supply chain graphs for the GNN
    """
    
    # Node feature indices
    NODE_CONGESTION = 0
    NODE_WAIT_TIME = 1
    NODE_CAPACITY = 2
    NODE_LAT = 3
    NODE_LNG = 4
    NODE_IS_ORIGIN = 5
    
    # Edge feature indices
    EDGE_DISTANCE = 0
    EDGE_TRANSIT_TIME = 1
    EDGE_WEATHER_RISK = 2
    EDGE_CURRENT_DELAY = 3
    
    def __init__(self):
        self.ports: List[Dict] = []
        self.routes: List[Dict] = []
        self.port_to_idx: Dict[str, int] = {}
    
    def add_port(
        self,
        code: str,
        congestion: float,
        wait_time: float,
        capacity: float,
        lat: float,
        lng: float,
        is_origin: bool = False
    ):
        """Add a port/facility node to the graph"""
        idx = len(self.ports)
        self.port_to_idx[code] = idx
        self.ports.append({
            'code': code,
            'congestion': congestion,
            'wait_time': wait_time,
            'capacity': capacity,
            'lat': lat,
            'lng': lng,
            'is_origin': is_origin
        })
    
    def add_route(
        self,
        origin_code: str,
        dest_code: str,
        distance: float,
        transit_time: float,
        weather_risk: float,
        current_delay: float
    ):
        """Add a shipping route edge to the graph"""
        self.routes.append({
            'origin': origin_code,
            'dest': dest_code,
            'distance': distance,
            'transit_time': transit_time,
            'weather_risk': weather_risk,
            'current_delay': current_delay
        })
    
    def to_pyg_data(self):
        """Convert to PyTorch Geometric Data object or numpy dict"""
        # Node features
        node_features = []
        for port in self.ports:
            node_features.append([
                port['congestion'],
                port['wait_time'] / 48.0,  # Normalize to ~0-1
                port['capacity'] / 50_000_000,  # Normalize
                (port['lat'] + 90) / 180,  # Normalize lat
                (port['lng'] + 180) / 360,  # Normalize lng
                float(port['is_origin'])
            ])
        
        # Edge index and features
        edge_index = []
        edge_features = []
        for route in self.routes:
            src = self.port_to_idx.get(route['origin'])
            dst = self.port_to_idx.get(route['dest'])
            if src is not None and dst is not None:
                # Add bidirectional edges
                edge_index.append([src, dst])
                edge_index.append([dst, src])
                
                edge_feat = [
                    route['distance'] / 10000,  # Normalize
                    route['transit_time'] / 30,  # Normalize
                    route['weather_risk'],
                    route['current_delay'] / 10  # Normalize
                ]
                edge_features.append(edge_feat)
                edge_features.append(edge_feat)  # Same for reverse edge
        
        if HAS_TORCH:
            x = torch.tensor(node_features, dtype=torch.float)
            edge_idx = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
            edge_attr = torch.tensor(edge_features, dtype=torch.float)
            
            if HAS_PYGEOMETRIC:
                return Data(x=x, edge_index=edge_idx, edge_attr=edge_attr)
            else:
                return {'x': x, 'edge_index': edge_idx, 'edge_attr': edge_attr}
        else:
            # Numpy fallback
            x = np.array(node_features, dtype=np.float32)
            edge_idx = np.array(edge_index, dtype=np.int64).T
            edge_attr = np.array(edge_features, dtype=np.float32)
            return {'x': x, 'edge_index': edge_idx, 'edge_attr': edge_attr}
    
    @classmethod
    def from_dashboard_data(cls, data: Dict) -> 'SupplyChainGraph':
        """
        Build graph from dashboard live data
        
        Args:
            data: Response from /api/v1/dashboard/live
        """
        graph = cls()
        
        # Add ports as nodes
        for port in data.get('ports', []):
            graph.add_port(
                code=port['code'],
                congestion=port['congestion_level'],
                wait_time=port['wait_time_hours'],
                capacity=port.get('capacity_teus', 10_000_000),
                lat=port['lat'],
                lng=port['lng'],
                is_origin=port['country'] in ['Taiwan', 'China', 'Hong Kong', 'Singapore']
            )
        
        # Add routes as edges
        for route in data.get('routes', []):
            weather_risk = route.get('weather_impact', {}).get('risk_increase', 0) / 100
            graph.add_route(
                origin_code=route['origin_code'],
                dest_code=route['dest_code'],
                distance=route['distance_nm'],
                transit_time=route['typical_days'],
                weather_risk=weather_risk,
                current_delay=route.get('predicted_delay_days', 0)
            )
        
        return graph


# Pre-trained model weights (simplified - in production would load from file)
def get_pretrained_model() -> SupplyChainGNN:
    """
    Get a pre-trained GNN model
    In production, this would load weights from a file
    """
    model = SupplyChainGNN(
        node_features=6,
        edge_features=4,
        hidden_dim=64,
        num_heads=4,
        num_layers=3
    )
    model.eval()
    return model
