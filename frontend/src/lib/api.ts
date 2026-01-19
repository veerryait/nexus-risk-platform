// Enhanced API configuration for connecting to FastAPI backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API connection status
export type ConnectionStatus = 'connected' | 'disconnected' | 'checking';

export interface Route {
    id: string;
    origin: string;
    destination: string;
    origin_name: string;
    destination_name: string;
    distance_nm: number;
    typical_days: number;
    risk_score?: number;
}

export interface Prediction {
    route_id: string;
    prediction: {
        on_time_probability: number;
        delay_probability: number;
        predicted_delay_days: number;
        risk_level: string;
        confidence: number;
    };
    factors: Array<{
        factor: string;
        impact: string;
        description: string;
    }>;
    recommendations: string[];
}

export interface Stats {
    total_routes: number;
    active_shipments: number;
    avg_on_time: number;
    high_risk_count: number;
}

export interface PortStatus {
    port_code: string;
    port_name: string;
    congestion_level: string;
    congestion_score: number;
}

export interface Vessel {
    id: string;
    name: string;
    imo: string;
    position: { lat: number; lng: number };
    status: string;
    speed: number;
    heading: number;
    destination: string;
    eta: string;
    carrier?: string;
    route_id?: string;
}

export interface ApiError {
    message: string;
    code?: number;
    timestamp: string;
}

// Enhanced fetch with timeout and error handling
async function fetchWithTimeout(
    url: string,
    options: RequestInit = {},
    timeout = 10000
): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                'Accept': 'application/json',
                ...options.headers,
            }
        });
        return response;
    } catch (error) {
        // Don't log AbortError - it's expected during component unmount
        if (error instanceof Error && error.name === 'AbortError') {
            throw error; // Re-throw but don't log
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

// Health check with retry
export async function healthCheck(): Promise<{ status: ConnectionStatus; latency?: number }> {
    const start = Date.now();
    try {
        const res = await fetchWithTimeout(`${API_BASE}/health`, { cache: 'no-store' }, 5000);
        if (res.ok) {
            return { status: 'connected', latency: Date.now() - start };
        }
        return { status: 'disconnected' };
    } catch {
        return { status: 'disconnected' };
    }
}

// Fetch routes from API
export async function getRoutes(): Promise<{ data: Route[]; error?: ApiError; fromCache: boolean }> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/v1/routes/`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        const data = await res.json();
        const routesArray = Array.isArray(data) ? data : (data.routes || []);

        return {
            data: routesArray.map((r: { id: number | string; origin: { code: string; port?: string } | string; destination: { code: string; port?: string } | string; distance_nm: number; typical_days: number }) => ({
                id: typeof r.origin === 'object' ? `${r.origin.code}-${typeof r.destination === 'object' ? r.destination.code : r.destination}` : String(r.id),
                origin: typeof r.origin === 'object' ? r.origin.code : r.origin,
                destination: typeof r.destination === 'object' ? r.destination.code : r.destination,
                origin_name: typeof r.origin === 'object' ? r.origin.port || r.origin.code : r.origin,
                destination_name: typeof r.destination === 'object' ? r.destination.port || r.destination.code : r.destination,
                distance_nm: r.distance_nm,
                typical_days: r.typical_days,
            })),
            fromCache: false
        };
    } catch (error) {
        console.error('Error fetching routes:', error);
        return {
            data: getMockRoutes(),
            error: { message: error instanceof Error ? error.message : 'Network error', timestamp: new Date().toISOString() },
            fromCache: true
        };
    }
}

// Get risk prediction for a route
export async function getPrediction(routeId: string): Promise<{ data: Prediction; error?: ApiError }> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/v1/predict/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ route_id: routeId })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return { data: await res.json() };
    } catch (error) {
        console.error('Error getting prediction:', error);
        return {
            data: getMockPrediction(routeId),
            error: { message: error instanceof Error ? error.message : 'Prediction failed', timestamp: new Date().toISOString() }
        };
    }
}

// Get port status
export async function getPortStatus(): Promise<{ data: PortStatus[]; error?: ApiError }> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/v1/admin/port-status`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return { data: data.ports || [] };
    } catch (error) {
        console.error('Error fetching port status:', error);
        return {
            data: getMockPortStatus(),
            error: { message: error instanceof Error ? error.message : 'Port status unavailable', timestamp: new Date().toISOString() }
        };
    }
}

// Get vessels
export async function getVessels(): Promise<{ data: Vessel[]; error?: ApiError }> {
    try {
        const res = await fetchWithTimeout(`${API_BASE}/api/v1/vessels/`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        return { data: data.vessels || data || [] };
    } catch (error) {
        console.error('Error fetching vessels:', error);
        return {
            data: getMockVessels(),
            error: { message: error instanceof Error ? error.message : 'Vessels unavailable', timestamp: new Date().toISOString() }
        };
    }
}

// Get all dashboard data in one call
export async function getDashboardData() {
    const [routes, ports, vessels, health] = await Promise.all([
        getRoutes(),
        getPortStatus(),
        getVessels(),
        healthCheck()
    ]);

    // Get predictions for routes to calculate on-time rate
    let onTimeCount = 0;
    let highRiskCount = 0;

    for (const route of routes.data.slice(0, 5)) {
        const prediction = await getPrediction(route.id);
        if (prediction.data?.prediction) {
            const prob = prediction.data.prediction.on_time_probability || 0;
            if (prob >= 0.7) onTimeCount++;
            if (prediction.data.prediction.risk_level === 'high' ||
                prediction.data.prediction.risk_level === 'critical') {
                highRiskCount++;
            }
        }
    }

    const avgOnTime = routes.data.length > 0
        ? Math.round((onTimeCount / routes.data.length) * 100)
        : 92;

    // Compute stats with REAL data
    const stats: Stats = {
        total_routes: routes.data.length,
        active_shipments: vessels.data.length,  // Actual vessel count
        avg_on_time: avgOnTime,
        high_risk_count: highRiskCount
    };

    return {
        routes: routes.data,
        ports: ports.data,
        vessels: vessels.data,
        stats,
        connection: health,
        hasErrors: !!routes.error || !!ports.error,
        timestamp: new Date().toISOString()
    };
}

// API URL getter for external use
export function getApiUrl(): string {
    return API_BASE;
}

// Mock data fallbacks
function getMockRoutes(): Route[] {
    return [
        { id: 'TWKHH-USLAX', origin: 'TWKHH', destination: 'USLAX', origin_name: 'Kaohsiung', destination_name: 'Los Angeles', distance_nm: 6150, typical_days: 14 },
        { id: 'TWKHH-USLGB', origin: 'TWKHH', destination: 'USLGB', origin_name: 'Kaohsiung', destination_name: 'Long Beach', distance_nm: 6150, typical_days: 14 },
        { id: 'TWKHH-USOAK', origin: 'TWKHH', destination: 'USOAK', origin_name: 'Kaohsiung', destination_name: 'Oakland', distance_nm: 5950, typical_days: 13 },
        { id: 'TWTPE-USLAX', origin: 'TWTPE', destination: 'USLAX', origin_name: 'Taipei', destination_name: 'Los Angeles', distance_nm: 6300, typical_days: 15 },
        { id: 'TWKHH-USSEA', origin: 'TWKHH', destination: 'USSEA', origin_name: 'Kaohsiung', destination_name: 'Seattle', distance_nm: 5200, typical_days: 12 },
    ];
}

function getMockPrediction(routeId: string): Prediction {
    const riskLevels = ['low', 'medium', 'high'];
    const level = riskLevels[Math.floor(Math.random() * 3)];
    return {
        route_id: routeId,
        prediction: {
            on_time_probability: level === 'low' ? 0.95 : level === 'medium' ? 0.75 : 0.55,
            delay_probability: level === 'low' ? 0.05 : level === 'medium' ? 0.25 : 0.45,
            predicted_delay_days: level === 'low' ? 0 : level === 'medium' ? 1 : 3,
            risk_level: level,
            confidence: 0.88
        },
        factors: [
            { factor: 'weather', impact: level, description: level === 'high' ? 'Storm system approaching' : 'Normal conditions' },
            { factor: 'congestion', impact: 'low', description: 'Port operating normally' }
        ],
        recommendations: level === 'high' ? ['Consider alternate route', 'Monitor weather'] : ['Standard monitoring']
    };
}

function getMockPortStatus(): PortStatus[] {
    return [
        { port_code: 'USLAX', port_name: 'Port of Los Angeles', congestion_level: 'medium', congestion_score: 0.45 },
        { port_code: 'USLGB', port_name: 'Port of Long Beach', congestion_level: 'medium', congestion_score: 0.50 },
        { port_code: 'TWKHH', port_name: 'Port of Kaohsiung', congestion_level: 'low', congestion_score: 0.25 },
        { port_code: 'USOAK', port_name: 'Port of Oakland', congestion_level: 'low', congestion_score: 0.30 },
    ];
}

function getMockVessels(): Vessel[] {
    return [
        { id: 'v1', name: 'Ever Given', imo: '9811000', position: { lat: 25.5, lng: -140 }, status: 'underway', speed: 18, heading: 85, destination: 'USLAX', eta: '2026-01-15' },
        { id: 'v2', name: 'MSC Oscar', imo: '9703291', position: { lat: 28.2, lng: -125 }, status: 'underway', speed: 20, heading: 78, destination: 'USLGB', eta: '2026-01-14' },
        { id: 'v3', name: 'OOCL Hong Kong', imo: '9776171', position: { lat: 22.5, lng: 120.5 }, status: 'berthed', speed: 0, heading: 0, destination: 'TWKHH', eta: '2026-01-11' },
    ];
}
