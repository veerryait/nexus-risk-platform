'use client';

import { useState, useEffect } from 'react';
import { Navigation, PageHeader } from '@/components/Navigation';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Scenario {
    id: string;
    name: string;
    description: string;
    icon: string;
    affected_regions: string[];
    primary_impact: string;
}

interface RouteImpact {
    route_id: string;
    origin: string;
    destination: string;
    original_delay: number;
    simulated_delay: number;
    delay_increase: number;
    cost_increase_percent: number;
    status: string;
}

interface AlternativeRoute {
    route_id: string;
    origin: string;
    destination: string;
    via: string[];
    additional_distance_nm: number;
    additional_days: number;
    cost_increase_percent: number;
    capacity_available?: number;
    recommendation: string;
}

interface ModelMetrics {
    confidence_score: number;
    data_quality: string;
    calibration_source: string;
    estimated_accuracy: number;
    precision_estimate: number;
    recall_estimate: number;
    f1_score: number;
    historical_events_used: number;
    data_freshness_days: number;
    model_version: string;
}

interface SimulationResult {
    scenario_id: string;
    scenario_type: string;
    severity: string;
    duration_days: number;
    simulated_at: string;
    total_routes_affected: number;
    routes_blocked: number;
    routes_severely_impacted: number;
    average_delay_increase: number;
    max_delay_increase: number;
    average_cost_increase: number;
    route_impacts: RouteImpact[];
    alternative_routes: AlternativeRoute[];
    recommendations: string[];
    supply_chain_risk_score: number;
    recovery_time_estimate: number;
    economic_impact_million_usd: number;
    model_metrics?: ModelMetrics;
}

const SEVERITY_LEVELS = [
    { id: 'low', label: 'Low', color: 'bg-emerald-500', description: 'Minor disruption' },
    { id: 'medium', label: 'Medium', color: 'bg-amber-500', description: 'Moderate impact' },
    { id: 'high', label: 'High', color: 'bg-orange-500', description: 'Significant disruption' },
    { id: 'critical', label: 'Critical', color: 'bg-rose-500', description: 'Severe crisis' },
];

export default function ScenariosPage() {
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [selectedScenario, setSelectedScenario] = useState<string>('taiwan_strait');
    const [severity, setSeverity] = useState<string>('high');
    const [duration, setDuration] = useState<number>(14);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState<SimulationResult | null>(null);
    const [showResults, setShowResults] = useState(false);

    // Fetch available scenarios
    useEffect(() => {
        const fetchScenarios = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/scenarios/scenarios`);
                if (res.ok) {
                    const data = await res.json();
                    setScenarios(data.scenarios || []);
                }
            } catch (err) {
                console.error('Failed to fetch scenarios:', err);
                // Fallback scenarios
                setScenarios([
                    { id: 'taiwan_strait', name: 'Taiwan Strait Closure', description: 'Military tensions restricting shipping', icon: '⚔️', affected_regions: ['Taiwan'], primary_impact: 'Semiconductor supply chain' },
                    { id: 'port_strike', name: 'Major Port Strike', description: 'Labor dispute causing port shutdown', icon: '✊', affected_regions: ['US West Coast'], primary_impact: 'Container throughput' },
                    { id: 'typhoon', name: 'Super Typhoon', description: 'Category 5 typhoon affecting Asia', icon: '🌀', affected_regions: ['Taiwan', 'Japan'], primary_impact: 'Vessel diversions' },
                    { id: 'suez_closure', name: 'Suez Canal Blockage', description: 'Canal obstruction', icon: '🚢', affected_regions: ['Global'], primary_impact: 'Global rerouting' },
                ]);
            }
        };
        fetchScenarios();
    }, []);

    const runSimulation = async () => {
        setLoading(true);
        setShowResults(false);

        try {
            const res = await fetch(`${API_BASE}/api/v1/scenarios/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scenario_type: selectedScenario,
                    severity: severity,
                    duration_days: duration
                })
            });

            if (res.ok) {
                const data = await res.json();
                setResult(data);
                setShowResults(true);
            } else {
                console.error('Simulation failed');
            }
        } catch (err) {
            console.error('Error running simulation:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'blocked': return 'bg-rose-500 text-white';
            case 'severely_impacted': return 'bg-orange-500 text-white';
            case 'moderately_impacted': return 'bg-amber-500 text-black';
            default: return 'bg-emerald-500 text-white';
        }
    };

    const selectedScenarioData = scenarios.find(s => s.id === selectedScenario);

    return (
        <div className="min-h-screen bg-zinc-950 grid-bg">
            <Navigation />

            <main className="max-w-7xl mx-auto px-4 py-8">
                <PageHeader
                    icon="🎯"
                    title="Scenario Simulation"
                    subtitle="Interactive 'What-If' Analysis for Supply Chain Disruptions"
                />

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Panel - Scenario Builder */}
                    <div className="lg:col-span-1">
                        <div className="glass-card rounded-2xl p-6 sticky top-6">
                            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                                <span className="text-2xl">🎮</span> Scenario Builder
                            </h2>

                            {/* Scenario Type Selection */}
                            <div className="mb-6">
                                <label className="block text-sm text-zinc-400 mb-3">Event Type</label>
                                <div className="grid grid-cols-2 gap-2">
                                    {scenarios.map(scenario => (
                                        <button
                                            key={scenario.id}
                                            onClick={() => setSelectedScenario(scenario.id)}
                                            className={`p-3 rounded-xl border text-left transition-all ${selectedScenario === scenario.id
                                                ? 'border-cyan-500 bg-cyan-500/20 shadow-lg shadow-cyan-500/20'
                                                : 'border-zinc-700 bg-zinc-800/50 hover:border-zinc-600'
                                                }`}
                                        >
                                            <span className="text-2xl block mb-1">{scenario.icon}</span>
                                            <span className="text-xs font-medium text-white block truncate">{scenario.name}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Selected Scenario Info */}
                            {selectedScenarioData && (
                                <div className="mb-6 p-3 bg-zinc-800/50 rounded-xl border border-zinc-700">
                                    <p className="text-sm text-zinc-300">{selectedScenarioData.description}</p>
                                    <div className="mt-2 flex flex-wrap gap-1">
                                        {selectedScenarioData.affected_regions.map(region => (
                                            <span key={region} className="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 rounded">
                                                {region}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Severity Slider */}
                            <div className="mb-6">
                                <label className="block text-sm text-zinc-400 mb-3">Severity Level</label>
                                <div className="flex gap-2">
                                    {SEVERITY_LEVELS.map(level => (
                                        <button
                                            key={level.id}
                                            onClick={() => setSeverity(level.id)}
                                            className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all ${severity === level.id
                                                ? `${level.color} text-white shadow-lg`
                                                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                                }`}
                                        >
                                            {level.label}
                                        </button>
                                    ))}
                                </div>
                                <p className="text-xs text-zinc-500 mt-2">
                                    {SEVERITY_LEVELS.find(l => l.id === severity)?.description}
                                </p>
                            </div>

                            {/* Duration Slider */}
                            <div className="mb-6">
                                <label className="block text-sm text-zinc-400 mb-3">
                                    Duration: <span className="text-white font-bold">{duration} days</span>
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="90"
                                    value={duration}
                                    onChange={(e) => setDuration(parseInt(e.target.value))}
                                    className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                                />
                                <div className="flex justify-between text-xs text-zinc-500 mt-1">
                                    <span>1 day</span>
                                    <span>90 days</span>
                                </div>
                            </div>

                            {/* Run Simulation Button */}
                            <button
                                onClick={runSimulation}
                                disabled={loading}
                                className="w-full py-4 rounded-xl font-bold text-lg transition-all duration-300 relative overflow-hidden group disabled:opacity-50"
                                style={{
                                    background: 'linear-gradient(135deg, #00f0ff 0%, #ff00ff 100%)',
                                }}
                            >
                                <span className="relative z-10 text-black">
                                    {loading ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <span className="animate-spin">⏳</span> Simulating...
                                        </span>
                                    ) : (
                                        '🚀 Run Simulation'
                                    )}
                                </span>
                                <div className="absolute inset-0 bg-white opacity-0 group-hover:opacity-20 transition-opacity" />
                            </button>
                        </div>
                    </div>

                    {/* Right Panel - Results */}
                    <div className="lg:col-span-2">
                        {!showResults ? (
                            <div className="glass-card rounded-2xl p-12 text-center">
                                <div className="text-6xl mb-4">🎯</div>
                                <h3 className="text-xl font-bold text-white mb-2">Ready to Simulate</h3>
                                <p className="text-zinc-400">
                                    Configure your scenario parameters and click "Run Simulation" to see the impact analysis.
                                </p>
                            </div>
                        ) : result && (
                            <div className="space-y-6 animate-fadeIn">
                                {/* Summary Cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="glass-card rounded-xl p-4 text-center border-l-4 border-rose-500">
                                        <p className="text-3xl font-bold text-rose-400">{result.total_routes_affected}</p>
                                        <p className="text-xs text-zinc-400 mt-1">Routes Affected</p>
                                    </div>
                                    <div className="glass-card rounded-xl p-4 text-center border-l-4 border-orange-500">
                                        <p className="text-3xl font-bold text-orange-400">+{result.average_delay_increase}d</p>
                                        <p className="text-xs text-zinc-400 mt-1">Avg Delay Increase</p>
                                    </div>
                                    <div className="glass-card rounded-xl p-4 text-center border-l-4 border-amber-500">
                                        <p className="text-3xl font-bold text-amber-400">+{result.average_cost_increase}%</p>
                                        <p className="text-xs text-zinc-400 mt-1">Cost Increase</p>
                                    </div>
                                    <div className="glass-card rounded-xl p-4 text-center border-l-4 border-cyan-500">
                                        <p className="text-3xl font-bold text-cyan-400">{result.alternative_routes.length}</p>
                                        <p className="text-xs text-zinc-400 mt-1">Alternatives Found</p>
                                    </div>
                                </div>

                                {/* Risk Score Gauge */}
                                <div className="glass-card rounded-xl p-6">
                                    <h3 className="text-lg font-bold text-white mb-4">Supply Chain Risk Assessment</h3>
                                    <div className="flex items-center gap-6">
                                        <div className="relative w-32 h-32">
                                            <svg className="w-32 h-32 transform -rotate-90">
                                                <circle cx="64" cy="64" r="56" stroke="#27272a" strokeWidth="8" fill="none" />
                                                <circle
                                                    cx="64" cy="64" r="56"
                                                    stroke={result.supply_chain_risk_score > 70 ? '#f43f5e' : result.supply_chain_risk_score > 40 ? '#f59e0b' : '#22c55e'}
                                                    strokeWidth="8"
                                                    fill="none"
                                                    strokeLinecap="round"
                                                    strokeDasharray={`${result.supply_chain_risk_score * 3.52} 352`}
                                                    className="transition-all duration-1000"
                                                />
                                            </svg>
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <span className="text-2xl font-bold text-white">{Math.round(result.supply_chain_risk_score)}</span>
                                            </div>
                                        </div>
                                        <div className="flex-1 grid grid-cols-2 gap-4">
                                            <div>
                                                <p className="text-sm text-zinc-400">Recovery Time</p>
                                                <p className="text-xl font-bold text-white">{result.recovery_time_estimate} days</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-zinc-400">Economic Impact</p>
                                                <p className="text-xl font-bold text-white">${result.economic_impact_million_usd}M</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-zinc-400">Routes Blocked</p>
                                                <p className="text-xl font-bold text-rose-400">{result.routes_blocked}</p>
                                            </div>
                                            <div>
                                                <p className="text-sm text-zinc-400">Severely Impacted</p>
                                                <p className="text-xl font-bold text-orange-400">{result.routes_severely_impacted}</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Recommendations */}
                                <div className="glass-card rounded-xl p-6">
                                    <h3 className="text-lg font-bold text-white mb-4">📋 Recommendations</h3>
                                    <div className="space-y-2">
                                        {result.recommendations.map((rec, idx) => (
                                            <div key={idx} className="flex items-start gap-3 p-3 bg-zinc-800/50 rounded-lg">
                                                <span className="text-lg">{rec.split(' ')[0]}</span>
                                                <p className="text-sm text-zinc-300">{rec.split(' ').slice(1).join(' ')}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Model Accuracy Metrics */}
                                {result.model_metrics && (
                                    <div className="glass-card rounded-xl p-6 border border-purple-500/30">
                                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                            <span>📈</span> Model Accuracy Metrics
                                            <span className="ml-auto text-xs font-normal px-2 py-1 bg-purple-500/20 text-purple-400 rounded">
                                                v{result.model_metrics.model_version}
                                            </span>
                                        </h3>

                                        {/* Calibration Source */}
                                        <div className="mb-4 p-3 bg-zinc-800/50 rounded-lg border border-zinc-700">
                                            <p className="text-xs text-zinc-400">Calibrated Against:</p>
                                            <p className="text-sm font-medium text-cyan-400">{result.model_metrics.calibration_source}</p>
                                        </div>

                                        {/* Metrics Grid */}
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                            <div className="text-center">
                                                <div className="relative w-16 h-16 mx-auto mb-2">
                                                    <svg className="w-16 h-16 transform -rotate-90">
                                                        <circle cx="32" cy="32" r="28" stroke="#27272a" strokeWidth="4" fill="none" />
                                                        <circle
                                                            cx="32" cy="32" r="28"
                                                            stroke="#a855f7"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            strokeLinecap="round"
                                                            strokeDasharray={`${result.model_metrics.confidence_score * 176} 176`}
                                                        />
                                                    </svg>
                                                    <div className="absolute inset-0 flex items-center justify-center">
                                                        <span className="text-sm font-bold text-white">{Math.round(result.model_metrics.confidence_score * 100)}%</span>
                                                    </div>
                                                </div>
                                                <p className="text-xs text-zinc-400">Confidence</p>
                                            </div>

                                            <div className="text-center">
                                                <div className="relative w-16 h-16 mx-auto mb-2">
                                                    <svg className="w-16 h-16 transform -rotate-90">
                                                        <circle cx="32" cy="32" r="28" stroke="#27272a" strokeWidth="4" fill="none" />
                                                        <circle
                                                            cx="32" cy="32" r="28"
                                                            stroke="#22c55e"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            strokeLinecap="round"
                                                            strokeDasharray={`${result.model_metrics.estimated_accuracy * 176} 176`}
                                                        />
                                                    </svg>
                                                    <div className="absolute inset-0 flex items-center justify-center">
                                                        <span className="text-sm font-bold text-white">{Math.round(result.model_metrics.estimated_accuracy * 100)}%</span>
                                                    </div>
                                                </div>
                                                <p className="text-xs text-zinc-400">Accuracy</p>
                                            </div>

                                            <div className="text-center">
                                                <div className="relative w-16 h-16 mx-auto mb-2">
                                                    <svg className="w-16 h-16 transform -rotate-90">
                                                        <circle cx="32" cy="32" r="28" stroke="#27272a" strokeWidth="4" fill="none" />
                                                        <circle
                                                            cx="32" cy="32" r="28"
                                                            stroke="#3b82f6"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            strokeLinecap="round"
                                                            strokeDasharray={`${result.model_metrics.precision_estimate * 176} 176`}
                                                        />
                                                    </svg>
                                                    <div className="absolute inset-0 flex items-center justify-center">
                                                        <span className="text-sm font-bold text-white">{Math.round(result.model_metrics.precision_estimate * 100)}%</span>
                                                    </div>
                                                </div>
                                                <p className="text-xs text-zinc-400">Precision</p>
                                            </div>

                                            <div className="text-center">
                                                <div className="relative w-16 h-16 mx-auto mb-2">
                                                    <svg className="w-16 h-16 transform -rotate-90">
                                                        <circle cx="32" cy="32" r="28" stroke="#27272a" strokeWidth="4" fill="none" />
                                                        <circle
                                                            cx="32" cy="32" r="28"
                                                            stroke="#f59e0b"
                                                            strokeWidth="4"
                                                            fill="none"
                                                            strokeLinecap="round"
                                                            strokeDasharray={`${result.model_metrics.recall_estimate * 176} 176`}
                                                        />
                                                    </svg>
                                                    <div className="absolute inset-0 flex items-center justify-center">
                                                        <span className="text-sm font-bold text-white">{Math.round(result.model_metrics.recall_estimate * 100)}%</span>
                                                    </div>
                                                </div>
                                                <p className="text-xs text-zinc-400">Recall</p>
                                            </div>
                                        </div>

                                        {/* F1 Score Bar */}
                                        <div className="mb-4">
                                            <div className="flex justify-between text-xs mb-1">
                                                <span className="text-zinc-400">F1 Score</span>
                                                <span className="text-white font-bold">{Math.round(result.model_metrics.f1_score * 100)}%</span>
                                            </div>
                                            <div className="h-2 bg-zinc-700 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 rounded-full transition-all duration-500"
                                                    style={{ width: `${result.model_metrics.f1_score * 100}%` }}
                                                />
                                            </div>
                                        </div>

                                        {/* Data Quality */}
                                        <div className="flex items-center justify-between text-xs">
                                            <span className="text-zinc-400">Data Quality:
                                                <span className={`ml-1 font-bold ${result.model_metrics.data_quality === 'high' ? 'text-emerald-400' :
                                                    result.model_metrics.data_quality === 'medium' ? 'text-amber-400' : 'text-rose-400'
                                                    }`}>
                                                    {result.model_metrics.data_quality.toUpperCase()}
                                                </span>
                                            </span>
                                            <span className="text-zinc-500">
                                                {result.model_metrics.historical_events_used} events | Updated {result.model_metrics.data_freshness_days}d ago
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Alternative Routes */}
                                {result.alternative_routes.length > 0 && (
                                    <div className="glass-card rounded-xl p-6">
                                        <h3 className="text-lg font-bold text-white mb-4">🔄 Alternative Routes</h3>
                                        <div className="space-y-3">
                                            {result.alternative_routes.map((alt, idx) => (
                                                <div key={idx} className="p-4 bg-zinc-800/50 rounded-xl border border-zinc-700">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className="text-sm font-bold text-cyan-400">{alt.route_id}</span>
                                                        <span className="px-2 py-1 text-xs bg-emerald-500/20 text-emerald-400 rounded">
                                                            +{alt.additional_days} days
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-zinc-300">
                                                        {alt.origin} → {alt.via.join(' → ')} → {alt.destination}
                                                    </p>
                                                    <div className="flex items-center gap-4 mt-2 text-xs text-zinc-400">
                                                        <span>+{alt.additional_distance_nm} nm</span>
                                                        <span>+{alt.cost_increase_percent}% cost</span>
                                                        {alt.capacity_available && (
                                                            <span className="text-emerald-400">{Math.round(alt.capacity_available * 100)}% capacity</span>
                                                        )}
                                                    </div>
                                                    <p className="text-xs text-zinc-500 mt-2 italic">{alt.recommendation}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Detailed Route Impacts */}
                                <div className="glass-card rounded-xl p-6">
                                    <h3 className="text-lg font-bold text-white mb-4">📊 Route Impact Details</h3>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-left text-zinc-400 border-b border-zinc-700">
                                                    <th className="py-2 px-3">Route</th>
                                                    <th className="py-2 px-3">Origin → Destination</th>
                                                    <th className="py-2 px-3">Delay</th>
                                                    <th className="py-2 px-3">Cost</th>
                                                    <th className="py-2 px-3">Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {result.route_impacts.map((route, idx) => (
                                                    <tr key={idx} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                                                        <td className="py-2 px-3 font-mono text-cyan-400">{route.route_id}</td>
                                                        <td className="py-2 px-3 text-zinc-300">
                                                            <span className="text-xs">{route.origin} → {route.destination}</span>
                                                        </td>
                                                        <td className="py-2 px-3">
                                                            <span className="text-white">+{route.delay_increase}d</span>
                                                            <span className="text-zinc-500 text-xs ml-1">({route.simulated_delay}d total)</span>
                                                        </td>
                                                        <td className={`py-2 px-3 ${route.cost_increase_percent > 50 ? 'text-rose-400' : route.cost_increase_percent > 20 ? 'text-amber-400' : 'text-zinc-300'}`}>
                                                            +{route.cost_increase_percent}%
                                                        </td>
                                                        <td className="py-2 px-3">
                                                            <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(route.status)}`}>
                                                                {route.status.replace('_', ' ')}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Simulation ID */}
                                <p className="text-xs text-zinc-500 text-center">
                                    Simulation ID: {result.scenario_id} | Generated at: {new Date(result.simulated_at).toLocaleString()}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}
