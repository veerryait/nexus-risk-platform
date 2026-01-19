'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { Navigation, PageHeader } from '@/components/Navigation';

const PortCongestionHeatmap = dynamic(() => import('@/components/PortCongestionHeatmap').then(m => m.PortCongestionHeatmap), { ssr: false });
const WeatherOverlay = dynamic(() => import('@/components/WeatherOverlay').then(m => m.WeatherOverlay), { ssr: false });
const DelayPredictionChart = dynamic(() => import('@/components/Charts').then(m => m.DelayPredictionChart), { ssr: false });
const OnTimeRateChart = dynamic(() => import('@/components/Charts').then(m => m.OnTimeRateChart), { ssr: false });

export default function OperationsPage() {
    const [activeSection, setActiveSection] = useState<'ports' | 'weather' | 'analytics'>('ports');

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <Navigation />

            <main className="max-w-7xl mx-auto px-4 py-8">
                <PageHeader
                    icon="⚙️"
                    title="Operations"
                    subtitle="Monitor port congestion, weather conditions, and operational metrics"
                />

                {/* Section Navigation */}
                <div className="flex gap-2 mb-6">
                    {[
                        { id: 'ports', label: 'Port Status', icon: '⚓' },
                        { id: 'weather', label: 'Weather', icon: '🌤️' },
                        { id: 'analytics', label: 'Analytics', icon: '📊' },
                    ].map((section) => (
                        <button
                            key={section.id}
                            onClick={() => setActiveSection(section.id as typeof activeSection)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeSection === section.id
                                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                }`}
                        >
                            {section.icon} {section.label}
                        </button>
                    ))}
                </div>

                {/* Section Content */}
                {activeSection === 'ports' && (
                    <section className="space-y-6">
                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">🚢 Port Congestion Overview</h2>
                            <p className="text-sm text-zinc-400 mb-6">
                                Real-time congestion levels at major Pacific ports. Higher congestion leads to longer wait times and increased delay risk.
                            </p>
                            <PortCongestionHeatmap />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <PortInfoCard
                                name="Los Angeles"
                                code="USLAX"
                                status="moderate"
                                waitTime={18}
                                capacity={62}
                            />
                            <PortInfoCard
                                name="Shanghai"
                                code="CNSHA"
                                status="busy"
                                waitTime={24}
                                capacity={78}
                            />
                            <PortInfoCard
                                name="Singapore"
                                code="SGSIN"
                                status="normal"
                                waitTime={8}
                                capacity={45}
                            />
                        </div>
                    </section>
                )}

                {activeSection === 'weather' && (
                    <section className="space-y-6">
                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">🌤️ Weather Conditions</h2>
                            <p className="text-sm text-zinc-400 mb-6">
                                Active weather systems affecting Pacific shipping routes. Storms and typhoons can significantly impact transit times.
                            </p>
                            <WeatherOverlay />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <WeatherAlertCard
                                type="Typhoon Watch"
                                region="Western Pacific"
                                severity="moderate"
                                description="Tropical depression forming east of Taiwan. Monitor for potential intensification over the next 48 hours."
                            />
                            <WeatherAlertCard
                                type="Heavy Seas"
                                region="North Pacific"
                                severity="low"
                                description="Moderate swells expected along the great circle route. Minimal impact on vessel operations expected."
                            />
                        </div>
                    </section>
                )}

                {activeSection === 'analytics' && (
                    <section className="space-y-6">
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="glass-card p-6 rounded-2xl">
                                <h2 className="text-lg font-semibold text-white mb-4">📊 Delay Distribution</h2>
                                <DelayPredictionChart height={300} />
                            </div>
                            <div className="glass-card p-6 rounded-2xl">
                                <h2 className="text-lg font-semibold text-white mb-4">✅ On-Time Performance</h2>
                                <OnTimeRateChart height={300} />
                            </div>
                        </div>

                        <div className="glass-card p-6 rounded-2xl">
                            <h2 className="text-lg font-semibold text-white mb-4">📈 Key Performance Indicators</h2>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <KPICard
                                    label="Avg Transit Time"
                                    value="12.3 days"
                                    change="+0.5"
                                    trend="up"
                                />
                                <KPICard
                                    label="On-Time Rate"
                                    value="87%"
                                    change="+2.1%"
                                    trend="up"
                                />
                                <KPICard
                                    label="Port Efficiency"
                                    value="94%"
                                    change="-1.2%"
                                    trend="down"
                                />
                                <KPICard
                                    label="Weather Delays"
                                    value="3 events"
                                    change="0"
                                    trend="stable"
                                />
                            </div>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

function PortInfoCard({
    name,
    code,
    status,
    waitTime,
    capacity
}: {
    name: string;
    code: string;
    status: 'normal' | 'moderate' | 'busy';
    waitTime: number;
    capacity: number;
}) {
    const statusColors = {
        normal: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        moderate: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        busy: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    };

    return (
        <div className="glass-card p-4 rounded-xl">
            <div className="flex items-center justify-between mb-3">
                <div>
                    <p className="font-semibold text-white">{name}</p>
                    <p className="text-xs text-zinc-500">{code}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium border ${statusColors[status]}`}>
                    {status.toUpperCase()}
                </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <p className="text-zinc-400">Wait Time</p>
                    <p className="font-medium text-white">{waitTime}h</p>
                </div>
                <div>
                    <p className="text-zinc-400">Capacity</p>
                    <p className="font-medium text-white">{capacity}%</p>
                </div>
            </div>
        </div>
    );
}

function WeatherAlertCard({
    type,
    region,
    severity,
    description
}: {
    type: string;
    region: string;
    severity: 'low' | 'moderate' | 'high';
    description: string;
}) {
    const severityColors = {
        low: 'border-emerald-500/30 bg-emerald-500/10',
        moderate: 'border-amber-500/30 bg-amber-500/10',
        high: 'border-rose-500/30 bg-rose-500/10',
    };

    return (
        <div className={`p-4 rounded-xl border ${severityColors[severity]}`}>
            <div className="flex items-center justify-between mb-2">
                <p className="font-semibold text-white">{type}</p>
                <span className="text-xs text-zinc-400">{region}</span>
            </div>
            <p className="text-sm text-zinc-300">{description}</p>
        </div>
    );
}

function KPICard({
    label,
    value,
    change,
    trend
}: {
    label: string;
    value: string;
    change: string;
    trend: 'up' | 'down' | 'stable';
}) {
    const trendColors = {
        up: 'text-emerald-400',
        down: 'text-rose-400',
        stable: 'text-zinc-400',
    };

    return (
        <div className="bg-zinc-800/50 p-4 rounded-xl">
            <p className="text-xs text-zinc-400 mb-1">{label}</p>
            <p className="text-xl font-bold text-white">{value}</p>
            <p className={`text-xs ${trendColors[trend]}`}>
                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {change}
            </p>
        </div>
    );
}
