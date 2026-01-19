'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { Navigation, PageHeader } from '@/components/Navigation';
import { FilterBar } from '@/components/FilterBar';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types matching actual API response
interface PortInfo {
    port: string;
    country: string;
    code: string;
}

interface Route {
    id: number;
    name: string;
    origin: PortInfo;
    destination: PortInfo;
    distance_nm: number;
    typical_days: number;
    transit_points: string[];
}

interface Vessel {
    id: string;
    name: string;
    position: { lat: number; lng: number };
    status: string;
    destination: string;
    speed: number;
    heading: number;
    eta: string;
}

interface Prediction {
    route_id: string;
    prediction: {
        risk_level: string;
        risk_score: number;
        predicted_delay_days: number;
        on_time_probability: number;
    };
    factors: { factor: string; description: string; severity: string }[];
}

const GlobeMap = dynamic(() => import('@/components/GlobeMap').then(m => m.GlobeMap), {
    ssr: false,
    loading: () => (
        <div className="h-[500px] bg-zinc-900 rounded-2xl flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin text-4xl mb-4">🌍</div>
                <p className="text-zinc-400">Loading 3D Globe...</p>
            </div>
        </div>
    )
});

export default function RoutesPage() {
    const [routes, setRoutes] = useState<Route[]>([]);
    const [vessels, setVessels] = useState<Vessel[]>([]);
    const [predictions, setPredictions] = useState<Map<string, Prediction>>(new Map());
    const [loading, setLoading] = useState(true);
    const [riskFilter, setRiskFilter] = useState('all');
    const [sortBy, setSortBy] = useState('risk');
    const [selectedRoute, setSelectedRoute] = useState<number | undefined>();

    const fetchData = useCallback(async () => {
        try {
            const [routesRes, vesselsRes] = await Promise.all([
                fetch(`${API_BASE}/api/v1/routes/`),
                fetch(`${API_BASE}/api/v1/vessels/`)
            ]);

            const routesData = await routesRes.json();
            const vesselsData = await vesselsRes.json();

            setRoutes(routesData || []);
            setVessels(vesselsData.vessels || vesselsData || []);

            // Fetch predictions for each route using POST
            const predsMap = new Map<string, Prediction>();
            for (const route of (routesData || []).slice(0, 10)) {
                try {
                    const predRes = await fetch(`${API_BASE}/api/v1/predict/`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            route_id: `${route.origin.code}-${route.destination.code}`,
                            origin: route.origin.code,
                            destination: route.destination.code,
                            distance_nm: route.distance_nm,
                            eta_delay: 0,
                            speed_knots: 19.3,
                            congestion: 0.3,
                            storm_risk: 0.2,
                            news_risk: 0.2,
                            carrier_rate: 0.88
                        })
                    });
                    if (predRes.ok) {
                        const pred = await predRes.json();
                        predsMap.set(String(route.id), pred);
                    }
                } catch { }
            }
            setPredictions(predsMap);
        } catch (error) {
            console.error('Failed to fetch data:', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Filter and sort routes
    const filteredRoutes = routes.filter(route => {
        if (riskFilter === 'all') return true;
        const pred = predictions.get(String(route.id));
        return pred?.prediction?.risk_level === riskFilter;
    });

    // Risk level priority for sorting
    const riskPriority: Record<string, number> = {
        critical: 4,
        high: 3,
        medium: 2,
        low: 1,
        unknown: 0
    };

    const sortedRoutes = [...filteredRoutes].sort((a, b) => {
        const predA = predictions.get(String(a.id));
        const predB = predictions.get(String(b.id));

        if (sortBy === 'risk') {
            // Sort by risk level priority (critical first)
            const riskA = riskPriority[predA?.prediction?.risk_level || 'unknown'] || 0;
            const riskB = riskPriority[predB?.prediction?.risk_level || 'unknown'] || 0;
            return riskB - riskA;
        }
        if (sortBy === 'delay') {
            // Sort by predicted delay (highest first)
            return (predB?.prediction?.predicted_delay_days || 0) - (predA?.prediction?.predicted_delay_days || 0);
        }
        if (sortBy === 'distance') {
            // Sort by distance
            return b.distance_nm - a.distance_nm;
        }
        if (sortBy === 'transit') {
            // Sort by transit time
            return b.typical_days - a.typical_days;
        }
        if (sortBy === 'ontime') {
            // Sort by on-time probability (lowest first - worst performers)
            return (predA?.prediction?.on_time_probability || 1) - (predB?.prediction?.on_time_probability || 1);
        }
        return 0;
    });

    return (
        <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
            <Navigation />

            <main className="max-w-7xl mx-auto px-4 py-8">
                <PageHeader
                    icon="🚢"
                    title="Routes & Vessels"
                    subtitle="Track shipping routes and vessel positions in real-time"
                />

                {loading ? (
                    <div className="animate-pulse space-y-6">
                        <div className="h-[500px] bg-zinc-800 rounded-2xl"></div>
                        <div className="h-48 bg-zinc-800 rounded-2xl"></div>
                    </div>
                ) : (
                    <>
                        {/* 3D Globe */}
                        <section className="mb-8">
                            <GlobeMap
                                vessels={vessels.map(v => ({
                                    id: v.id,
                                    name: v.name,
                                    lat: v.position?.lat,
                                    lng: v.position?.lng,
                                    status: v.status,
                                    destination: v.destination,
                                    speed: v.speed,
                                    heading: v.heading,
                                    eta: v.eta
                                }))}
                            />
                        </section>

                        {/* Filter Bar */}
                        <section className="mb-6">
                            <FilterBar
                                riskFilter={riskFilter}
                                onRiskFilterChange={setRiskFilter}
                                sortBy={sortBy}
                                onSortChange={setSortBy}
                            />
                        </section>

                        {/* Route Cards */}
                        <section>
                            <h2 className="text-lg font-semibold text-white mb-4">
                                Shipping Routes ({sortedRoutes.length})
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                                {sortedRoutes.map((route) => {
                                    const pred = predictions.get(String(route.id));
                                    const riskLevel = pred?.prediction?.risk_level || 'unknown';
                                    const onTimeProb = pred?.prediction?.on_time_probability
                                        ? Math.round(pred.prediction.on_time_probability * 100)
                                        : null;

                                    const riskColors: Record<string, string> = {
                                        low: 'border-emerald-500 bg-emerald-500/10',
                                        medium: 'border-amber-500 bg-amber-500/10',
                                        high: 'border-orange-500 bg-orange-500/10',
                                        critical: 'border-rose-500 bg-rose-500/10',
                                        unknown: 'border-zinc-700 bg-zinc-800/50'
                                    };

                                    const riskBadges: Record<string, string> = {
                                        low: 'bg-emerald-500/20 text-emerald-400',
                                        medium: 'bg-amber-500/20 text-amber-400',
                                        high: 'bg-orange-500/20 text-orange-400',
                                        critical: 'bg-rose-500/20 text-rose-400',
                                        unknown: 'bg-zinc-700 text-zinc-400'
                                    };

                                    return (
                                        <div
                                            key={route.id}
                                            className={`rounded-xl border-2 p-5 cursor-pointer transition-all hover:scale-[1.02] ${riskColors[riskLevel] || riskColors.unknown}`}
                                            onClick={() => setSelectedRoute(route.id)}
                                        >
                                            {/* Header */}
                                            <div className="flex items-center justify-between mb-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-10 h-10 rounded-full bg-zinc-700 flex items-center justify-center">
                                                        <span className="text-lg">🚢</span>
                                                    </div>
                                                    <div>
                                                        <h3 className="font-semibold text-white">{route.name}</h3>
                                                        <p className="text-xs text-zinc-400">
                                                            {route.origin.code} → {route.destination.code}
                                                        </p>
                                                    </div>
                                                </div>
                                                <span className={`px-3 py-1 rounded-full text-xs font-medium uppercase ${riskBadges[riskLevel] || riskBadges.unknown}`}>
                                                    {riskLevel}
                                                </span>
                                            </div>

                                            {/* Stats */}
                                            <div className="grid grid-cols-3 gap-4">
                                                <div>
                                                    <p className="text-xs text-zinc-500">Distance</p>
                                                    <p className="font-semibold text-sm text-white">{route.distance_nm.toLocaleString()} nm</p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-zinc-500">Transit Time</p>
                                                    <p className="font-semibold text-sm text-white">{route.typical_days} days</p>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-zinc-500">On-Time</p>
                                                    <p className={`font-semibold text-sm ${onTimeProb && onTimeProb >= 90 ? 'text-emerald-400' : onTimeProb && onTimeProb >= 70 ? 'text-amber-400' : 'text-zinc-400'}`}>
                                                        {onTimeProb !== null ? `${onTimeProb}%` : '—'}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Risk Factors */}
                                            {pred?.factors && pred.factors.length > 0 && (
                                                <div className="mt-4 pt-4 border-t border-zinc-700">
                                                    <p className="text-xs text-zinc-500 mb-2">Risk Factors</p>
                                                    <div className="flex flex-wrap gap-2">
                                                        {pred.factors.slice(0, 3).map((factor, i) => (
                                                            <span key={i} className="text-xs px-2 py-1 rounded-full bg-zinc-700 text-zinc-300">
                                                                {factor.factor}
                                                            </span>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </section>
                    </>
                )}
            </main>
        </div>
    );
}
