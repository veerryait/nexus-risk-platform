'use client';

import { useState, useEffect } from 'react';
import {
    LineChart,
    Line,
    AreaChart,
    Area,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
    PieChart,
    Pie,
    Cell,
} from 'recharts';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface TrendData {
    date: string;
    low: number;
    medium: number;
    high: number;
    critical: number;
}

interface PerformanceData {
    month: string;
    onTime: number;
    delays: number;
}

interface DelayData {
    route: string;
    predicted: number;
    actual: number;
}

// Fetch risk trends from API
async function fetchTrends(): Promise<TrendData[]> {
    try {
        const res = await fetch(`${API_BASE}/api/v1/analytics/trends?months=12`);
        if (res.ok) {
            const data = await res.json();
            return data.trends || [];
        }
    } catch (e) {
        console.error('Failed to fetch trends:', e);
    }
    return getDefaultTrends();
}

// Fetch performance data from API
async function fetchPerformance(): Promise<PerformanceData[]> {
    try {
        const res = await fetch(`${API_BASE}/api/v1/analytics/performance?months=6`);
        if (res.ok) {
            const data = await res.json();
            return data.data || [];
        }
    } catch (e) {
        console.error('Failed to fetch performance:', e);
    }
    return getDefaultPerformance();
}

// Fetch delay comparison from API
async function fetchDelayComparison(): Promise<DelayData[]> {
    try {
        const res = await fetch(`${API_BASE}/api/v1/analytics/delay-comparison`);
        if (res.ok) {
            const data = await res.json();
            return data.data || [];
        }
    } catch (e) {
        console.error('Failed to fetch delay comparison:', e);
    }
    return getDefaultDelays();
}

// Default data fallbacks
function getDefaultTrends(): TrendData[] {
    return [
        { date: 'Jan', low: 85, medium: 10, high: 4, critical: 1 },
        { date: 'Feb', low: 82, medium: 12, high: 5, critical: 1 },
        { date: 'Mar', low: 88, medium: 8, high: 3, critical: 1 },
        { date: 'Apr', low: 90, medium: 7, high: 2, critical: 1 },
        { date: 'May', low: 87, medium: 9, high: 3, critical: 1 },
        { date: 'Jun', low: 78, medium: 14, high: 6, critical: 2 },
    ];
}

function getDefaultPerformance(): PerformanceData[] {
    return [
        { month: 'Jan', onTime: 91, delays: 1.2 },
        { month: 'Feb', onTime: 89, delays: 1.5 },
        { month: 'Mar', onTime: 93, delays: 0.8 },
        { month: 'Apr', onTime: 95, delays: 0.5 },
        { month: 'May', onTime: 92, delays: 1.0 },
        { month: 'Jun', onTime: 88, delays: 1.8 },
    ];
}

function getDefaultDelays(): DelayData[] {
    return [
        { route: 'TWKHH-USLAX', predicted: 0.5, actual: 0.3 },
        { route: 'TWKHH-USLGB', predicted: 0.8, actual: 0.6 },
        { route: 'TWKHH-USOAK', predicted: 0.3, actual: 0.2 },
        { route: 'TWTPE-USLAX', predicted: 0.6, actual: 0.5 },
        { route: 'TWKHH-USSEA', predicted: 0.4, actual: 0.3 },
    ];
}

interface RiskTrendsChartProps {
    height?: number;
}

export function RiskTrendsChart({ height = 300 }: RiskTrendsChartProps) {
    const [data, setData] = useState<TrendData[]>(getDefaultTrends());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTrends().then(trends => {
            setData(trends.length > 0 ? trends : getDefaultTrends());
            setLoading(false);
        });
    }, []);

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                Risk Distribution Trend
            </h3>
            {loading ? (
                <div className="h-[300px] animate-pulse bg-zinc-200 dark:bg-zinc-700 rounded" />
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <AreaChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis dataKey="date" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                        <YAxis stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} label={{ value: '% of Routes', angle: -90, position: 'insideLeft', fill: '#9ca3af' }} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', color: '#fff' }} />
                        <Legend />
                        <Area type="monotone" dataKey="critical" stackId="1" stroke="#ef4444" fill="#ef4444" name="Critical" />
                        <Area type="monotone" dataKey="high" stackId="1" stroke="#f97316" fill="#f97316" name="High" />
                        <Area type="monotone" dataKey="medium" stackId="1" stroke="#f59e0b" fill="#f59e0b" name="Medium" />
                        <Area type="monotone" dataKey="low" stackId="1" stroke="#10b981" fill="#10b981" name="Low" />
                    </AreaChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}

interface DelayPredictionChartProps {
    height?: number;
}

export function DelayPredictionChart({ height = 300 }: DelayPredictionChartProps) {
    const [data, setData] = useState<DelayData[]>(getDefaultDelays());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDelayComparison().then(delays => {
            setData(delays.length > 0 ? delays : getDefaultDelays());
            setLoading(false);
        });
    }, []);

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                Delay Prediction vs Actual
            </h3>
            {loading ? (
                <div className="h-[300px] animate-pulse bg-zinc-200 dark:bg-zinc-700 rounded" />
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart data={data} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis type="number" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} label={{ value: 'Days', position: 'insideBottom', fill: '#9ca3af', offset: -5 }} />
                        <YAxis type="category" dataKey="route" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 11 }} width={100} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', color: '#fff' }} formatter={(value) => `${value} days`} />
                        <Legend />
                        <Bar dataKey="predicted" fill="#6366f1" name="Predicted Delay" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="actual" fill="#22d3ee" name="Actual Delay" radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}

interface OnTimeRateChartProps {
    onTimeRate?: number;
    height?: number;
}

export function OnTimeRateChart({ onTimeRate = 92, height = 200 }: OnTimeRateChartProps) {
    const data = [
        { name: 'On-Time', value: onTimeRate, color: '#10b981' },
        { name: 'Delayed', value: 100 - onTimeRate, color: '#f59e0b' },
    ];

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                On-Time Delivery Rate
            </h3>
            <ResponsiveContainer width="100%" height={height}>
                <PieChart>
                    <Pie
                        data={data}
                        cx="50%"
                        cy="50%"
                        innerRadius={55}
                        outerRadius={75}
                        paddingAngle={2}
                        dataKey="value"
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', color: '#fff' }} formatter={(value) => `${value}%`} />
                    <Legend
                        verticalAlign="middle"
                        align="right"
                        layout="vertical"
                        iconType="circle"
                        formatter={(value, entry) => {
                            const item = data.find(d => d.name === value);
                            return <span className="text-sm text-zinc-600 dark:text-zinc-300">{value}: {item?.value}%</span>;
                        }}
                    />
                </PieChart>
            </ResponsiveContainer>
            <div className="text-center mt-2">
                <span className="text-3xl font-bold text-emerald-500">{onTimeRate}%</span>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">30-Day Average</p>
            </div>
        </div>
    );
}

interface PerformanceLineChartProps {
    height?: number;
}

export function PerformanceLineChart({ height = 250 }: PerformanceLineChartProps) {
    const [data, setData] = useState<PerformanceData[]>(getDefaultPerformance());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchPerformance().then(perf => {
            setData(perf.length > 0 ? perf : getDefaultPerformance());
            setLoading(false);
        });
    }, []);

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                Route Performance
            </h3>
            {loading ? (
                <div className="h-[250px] animate-pulse bg-zinc-200 dark:bg-zinc-700 rounded" />
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
                        <XAxis dataKey="month" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} />
                        <YAxis yAxisId="left" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} domain={[80, 100]} />
                        <YAxis yAxisId="right" orientation="right" stroke="#9ca3af" tick={{ fill: '#9ca3af', fontSize: 12 }} domain={[0, 3]} />
                        <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px', color: '#fff' }} />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="onTime" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', strokeWidth: 2 }} name="On-Time %" />
                        <Line yAxisId="right" type="monotone" dataKey="delays" stroke="#f59e0b" strokeWidth={2} dot={{ fill: '#f59e0b', strokeWidth: 2 }} name="Avg Delay (days)" />
                    </LineChart>
                </ResponsiveContainer>
            )}
        </div>
    );
}
