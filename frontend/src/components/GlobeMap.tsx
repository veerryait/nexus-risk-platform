'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { VesselCinematicView } from './VesselCinematicView';

// Port coordinates
const PORTS = {
    TWKHH: { name: 'Kaohsiung', lat: 22.6163, lng: 120.3133, country: 'Taiwan' },
    TWTPE: { name: 'Taipei/Keelung', lat: 25.1286, lng: 121.7419, country: 'Taiwan' },
    TWTXG: { name: 'Taichung', lat: 24.2632, lng: 120.5149, country: 'Taiwan' },
    USLAX: { name: 'Los Angeles', lat: 33.7406, lng: -118.26, country: 'USA' },
    USLGB: { name: 'Long Beach', lat: 33.7701, lng: -118.1937, country: 'USA' },
    USOAK: { name: 'Oakland', lat: 37.7955, lng: -122.2791, country: 'USA' },
    USSEA: { name: 'Seattle', lat: 47.5826, lng: -122.3495, country: 'USA' },
};

interface VesselData {
    id: string;
    name: string;
    lat?: number;
    lng?: number;
    status: string;
    destination: string;
    speed: number;
    heading: number;
    eta?: string;
    imo?: string;
}

interface GlobeMapProps {
    vessels: VesselData[];
    onVesselSelect?: (vessel: VesselData) => void;
    selectedVessel?: string;
    height?: string;
}

// Generate arc data for routes
function generateRoutes() {
    const routes: Array<{
        startLat: number;
        startLng: number;
        endLat: number;
        endLng: number;
        color: string;
    }> = [];

    const taiwanPorts = [PORTS.TWKHH, PORTS.TWTPE];
    const usPorts = [PORTS.USLAX, PORTS.USLGB, PORTS.USOAK, PORTS.USSEA];

    taiwanPorts.forEach(origin => {
        usPorts.forEach(dest => {
            routes.push({
                startLat: origin.lat,
                startLng: origin.lng,
                endLat: dest.lat,
                endLng: dest.lng,
                color: 'rgba(0, 200, 255, 0.6)',
            });
        });
    });

    return routes;
}

// Calculate vessel position along route
function getVesselPosition(vessel: VesselData, index: number) {
    const destToPort: Record<string, { lat: number; lng: number }> = {
        'Los Angeles': PORTS.USLAX,
        'Long Beach': PORTS.USLGB,
        'Oakland': PORTS.USOAK,
        'Seattle': PORTS.USSEA,
    };

    const taiwanPorts = [PORTS.TWKHH, PORTS.TWTPE, PORTS.TWTXG];

    if (vessel.lat && vessel.lng) {
        return { lat: vessel.lat, lng: vessel.lng };
    }

    const destPort = destToPort[vessel.destination] || PORTS.USLAX;
    const originPort = taiwanPorts[index % 3];

    if (vessel.status === 'at_port' || vessel.status === 'berthed') {
        return { lat: destPort.lat, lng: destPort.lng };
    }

    // Simulate position along route
    const progress = 0.15 + (index * 0.06) % 0.7;

    // Great circle interpolation
    const lat = originPort.lat + (destPort.lat - originPort.lat) * progress;
    let lng = originPort.lng + (destPort.lng - originPort.lng + 360) * progress;
    if (lng > 180) lng -= 360;

    // Add arc height
    const arcLat = lat + Math.sin(progress * Math.PI) * 10;

    return { lat: arcLat, lng };
}

export function GlobeMap({ vessels, onVesselSelect, selectedVessel, height = '600px' }: GlobeMapProps) {
    const globeEl = useRef<HTMLDivElement>(null);
    const globeInstance = useRef<any>(null);
    const [mounted, setMounted] = useState(false);
    const [Globe, setGlobe] = useState<any>(null);
    const [hoveredVessel, setHoveredVessel] = useState<VesselData | null>(null);
    const [cinematicVessel, setCinematicVessel] = useState<VesselData | null>(null);
    const [showCinematic, setShowCinematic] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false);

    // Dynamically import globe.gl (client-side only)
    useEffect(() => {
        import('globe.gl').then(module => {
            setGlobe(() => module.default);
            setMounted(true);
        });
    }, []);

    // Initialize globe
    useEffect(() => {
        if (!mounted || !Globe || !globeEl.current || globeInstance.current) return;

        const globe = Globe()
            .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
            .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
            .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
            .showAtmosphere(true)
            .atmosphereColor('#3a6ea5')
            .atmosphereAltitude(0.25)
            .width(globeEl.current.clientWidth)
            .height(parseInt(height));

        globe(globeEl.current);

        // Set initial view to Pacific
        globe.pointOfView({ lat: 25, lng: 180, altitude: 2.5 }, 0);

        // Enable controls
        globe.controls().enableZoom = true;
        globe.controls().autoRotate = true;
        globe.controls().autoRotateSpeed = 0.3;

        globeInstance.current = globe;

        // Cleanup
        return () => {
            if (globeInstance.current) {
                globeInstance.current._destructor?.();
                globeInstance.current = null;
            }
        };
    }, [mounted, Globe, height]);

    // Add routes (arcs)
    useEffect(() => {
        if (!globeInstance.current) return;

        const routes = generateRoutes();

        globeInstance.current
            .arcsData(routes)
            .arcColor('color')
            .arcAltitude(0.15)
            .arcStroke(0.5)
            .arcDashLength(0.5)
            .arcDashGap(0.1)
            .arcDashAnimateTime(4000);
    }, [mounted, Globe]);

    // Add port markers
    useEffect(() => {
        if (!globeInstance.current) return;

        const portData = Object.entries(PORTS).map(([code, port]) => ({
            lat: port.lat,
            lng: port.lng,
            name: port.name,
            code,
            country: port.country,
            size: port.country === 'Taiwan' ? 0.4 : 0.3,
            color: port.country === 'Taiwan' ? '#00d4ff' : '#a855f7',
        }));

        globeInstance.current
            .pointsData(portData)
            .pointAltitude(0.01)
            .pointColor('color')
            .pointRadius('size')
            .pointLabel((d: any) => `
                <div style="
                    background: rgba(0,0,0,0.8);
                    padding: 8px 12px;
                    border-radius: 8px;
                    color: white;
                    font-size: 12px;
                ">
                    <strong>${d.name}</strong><br/>
                    <span style="color: #888;">${d.country}</span>
                </div>
            `);
    }, [mounted, Globe]);

    // Add vessel markers
    useEffect(() => {
        if (!globeInstance.current || !vessels.length) return;

        const vesselData = vessels.map((vessel, index) => {
            const pos = getVesselPosition(vessel, index);
            return {
                ...vessel,
                lat: pos.lat,
                lng: pos.lng,
                size: selectedVessel === vessel.id ? 0.8 : 0.5,
                color: vessel.status === 'underway' ? '#10b981' :
                    vessel.status === 'at_port' ? '#3b82f6' : '#f59e0b',
            };
        });

        globeInstance.current
            .customLayerData(vesselData)
            .customThreeObject((d: any) => {
                const THREE = require('three');
                const geometry = new THREE.SphereGeometry(d.size, 16, 16);
                const material = new THREE.MeshBasicMaterial({
                    color: d.color,
                    transparent: true,
                    opacity: 0.9,
                });
                const mesh = new THREE.Mesh(geometry, material);

                // Add glow effect
                const glowGeometry = new THREE.SphereGeometry(d.size * 1.5, 16, 16);
                const glowMaterial = new THREE.MeshBasicMaterial({
                    color: d.color,
                    transparent: true,
                    opacity: 0.3,
                });
                const glow = new THREE.Mesh(glowGeometry, glowMaterial);
                mesh.add(glow);

                // Add pulsing animation
                const pulse = new THREE.SphereGeometry(d.size * 2, 16, 16);
                const pulseMaterial = new THREE.MeshBasicMaterial({
                    color: d.color,
                    transparent: true,
                    opacity: 0.15,
                });
                const pulseRing = new THREE.Mesh(pulse, pulseMaterial);
                mesh.add(pulseRing);

                return mesh;
            })
            .customThreeObjectUpdate((obj: any, d: any) => {
                const coords = globeInstance.current.getCoords(d.lat, d.lng, 0.02);
                obj.position.set(coords.x, coords.y, coords.z);
            })
            .onCustomLayerClick((vessel: any) => {
                if (vessel && !isTransitioning) {
                    handleVesselClick(vessel);
                }
            })
            .onCustomLayerHover((vessel: any) => {
                setHoveredVessel(vessel);
                if (globeEl.current) {
                    globeEl.current.style.cursor = vessel ? 'pointer' : 'grab';
                }
            });
    }, [vessels, selectedVessel, mounted, Globe, isTransitioning]);

    // Handle vessel click - zoom then transition to cinematic view
    const handleVesselClick = useCallback((vessel: VesselData) => {
        if (!globeInstance.current) return;

        setIsTransitioning(true);
        setCinematicVessel(vessel);
        onVesselSelect?.(vessel);

        // Stop auto-rotation
        globeInstance.current.controls().autoRotate = false;

        // Zoom into the vessel location
        globeInstance.current.pointOfView(
            { lat: vessel.lat, lng: vessel.lng, altitude: 0.3 },
            1500 // 1.5 second zoom animation
        );

        // After zoom completes, show cinematic view
        setTimeout(() => {
            setShowCinematic(true);
            setIsTransitioning(false);
        }, 1500);
    }, [onVesselSelect]);

    // Handle closing cinematic view
    const handleCloseCinematic = useCallback(() => {
        setShowCinematic(false);

        // Zoom back out after a brief delay
        setTimeout(() => {
            if (globeInstance.current) {
                globeInstance.current.controls().autoRotate = true;
                globeInstance.current.pointOfView(
                    { lat: 25, lng: 180, altitude: 2.5 },
                    1500
                );
            }
            setCinematicVessel(null);
        }, 500);
    }, []);

    // Handle resize
    useEffect(() => {
        if (!globeInstance.current || !globeEl.current) return;

        const handleResize = () => {
            if (globeEl.current && globeInstance.current) {
                globeInstance.current
                    .width(globeEl.current.clientWidth)
                    .height(parseInt(height));
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [height, mounted]);

    if (!mounted) {
        return (
            <div
                style={{ height }}
                className="bg-zinc-900 rounded-2xl flex items-center justify-center"
            >
                <div className="text-center">
                    <div className="animate-spin text-4xl mb-4">🌍</div>
                    <p className="text-zinc-400">Loading 3D Globe...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="relative rounded-2xl overflow-hidden border border-zinc-800 bg-black" style={{ height }}>
            {/* Globe */}
            <div className={`transition-opacity duration-500 ${showCinematic ? 'opacity-0' : 'opacity-100'}`}>
                <div ref={globeEl} style={{ height }} />
            </div>

            {/* Hover tooltip */}
            {hoveredVessel && !isTransitioning && !showCinematic && (
                <div className="absolute top-4 left-4 bg-zinc-900/90 backdrop-blur rounded-lg p-3 text-sm z-10 border border-zinc-700">
                    <p className="font-semibold text-white">🚢 {hoveredVessel.name}</p>
                    <p className="text-zinc-400">{hoveredVessel.destination}</p>
                    <p className="text-xs text-zinc-500 mt-1">Click to view details</p>
                </div>
            )}

            {/* Transitioning overlay */}
            {isTransitioning && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm z-20">
                    <div className="text-center">
                        <div className="animate-pulse text-4xl mb-2">🚢</div>
                        <p className="text-cyan-400 text-sm">Engaging vessel view...</p>
                    </div>
                </div>
            )}

            {/* Legend - only show when not in cinematic mode */}
            {!showCinematic && (
                <div className="absolute bottom-4 left-4 bg-zinc-900/90 backdrop-blur rounded-lg p-3 text-sm z-10 border border-zinc-700">
                    <p className="font-semibold text-white mb-2">🌍 3D Globe View</p>
                    <div className="space-y-1 text-xs">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-cyan-400" />
                            <span className="text-zinc-400">Taiwan Ports</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-violet-500" />
                            <span className="text-zinc-400">US Ports</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-emerald-500" />
                            <span className="text-zinc-400">Underway</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-sky-500" />
                            <span className="text-zinc-400">At Port</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Controls hint */}
            {!showCinematic && (
                <div className="absolute bottom-4 right-4 bg-zinc-900/90 backdrop-blur rounded-lg p-2 text-xs z-10 border border-zinc-700">
                    <p className="text-zinc-400">🖱️ Drag to rotate • Scroll to zoom</p>
                </div>
            )}

            {/* Cinematic Vessel View - positioned within container */}
            {cinematicVessel && (
                <VesselCinematicView
                    vessel={cinematicVessel}
                    onClose={handleCloseCinematic}
                    isVisible={showCinematic}
                    containerHeight={height}
                />
            )}
        </div>
    );
}
