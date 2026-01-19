'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Navigation, PageHeader } from '@/components/Navigation';

const GNNVisualization = dynamic(() => import('@/components/GNNVisualization').then(m => m.GNNVisualization), { ssr: false });
const RiskTrendsChart = dynamic(() => import('@/components/Charts').then(m => m.RiskTrendsChart), { ssr: false });
const PerformanceLineChart = dynamic(() => import('@/components/Charts').then(m => m.PerformanceLineChart), { ssr: false });
const FeatureImportanceChart = dynamic(() => import('@/components/AIInsights').then(m => m.FeatureImportanceChart), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface GNNInfo {
    model_name: string;
    architecture: string;
    version: string;
    pytorch_geometric_available: boolean;
    inference_mode: string;
}

export default function RiskAnalysisPage() {
    const [modelInfo, setModelInfo] = useState<GNNInfo | null>(null);
    const [activeTab, setActiveTab] = useState<'network' | 'trends' | 'importance'>('network');

    useEffect(() => {
        fetch(`${API_BASE}/api/v1/gnn/info`)
            .then(res => res.json())
            .then(setModelInfo)
            .catch(console.error);
    }, []);

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <Navigation />

            <main className="max-w-7xl mx-auto px-4 py-8">
                <PageHeader
                    icon="🧠"
                    title="Risk Analysis"
                    subtitle="AI-powered risk predictions using Graph Neural Networks"
                />

                {/* Model Info Banner */}
                {modelInfo && (
                    <div className="mb-6 glass-card p-4 rounded-xl flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className={`w-3 h-3 rounded-full ${modelInfo.pytorch_geometric_available ? 'bg-emerald-500' : 'bg-amber-500'} animate-pulse`}></div>
                            <div>
                                <p className="text-sm font-medium text-white">{modelInfo.architecture}</p>
                                <p className="text-xs text-zinc-400">{modelInfo.inference_mode}</p>
                            </div>
                        </div>
                        <span className="text-xs text-zinc-500">v{modelInfo.version}</span>
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex gap-2 mb-6">
                    {[
                        { id: 'network', label: 'Network Analysis', icon: '🔗' },
                        { id: 'trends', label: 'Risk Trends', icon: '📈' },
                        { id: 'importance', label: 'Feature Analysis', icon: '🎯' },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as typeof activeTab)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab.id
                                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                }`}
                        >
                            {tab.icon} {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                {activeTab === 'network' && (
                    <section>
                        <GNNVisualization />
                    </section>
                )}

                {activeTab === 'trends' && (
                    <section className="space-y-6">
                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">📊 Historical Risk Trends</h2>
                            <RiskTrendsChart height={350} />
                        </div>
                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">📈 Performance Over Time</h2>
                            <PerformanceLineChart height={300} />
                        </div>
                    </section>
                )}

                {activeTab === 'importance' && (
                    <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <h2 className="text-lg font-semibold text-white mb-4">🎯 Delay Prediction Factors</h2>
                            <FeatureImportanceChart predictionType="delay" />
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white mb-4">⚠️ Risk Score Factors</h2>
                            <FeatureImportanceChart predictionType="risk" />
                        </div>
                        <div className="lg:col-span-2 glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">💡 How Predictions Work</h2>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <ExplainerCard
                                    icon="🌤️"
                                    title="Weather Analysis"
                                    description="Real-time weather data is processed to identify storms, typhoons, and adverse conditions along shipping routes."
                                />
                                <ExplainerCard
                                    icon="🔗"
                                    title="Network Effects"
                                    description="The GNN analyzes how ports are connected, identifying how a disruption at one port cascades to others."
                                />
                                <ExplainerCard
                                    icon="📊"
                                    title="Historical Patterns"
                                    description="Machine learning models learn from past delays, congestion events, and seasonal patterns."
                                />
                            </div>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

function ExplainerCard({ icon, title, description }: { icon: string; title: string; description: string }) {
    return (
        <div className="bg-zinc-800/50 p-4 rounded-xl">
            <span className="text-2xl mb-2 block">{icon}</span>
            <h3 className="font-semibold text-white mb-1">{title}</h3>
            <p className="text-sm text-zinc-400">{description}</p>
        </div>
    );
}
