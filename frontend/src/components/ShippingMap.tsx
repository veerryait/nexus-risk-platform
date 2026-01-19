'use client';

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Port coordinates
const PORTS = {
    TWKHH: { name: 'Kaohsiung', lat: 22.6163, lng: 120.3133 },
    TWTPE: { name: 'Taipei/Keelung', lat: 25.1286, lng: 121.7419 },
    TWTXG: { name: 'Taichung', lat: 24.2632, lng: 120.5149 },
    USLAX: { name: 'Los Angeles', lat: 33.7406, lng: -118.26 },
    USLGB: { name: 'Long Beach', lat: 33.7701, lng: -118.1937 },
    USOAK: { name: 'Oakland', lat: 37.7955, lng: -122.2791 },
    USSEA: { name: 'Seattle', lat: 47.5826, lng: -122.3495 },
};

interface Route {
    id: string;
    origin: string;
    destination: string;
    riskLevel?: 'low' | 'medium' | 'high' | 'critical';
}

interface VesselOnMap {
    id: string;
    name: string;
    lat?: number;
    lng?: number;
    status: string;
    destination: string;
    speed: number;
    heading: number;
}

interface ShippingMapProps {
    routes: Route[];
    vessels?: VesselOnMap[];
    selectedRoute?: string;
    selectedVessel?: string;
    onRouteSelect?: (routeId: string) => void;
    onVesselSelect?: (vesselId: string) => void;
    height?: string;
}

// Risk colors
const riskColors = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#f97316',
    critical: '#ef4444',
    unknown: '#6b7280',
};

export function ShippingMap({ routes, vessels = [], selectedRoute, selectedVessel, onRouteSelect, onVesselSelect, height = '500px' }: ShippingMapProps) {
    const mapContainer = useRef<HTMLDivElement>(null);
    const mapRef = useRef<L.Map | null>(null);
    const vesselMarkersRef = useRef<L.Marker[]>([]);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    useEffect(() => {
        if (!mounted || !mapContainer.current || mapRef.current) return;

        // Initialize map centered on Pacific Ocean
        const map = L.map(mapContainer.current, {
            center: [25, 180], // Pacific center (date line)
            zoom: 2,
            minZoom: 2,
            maxZoom: 10,
            worldCopyJump: false,
        });

        // Add dark-themed tiles
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap, &copy; CARTO',
            maxZoom: 19,
            noWrap: false,
        }).addTo(map);

        mapRef.current = map;

        // Add port markers at multiple world copies for infinite scroll
        const worldOffsets = [-360, 0, 360]; // Left copy, center, right copy

        Object.entries(PORTS).forEach(([code, port]) => {
            const isTaiwan = code.startsWith('TW');

            const icon = L.divIcon({
                className: 'port-marker',
                html: `<div style="
          width: 14px;
          height: 14px;
          border-radius: 50%;
          background: ${isTaiwan ? '#06b6d4' : '#8b5cf6'};
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.4);
        "></div>`,
                iconSize: [14, 14],
                iconAnchor: [7, 7],
            });

            // Add marker at each world copy
            worldOffsets.forEach(offset => {
                L.marker([port.lat, port.lng + offset], { icon })
                    .addTo(map)
                    .bindPopup(`<strong>${port.name}</strong><br/><span style="color:#666">${code}</span>`);
            });
        });

        return () => {
            map.remove();
            mapRef.current = null;
        };
    }, [mounted]);

    // Add routes
    useEffect(() => {
        if (!mapRef.current || !mounted) return;
        const map = mapRef.current;

        // Remove existing polylines
        map.eachLayer(layer => {
            if (layer instanceof L.Polyline && !(layer instanceof L.Polygon)) {
                map.removeLayer(layer);
            }
        });

        // World offsets for infinite scroll
        const worldOffsets = [-360, 0, 360];

        // Add route lines at each world copy
        routes.forEach(route => {
            const origin = PORTS[route.origin as keyof typeof PORTS];
            const dest = PORTS[route.destination as keyof typeof PORTS];
            if (!origin || !dest) return;

            const color = riskColors[route.riskLevel || 'unknown'];
            const isSelected = selectedRoute === route.id;

            // Create route for each world copy
            worldOffsets.forEach(offset => {
                // Taiwan (~120°E) to US (~-120°W = 240°E when going east)
                const startLng = origin.lng + offset;
                // For destinations with negative longitude, add 360 to go "east"
                const endLng = (dest.lng < 0 ? dest.lng + 360 : dest.lng) + offset;

                const points: L.LatLngExpression[] = [];
                const numPoints = 50;

                for (let i = 0; i <= numPoints; i++) {
                    const t = i / numPoints;
                    const lng = startLng + (endLng - startLng) * t;
                    const lat = origin.lat + (dest.lat - origin.lat) * t;

                    // Add slight arc for visual appeal
                    const arcHeight = Math.sin(t * Math.PI) * 8;

                    points.push([lat + arcHeight, lng]);
                }

                const polyline = L.polyline(points, {
                    color: color,
                    weight: isSelected ? 4 : 2,
                    opacity: isSelected ? 1 : 0.7,
                    dashArray: isSelected ? undefined : '5, 5',
                }).addTo(map);

                polyline.on('click', () => {
                    onRouteSelect?.(route.id);
                });

                polyline.bindPopup(`
                    <strong>${route.id}</strong><br/>
                    <span style="color:${color}">Risk: ${route.riskLevel || 'unknown'}</span>
                `);
            });
        });
    }, [routes, selectedRoute, onRouteSelect, mounted]);

    // Add vessel markers
    useEffect(() => {
        if (!mapRef.current || !mounted) return;
        const map = mapRef.current;

        // Remove existing vessel markers
        vesselMarkersRef.current.forEach(marker => map.removeLayer(marker));
        vesselMarkersRef.current = [];

        if (!vessels.length) return;

        // World offsets for infinite scroll
        const worldOffsets = [-360, 0, 360];

        // Port lookup for destination matching
        const destToPort: Record<string, { lat: number; lng: number }> = {
            'Los Angeles': PORTS.USLAX,
            'Long Beach': PORTS.USLGB,
            'Oakland': PORTS.USOAK,
            'Seattle': PORTS.USSEA,
        };

        // Taiwan ports as origin
        const taiwanPorts = [PORTS.TWKHH, PORTS.TWTPE, PORTS.TWTXG];

        vessels.forEach((vessel, index) => {
            // Calculate position - if vessel has lat/lng, use it
            // Otherwise, interpolate based on status/destination
            let vesselLat: number;
            let vesselLng: number;

            if (vessel.lat && vessel.lng) {
                vesselLat = vessel.lat;
                vesselLng = vessel.lng;
            } else {
                // Simulate position based on vessel index and status
                const destPort = destToPort[vessel.destination] || PORTS.USLAX;
                const originPort = taiwanPorts[index % 3];

                if (vessel.status === 'at_port' || vessel.status === 'berthed') {
                    // At destination port
                    vesselLat = destPort.lat;
                    vesselLng = destPort.lng;
                } else {
                    // Underway - interpolate position (spread across route)
                    const progress = 0.2 + (index * 0.08) % 0.6; // 20-80% along route

                    // Calculate position going EAST across Pacific
                    const startLng = originPort.lng;
                    const endLng = destPort.lng < 0 ? destPort.lng + 360 : destPort.lng;

                    vesselLng = startLng + (endLng - startLng) * progress;
                    vesselLat = originPort.lat + (destPort.lat - originPort.lat) * progress;

                    // Add arc
                    vesselLat += Math.sin(progress * Math.PI) * 8;

                    // Normalize longitude
                    if (vesselLng > 180) vesselLng -= 360;
                }
            }

            // Create ship icon
            const isSelected = selectedVessel === vessel.id;
            const statusColor = vessel.status === 'underway' ? '#10b981' :
                vessel.status === 'at_port' ? '#3b82f6' : '#f59e0b';

            const icon = L.divIcon({
                className: 'vessel-marker',
                html: `<div style="
                    font-size: 20px;
                    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
                    transform: rotate(${vessel.heading - 45}deg);
                    ${isSelected ? 'transform: scale(1.3) rotate(' + (vessel.heading - 45) + 'deg);' : ''}
                ">🚢</div>
                <div style="
                    position: absolute;
                    bottom: -18px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: ${statusColor};
                    color: white;
                    padding: 1px 6px;
                    border-radius: 4px;
                    font-size: 10px;
                    font-weight: 600;
                    white-space: nowrap;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                ">${vessel.name.split(' ').slice(0, 2).join(' ')}</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15],
            });

            // Add marker at each world copy
            worldOffsets.forEach(offset => {
                const marker = L.marker([vesselLat, vesselLng + offset], { icon })
                    .addTo(map)
                    .bindPopup(`
                        <div style="min-width: 150px;">
                            <strong style="font-size: 14px;">🚢 ${vessel.name}</strong><br/>
                            <div style="margin-top: 8px; font-size: 12px; color: #666;">
                                <div><strong>Status:</strong> ${vessel.status}</div>
                                <div><strong>Speed:</strong> ${vessel.speed} kts</div>
                                <div><strong>Heading:</strong> ${vessel.heading}°</div>
                                <div><strong>Destination:</strong> ${vessel.destination}</div>
                            </div>
                        </div>
                    `);

                marker.on('click', () => {
                    onVesselSelect?.(vessel.id);
                });

                vesselMarkersRef.current.push(marker);
            });
        });
    }, [vessels, selectedVessel, onVesselSelect, mounted]);

    if (!mounted) {
        return <div className="h-[400px] bg-zinc-200 dark:bg-zinc-800 rounded-2xl animate-pulse" />;
    }

    return (
        <div className="relative rounded-2xl overflow-hidden border border-zinc-200 dark:border-zinc-800">
            <div ref={mapContainer} style={{ height }} className="w-full" />

            {/* Legend */}
            <div className="absolute bottom-4 left-4 bg-white/90 dark:bg-zinc-900/90 backdrop-blur rounded-lg p-3 text-sm z-[1000]">
                <p className="font-semibold text-zinc-900 dark:text-zinc-100 mb-2">Route Risk</p>
                <div className="space-y-1">
                    {Object.entries(riskColors).filter(([k]) => k !== 'unknown').map(([level, color]) => (
                        <div key={level} className="flex items-center gap-2">
                            <div style={{ background: color }} className="w-3 h-3 rounded-full" />
                            <span className="text-zinc-600 dark:text-zinc-400 capitalize">{level}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Port Legend */}
            <div className="absolute bottom-4 right-4 bg-white/90 dark:bg-zinc-900/90 backdrop-blur rounded-lg p-3 text-sm z-[1000]">
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-cyan-500" />
                    <span className="text-zinc-600 dark:text-zinc-400">Taiwan Ports</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-violet-500" />
                    <span className="text-zinc-600 dark:text-zinc-400">US Ports</span>
                </div>
            </div>
        </div>
    );
}

// Create arc path across Pacific (Taiwan → US goes EAST across Pacific)
function createArcPath(start: [number, number], end: [number, number]): [number, number][] {
    const points: [number, number][] = [];
    const numPoints = 50;

    let startLng = start[1];
    let endLng = end[1];

    // Taiwan (~120°E) to US (~-120°W): go EAST across Pacific
    // Need to add 360 to US longitude to make it go east (120 to 240 instead of 120 to -120)
    if (startLng > 0 && endLng < 0) {
        // Going from positive (Taiwan) to negative (US) longitude
        // The Pacific route goes EAST, so we need US to be "ahead" of Taiwan
        endLng += 360; // -120 becomes 240, so path goes 120 → 240 (east)
    }

    for (let i = 0; i <= numPoints; i++) {
        const t = i / numPoints;
        const lng = startLng + (endLng - startLng) * t;
        const lat = start[0] + (end[0] - start[0]) * t;

        // Add slight arc for visual appeal (great circle approximation)
        const arcHeight = Math.sin(t * Math.PI) * 5;

        // Normalize longitude back to -180 to 180 range
        let normalizedLng = lng;
        if (normalizedLng > 180) normalizedLng -= 360;

        points.push([lat + arcHeight, normalizedLng]);
    }

    return points;
}

