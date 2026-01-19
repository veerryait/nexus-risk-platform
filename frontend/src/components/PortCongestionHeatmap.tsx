'use client';

import { useState, useEffect } from 'react';

interface PortCongestion {
    port_code: string;
    port_name: string;
    country: string;
    congestion_level: 'low' | 'medium' | 'high' | 'severe';
    congestion_score: number;
    vessels_waiting: number;
    avg_wait_days: number;
    berth_utilization: number;
    trend: 'improving' | 'stable' | 'worsening';
    lat: number;
    lng: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Mock data for major semiconductor shipping ports
const MOCK_PORTS: PortCongestion[] = [
    { port_code: 'TWKHH', port_name: 'Kaohsiung', country: 'Taiwan', congestion_level: 'low', congestion_score: 0.25, vessels_waiting: 3, avg_wait_days: 0.5, berth_utilization: 0.62, trend: 'stable', lat: 22.6273, lng: 120.2653 },
    { port_code: 'TWKEL', port_name: 'Keelung', country: 'Taiwan', congestion_level: 'low', congestion_score: 0.20, vessels_waiting: 2, avg_wait_days: 0.3, berth_utilization: 0.55, trend: 'improving', lat: 25.1276, lng: 121.7392 },
    { port_code: 'CNSHA', port_name: 'Shanghai', country: 'China', congestion_level: 'medium', congestion_score: 0.45, vessels_waiting: 12, avg_wait_days: 1.8, berth_utilization: 0.78, trend: 'stable', lat: 31.2304, lng: 121.4737 },
    { port_code: 'CNNGB', port_name: 'Ningbo', country: 'China', congestion_level: 'medium', congestion_score: 0.52, vessels_waiting: 8, avg_wait_days: 2.1, berth_utilization: 0.82, trend: 'worsening', lat: 29.8683, lng: 121.5440 },
    { port_code: 'HKHKG', port_name: 'Hong Kong', country: 'Hong Kong', congestion_level: 'low', congestion_score: 0.30, vessels_waiting: 5, avg_wait_days: 0.8, berth_utilization: 0.65, trend: 'improving', lat: 22.2855, lng: 114.1577 },
    { port_code: 'SGSIN', port_name: 'Singapore', country: 'Singapore', congestion_level: 'medium', congestion_score: 0.48, vessels_waiting: 15, avg_wait_days: 1.5, berth_utilization: 0.75, trend: 'stable', lat: 1.2644, lng: 103.8222 },
    { port_code: 'KRPUS', port_name: 'Busan', country: 'South Korea', congestion_level: 'low', congestion_score: 0.28, vessels_waiting: 4, avg_wait_days: 0.6, berth_utilization: 0.60, trend: 'stable', lat: 35.1028, lng: 129.0403 },
    { port_code: 'JPYOK', port_name: 'Yokohama', country: 'Japan', congestion_level: 'low', congestion_score: 0.32, vessels_waiting: 6, avg_wait_days: 0.9, berth_utilization: 0.68, trend: 'improving', lat: 35.4437, lng: 139.6380 },
    { port_code: 'USLAX', port_name: 'Los Angeles', country: 'USA', congestion_level: 'high', congestion_score: 0.72, vessels_waiting: 22, avg_wait_days: 3.5, berth_utilization: 0.88, trend: 'worsening', lat: 33.7405, lng: -118.2608 },
    { port_code: 'USLGB', port_name: 'Long Beach', country: 'USA', congestion_level: 'high', congestion_score: 0.68, vessels_waiting: 18, avg_wait_days: 3.2, berth_utilization: 0.85, trend: 'stable', lat: 33.7546, lng: -118.2163 },
    { port_code: 'USOAK', port_name: 'Oakland', country: 'USA', congestion_level: 'medium', congestion_score: 0.55, vessels_waiting: 8, avg_wait_days: 2.0, berth_utilization: 0.76, trend: 'improving', lat: 37.7956, lng: -122.2789 },
    { port_code: 'USSEA', port_name: 'Seattle', country: 'USA', congestion_level: 'medium', congestion_score: 0.42, vessels_waiting: 6, avg_wait_days: 1.4, berth_utilization: 0.70, trend: 'stable', lat: 47.5806, lng: -122.3384 },
];

const getCongestionColor = (level: string, score: number) => {
    if (level === 'severe' || score >= 0.8) return { bg: 'bg-rose-500', text: 'text-rose-500', glow: 'shadow-rose-500/50' };
    if (level === 'high' || score >= 0.6) return { bg: 'bg-orange-500', text: 'text-orange-500', glow: 'shadow-orange-500/50' };
    if (level === 'medium' || score >= 0.4) return { bg: 'bg-amber-500', text: 'text-amber-500', glow: 'shadow-amber-500/50' };
    return { bg: 'bg-emerald-500', text: 'text-emerald-500', glow: 'shadow-emerald-500/50' };
};

const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return { icon: '↗', color: 'text-emerald-400' };
    if (trend === 'worsening') return { icon: '↘', color: 'text-rose-400' };
    return { icon: '→', color: 'text-zinc-400' };
};

export function PortCongestionHeatmap() {
    const [ports, setPorts] = useState<PortCongestion[]>(MOCK_PORTS);
    const [selectedPort, setSelectedPort] = useState<PortCongestion | null>(null);
    const [filter, setFilter] = useState<'all' | 'asia' | 'usa'>('all');
    const [loading, setLoading] = useState(false);

    // Fetch real data from API
    useEffect(() => {
        const fetchPorts = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/v1/admin/port-status`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.ports?.length > 0) {
                        // Merge with mock data for coordinates
                        const merged = MOCK_PORTS.map(mock => {
                            const real = data.ports.find((p: any) => p.port_code === mock.port_code);
                            return real ? { ...mock, ...real } : mock;
                        });
                        setPorts(merged);
                    }
                }
            } catch (err) {
                // Using mock data for demo
            }
        };
        fetchPorts();
    }, []);

    const filteredPorts = ports.filter(p => {
        if (filter === 'asia') return ['Taiwan', 'China', 'Hong Kong', 'Singapore', 'South Korea', 'Japan'].includes(p.country);
        if (filter === 'usa') return p.country === 'USA';
        return true;
    });

    const avgCongestion = (filteredPorts.reduce((acc, p) => acc + p.congestion_score, 0) / filteredPorts.length * 100).toFixed(0);
    const totalWaiting = filteredPorts.reduce((acc, p) => acc + p.vessels_waiting, 0);

    return (
        <div className="glass-card p-6 rounded-2xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-white font-futuristic flex items-center gap-2">
                        <span className="text-2xl">🌡️</span> Port Congestion Heatmap
                    </h2>
                    <p className="text-sm text-zinc-400 mt-1">Real-time congestion levels at major ports</p>
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center gap-2">
                    {(['all', 'asia', 'usa'] as const).map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${filter === f
                                ? 'bg-cyan-500 text-black'
                                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                }`}
                        >
                            {f === 'all' ? 'All Ports' : f === 'asia' ? '🌏 Asia' : '🇺🇸 USA'}
                        </button>
                    ))}
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-white">{filteredPorts.length}</p>
                    <p className="text-xs text-zinc-400">Ports Monitored</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-amber-400">{avgCongestion}%</p>
                    <p className="text-xs text-zinc-400">Avg Congestion</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-cyan-400">{totalWaiting}</p>
                    <p className="text-xs text-zinc-400">Vessels Waiting</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-rose-400">
                        {filteredPorts.filter(p => p.congestion_level === 'high' || p.congestion_level === 'severe').length}
                    </p>
                    <p className="text-xs text-zinc-400">High Congestion</p>
                </div>
            </div>

            {/* Heatmap Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {filteredPorts
                    .sort((a, b) => b.congestion_score - a.congestion_score)
                    .map(port => {
                        const colors = getCongestionColor(port.congestion_level, port.congestion_score);
                        const trend = getTrendIcon(port.trend);

                        return (
                            <div
                                key={port.port_code}
                                onClick={() => setSelectedPort(selectedPort?.port_code === port.port_code ? null : port)}
                                className={`relative p-4 rounded-xl border cursor-pointer transition-all duration-300 ${selectedPort?.port_code === port.port_code
                                    ? `border-2 ${colors.bg.replace('bg-', 'border-')} shadow-lg ${colors.glow}`
                                    : 'border-zinc-700 hover:border-zinc-600'
                                    } bg-zinc-900/80`}
                            >
                                {/* Congestion Bar */}
                                <div className="absolute top-0 left-0 right-0 h-1 rounded-t-xl overflow-hidden bg-zinc-800">
                                    <div
                                        className={`h-full ${colors.bg} transition-all duration-500`}
                                        style={{ width: `${port.congestion_score * 100}%` }}
                                    />
                                </div>

                                {/* Port Info */}
                                <div className="mt-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs text-zinc-500">{port.port_code}</span>
                                        <span className={`text-xs font-medium ${trend.color}`}>{trend.icon}</span>
                                    </div>
                                    <h3 className="font-semibold text-white text-sm mt-1">{port.port_name}</h3>
                                    <p className="text-xs text-zinc-500">{port.country}</p>

                                    {/* Congestion Score */}
                                    <div className="mt-3 flex items-center justify-between">
                                        <span className={`text-lg font-bold ${colors.text}`}>
                                            {Math.round(port.congestion_score * 100)}%
                                        </span>
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors.bg} text-white`}>
                                            {port.congestion_level.toUpperCase()}
                                        </span>
                                    </div>
                                </div>

                                {/* Expanded Details */}
                                {selectedPort?.port_code === port.port_code && (
                                    <div className="mt-4 pt-4 border-t border-zinc-700 space-y-2 animate-fadeIn">
                                        <div className="flex justify-between text-xs">
                                            <span className="text-zinc-400">Vessels Waiting</span>
                                            <span className="text-white font-medium">{port.vessels_waiting}</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-zinc-400">Avg Wait Time</span>
                                            <span className="text-white font-medium">{port.avg_wait_days} days</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-zinc-400">Berth Utilization</span>
                                            <span className="text-white font-medium">{Math.round(port.berth_utilization * 100)}%</span>
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-zinc-400">Trend</span>
                                            <span className={`font-medium ${trend.color}`}>
                                                {port.trend.charAt(0).toUpperCase() + port.trend.slice(1)}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
            </div>

            {/* Legend */}
            <div className="mt-6 flex items-center justify-center gap-6 text-xs text-zinc-400">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                    <span>Low (&lt;40%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                    <span>Medium (40-60%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                    <span>High (60-80%)</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                    <span>Severe (&gt;80%)</span>
                </div>
            </div>
        </div>
    );
}
