'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== TYPES ====================

export interface WeatherSystem {
    id: string;
    type: string;
    name: string;
    lat: number;
    lng: number;
    intensity: string;
    wind_speed_knots: number;
    wave_height_m: number;
    radius_nm: number;
    direction: number;
    speed_knots: number;
    warning_level: string;
    impact_description: string;
    forecast_path?: Array<{ lat: number; lng: number; hours: number }>;
}

export interface SeaCondition {
    region: string;
    lat: number;
    lng: number;
    sea_state: number;
    wave_height_m: number;
    wind_direction: number;
    wind_speed_knots: number;
    visibility_nm: number;
    condition: string;
}

export interface PortData {
    code: string;
    name: string;
    country: string;
    lat: number;
    lng: number;
    capacity_teus: number;
    congestion_level: number;
    wait_time_hours: number;
    berth_utilization: number;
    trend: string;
}

export interface RouteData {
    id: string;
    origin: string;
    origin_code: string;
    dest: string;
    dest_code: string;
    distance_nm: number;
    typical_days: number;
    weather_impact: {
        delay_factor: number;
        risk_increase: number;
        affecting_systems: Array<{ id: string; name: string; type: string; impact_level: string }>;
    };
    origin_port_status: PortData;
    dest_port_status: PortData;
    predicted_delay_days: number;
    adjusted_transit_days: number;
    risk_score: number;
    risk_level: string;
}

export interface VesselData {
    vessel_id: string;
    name: string;
    imo: string;
    carrier: string;
    lat: number;
    lng: number;
    speed_knots: number;
    heading: number;
    route_id: string;
    origin: string;
    destination: string;
    progress_percent: number;
    eta: string;
    status: string;
}

export interface Analytics {
    risk_distribution: {
        low: number;
        medium: number;
        high: number;
        critical: number;
    };
    avg_delay_days: number;
    on_time_rate: number;
    total_routes_monitored: number;
}

export interface DashboardData {
    timestamp: string;
    time_factor: number;
    seasonal_factor: number;
    routes: RouteData[];
    vessels: VesselData[];
    weather_systems: WeatherSystem[];
    sea_conditions: SeaCondition[];
    ports: PortData[];
    analytics: Analytics;
    summary: {
        total_routes: number;
        total_vessels: number;
        active_weather_systems: number;
        ports_monitored: number;
        high_risk_routes: number;
        avg_delay: number;
        on_time_rate: number;
    };
}

interface DataContextType {
    data: DashboardData | null;
    loading: boolean;
    error: string | null;
    lastUpdated: Date | null;
    refresh: () => Promise<void>;
    isStale: boolean;
}

// ==================== CONTEXT ====================

const DataContext = createContext<DataContextType | undefined>(undefined);

const REFRESH_INTERVAL = 30000; // 30 seconds
const STALE_THRESHOLD = 60000; // 1 minute

export function DataProvider({ children }: { children: ReactNode }) {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

    const fetchData = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/v1/dashboard/live`, {
                cache: 'no-store',
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const newData = await response.json();
            setData(newData);
            setLastUpdated(new Date());
            setError(null);
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
            setError(err instanceof Error ? err.message : 'Failed to fetch data');
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Auto-refresh
    useEffect(() => {
        const interval = setInterval(fetchData, REFRESH_INTERVAL);
        return () => clearInterval(interval);
    }, [fetchData]);

    // Check if data is stale
    const isStale = lastUpdated
        ? (Date.now() - lastUpdated.getTime()) > STALE_THRESHOLD
        : true;

    const value: DataContextType = {
        data,
        loading,
        error,
        lastUpdated,
        refresh: fetchData,
        isStale,
    };

    return (
        <DataContext.Provider value={value}>
            {children}
        </DataContext.Provider>
    );
}

export function useData(): DataContextType {
    const context = useContext(DataContext);
    if (context === undefined) {
        throw new Error('useData must be used within a DataProvider');
    }
    return context;
}

// ==================== HOOKS FOR SPECIFIC DATA ====================

export function useRoutes() {
    const { data, loading, error } = useData();
    return {
        routes: data?.routes ?? [],
        loading,
        error,
    };
}

export function useVessels() {
    const { data, loading, error } = useData();
    return {
        vessels: data?.vessels ?? [],
        loading,
        error,
    };
}

export function useWeather() {
    const { data, loading, error } = useData();
    return {
        systems: data?.weather_systems ?? [],
        conditions: data?.sea_conditions ?? [],
        loading,
        error,
    };
}

export function usePorts() {
    const { data, loading, error } = useData();
    return {
        ports: data?.ports ?? [],
        loading,
        error,
    };
}

export function useAnalytics() {
    const { data, loading, error } = useData();
    return {
        analytics: data?.analytics ?? null,
        summary: data?.summary ?? null,
        loading,
        error,
    };
}
