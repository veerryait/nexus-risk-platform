'use client';

import { useEffect, useState, useRef } from 'react';

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

interface VesselCinematicViewProps {
    vessel: VesselData;
    onClose: () => void;
    isVisible: boolean;
    containerHeight?: string;
}

export function VesselCinematicView({ vessel, onClose, isVisible, containerHeight = '600px' }: VesselCinematicViewProps) {
    const [showContent, setShowContent] = useState(false);
    const [journeyProgress] = useState(() => Math.floor(Math.random() * 30) + 50);
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        if (isVisible) {
            const timer = setTimeout(() => setShowContent(true), 500);
            if (videoRef.current) {
                videoRef.current.play().catch(() => { });
            }
            return () => clearTimeout(timer);
        } else {
            setShowContent(false);
            if (videoRef.current) {
                videoRef.current.pause();
            }
        }
    }, [isVisible]);

    const getETADisplay = () => {
        if (!vessel.eta) return '-- DAYS -- HRS';
        const eta = new Date(vessel.eta);
        const now = new Date();
        const diff = eta.getTime() - now.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        return `${days} DAYS ${hours} HRS`;
    };

    const getHeadingText = () => {
        const h = vessel.heading;
        if (h >= 337.5 || h < 22.5) return 'N';
        if (h >= 22.5 && h < 67.5) return 'NE';
        if (h >= 67.5 && h < 112.5) return 'E';
        if (h >= 112.5 && h < 157.5) return 'SE';
        if (h >= 157.5 && h < 202.5) return 'S';
        if (h >= 202.5 && h < 247.5) return 'SW';
        if (h >= 247.5 && h < 292.5) return 'W';
        return 'NW';
    };

    if (!isVisible) return null;

    return (
        <div
            className={`absolute inset-0 z-30 transition-opacity duration-1000 rounded-2xl overflow-hidden ${showContent ? 'opacity-100' : 'opacity-0'}`}
            style={{ height: containerHeight }}
        >
            {/* Video Background */}
            <div className="absolute inset-0 overflow-hidden">
                <video
                    ref={videoRef}
                    className="absolute w-full h-full object-cover"
                    src="/Aeriel-shot.mov"
                    autoPlay
                    loop
                    muted
                    playsInline
                />

                {/* Subtle overlay for better HUD readability */}
                <div className="absolute inset-0" style={{
                    background: 'radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.3) 100%)',
                }} />
            </div>

            {/* HUD Elements */}
            <div className={`absolute inset-0 transition-opacity duration-1000 delay-500 ${showContent ? 'opacity-100' : 'opacity-0'}`}>

                {/* Vessel Name */}
                <div className="absolute top-4 left-1/2 -translate-x-1/2">
                    <div className="px-6 py-3 backdrop-blur-md hud-panel">
                        <h1 className="text-xl md:text-2xl font-bold text-center tracking-[0.2em] hud-text">{vessel.name.toUpperCase()}</h1>
                        {vessel.imo && <p className="text-cyan-400/60 text-[10px] text-center mt-1 tracking-wider">IMO: {vessel.imo}</p>}
                    </div>
                </div>

                {/* Speed Gauge */}
                <div className="absolute top-16 left-4">
                    <div className="w-20 h-20 md:w-24 md:h-24 rounded-full flex flex-col items-center justify-center backdrop-blur-md hud-panel-round relative">
                        <svg className="absolute w-full h-full -rotate-90">
                            <circle cx="50%" cy="50%" r="40%" fill="transparent" stroke="rgba(0,212,255,0.2)" strokeWidth="3" />
                            <circle cx="50%" cy="50%" r="40%" fill="transparent" stroke="rgba(0,255,255,0.8)" strokeWidth="3"
                                strokeDasharray={`${(vessel.speed / 25) * 251} 251`} className="hud-glow" />
                        </svg>
                        <span className="text-xl md:text-2xl font-bold hud-text">{vessel.speed}</span>
                        <span className="text-cyan-400/70 text-[10px] tracking-wider">KTS</span>
                    </div>
                </div>

                {/* Compass */}
                <div className="absolute top-16 right-4">
                    <div className="w-20 h-20 md:w-24 md:h-24 rounded-full flex flex-col items-center justify-center backdrop-blur-md hud-panel-round relative">
                        {['N', 'E', 'S', 'W'].map((dir, i) => (
                            <span key={dir} className="absolute text-[10px] text-cyan-400/60" style={{
                                top: i === 0 ? '4px' : i === 2 ? 'auto' : '50%',
                                bottom: i === 2 ? '4px' : 'auto',
                                left: i === 3 ? '4px' : i === 1 ? 'auto' : '50%',
                                right: i === 1 ? '4px' : 'auto',
                                transform: i === 0 || i === 2 ? 'translateX(-50%)' : 'translateY(-50%)',
                            }}>{dir}</span>
                        ))}
                        <div className="absolute w-8 h-8" style={{ transform: `rotate(${vessel.heading}deg)` }}>
                            <div className="compass-needle" />
                        </div>
                        <span className="text-[10px] font-bold mt-5 hud-text">{vessel.heading}° {getHeadingText()}</span>
                    </div>
                </div>

                {/* Destination */}
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <div className="px-3 py-2 backdrop-blur-md hud-panel">
                        <div className="flex items-center gap-2">
                            <span className="text-base hud-text">➤</span>
                            <div>
                                <p className="text-cyan-400/60 text-[10px] tracking-wider">DESTINATION</p>
                                <p className="text-sm font-bold hud-text">{vessel.destination.toUpperCase()}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ETA */}
                <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    <div className="px-3 py-2 backdrop-blur-md hud-panel text-right">
                        <p className="text-cyan-400/60 text-[10px] tracking-wider">ETA</p>
                        <p className="text-sm font-bold hud-text">{getETADisplay()}</p>
                    </div>
                </div>

                {/* Journey Progress */}
                <div className="absolute bottom-4 right-4">
                    <div className="w-20 h-20 md:w-24 md:h-24 rounded-lg flex flex-col items-center justify-center backdrop-blur-md hud-panel relative">
                        <svg className="w-16 h-16 -rotate-90">
                            <circle cx="32" cy="32" r="26" fill="transparent" stroke="rgba(0,212,255,0.2)" strokeWidth="4" />
                            <circle cx="32" cy="32" r="26" fill="transparent" stroke="rgba(0,255,255,0.8)" strokeWidth="4"
                                strokeDasharray={`${journeyProgress * 1.63} 163`} className="hud-glow" />
                        </svg>
                        <div className="absolute flex flex-col items-center">
                            <span className="text-base font-bold hud-text">{journeyProgress}%</span>
                            <span className="text-cyan-400/60 text-[8px] tracking-wider">JOURNEY</span>
                        </div>
                    </div>
                </div>

                {/* Status Badge */}
                <div className="absolute bottom-4 left-4">
                    <div className={`px-3 py-1.5 rounded-full font-bold text-xs tracking-wider backdrop-blur-md ${vessel.status === 'underway' ? 'status-underway' : 'status-port'}`}>
                        ● {vessel.status.toUpperCase()}
                    </div>
                </div>

                {/* Back Button */}
                <button onClick={onClose} className="absolute bottom-4 left-1/2 -translate-x-1/2 px-5 py-2 rounded-full font-medium text-sm tracking-wider backdrop-blur-md hud-panel hud-text transition-all hover:scale-105">
                    ← BACK TO GLOBE
                </button>
            </div>

            <style jsx>{`
                .hud-panel {
                    background: linear-gradient(135deg, rgba(0,50,60,0.7) 0%, rgba(0,30,40,0.8) 100%);
                    border: 1px solid rgba(0,212,255,0.5);
                    border-radius: 8px;
                    box-shadow: 0 0 20px rgba(0,212,255,0.3);
                }
                .hud-panel-round {
                    background: linear-gradient(135deg, rgba(0,50,60,0.7) 0%, rgba(0,30,40,0.8) 100%);
                    border: 2px solid rgba(0,212,255,0.5);
                    box-shadow: 0 0 20px rgba(0,212,255,0.3);
                }
                .hud-text {
                    color: #00ffff;
                    text-shadow: 0 0 10px rgba(0,255,255,0.8);
                }
                .hud-glow {
                    filter: drop-shadow(0 0 6px rgba(0,255,255,0.8));
                }
                .compass-needle {
                    position: absolute;
                    top: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 0;
                    height: 0;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-bottom: 12px solid #00ffff;
                    filter: drop-shadow(0 0 5px rgba(0,255,255,0.8));
                }
                .status-underway {
                    color: #10b981;
                    background: linear-gradient(135deg, rgba(16,185,129,0.3) 0%, rgba(16,185,129,0.2) 100%);
                    border: 1px solid rgba(16,185,129,0.6);
                    box-shadow: 0 0 15px rgba(16,185,129,0.4);
                    text-shadow: 0 0 8px #10b981;
                }
                .status-port {
                    color: #00d4ff;
                    background: linear-gradient(135deg, rgba(0,212,255,0.3) 0%, rgba(0,212,255,0.2) 100%);
                    border: 1px solid rgba(0,212,255,0.6);
                    box-shadow: 0 0 15px rgba(0,212,255,0.4);
                    text-shadow: 0 0 8px #00d4ff;
                }
            `}</style>
        </div>
    );
}
