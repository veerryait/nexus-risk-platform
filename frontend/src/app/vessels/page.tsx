'use client';

import { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import { Header } from '@/components/Header';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { Vessel } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const GlobeMap = dynamic(() => import('@/components/GlobeMap').then(m => m.GlobeMap), {
    ssr: false,
    loading: () => (
        <div className="h-[600px] bg-zinc-900 rounded-2xl flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin text-4xl mb-4">🌍</div>
                <p className="text-zinc-400">Loading 3D Globe...</p>
            </div>
        </div>
    )
});

interface VesselResponse {
    vessels: Vessel[];
    count: number;
    source: 'aisstream' | 'database' | 'simulated';
    aisstream_configured?: boolean;
    note?: string;
}

export default function VesselsPage() {
    const [vessels, setVessels] = useState<Vessel[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedVessel, setSelectedVessel] = useState<string | null>(null);
    const [dataSource, setDataSource] = useState<string>('loading');
    const [aisstreamConfigured, setAisstreamConfigured] = useState(false);
    const [viewMode, setViewMode] = useState<'list' | 'fleet'>('list');
    const [watchlist, setWatchlist] = useState<string[]>([]);
    const [filterCarrier, setFilterCarrier] = useState<string>('all');
    const [showWatchlistOnly, setShowWatchlistOnly] = useState(false);
    const [anomalies, setAnomalies] = useState<any[]>([]);
    const [showAnomalyPanel, setShowAnomalyPanel] = useState(false);
    const [modelMetrics, setModelMetrics] = useState<any>(null);
    const [alertFilter, setAlertFilter] = useState<'all' | 'high' | 'marginal'>('all');
    const [feedback, setFeedback] = useState<Record<string, 'confirmed' | 'false_positive'>>({});

    // Fetch anomaly alerts with ML predictions
    useEffect(() => {
        async function fetchAnomalies() {
            try {
                // Fetch ML-based predictions
                const res = await fetch(`${API_BASE}/api/v1/anomaly/ml/fleet`);
                const data = await res.json();

                // Transform predictions to alerts format
                const alerts = (data.predictions || [])
                    .filter((p: any) => p.is_anomaly)
                    .map((p: any) => ({
                        ...p,
                        confidence: Math.round((p.anomaly_score || 0) * 100),
                        isHighConfidence: (p.anomaly_score || 0) >= 0.95,
                        type: p.factors?.[0] || 'anomaly',
                        title: p.factors?.[0] || 'Anomaly Detected',
                        description: p.factors?.join(', ') || 'Unusual behavior pattern'
                    }));

                setAnomalies(alerts);
                setModelMetrics(data.model_info || null);
            } catch (err) {
                console.error('Failed to load anomalies:', err);
            }
        }
        fetchAnomalies();
        const interval = setInterval(fetchAnomalies, 60000);
        return () => clearInterval(interval);
    }, []);

    // Tiered alerts
    const highConfidenceAlerts = anomalies.filter(a => a.isHighConfidence);
    const marginalAlerts = anomalies.filter(a => !a.isHighConfidence);
    const filteredAlerts = alertFilter === 'high' ? highConfidenceAlerts :
        alertFilter === 'marginal' ? marginalAlerts : anomalies;

    // Handle feedback
    const submitFeedback = (alertId: string, type: 'confirmed' | 'false_positive') => {
        setFeedback(prev => ({ ...prev, [alertId]: type }));
        // TODO: Send to backend for model retraining
        // Feedback recorded - could send to API
    };

    // Load watchlist from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('vessel-watchlist');
        if (saved) setWatchlist(JSON.parse(saved));
    }, []);

    // Save watchlist to localStorage
    useEffect(() => {
        localStorage.setItem('vessel-watchlist', JSON.stringify(watchlist));
    }, [watchlist]);

    useEffect(() => {
        async function loadData() {
            try {
                const res = await fetch(`${API_BASE}/api/v1/vessels/`);
                const data: VesselResponse = await res.json();
                setVessels(data.vessels || []);
                setDataSource(data.source || 'unknown');
                setAisstreamConfigured(data.aisstream_configured || false);
            } catch (err) {
                console.error('Failed to load vessels:', err);
                setDataSource('error');
            } finally {
                setLoading(false);
            }
        }
        loadData();
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    }, []);

    // Group vessels by carrier
    const vesselsByCarrier = useMemo(() => {
        const groups: Record<string, Vessel[]> = {};
        vessels.forEach(v => {
            const carrier = v.carrier || 'Unknown';
            if (!groups[carrier]) groups[carrier] = [];
            groups[carrier].push(v);
        });
        return groups;
    }, [vessels]);

    // Get unique carriers
    const carriers = useMemo(() => ['all', ...Object.keys(vesselsByCarrier)], [vesselsByCarrier]);

    // Filter vessels
    const filteredVessels = useMemo(() => {
        let result = vessels;
        if (filterCarrier !== 'all') {
            result = result.filter(v => v.carrier === filterCarrier);
        }
        if (showWatchlistOnly) {
            result = result.filter(v => watchlist.includes(v.id));
        }
        return result;
    }, [vessels, filterCarrier, showWatchlistOnly, watchlist]);

    // Toggle watchlist
    const toggleWatchlist = (vesselId: string) => {
        setWatchlist(prev =>
            prev.includes(vesselId)
                ? prev.filter(id => id !== vesselId)
                : [...prev, vesselId]
        );
    };

    // Export to CSV
    const exportToCSV = () => {
        const headers = ['Name', 'IMO', 'Carrier', 'Status', 'Speed (kts)', 'Heading', 'Destination', 'ETA', 'Lat', 'Lng'];
        const rows = vessels.map(v => [
            v.name, v.imo, v.carrier || '', v.status, v.speed, v.heading,
            v.destination, v.eta, v.position?.lat, v.position?.lng
        ]);
        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `vessels_export_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    const statusColors: Record<string, string> = {
        underway: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
        at_port: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
        berthed: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
        anchored: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
        unknown: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400',
    };

    const carrierColors: Record<string, string> = {
        'Evergreen': 'from-green-500 to-emerald-600',
        'Yang Ming': 'from-orange-500 to-red-600',
        'Maersk': 'from-sky-500 to-blue-600',
        'COSCO': 'from-red-500 to-rose-600',
        'ONE': 'from-pink-500 to-fuchsia-600',
        'MSC': 'from-amber-500 to-yellow-600',
    };

    const sourceConfig: Record<string, { label: string; color: string; icon: string }> = {
        aisstream: { label: 'AISStream Live', color: 'bg-emerald-500 text-white', icon: '📡' },
        database: { label: 'Database', color: 'bg-sky-500 text-white', icon: '💾' },
        simulated: { label: 'Simulated', color: 'bg-amber-500 text-white', icon: '🔄' },
        loading: { label: 'Loading...', color: 'bg-zinc-400 text-white', icon: '⏳' },
        error: { label: 'Error', color: 'bg-rose-500 text-white', icon: '❌' },
        unknown: { label: 'Unknown', color: 'bg-zinc-500 text-white', icon: '❓' },
    };

    const source = sourceConfig[dataSource] || sourceConfig.unknown;

    return (
        <ErrorBoundary>
            <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
                <Header />
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="mb-8 flex items-center justify-between flex-wrap gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">Vessel Tracking</h1>
                            <p className="text-zinc-600 dark:text-zinc-400 mt-1">
                                Real-time tracking of vessels on Taiwan → US routes
                            </p>
                        </div>

                        <div className="flex items-center gap-3 flex-wrap">
                            {/* Data Source Badge */}
                            <div className={`flex items-center gap-2 px-3 py-2 rounded-full ${source.color} shadow-lg`}>
                                <span>{source.icon}</span>
                                <span className="font-medium text-sm">{source.label}</span>
                            </div>
                            {aisstreamConfigured && dataSource !== 'aisstream' && (
                                <span className="text-xs text-zinc-500 dark:text-zinc-400">
                                    AIS ready (no vessels in range)
                                </span>
                            )}
                        </div>
                    </div>

                    {/* 3D Globe Map */}
                    <section className="mb-8">
                        <GlobeMap
                            vessels={filteredVessels.map(v => ({
                                id: v.id,
                                name: v.name,
                                lat: v.position?.lat,
                                lng: v.position?.lng,
                                status: v.status,
                                destination: v.destination,
                                speed: v.speed,
                                heading: v.heading,
                                eta: v.eta,
                                imo: v.imo,
                            }))}
                            selectedVessel={selectedVessel || undefined}
                            onVesselSelect={(vessel) => setSelectedVessel(vessel.id)}
                            height="600px"
                        />
                    </section>

                    {/* Anomaly Alerts Panel - Enhanced */}
                    {anomalies.length > 0 && (
                        <section className="mb-6">
                            {/* Header with Model Metrics */}
                            <div className="bg-zinc-900 dark:bg-zinc-950 rounded-2xl overflow-hidden border-2 border-rose-500/30">
                                <button
                                    onClick={() => setShowAnomalyPanel(!showAnomalyPanel)}
                                    className="w-full flex items-center justify-between p-4 hover:bg-zinc-800 transition-colors"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 rounded-full bg-rose-500/20 flex items-center justify-center">
                                            <span className="text-2xl">🚨</span>
                                        </div>
                                        <div className="text-left">
                                            <h3 className="font-bold text-white text-lg">
                                                {anomalies.length} Anomaly Alert{anomalies.length > 1 ? 's' : ''} Detected
                                            </h3>
                                            <div className="flex items-center gap-4 mt-1">
                                                <span className="text-sm text-rose-400">
                                                    🔴 {highConfidenceAlerts.length} High Confidence
                                                </span>
                                                <span className="text-sm text-amber-400">
                                                    🟡 {marginalAlerts.length} Marginal
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Model Quality Widget */}
                                    {modelMetrics && (
                                        <div className="hidden md:flex items-center gap-4 mr-4">
                                            <div className="text-center px-3 py-1 bg-emerald-500/20 rounded-lg">
                                                <p className="text-xs text-emerald-400">Recall</p>
                                                <p className="font-bold text-emerald-300">{Math.round((modelMetrics.metrics?.recall || 0.8) * 100)}%</p>
                                            </div>
                                            <div className="text-center px-3 py-1 bg-sky-500/20 rounded-lg">
                                                <p className="text-xs text-sky-400">Precision</p>
                                                <p className="font-bold text-sky-300">{Math.round((modelMetrics.metrics?.precision || 1) * 100)}%</p>
                                            </div>
                                            <div className="text-center px-3 py-1 bg-violet-500/20 rounded-lg">
                                                <p className="text-xs text-violet-400">Model</p>
                                                <p className="font-bold text-violet-300">v{modelMetrics.version || '2.0'}</p>
                                            </div>
                                        </div>
                                    )}

                                    <span className="text-zinc-400 text-xl">
                                        {showAnomalyPanel ? '▲' : '▼'}
                                    </span>
                                </button>

                                {showAnomalyPanel && (
                                    <div className="border-t border-zinc-800 p-4">
                                        {/* Alert Filter Tabs */}
                                        <div className="flex items-center gap-2 mb-4">
                                            <button
                                                onClick={() => setAlertFilter('all')}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${alertFilter === 'all'
                                                    ? 'bg-rose-500 text-white'
                                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                                    }`}
                                            >
                                                All ({anomalies.length})
                                            </button>
                                            <button
                                                onClick={() => setAlertFilter('high')}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${alertFilter === 'high'
                                                    ? 'bg-rose-500 text-white'
                                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                                    }`}
                                            >
                                                🔴 High Confidence ({highConfidenceAlerts.length})
                                            </button>
                                            <button
                                                onClick={() => setAlertFilter('marginal')}
                                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${alertFilter === 'marginal'
                                                    ? 'bg-amber-500 text-white'
                                                    : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                                                    }`}
                                            >
                                                🟡 Marginal ({marginalAlerts.length})
                                            </button>
                                        </div>

                                        {/* Alert Cards */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                            {filteredAlerts.slice(0, 9).map((alert, idx) => (
                                                <div
                                                    key={idx}
                                                    className={`relative p-4 rounded-xl border-2 transition-all ${feedback[alert.vessel_id] === 'confirmed' ? 'opacity-60' :
                                                        feedback[alert.vessel_id] === 'false_positive' ? 'opacity-40 grayscale' :
                                                            alert.isHighConfidence
                                                                ? 'bg-rose-950/50 border-rose-500/50 hover:border-rose-400'
                                                                : 'bg-amber-950/30 border-amber-500/30 hover:border-amber-400'
                                                        }`}
                                                >
                                                    {/* Confidence Badge */}
                                                    <div className="absolute top-3 right-3">
                                                        <div className={`px-2 py-1 rounded-lg text-xs font-bold ${alert.isHighConfidence
                                                            ? 'bg-rose-500 text-white'
                                                            : 'bg-amber-500/50 text-amber-200'
                                                            }`}>
                                                            {alert.confidence}% conf
                                                        </div>
                                                    </div>

                                                    {/* Header */}
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className={`w-3 h-3 rounded-full ${alert.isHighConfidence ? 'bg-rose-500' : 'bg-amber-500'
                                                            }`}></span>
                                                        <span className="text-xs text-zinc-400 uppercase">
                                                            {alert.severity}
                                                        </span>
                                                    </div>

                                                    {/* Vessel Name */}
                                                    <h4 className="font-bold text-white mb-1 pr-16">
                                                        {alert.vessel_name}
                                                    </h4>

                                                    {/* Reasoning */}
                                                    <div className="mt-3 p-2 bg-zinc-800/50 rounded-lg">
                                                        <p className="text-xs text-zinc-400 mb-1">WHY FLAGGED:</p>
                                                        <ul className="text-sm text-zinc-300">
                                                            {alert.factors?.map((f: string, i: number) => (
                                                                <li key={i} className="flex items-center gap-2">
                                                                    <span className="text-rose-400">•</span> {f}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>

                                                    {/* Feedback Buttons */}
                                                    {!feedback[alert.vessel_id] && (
                                                        <div className="flex items-center gap-2 mt-3">
                                                            <button
                                                                onClick={() => submitFeedback(alert.vessel_id, 'confirmed')}
                                                                className="flex-1 py-1.5 text-xs font-medium bg-emerald-600/30 hover:bg-emerald-600/50 text-emerald-300 rounded-lg transition-colors"
                                                            >
                                                                ✓ Confirm
                                                            </button>
                                                            <button
                                                                onClick={() => submitFeedback(alert.vessel_id, 'false_positive')}
                                                                className="flex-1 py-1.5 text-xs font-medium bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded-lg transition-colors"
                                                            >
                                                                ✗ False Alarm
                                                            </button>
                                                        </div>
                                                    )}
                                                    {feedback[alert.vessel_id] && (
                                                        <div className="mt-3 text-xs text-center text-zinc-500">
                                                            {feedback[alert.vessel_id] === 'confirmed' ? '✓ Marked as real anomaly' : '✗ Marked as false alarm'}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {/* Footer with Legend */}
                                        <div className="mt-4 pt-4 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-500">
                                            <div>
                                                <span className="text-rose-400">🔴 High Confidence:</span> Score ≥95% — prioritize investigation
                                                <span className="mx-3">|</span>
                                                <span className="text-amber-400">🟡 Marginal:</span> Score &lt;95% — monitor activity
                                            </div>
                                            <div>
                                                Model: {modelMetrics?.model_type || 'ML'} | Missed: ~{Math.round((1 - (modelMetrics?.metrics?.recall || 0.8)) * 100)}%
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </section>
                    )}

                    {/* Controls Bar */}
                    <section className="mb-6 flex items-center justify-between flex-wrap gap-4">
                        <div className="flex items-center gap-3">
                            {/* View Toggle */}
                            <div className="flex bg-zinc-200 dark:bg-zinc-800 rounded-lg p-1">
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'list' ? 'bg-white dark:bg-zinc-700 shadow text-zinc-900 dark:text-zinc-100' : 'text-zinc-600 dark:text-zinc-400'}`}
                                >
                                    📋 List View
                                </button>
                                <button
                                    onClick={() => setViewMode('fleet')}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'fleet' ? 'bg-white dark:bg-zinc-700 shadow text-zinc-900 dark:text-zinc-100' : 'text-zinc-600 dark:text-zinc-400'}`}
                                >
                                    🏢 Fleet View
                                </button>
                            </div>

                            {/* Carrier Filter */}
                            <select
                                value={filterCarrier}
                                onChange={(e) => setFilterCarrier(e.target.value)}
                                className="px-4 py-2 rounded-lg bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-sm"
                            >
                                {carriers.map(c => (
                                    <option key={c} value={c}>{c === 'all' ? 'All Carriers' : c}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-center gap-3">
                            {/* Watchlist Filter Toggle */}
                            {watchlist.length > 0 && (
                                <button
                                    onClick={() => setShowWatchlistOnly(!showWatchlistOnly)}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${showWatchlistOnly
                                        ? 'bg-amber-500 text-white shadow-lg'
                                        : 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-900/50'
                                        }`}
                                >
                                    ⭐ {showWatchlistOnly ? 'Showing Watchlist' : `Watchlist (${watchlist.length})`}
                                </button>
                            )}

                            {/* Export Button */}
                            <button
                                onClick={exportToCSV}
                                className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-sm font-medium transition-colors shadow-lg"
                            >
                                📥 Export CSV
                            </button>
                        </div>
                    </section>

                    {/* Vessel Display */}
                    <section>
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
                                {viewMode === 'fleet' ? 'Fleet Overview' : `Active Vessels (${filteredVessels.length})`}
                            </h2>
                            <span className="text-xs text-zinc-500 dark:text-zinc-400">
                                Auto-refresh: 30s
                            </span>
                        </div>

                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="h-36 bg-zinc-200 dark:bg-zinc-800 rounded-xl animate-pulse" />
                                ))}
                            </div>
                        ) : viewMode === 'fleet' ? (
                            /* Fleet View - Grouped by Carrier */
                            <div className="space-y-8">
                                {Object.entries(vesselsByCarrier).map(([carrier, carrierVessels]) => (
                                    <div key={carrier} className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                                        <div className={`h-2 bg-gradient-to-r ${carrierColors[carrier] || 'from-zinc-500 to-zinc-600'}`} />
                                        <div className="p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <h3 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">{carrier}</h3>
                                                <span className="px-3 py-1 bg-zinc-100 dark:bg-zinc-800 rounded-full text-sm">
                                                    {carrierVessels.length} vessels
                                                </span>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                                {carrierVessels.map(vessel => (
                                                    <VesselCard
                                                        key={vessel.id}
                                                        vessel={vessel}
                                                        isSelected={selectedVessel === vessel.id}
                                                        isWatched={watchlist.includes(vessel.id)}
                                                        onClick={() => setSelectedVessel(vessel.id)}
                                                        onToggleWatch={() => toggleWatchlist(vessel.id)}
                                                        statusColors={statusColors}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            /* List View */
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {filteredVessels.map(vessel => (
                                    <VesselCard
                                        key={vessel.id}
                                        vessel={vessel}
                                        isSelected={selectedVessel === vessel.id}
                                        isWatched={watchlist.includes(vessel.id)}
                                        onClick={() => setSelectedVessel(vessel.id)}
                                        onToggleWatch={() => toggleWatchlist(vessel.id)}
                                        statusColors={statusColors}
                                    />
                                ))}
                            </div>
                        )}
                    </section>
                </main>
            </div>
        </ErrorBoundary>
    );
}

// Vessel Card Component
function VesselCard({ vessel, isSelected, isWatched, onClick, onToggleWatch, statusColors }: {
    vessel: Vessel;
    isSelected: boolean;
    isWatched: boolean;
    onClick: () => void;
    onToggleWatch: () => void;
    statusColors: Record<string, string>;
}) {
    return (
        <div
            onClick={onClick}
            className={`relative p-5 rounded-xl border-2 cursor-pointer transition-all card-hover animate-fadeIn ${isSelected
                ? 'border-sky-500 bg-sky-50 dark:bg-sky-900/20'
                : 'border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900'
                }`}
        >
            {/* Watchlist Star */}
            <button
                onClick={(e) => { e.stopPropagation(); onToggleWatch(); }}
                className={`absolute top-3 right-3 text-xl transition-transform hover:scale-125 ${isWatched ? 'text-amber-400' : 'text-zinc-300 dark:text-zinc-600'}`}
            >
                {isWatched ? '⭐' : '☆'}
            </button>

            <div className="flex items-center gap-3 mb-3 pr-8">
                <div className="w-10 h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center">
                    <span className="text-lg">🚢</span>
                </div>
                <div>
                    <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">{vessel.name}</h3>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">IMO: {vessel.imo}</p>
                </div>
            </div>

            <div className="flex items-center gap-2 mb-3">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[vessel.status] || statusColors.unknown}`}>
                    {vessel.status}
                </span>
                {vessel.carrier && (
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">
                        {vessel.carrier}
                    </span>
                )}
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">Speed</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{vessel.speed} kts</p>
                </div>
                <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">Heading</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{vessel.heading}°</p>
                </div>
                <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">Destination</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{vessel.destination}</p>
                </div>
                <div>
                    <p className="text-xs text-zinc-500 dark:text-zinc-400">ETA</p>
                    <p className="font-semibold text-zinc-900 dark:text-zinc-100">{new Date(vessel.eta).toLocaleDateString()}</p>
                </div>
            </div>

            {/* CO2 Emissions Estimate */}
            <div className="mt-3 pt-3 border-t border-zinc-200 dark:border-zinc-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-lg">🌱</span>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">Est. CO₂ Emissions</p>
                    </div>
                    <p className="font-semibold text-emerald-600 dark:text-emerald-400 text-sm">
                        ~{Math.round((6150 / (vessel.speed * 24)) * 180 * 3.151)} tons
                    </p>
                </div>
            </div>
        </div>
    );
}
