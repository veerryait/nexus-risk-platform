"""
ML Module Init
Provides graceful initialization when PyTorch is not available
"""

try:
    from .gnn_model import SupplyChainGNN, SupplyChainGraph, get_pretrained_model, HAS_TORCH, HAS_PYGEOMETRIC
    from .gnn_inference import GNNInferenceService, get_gnn_service
    
    __all__ = [
        'SupplyChainGNN',
        'SupplyChainGraph', 
        'get_pretrained_model',
        'GNNInferenceService',
        'get_gnn_service',
        'HAS_TORCH',
        'HAS_PYGEOMETRIC'
    ]
except ImportError as e:
    print(f"Warning: Could not import GNN modules: {e}")
    
    # Provide fallback stubs
    HAS_TORCH = False
    HAS_PYGEOMETRIC = False
    
    __all__ = ['HAS_TORCH', 'HAS_PYGEOMETRIC']
