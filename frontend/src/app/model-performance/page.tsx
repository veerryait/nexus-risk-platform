'use client';

import { useState, useEffect } from 'react';
import { Navigation, PageHeader } from '@/components/Navigation';
import dynamic from 'next/dynamic';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
interface HealthStatus {
    score: number;
    status: 'excellent' | 'good' | 'fair' | 'needs_attention';
    last_updated: string;
}

interface CurrentMetrics {
    mae: number;
    rmse: number;
    mape: number;
    precision: number;
    recall: number;
    f1_score: number;
    accuracy: number;
    calibration_error: number;
    sample_size: number;
}

interface CalibrationPoint {
    predicted_confidence: number;
    actual_accuracy: number;
    sample_count: number;
}

interface CalibrationData {
    calibration_curve: CalibrationPoint[];
    expected_calibration_error: number;
    is_well_calibrated: boolean;
    interpretation: string;
}

interface DriftAnalysis {
    status: 'stable' | 'drift_detected';
    feature_drift: { current: number; previous: number; change: number; alert: boolean };
    prediction_drift: { current: number; previous: number; change: number; alert: boolean };
    accuracy_trend: { current: number; previous: number; change: number; alert: boolean };
    recommendation: string;
}

interface PredictionRecord {
    id: string;
    route: string;
    predicted: number;
    actual: number;
    error: number;
    within_1_day: boolean;
    confidence: number;
}

interface PerformanceSummary {
    overall_health: HealthStatus;
    current_metrics: CurrentMetrics;
    trends: {
        timestamps: string[];
        mae: number[];
        precision: number[];
        recall: number[];
        f1_score: number[];
        accuracy: number[];
    };
    calibration: CalibrationData;
    drift_analysis: DriftAnalysis;
    prediction_vs_actual: {
        predictions: PredictionRecord[];
        summary: { total: number; within_1_day: number; within_2_days: number; avg_error: number };
    };
}

export default function ModelPerformancePage() {
    const [summary, setSummary] = useState<PerformanceSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'accuracy' | 'calibration' | 'drift'>('overview');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/model-metrics/summary`);
                if (res.ok) {
                    const data = await res.json();
                    setSummary(data);
                }
            } catch (error) {
                console.error('Failed to fetch model metrics:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <Navigation />

            <main className="max-w-7xl mx-auto px-4 py-8">
                <PageHeader
                    icon="📈"
                    title="Model Performance"
                    subtitle="Track ML model accuracy, calibration, and drift over time"
                />

                {loading ? (
                    <div className="animate-pulse space-y-6">
                        <div className="h-32 bg-zinc-800 rounded-2xl"></div>
                        <div className="h-64 bg-zinc-800 rounded-2xl"></div>
                    </div>
                ) : summary ? (
                    <>
                        {/* Health Score Banner */}
                        <section className="mb-8">
                            <HealthScoreBanner health={summary.overall_health} />
                        </section>

                        {/* Tab Navigation */}
                        <div className="flex gap-2 mb-6 overflow-x-auto">
                            {[
                                { id: 'overview', label: 'Overview', icon: '📊' },
                                { id: 'accuracy', label: 'Accuracy Trends', icon: '📈' },
                                { id: 'calibration', label: 'Calibration', icon: '🎯' },
                                { id: 'drift', label: 'Drift Detection', icon: '📉' },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                                        : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                        }`}
                                >
                                    {tab.icon} {tab.label}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        {activeTab === 'overview' && (
                            <OverviewTab
                                metrics={summary.current_metrics}
                                predVsActual={summary.prediction_vs_actual}
                            />
                        )}

                        {activeTab === 'accuracy' && (
                            <AccuracyTrendsTab trends={summary.trends} />
                        )}

                        {activeTab === 'calibration' && (
                            <CalibrationTab calibration={summary.calibration} />
                        )}

                        {activeTab === 'drift' && (
                            <DriftTab drift={summary.drift_analysis} />
                        )}
                    </>
                ) : (
                    <div className="glass-card p-8 rounded-2xl text-center">
                        <p className="text-zinc-400">Unable to load model metrics</p>
                    </div>
                )}
            </main>
        </div>
    );
}

function HealthScoreBanner({ health }: { health: HealthStatus }) {
    const statusColors = {
        excellent: 'from-emerald-500 to-emerald-600',
        good: 'from-cyan-500 to-cyan-600',
        fair: 'from-amber-500 to-amber-600',
        needs_attention: 'from-rose-500 to-rose-600'
    };

    const statusEmojis = {
        excellent: '🌟',
        good: '✅',
        fair: '⚠️',
        needs_attention: '🚨'
    };

    return (
        <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-r ${statusColors[health.status]} p-6`}>
            <div className="relative z-10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="text-5xl">{statusEmojis[health.status]}</div>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Model Health Score</h2>
                        <p className="text-white/80 capitalize">{health.status.replace('_', ' ')}</p>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-6xl font-bold text-white">{health.score}</div>
                    <div className="text-white/60 text-sm">out of 100</div>
                </div>
            </div>
            {/* Decorative circles */}
            <div className="absolute -right-10 -top-10 w-40 h-40 bg-white/10 rounded-full"></div>
            <div className="absolute -right-5 -bottom-5 w-24 h-24 bg-white/5 rounded-full"></div>
        </div>
    );
}

function OverviewTab({ metrics, predVsActual }: { metrics: CurrentMetrics; predVsActual: any }) {
    return (
        <div className="space-y-6">
            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <MetricCard
                    label="Accuracy"
                    value={`${(metrics.accuracy * 100).toFixed(1)}%`}
                    icon="🎯"
                    description="Overall prediction accuracy"
                    status={metrics.accuracy > 0.9 ? 'good' : metrics.accuracy > 0.8 ? 'fair' : 'poor'}
                />
                <MetricCard
                    label="Precision"
                    value={`${(metrics.precision * 100).toFixed(1)}%`}
                    icon="✓"
                    description="True positive rate"
                    status={metrics.precision > 0.9 ? 'good' : 'fair'}
                />
                <MetricCard
                    label="Recall"
                    value={`${(metrics.recall * 100).toFixed(1)}%`}
                    icon="🔍"
                    description="Sensitivity to true cases"
                    status={metrics.recall > 0.85 ? 'good' : 'fair'}
                />
                <MetricCard
                    label="F1 Score"
                    value={`${(metrics.f1_score * 100).toFixed(1)}%`}
                    icon="⚖️"
                    description="Harmonic mean of P&R"
                    status={metrics.f1_score > 0.88 ? 'good' : 'fair'}
                />
            </div>

            {/* Regression Metrics */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">📏 Delay Prediction Accuracy</h3>
                <div className="grid grid-cols-3 gap-6">
                    <div className="text-center">
                        <p className="text-3xl font-bold text-cyan-400">{metrics.mae.toFixed(2)}</p>
                        <p className="text-sm text-zinc-400">MAE (days)</p>
                        <p className="text-xs text-zinc-500 mt-1">Mean Absolute Error</p>
                    </div>
                    <div className="text-center">
                        <p className="text-3xl font-bold text-purple-400">{metrics.rmse.toFixed(2)}</p>
                        <p className="text-sm text-zinc-400">RMSE (days)</p>
                        <p className="text-xs text-zinc-500 mt-1">Root Mean Square Error</p>
                    </div>
                    <div className="text-center">
                        <p className="text-3xl font-bold text-amber-400">{metrics.mape.toFixed(1)}%</p>
                        <p className="text-sm text-zinc-400">MAPE</p>
                        <p className="text-xs text-zinc-500 mt-1">Mean Abs Percentage Error</p>
                    </div>
                </div>
            </div>

            {/* Prediction vs Actual Scatter */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">🎯 Prediction vs Actual (Recent)</h3>
                <div className="flex items-center gap-4 mb-4">
                    <div className="flex-1 grid grid-cols-3 gap-4 text-center">
                        <div className="bg-emerald-500/20 p-3 rounded-xl">
                            <p className="text-2xl font-bold text-emerald-400">{predVsActual.summary.within_1_day}</p>
                            <p className="text-xs text-zinc-400">Within 1 day</p>
                        </div>
                        <div className="bg-amber-500/20 p-3 rounded-xl">
                            <p className="text-2xl font-bold text-amber-400">{predVsActual.summary.within_2_days}</p>
                            <p className="text-xs text-zinc-400">Within 2 days</p>
                        </div>
                        <div className="bg-cyan-500/20 p-3 rounded-xl">
                            <p className="text-2xl font-bold text-cyan-400">{predVsActual.summary.avg_error}</p>
                            <p className="text-xs text-zinc-400">Avg Error (days)</p>
                        </div>
                    </div>
                </div>

                {/* Mini scatter plot representation */}
                <div className="h-64 bg-zinc-800/50 rounded-xl p-4 relative">
                    <div className="absolute inset-4">
                        {/* Perfect prediction line */}
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-full h-0.5 bg-zinc-600 rotate-45 origin-center" style={{ width: '141%', marginLeft: '-20%' }}></div>
                        </div>
                        {/* Data points */}
                        {predVsActual.predictions.slice(0, 30).map((p: PredictionRecord, i: number) => {
                            const x = (p.predicted / 12) * 100;
                            const y = 100 - (p.actual / 12) * 100;
                            return (
                                <div
                                    key={i}
                                    className={`absolute w-2.5 h-2.5 rounded-full transition-all hover:scale-150 ${p.within_1_day ? 'bg-emerald-400' : 'bg-rose-400'
                                        }`}
                                    style={{ left: `${Math.min(95, Math.max(5, x))}%`, top: `${Math.min(95, Math.max(5, y))}%` }}
                                    title={`Predicted: ${p.predicted.toFixed(1)}d, Actual: ${p.actual.toFixed(1)}d`}
                                />
                            );
                        })}
                    </div>
                    {/* Axes labels */}
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs text-zinc-500">Predicted Delay (days)</div>
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 -rotate-90 text-xs text-zinc-500">Actual Delay</div>
                </div>
                <div className="flex justify-center gap-4 mt-2 text-xs">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 bg-emerald-400 rounded-full"></span> Within 1 day</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 bg-rose-400 rounded-full"></span> &gt; 1 day error</span>
                    <span className="flex items-center gap-1"><span className="w-4 h-0.5 bg-zinc-500"></span> Perfect prediction</span>
                </div>
            </div>
        </div>
    );
}

function AccuracyTrendsTab({ trends }: { trends: any }) {
    const days = trends.accuracy.length;

    return (
        <div className="space-y-6">
            {/* Accuracy over time */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">📈 Accuracy Over Time ({days} days)</h3>
                <div className="h-64 relative">
                    <TrendChart data={trends.accuracy} color="#22c55e" label="Accuracy" />
                </div>
            </div>

            {/* Precision, Recall, F1 trends */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="glass-card p-4 rounded-xl">
                    <h4 className="text-sm font-medium text-zinc-400 mb-3">Precision Trend</h4>
                    <div className="h-32">
                        <TrendChart data={trends.precision} color="#8b5cf6" label="Precision" />
                    </div>
                    <p className="text-center text-lg font-bold text-purple-400 mt-2">
                        {(trends.precision[trends.precision.length - 1] * 100).toFixed(1)}%
                    </p>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <h4 className="text-sm font-medium text-zinc-400 mb-3">Recall Trend</h4>
                    <div className="h-32">
                        <TrendChart data={trends.recall} color="#f59e0b" label="Recall" />
                    </div>
                    <p className="text-center text-lg font-bold text-amber-400 mt-2">
                        {(trends.recall[trends.recall.length - 1] * 100).toFixed(1)}%
                    </p>
                </div>
                <div className="glass-card p-4 rounded-xl">
                    <h4 className="text-sm font-medium text-zinc-400 mb-3">F1 Score Trend</h4>
                    <div className="h-32">
                        <TrendChart data={trends.f1_score} color="#06b6d4" label="F1" />
                    </div>
                    <p className="text-center text-lg font-bold text-cyan-400 mt-2">
                        {(trends.f1_score[trends.f1_score.length - 1] * 100).toFixed(1)}%
                    </p>
                </div>
            </div>

            {/* MAE trend */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">📉 Mean Absolute Error Over Time</h3>
                <div className="h-48">
                    <TrendChart data={trends.mae} color="#f43f5e" label="MAE (days)" invert />
                </div>
                <p className="text-center text-sm text-zinc-400 mt-2">
                    Lower is better • Current: <span className="text-rose-400 font-bold">{trends.mae[trends.mae.length - 1].toFixed(2)} days</span>
                </p>
            </div>
        </div>
    );
}

function TrendChart({ data, color, label, invert = false }: { data: number[]; color: string; label: string; invert?: boolean }) {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    return (
        <svg className="w-full h-full" viewBox="0 0 300 100" preserveAspectRatio="none">
            {/* Grid lines */}
            {[0, 25, 50, 75, 100].map(y => (
                <line key={y} x1="0" y1={y} x2="300" y2={y} stroke="#27272a" strokeWidth="0.5" />
            ))}
            {/* Line chart */}
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="2"
                points={data.map((v, i) => {
                    const x = (i / (data.length - 1)) * 300;
                    const y = invert
                        ? ((v - min) / range) * 90 + 5
                        : 95 - ((v - min) / range) * 90;
                    return `${x},${y}`;
                }).join(' ')}
            />
            {/* Area fill */}
            <polygon
                fill={`${color}20`}
                points={`0,100 ${data.map((v, i) => {
                    const x = (i / (data.length - 1)) * 300;
                    const y = invert
                        ? ((v - min) / range) * 90 + 5
                        : 95 - ((v - min) / range) * 90;
                    return `${x},${y}`;
                }).join(' ')} 300,100`}
            />
        </svg>
    );
}

function CalibrationTab({ calibration }: { calibration: CalibrationData }) {
    return (
        <div className="space-y-6">
            {/* ECE Score */}
            <div className={`glass-card p-6 rounded-2xl border-2 ${calibration.is_well_calibrated ? 'border-emerald-500/30' : 'border-amber-500/30'
                }`}>
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-semibold text-white">Expected Calibration Error (ECE)</h3>
                        <p className="text-sm text-zinc-400 mt-1">{calibration.interpretation}</p>
                    </div>
                    <div className="text-right">
                        <p className={`text-4xl font-bold ${calibration.is_well_calibrated ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {(calibration.expected_calibration_error * 100).toFixed(1)}%
                        </p>
                        <p className="text-xs text-zinc-500">Target: &lt;10%</p>
                    </div>
                </div>
            </div>

            {/* Calibration Curve */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">🎯 Calibration Curve</h3>
                <p className="text-sm text-zinc-400 mb-4">
                    Shows predicted confidence vs actual accuracy. A perfectly calibrated model falls on the diagonal.
                </p>

                <div className="h-72 relative bg-zinc-800/50 rounded-xl p-4">
                    {/* Perfect calibration diagonal */}
                    <div className="absolute inset-4 border-b border-l border-zinc-600">
                        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                            {/* Diagonal line */}
                            <line x1="0" y1="100" x2="100" y2="0" stroke="#666" strokeWidth="1" strokeDasharray="4" />
                            {/* Calibration points */}
                            {calibration.calibration_curve.map((point, i) => (
                                <g key={i}>
                                    <circle
                                        cx={point.predicted_confidence * 100}
                                        cy={100 - point.actual_accuracy * 100}
                                        r="4"
                                        fill="#22c55e"
                                        className="drop-shadow-lg"
                                    />
                                </g>
                            ))}
                            {/* Connect points with line */}
                            <polyline
                                fill="none"
                                stroke="#22c55e"
                                strokeWidth="2"
                                points={calibration.calibration_curve.map(p =>
                                    `${p.predicted_confidence * 100},${100 - p.actual_accuracy * 100}`
                                ).join(' ')}
                            />
                        </svg>
                    </div>
                    {/* Axis labels */}
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs text-zinc-400">
                        Predicted Confidence
                    </div>
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 -rotate-90 text-xs text-zinc-400">
                        Actual Accuracy
                    </div>
                </div>

                <div className="flex justify-center gap-6 mt-4 text-xs">
                    <span className="flex items-center gap-2">
                        <span className="w-3 h-3 bg-emerald-500 rounded-full"></span> Model calibration
                    </span>
                    <span className="flex items-center gap-2">
                        <span className="w-4 border-t-2 border-dashed border-zinc-500"></span> Perfect calibration
                    </span>
                </div>
            </div>

            {/* Calibration Table */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">📊 Calibration by Confidence Bucket</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-left text-zinc-400 border-b border-zinc-700">
                                <th className="py-2 px-3">Confidence</th>
                                <th className="py-2 px-3">Actual Accuracy</th>
                                <th className="py-2 px-3">Samples</th>
                                <th className="py-2 px-3">Calibration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {calibration.calibration_curve.map((point, i) => {
                                const diff = point.predicted_confidence - point.actual_accuracy;
                                const status = Math.abs(diff) < 0.1 ? 'good' : Math.abs(diff) < 0.2 ? 'fair' : 'poor';
                                return (
                                    <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                                        <td className="py-2 px-3 text-white">{(point.predicted_confidence * 100).toFixed(0)}%</td>
                                        <td className="py-2 px-3 text-cyan-400">{(point.actual_accuracy * 100).toFixed(1)}%</td>
                                        <td className="py-2 px-3 text-zinc-400">{point.sample_count}</td>
                                        <td className="py-2 px-3">
                                            <span className={`px-2 py-0.5 rounded text-xs ${status === 'good' ? 'bg-emerald-500/20 text-emerald-400' :
                                                status === 'fair' ? 'bg-amber-500/20 text-amber-400' :
                                                    'bg-rose-500/20 text-rose-400'
                                                }`}>
                                                {diff > 0 ? 'Overconfident' : diff < -0.05 ? 'Underconfident' : 'Well-calibrated'}
                                            </span>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

function DriftTab({ drift }: { drift: DriftAnalysis }) {
    return (
        <div className="space-y-6">
            {/* Status Banner */}
            <div className={`glass-card p-6 rounded-2xl border-2 ${drift.status === 'stable' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-rose-500/30 bg-rose-500/5'
                }`}>
                <div className="flex items-center gap-4">
                    <span className="text-4xl">{drift.status === 'stable' ? '✅' : '🚨'}</span>
                    <div>
                        <h3 className="text-xl font-bold text-white">
                            {drift.status === 'stable' ? 'Model is Stable' : 'Drift Detected'}
                        </h3>
                        <p className="text-sm text-zinc-400 mt-1">{drift.recommendation}</p>
                    </div>
                </div>
            </div>

            {/* Drift Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <DriftCard
                    title="Feature Drift"
                    icon="📊"
                    current={drift.feature_drift.current}
                    previous={drift.feature_drift.previous}
                    change={drift.feature_drift.change}
                    alert={drift.feature_drift.alert}
                    description="Changes in input data distribution"
                />
                <DriftCard
                    title="Prediction Drift"
                    icon="🎯"
                    current={drift.prediction_drift.current}
                    previous={drift.prediction_drift.previous}
                    change={drift.prediction_drift.change}
                    alert={drift.prediction_drift.alert}
                    description="Changes in model output distribution"
                />
                <DriftCard
                    title="Accuracy Trend"
                    icon="📈"
                    current={drift.accuracy_trend.current}
                    previous={drift.accuracy_trend.previous}
                    change={drift.accuracy_trend.change}
                    alert={drift.accuracy_trend.alert}
                    description="Model performance over time"
                    isAccuracy
                />
            </div>

            {/* What is Drift */}
            <div className="glass-card p-6 rounded-2xl">
                <h3 className="text-lg font-semibold text-white mb-4">💡 Understanding Model Drift</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-zinc-800/50 p-4 rounded-xl">
                        <h4 className="font-medium text-white mb-2">📊 Feature Drift</h4>
                        <p className="text-sm text-zinc-400">
                            Occurs when the distribution of input features changes over time.
                            E.g., unusual weather patterns or new port congestion levels.
                        </p>
                    </div>
                    <div className="bg-zinc-800/50 p-4 rounded-xl">
                        <h4 className="font-medium text-white mb-2">🎯 Prediction Drift</h4>
                        <p className="text-sm text-zinc-400">
                            Occurs when model outputs shift without a change in inputs.
                            May indicate internal model degradation.
                        </p>
                    </div>
                    <div className="bg-zinc-800/50 p-4 rounded-xl">
                        <h4 className="font-medium text-white mb-2">📉 Performance Drift</h4>
                        <p className="text-sm text-zinc-400">
                            When actual model accuracy declines over time.
                            Trigger for model retraining or refresh.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function DriftCard({
    title, icon, current, previous, change, alert, description, isAccuracy = false
}: {
    title: string;
    icon: string;
    current: number;
    previous: number;
    change: number;
    alert: boolean;
    description: string;
    isAccuracy?: boolean;
}) {
    const isPositive = isAccuracy ? change >= 0 : change <= 0;

    return (
        <div className={`glass-card p-5 rounded-xl ${alert ? 'border border-rose-500/50' : ''}`}>
            <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{icon}</span>
                {alert && <span className="px-2 py-0.5 bg-rose-500/20 text-rose-400 text-xs rounded">Alert</span>}
            </div>
            <h4 className="font-semibold text-white">{title}</h4>
            <p className="text-xs text-zinc-500 mb-3">{description}</p>

            <div className="flex items-end justify-between">
                <div>
                    <p className="text-2xl font-bold text-white">
                        {isAccuracy ? `${(current * 100).toFixed(1)}%` : current.toFixed(3)}
                    </p>
                    <p className="text-xs text-zinc-500">Current</p>
                </div>
                <div className={`text-right ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                    <p className="font-medium">
                        {change >= 0 ? '+' : ''}{isAccuracy ? `${(change * 100).toFixed(1)}%` : change.toFixed(4)}
                    </p>
                    <p className="text-xs opacity-60">vs last week</p>
                </div>
            </div>
        </div>
    );
}

function MetricCard({
    label, value, icon, description, status
}: {
    label: string;
    value: string;
    icon: string;
    description: string;
    status: 'good' | 'fair' | 'poor';
}) {
    const statusColors = {
        good: 'border-emerald-500/30 bg-emerald-500/5',
        fair: 'border-amber-500/30 bg-amber-500/5',
        poor: 'border-rose-500/30 bg-rose-500/5'
    };

    return (
        <div className={`glass-card p-4 rounded-xl border ${statusColors[status]}`}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-xl">{icon}</span>
                <span className={`w-2 h-2 rounded-full ${status === 'good' ? 'bg-emerald-400' : status === 'fair' ? 'bg-amber-400' : 'bg-rose-400'
                    }`}></span>
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-sm text-zinc-400">{label}</p>
            <p className="text-xs text-zinc-500 mt-1">{description}</p>
        </div>
    );
}
