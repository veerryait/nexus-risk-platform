'use client';

import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
interface NodePrediction {
    port_code: string;
    gnn_risk_score: number;
    risk_level: string;
    congestion_input: number;
    is_origin_port: boolean;
}

interface GNNPrediction {
    timestamp: string;
    model_version: string;
    network_risk_score: number;
    total_nodes: number;
    total_edges: number;
    high_risk_nodes: number;
    node_predictions: NodePrediction[];
    model_info: {
        architecture: string;
        layers: number;
        hidden_dim: number;
        uses_pytorch: boolean;
        uses_pyg: boolean;
    };
}

interface CascadeResult {
    port_code: string;
    cascade_risk_increase: number;
    is_source: boolean;
    original_congestion: number;
    projected_congestion: number;
}

interface CascadeSimulation {
    timestamp: string;
    source_port: string;
    cascade_simulation: CascadeResult[];
    total_impact_score: number;
    affected_ports: number;
    propagation_depth: number;
}

// Port info
const PORT_INFO: Record<string, { name: string; region: 'asia' | 'usa' }> = {
    TWKHH: { name: 'Kaohsiung', region: 'asia' },
    TWTPE: { name: 'Keelung', region: 'asia' },
    CNSHA: { name: 'Shanghai', region: 'asia' },
    CNNGB: { name: 'Ningbo', region: 'asia' },
    HKHKG: { name: 'Hong Kong', region: 'asia' },
    SGSIN: { name: 'Singapore', region: 'asia' },
    USLAX: { name: 'Los Angeles', region: 'usa' },
    USLGB: { name: 'Long Beach', region: 'usa' },
    USOAK: { name: 'Oakland', region: 'usa' },
    USSEA: { name: 'Seattle', region: 'usa' },
};

// Helper functions
const getRiskColor = (score: number) => {
    if (score > 75) return '#ef4444'; // red
    if (score > 55) return '#f97316'; // orange
    if (score > 35) return '#eab308'; // yellow
    return '#22c55e'; // green
};

const getRiskBgClass = (level: string) => {
    switch (level) {
        case 'critical': return 'bg-gradient-to-br from-rose-500/30 to-rose-600/20 border-rose-500/50';
        case 'high': return 'bg-gradient-to-br from-orange-500/30 to-orange-600/20 border-orange-500/50';
        case 'medium': return 'bg-gradient-to-br from-amber-500/30 to-amber-600/20 border-amber-500/50';
        default: return 'bg-gradient-to-br from-emerald-500/30 to-emerald-600/20 border-emerald-500/50';
    }
};

export function GNNVisualization() {
    const [predictions, setPredictions] = useState<GNNPrediction | null>(null);
    const [cascade, setCascade] = useState<CascadeSimulation | null>(null);
    const [selectedPort, setSelectedPort] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [cascadeLoading, setCascadeLoading] = useState(false);

    // Fetch GNN predictions
    const fetchPredictions = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/gnn/predict`);
            if (response.ok) {
                const data = await response.json();
                setPredictions(data);
            }
        } catch (error) {
            console.error('Failed to fetch GNN predictions:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch cascade simulation
    const fetchCascade = useCallback(async (portCode: string) => {
        setCascadeLoading(true);
        try {
            const response = await fetch(`${API_BASE}/api/v1/gnn/cascade/${portCode}`);
            if (response.ok) {
                const data = await response.json();
                setCascade(data);
            }
        } catch (error) {
            console.error('Failed to fetch cascade:', error);
        } finally {
            setCascadeLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPredictions();
        const interval = setInterval(fetchPredictions, 30000);
        return () => clearInterval(interval);
    }, [fetchPredictions]);

    // Handle port click for cascade simulation
    const handlePortClick = (portCode: string) => {
        setSelectedPort(portCode);
        fetchCascade(portCode);
    };

    if (loading) {
        return (
            <div className="glass-card p-6 rounded-2xl animate-pulse">
                <div className="h-6 bg-zinc-800 rounded w-1/3 mb-4"></div>
                <div className="h-64 bg-zinc-800 rounded"></div>
            </div>
        );
    }

    if (!predictions) {
        return (
            <div className="glass-card p-6 rounded-2xl">
                <p className="text-zinc-400">Failed to load GNN predictions</p>
            </div>
        );
    }

    // Separate ports by region
    const asiaPorts = predictions.node_predictions.filter(p => PORT_INFO[p.port_code]?.region === 'asia');
    const usaPorts = predictions.node_predictions.filter(p => PORT_INFO[p.port_code]?.region === 'usa');

    return (
        <div className="glass-card p-6 rounded-2xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <span className="text-2xl">🧠</span> Graph Neural Network Analysis
                    </h2>
                    <p className="text-sm text-zinc-400 mt-1">
                        AI predicts how port failures cascade through the supply chain
                    </p>
                </div>
                <div className="text-right">
                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${predictions.model_info.uses_pytorch ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse`}></div>
                        <span className="text-xs text-zinc-400">
                            {predictions.model_info.uses_pytorch ? 'PyTorch' : 'NumPy'} Backend
                        </span>
                    </div>
                    <p className="text-3xl font-bold text-white mt-1">{predictions.network_risk_score}%</p>
                    <p className="text-xs text-zinc-500">Overall Network Risk</p>
                </div>
            </div>

            {/* Network Map - Two Regions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                {/* Asia Region */}
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-lg">🌏</span>
                        <h3 className="font-semibold text-white">Asia Pacific</h3>
                        <span className="text-xs text-zinc-500 ml-auto">Origin Ports</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        {asiaPorts.map((port) => (
                            <button
                                key={port.port_code}
                                onClick={() => handlePortClick(port.port_code)}
                                className={`relative p-4 rounded-xl border transition-all hover:scale-[1.02] ${selectedPort === port.port_code
                                        ? 'ring-2 ring-cyan-500 border-cyan-500'
                                        : getRiskBgClass(port.risk_level)
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-bold text-white text-sm">
                                        {PORT_INFO[port.port_code]?.name || port.port_code}
                                    </span>
                                    <span
                                        className="text-lg font-bold"
                                        style={{ color: getRiskColor(port.gnn_risk_score) }}
                                    >
                                        {port.gnn_risk_score}%
                                    </span>
                                </div>
                                <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{
                                            width: `${port.gnn_risk_score}%`,
                                            backgroundColor: getRiskColor(port.gnn_risk_score)
                                        }}
                                    />
                                </div>
                                <p className="text-xs text-zinc-500 mt-2">{port.port_code}</p>
                            </button>
                        ))}
                    </div>
                </div>

                {/* USA Region */}
                <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
                    <div className="flex items-center gap-2 mb-4">
                        <span className="text-lg">🌎</span>
                        <h3 className="font-semibold text-white">US West Coast</h3>
                        <span className="text-xs text-zinc-500 ml-auto">Destination Ports</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        {usaPorts.map((port) => (
                            <button
                                key={port.port_code}
                                onClick={() => handlePortClick(port.port_code)}
                                className={`relative p-4 rounded-xl border transition-all hover:scale-[1.02] ${selectedPort === port.port_code
                                        ? 'ring-2 ring-cyan-500 border-cyan-500'
                                        : getRiskBgClass(port.risk_level)
                                    }`}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-bold text-white text-sm">
                                        {PORT_INFO[port.port_code]?.name || port.port_code}
                                    </span>
                                    <span
                                        className="text-lg font-bold"
                                        style={{ color: getRiskColor(port.gnn_risk_score) }}
                                    >
                                        {port.gnn_risk_score}%
                                    </span>
                                </div>
                                <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-500"
                                        style={{
                                            width: `${port.gnn_risk_score}%`,
                                            backgroundColor: getRiskColor(port.gnn_risk_score)
                                        }}
                                    />
                                </div>
                                <p className="text-xs text-zinc-500 mt-2">{port.port_code}</p>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Cascade Simulation Results */}
            {selectedPort && (
                <div className="bg-gradient-to-br from-zinc-900 to-zinc-800/50 rounded-xl p-4 border border-zinc-700">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <span className="text-2xl">⚡</span>
                            <div>
                                <h3 className="font-semibold text-white">
                                    Cascade Simulation: {PORT_INFO[selectedPort]?.name || selectedPort}
                                </h3>
                                <p className="text-xs text-zinc-400">
                                    What happens if this port fails?
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => { setSelectedPort(null); setCascade(null); }}
                            className="text-zinc-400 hover:text-white transition-colors"
                        >
                            ✕
                        </button>
                    </div>

                    {cascadeLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full"></div>
                            <span className="ml-3 text-zinc-400">Simulating network cascade...</span>
                        </div>
                    ) : cascade ? (
                        <div>
                            {/* Impact Summary */}
                            <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                                    <p className="text-2xl font-bold text-orange-400">{cascade.affected_ports}</p>
                                    <p className="text-xs text-zinc-400">Ports Affected</p>
                                </div>
                                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                                    <p className="text-2xl font-bold text-rose-400">{cascade.propagation_depth}</p>
                                    <p className="text-xs text-zinc-400">Cascade Depth</p>
                                </div>
                                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                                    <p className="text-2xl font-bold text-amber-400">{Math.round(cascade.total_impact_score)}</p>
                                    <p className="text-xs text-zinc-400">Impact Score</p>
                                </div>
                            </div>

                            {/* Cascade Flow */}
                            <div className="space-y-2">
                                {cascade.cascade_simulation
                                    .filter(r => r.cascade_risk_increase > 0)
                                    .slice(0, 6)
                                    .map((result, idx) => (
                                        <div
                                            key={result.port_code}
                                            className={`flex items-center gap-3 p-3 rounded-lg ${result.is_source
                                                    ? 'bg-rose-500/20 border border-rose-500/50'
                                                    : 'bg-zinc-800/50'
                                                }`}
                                        >
                                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-zinc-700 flex items-center justify-center text-sm font-bold text-white">
                                                {idx + 1}
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-center justify-between">
                                                    <span className="font-medium text-white">
                                                        {PORT_INFO[result.port_code]?.name || result.port_code}
                                                        {result.is_source && (
                                                            <span className="ml-2 text-xs bg-rose-500 text-white px-2 py-0.5 rounded">
                                                                SOURCE
                                                            </span>
                                                        )}
                                                    </span>
                                                    <span className={`font-bold ${result.cascade_risk_increase >= 60 ? 'text-rose-400' :
                                                            result.cascade_risk_increase >= 30 ? 'text-orange-400' :
                                                                'text-amber-400'
                                                        }`}>
                                                        +{result.cascade_risk_increase}%
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-amber-500 to-rose-500 rounded-full transition-all duration-500"
                                                            style={{ width: `${result.projected_congestion}%` }}
                                                        />
                                                    </div>
                                                    <span className="text-xs text-zinc-400">
                                                        {result.original_congestion}% → {result.projected_congestion}%
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                            </div>

                            {/* Insight */}
                            <div className="mt-4 p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                                <p className="text-sm text-cyan-300">
                                    <span className="font-bold">💡 AI Insight:</span> If {PORT_INFO[selectedPort]?.name} experiences
                                    a major disruption, it will cascade to {cascade.affected_ports} connected ports within {cascade.propagation_depth} network hops.
                                </p>
                            </div>
                        </div>
                    ) : null}
                </div>
            )}

            {/* Instructions when no port selected */}
            {!selectedPort && (
                <div className="text-center py-6 text-zinc-500">
                    <p className="text-lg mb-2">👆 Click on any port above to simulate a failure cascade</p>
                    <p className="text-sm">The GNN predicts how disruptions propagate through the supply chain network</p>
                </div>
            )}

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs">
                    <span className="text-zinc-500">Risk Level:</span>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                        <span className="text-zinc-400">Low</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                        <span className="text-zinc-400">Medium</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                        <span className="text-zinc-400">High</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                        <span className="text-zinc-400">Critical</span>
                    </div>
                </div>
                <span className="text-xs text-zinc-500">
                    Updated: {new Date(predictions.timestamp).toLocaleTimeString()}
                </span>
            </div>
        </div>
    );
}

export default GNNVisualization;
