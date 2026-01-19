'use client';

import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface VesselData {
    id: string;
    name: string;
    status: string;
    destination: string;
    speed: number;
    heading: number;
    eta?: string;
    imo?: string;
}

interface VesselDetailViewProps {
    vessel: VesselData;
    onClose: () => void;
    isVisible: boolean;
}

export function VesselDetailView({ vessel, onClose, isVisible }: VesselDetailViewProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
    const sceneRef = useRef<THREE.Scene | null>(null);
    const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
    const shipRef = useRef<THREE.Group | null>(null);
    const animationRef = useRef<number>(0);
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (!containerRef.current || !isVisible) return;

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a1628);
        scene.fog = new THREE.Fog(0x0a1628, 100, 700);
        sceneRef.current = scene;

        // Camera
        const camera = new THREE.PerspectiveCamera(
            60,
            containerRef.current.clientWidth / containerRef.current.clientHeight,
            0.1,
            1000
        );
        camera.position.set(80, 40, 100);
        camera.lookAt(0, 0, 0);
        cameraRef.current = camera;

        // Renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 0.8;
        containerRef.current.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffaa55, 1.5);
        sunLight.position.set(100, 50, -100);
        sunLight.castShadow = true;
        scene.add(sunLight);

        const fillLight = new THREE.DirectionalLight(0x4488ff, 0.3);
        fillLight.position.set(-50, 30, 50);
        scene.add(fillLight);

        // Create ocean
        const oceanGeometry = new THREE.PlaneGeometry(2000, 2000, 128, 128);
        const oceanMaterial = new THREE.MeshStandardMaterial({
            color: 0x0066aa,
            metalness: 0.1,
            roughness: 0.3,
            transparent: true,
            opacity: 0.9,
        });
        const ocean = new THREE.Mesh(oceanGeometry, oceanMaterial);
        ocean.rotation.x = -Math.PI / 2;
        ocean.position.y = -5;
        scene.add(ocean);

        // Create ship
        const ship = createContainerShip();
        ship.position.y = 0;
        ship.rotation.y = Math.PI / 4;
        scene.add(ship);
        shipRef.current = ship;

        // Create wake effect
        const wakeGeometry = new THREE.PlaneGeometry(150, 40, 32, 8);
        const wakeMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide,
        });
        const wake = new THREE.Mesh(wakeGeometry, wakeMaterial);
        wake.rotation.x = -Math.PI / 2;
        wake.position.set(-60, -4, 0);
        ship.add(wake);

        // Animation
        let time = 0;
        const animate = () => {
            animationRef.current = requestAnimationFrame(animate);
            time += 0.01;

            // Ship bobbing
            if (shipRef.current) {
                shipRef.current.position.y = Math.sin(time) * 1;
                shipRef.current.rotation.z = Math.sin(time * 0.5) * 0.02;
                shipRef.current.rotation.x = Math.sin(time * 0.3) * 0.01;
            }

            // Ocean waves
            const positions = oceanGeometry.attributes.position;
            for (let i = 0; i < positions.count; i++) {
                const x = positions.getX(i);
                const z = positions.getZ(i);
                const y = Math.sin(x * 0.02 + time * 2) * 2 + Math.sin(z * 0.03 + time * 1.5) * 1.5;
                positions.setY(i, y);
            }
            positions.needsUpdate = true;

            // Slow camera orbit
            camera.position.x = Math.cos(time * 0.1) * 120;
            camera.position.z = Math.sin(time * 0.1) * 120;
            camera.lookAt(0, 10, 0);

            renderer.render(scene, camera);
        };

        setIsLoaded(true);
        animate();

        // Handle resize
        const handleResize = () => {
            if (!containerRef.current) return;
            camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            cancelAnimationFrame(animationRef.current);
            window.removeEventListener('resize', handleResize);
            if (containerRef.current && renderer.domElement) {
                containerRef.current.removeChild(renderer.domElement);
            }
            renderer.dispose();
        };
    }, [isVisible]);

    // Create a procedural container ship
    function createContainerShip(): THREE.Group {
        const ship = new THREE.Group();

        // Hull
        const hullShape = new THREE.Shape();
        hullShape.moveTo(-40, 0);
        hullShape.lineTo(-35, -8);
        hullShape.lineTo(35, -8);
        hullShape.lineTo(45, 0);
        hullShape.lineTo(45, 5);
        hullShape.lineTo(-40, 5);
        hullShape.closePath();

        const hullGeometry = new THREE.ExtrudeGeometry(hullShape, {
            depth: 20,
            bevelEnabled: false,
        });
        const hullMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a3a5c,
            metalness: 0.3,
            roughness: 0.7,
        });
        const hull = new THREE.Mesh(hullGeometry, hullMaterial);
        hull.rotation.x = Math.PI / 2;
        hull.position.set(0, 0, -10);
        ship.add(hull);

        // Deck
        const deckGeometry = new THREE.BoxGeometry(80, 2, 18);
        const deckMaterial = new THREE.MeshStandardMaterial({
            color: 0x2a4a6c,
            metalness: 0.2,
            roughness: 0.8,
        });
        const deck = new THREE.Mesh(deckGeometry, deckMaterial);
        deck.position.set(0, 6, 0);
        ship.add(deck);

        // Containers (colorful stacks)
        const containerColors = [0xe53935, 0x1e88e5, 0x43a047, 0xfdd835, 0x8e24aa, 0xff6f00];
        for (let row = 0; row < 8; row++) {
            for (let stack = 0; stack < 3; stack++) {
                for (let col = 0; col < 2; col++) {
                    const containerGeometry = new THREE.BoxGeometry(8, 5, 6);
                    const color = containerColors[Math.floor(Math.random() * containerColors.length)];
                    const containerMaterial = new THREE.MeshStandardMaterial({
                        color,
                        metalness: 0.4,
                        roughness: 0.6,
                    });
                    const container = new THREE.Mesh(containerGeometry, containerMaterial);
                    container.position.set(
                        -28 + row * 8,
                        8 + stack * 5.5,
                        -4 + col * 8
                    );
                    ship.add(container);
                }
            }
        }

        // Bridge (command tower)
        const bridgeGeometry = new THREE.BoxGeometry(12, 20, 14);
        const bridgeMaterial = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            metalness: 0.5,
            roughness: 0.3,
        });
        const bridge = new THREE.Mesh(bridgeGeometry, bridgeMaterial);
        bridge.position.set(35, 17, 0);
        ship.add(bridge);

        // Bridge windows
        const windowGeometry = new THREE.BoxGeometry(0.5, 4, 12);
        const windowMaterial = new THREE.MeshStandardMaterial({
            color: 0x0088ff,
            emissive: 0x0044aa,
            emissiveIntensity: 0.5,
        });
        const windows = new THREE.Mesh(windowGeometry, windowMaterial);
        windows.position.set(41, 22, 0);
        ship.add(windows);

        // Funnel
        const funnelGeometry = new THREE.CylinderGeometry(2, 3, 12, 16);
        const funnelMaterial = new THREE.MeshStandardMaterial({
            color: 0xff4444,
            metalness: 0.3,
            roughness: 0.5,
        });
        const funnel = new THREE.Mesh(funnelGeometry, funnelMaterial);
        funnel.position.set(30, 32, 0);
        ship.add(funnel);

        return ship;
    }

    // Calculate ETA display
    const getETADisplay = () => {
        if (!vessel.eta) return 'Calculating...';
        const eta = new Date(vessel.eta);
        const now = new Date();
        const diff = eta.getTime() - now.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        return `${days} DAYS ${hours} HRS`;
    };

    // Calculate journey progress (simulated)
    const getProgress = () => {
        return Math.floor(Math.random() * 30) + 45; // 45-75%
    };

    const progress = getProgress();

    if (!isVisible) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm animate-fadeIn">
            {/* 3D Scene Container */}
            <div ref={containerRef} className="absolute inset-0" />

            {/* Loading Overlay */}
            {!isLoaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                        <div className="animate-spin text-6xl mb-4">🚢</div>
                        <p className="text-cyan-400 text-xl">Loading vessel view...</p>
                    </div>
                </div>
            )}

            {/* Floating HUD Elements */}
            {isLoaded && (
                <>
                    {/* Vessel Name - Top Center */}
                    <div className="absolute top-8 left-1/2 -translate-x-1/2 text-center">
                        <div className="px-8 py-4 bg-cyan-500/10 border border-cyan-500/50 rounded-lg backdrop-blur-sm">
                            <h1 className="text-4xl font-bold text-cyan-400 tracking-wider" style={{ textShadow: '0 0 20px rgba(0,255,255,0.5)' }}>
                                {vessel.name}
                            </h1>
                            {vessel.imo && (
                                <p className="text-cyan-300/70 text-sm mt-1">IMO: {vessel.imo}</p>
                            )}
                        </div>
                    </div>

                    {/* Speed Gauge - Top Left */}
                    <div className="absolute top-32 left-8">
                        <div className="w-32 h-32 rounded-full bg-black/50 border-2 border-cyan-500/50 flex flex-col items-center justify-center backdrop-blur-sm">
                            <span className="text-4xl font-bold text-cyan-400" style={{ textShadow: '0 0 10px rgba(0,255,255,0.5)' }}>
                                {vessel.speed}
                            </span>
                            <span className="text-cyan-300/70 text-sm">KTS</span>
                        </div>
                    </div>

                    {/* Heading Compass - Top Right */}
                    <div className="absolute top-32 right-8">
                        <div className="w-32 h-32 rounded-full bg-black/50 border-2 border-cyan-500/50 flex flex-col items-center justify-center backdrop-blur-sm relative">
                            <div
                                className="absolute w-16 h-16"
                                style={{ transform: `rotate(${vessel.heading}deg)` }}
                            >
                                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[8px] border-r-[8px] border-b-[16px] border-transparent border-b-cyan-400" />
                            </div>
                            <span className="text-lg font-bold text-cyan-400 mt-8">
                                {vessel.heading}°
                            </span>
                            <span className="text-cyan-300/70 text-xs">HEADING</span>
                        </div>
                    </div>

                    {/* Destination - Left Middle */}
                    <div className="absolute left-8 top-1/2 -translate-y-1/2">
                        <div className="px-6 py-4 bg-black/50 border border-cyan-500/50 rounded-lg backdrop-blur-sm">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                                    <span className="text-cyan-400">➤</span>
                                </div>
                                <div>
                                    <p className="text-cyan-300/70 text-xs">DESTINATION</p>
                                    <p className="text-cyan-400 font-bold text-lg">{vessel.destination}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ETA - Right Middle */}
                    <div className="absolute right-8 top-1/2 -translate-y-1/2">
                        <div className="px-6 py-4 bg-black/50 border border-cyan-500/50 rounded-lg backdrop-blur-sm">
                            <p className="text-cyan-300/70 text-xs">ETA</p>
                            <p className="text-cyan-400 font-bold text-xl">{getETADisplay()}</p>
                        </div>
                    </div>

                    {/* Progress Ring - Bottom Right */}
                    <div className="absolute bottom-24 right-8">
                        <div className="w-36 h-36 relative">
                            <svg className="w-full h-full -rotate-90">
                                <circle
                                    cx="72"
                                    cy="72"
                                    r="60"
                                    fill="transparent"
                                    stroke="rgba(0,255,255,0.2)"
                                    strokeWidth="8"
                                />
                                <circle
                                    cx="72"
                                    cy="72"
                                    r="60"
                                    fill="transparent"
                                    stroke="rgba(0,255,255,0.8)"
                                    strokeWidth="8"
                                    strokeDasharray={`${progress * 3.77} 377`}
                                    style={{ filter: 'drop-shadow(0 0 10px rgba(0,255,255,0.5))' }}
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-cyan-400">{progress}%</span>
                                <span className="text-cyan-300/70 text-xs">JOURNEY</span>
                            </div>
                        </div>
                    </div>

                    {/* Status Badge - Bottom Left */}
                    <div className="absolute bottom-24 left-8">
                        <div className={`px-6 py-3 rounded-full font-bold text-lg backdrop-blur-sm ${vessel.status === 'underway'
                                ? 'bg-emerald-500/20 border border-emerald-500/50 text-emerald-400'
                                : 'bg-sky-500/20 border border-sky-500/50 text-sky-400'
                            }`} style={{ textShadow: '0 0 10px currentColor' }}>
                            ● {vessel.status.toUpperCase()}
                        </div>
                    </div>

                    {/* Back Button */}
                    <button
                        onClick={onClose}
                        className="absolute bottom-8 left-1/2 -translate-x-1/2 px-8 py-3 bg-black/50 border border-cyan-500/50 rounded-full text-cyan-400 font-medium hover:bg-cyan-500/20 transition-all backdrop-blur-sm"
                        style={{ textShadow: '0 0 10px rgba(0,255,255,0.5)' }}
                    >
                        ← Back to Globe
                    </button>
                </>
            )}
        </div>
    );
}
