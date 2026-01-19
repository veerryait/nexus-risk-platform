'use client';

import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
interface Insight {
    category: string;
    icon: string;
    title: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    action: string;
}

interface DashboardSummary {
    generated_at: string;
    overall_status: 'healthy' | 'warning' | 'critical';
    overall_message: string;
    insights: Insight[];
    quick_stats: {
        total_routes: number;
        high_risk_routes: number;
        delayed_routes: number;
        congested_ports: number;
        active_weather: number;
    };
}

interface DelayExplanation {
    route_id: string;
    summary: string;
    predicted_delay_days: number;
    risk_level: string;
    confidence: number;
    primary_causes: Array<{
        type: string;
        icon: string;
        title: string;
        description: string;
        impact: string;
    }>;
    contributing_factors: Array<{
        type: string;
        icon: string;
        description: string;
        impact: string;
    }>;
    recommendations: string[];
}

interface FeatureImportance {
    prediction_value: number;
    feature_contributions: Array<{
        feature: string;
        icon: string;
        importance_pct: number;
        direction: string;
    }>;
    interpretation: string;
}

const severityColors = {
    low: 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400',
    medium: 'bg-amber-500/20 border-amber-500/50 text-amber-400',
    high: 'bg-rose-500/20 border-rose-500/50 text-rose-400'
};

const statusColors = {
    healthy: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', icon: '✅' },
    warning: { bg: 'bg-amber-500/20', text: 'text-amber-400', icon: '⚠️' },
    critical: { bg: 'bg-rose-500/20', text: 'text-rose-400', icon: '🚨' }
};

export function AIInsightsPanel() {
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(false);

    const fetchSummary = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/xai/dashboard-summary`);
            if (response.ok) {
                const data = await response.json();
                setSummary(data);
            }
        } catch (error) {
            console.error('Failed to fetch AI summary:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSummary();
        const interval = setInterval(fetchSummary, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, [fetchSummary]);

    if (loading) {
        return (
            <div className="glass-card p-4 rounded-2xl animate-pulse">
                <div className="h-6 bg-zinc-800 rounded w-1/3 mb-3"></div>
                <div className="h-20 bg-zinc-800 rounded"></div>
            </div>
        );
    }

    if (!summary) return null;

    const status = statusColors[summary.overall_status];

    return (
        <div className="glass-card p-5 rounded-2xl mb-6">
            {/* Header with overall status */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <span className="text-3xl">{status.icon}</span>
                    <div>
                        <h2 className="text-lg font-bold text-white">AI Situation Analysis</h2>
                        <p className={`text-sm ${status.text}`}>{summary.overall_message}</p>
                    </div>
                </div>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="px-3 py-1.5 text-sm bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors"
                >
                    {expanded ? 'Show Less' : 'Show Details'}
                </button>
            </div>

            {/* Quick Stats Bar */}
            <div className="grid grid-cols-5 gap-3 mb-4">
                <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
                    <p className="text-xl font-bold text-white">{summary.quick_stats.total_routes}</p>
                    <p className="text-xs text-zinc-400">Routes</p>
                </div>
                <div className={`rounded-lg p-3 text-center ${summary.quick_stats.high_risk_routes > 0 ? 'bg-rose-500/20' : 'bg-zinc-800/50'}`}>
                    <p className={`text-xl font-bold ${summary.quick_stats.high_risk_routes > 0 ? 'text-rose-400' : 'text-white'}`}>
                        {summary.quick_stats.high_risk_routes}
                    </p>
                    <p className="text-xs text-zinc-400">High Risk</p>
                </div>
                <div className={`rounded-lg p-3 text-center ${summary.quick_stats.delayed_routes > 0 ? 'bg-amber-500/20' : 'bg-zinc-800/50'}`}>
                    <p className={`text-xl font-bold ${summary.quick_stats.delayed_routes > 0 ? 'text-amber-400' : 'text-white'}`}>
                        {summary.quick_stats.delayed_routes}
                    </p>
                    <p className="text-xs text-zinc-400">Delayed</p>
                </div>
                <div className={`rounded-lg p-3 text-center ${summary.quick_stats.congested_ports > 0 ? 'bg-orange-500/20' : 'bg-zinc-800/50'}`}>
                    <p className={`text-xl font-bold ${summary.quick_stats.congested_ports > 0 ? 'text-orange-400' : 'text-white'}`}>
                        {summary.quick_stats.congested_ports}
                    </p>
                    <p className="text-xs text-zinc-400">Congested</p>
                </div>
                <div className={`rounded-lg p-3 text-center ${summary.quick_stats.active_weather > 0 ? 'bg-cyan-500/20' : 'bg-zinc-800/50'}`}>
                    <p className={`text-xl font-bold ${summary.quick_stats.active_weather > 0 ? 'text-cyan-400' : 'text-white'}`}>
                        {summary.quick_stats.active_weather}
                    </p>
                    <p className="text-xs text-zinc-400">Weather</p>
                </div>
            </div>

            {/* Insights Cards */}
            {expanded && (
                <div className="space-y-3 mt-4 pt-4 border-t border-zinc-800">
                    <h3 className="text-sm font-semibold text-zinc-400 mb-3">💡 AI Insights & Recommendations</h3>
                    {summary.insights.map((insight, idx) => (
                        <div
                            key={idx}
                            className={`p-4 rounded-xl border ${severityColors[insight.severity]}`}
                        >
                            <div className="flex items-start gap-3">
                                <span className="text-2xl">{insight.icon}</span>
                                <div className="flex-1">
                                    <div className="flex items-center justify-between">
                                        <h4 className="font-semibold text-white">{insight.title}</h4>
                                        <span className={`text-xs px-2 py-0.5 rounded ${insight.severity === 'high' ? 'bg-rose-500/30 text-rose-300' :
                                                insight.severity === 'medium' ? 'bg-amber-500/30 text-amber-300' :
                                                    'bg-emerald-500/30 text-emerald-300'
                                            }`}>
                                            {insight.severity.toUpperCase()}
                                        </span>
                                    </div>
                                    <p className="text-sm text-zinc-300 mt-1">{insight.description}</p>
                                    <div className="mt-2 flex items-center gap-2">
                                        <span className="text-xs text-cyan-400">💡 Recommendation:</span>
                                        <span className="text-xs text-zinc-300">{insight.action}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* AI Badge */}
            <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                <span className="flex items-center gap-1">
                    <span className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse"></span>
                    Powered by Explainable AI
                </span>
                <span>Updated: {new Date(summary.generated_at).toLocaleTimeString()}</span>
            </div>
        </div>
    );
}

export function RouteExplanationCard({ routeId }: { routeId: string }) {
    const [explanation, setExplanation] = useState<DelayExplanation | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchExplanation = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v1/xai/delay/${routeId}`);
                if (response.ok) {
                    const data = await response.json();
                    setExplanation(data);
                }
            } catch (error) {
                console.error('Failed to fetch explanation:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchExplanation();
    }, [routeId]);

    if (loading) {
        return <div className="animate-pulse h-32 bg-zinc-800/50 rounded-xl"></div>;
    }

    if (!explanation) return null;

    const riskColors: Record<string, string> = {
        low: 'text-emerald-400',
        medium: 'text-amber-400',
        high: 'text-orange-400',
        critical: 'text-rose-400'
    };

    return (
        <div className="bg-gradient-to-br from-zinc-900 to-zinc-800/50 rounded-xl p-4 border border-zinc-700">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-xl">🧠</span>
                    <span className="font-semibold text-white">AI Analysis</span>
                </div>
                <span className={`text-sm font-bold ${riskColors[explanation.risk_level]}`}>
                    {explanation.predicted_delay_days.toFixed(1)} days delay
                </span>
            </div>

            {/* Summary */}
            <p className="text-sm text-zinc-300 mb-4">{explanation.summary}</p>

            {/* Primary Causes */}
            {explanation.primary_causes.length > 0 && (
                <div className="space-y-2 mb-4">
                    <h4 className="text-xs font-semibold text-zinc-400">⚠️ PRIMARY CAUSES</h4>
                    {explanation.primary_causes.map((cause, idx) => (
                        <div key={idx} className="flex items-start gap-2 bg-zinc-800/50 p-3 rounded-lg">
                            <span className="text-lg">{cause.icon}</span>
                            <div>
                                <p className="text-sm font-medium text-white">{cause.title}</p>
                                <p className="text-xs text-zinc-400">{cause.description}</p>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Contributing Factors */}
            {explanation.contributing_factors.length > 0 && (
                <div className="space-y-1 mb-4">
                    <h4 className="text-xs font-semibold text-zinc-400">📊 CONTRIBUTING FACTORS</h4>
                    <div className="flex flex-wrap gap-2">
                        {explanation.contributing_factors.map((factor, idx) => (
                            <span
                                key={idx}
                                className="inline-flex items-center gap-1 px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300"
                            >
                                {factor.icon} {factor.description}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Recommendations */}
            <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-cyan-400 mb-2">💡 RECOMMENDATIONS</h4>
                <ul className="space-y-1">
                    {explanation.recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm text-zinc-300 flex items-start gap-2">
                            <span className="text-cyan-400">→</span>
                            {rec}
                        </li>
                    ))}
                </ul>
            </div>

            {/* Confidence */}
            <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
                <span>Confidence: {Math.round(explanation.confidence * 100)}%</span>
                <span>Powered by ML + XAI</span>
            </div>
        </div>
    );
}

export function FeatureImportanceChart({ predictionType = 'delay' }: { predictionType?: string }) {
    const [data, setData] = useState<FeatureImportance | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/v1/xai/feature-importance/${predictionType}`);
                if (response.ok) {
                    const result = await response.json();
                    setData(result);
                }
            } catch (error) {
                console.error('Failed to fetch feature importance:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [predictionType]);

    if (loading || !data) return null;

    return (
        <div className="bg-zinc-900/50 rounded-xl p-4 border border-zinc-800">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <span>📊</span> Why This Prediction?
            </h3>

            <p className="text-xs text-zinc-400 mb-4">{data.interpretation}</p>

            <div className="space-y-2">
                {data.feature_contributions.map((feature, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                        <span className="w-6 text-center">{feature.icon}</span>
                        <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                                <span className="text-xs text-zinc-300">{feature.feature}</span>
                                <span className="text-xs text-zinc-400">{feature.importance_pct}%</span>
                            </div>
                            <div className="h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full rounded-full ${feature.direction === 'increases' ? 'bg-orange-500' : 'bg-emerald-500'
                                        }`}
                                    style={{ width: `${feature.importance_pct}%` }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <p className="text-xs text-zinc-500 mt-3 text-center">
                Orange = increases risk • Green = decreases risk
            </p>
        </div>
    );
}

export default AIInsightsPanel;
