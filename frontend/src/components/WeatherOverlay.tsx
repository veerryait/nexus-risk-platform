'use client';

import { useState } from 'react';
import { useWeather, WeatherSystem as WeatherSystemType, SeaCondition as SeaConditionType } from '@/lib/DataContext';

export type WeatherSystem = WeatherSystemType;
export type SeaCondition = SeaConditionType;

const getSystemIcon = (type: string) => {
    switch (type) {
        case 'typhoon': return '🌀';
        case 'storm': return '⛈️';
        case 'monsoon': return '🌧️';
        case 'fog': return '🌫️';
        case 'high_winds': return '💨';
        case 'rough_seas': return '🌊';
        default: return '🌡️';
    }
};

const getIntensityColor = (intensity: string) => {
    switch (intensity) {
        case 'severe': return { bg: 'bg-rose-500', text: 'text-rose-500', ring: 'ring-rose-500' };
        case 'high': return { bg: 'bg-orange-500', text: 'text-orange-500', ring: 'ring-orange-500' };
        case 'medium': return { bg: 'bg-amber-500', text: 'text-amber-500', ring: 'ring-amber-500' };
        default: return { bg: 'bg-emerald-500', text: 'text-emerald-500', ring: 'ring-emerald-500' };
    }
};

const getWarningBadge = (level: string) => {
    switch (level) {
        case 'emergency': return { bg: 'bg-rose-600', text: 'EMERGENCY' };
        case 'warning': return { bg: 'bg-orange-600', text: 'WARNING' };
        case 'watch': return { bg: 'bg-amber-600', text: 'WATCH' };
        default: return { bg: 'bg-blue-600', text: 'ADVISORY' };
    }
};

const getConditionColor = (condition: string) => {
    switch (condition) {
        case 'high': return 'text-rose-400';
        case 'very_rough': return 'text-orange-400';
        case 'rough': return 'text-amber-400';
        case 'moderate': return 'text-cyan-400';
        default: return 'text-emerald-400';
    }
};

interface WeatherOverlayProps {
    onWeatherSelect?: (weather: WeatherSystem) => void;
    showConditions?: boolean;
}

export function WeatherOverlay({ onWeatherSelect, showConditions = true }: WeatherOverlayProps) {
    // Use unified data from DataContext
    const { systems: weatherSystems, conditions: seaConditions, loading, error } = useWeather();

    const [selectedSystem, setSelectedSystem] = useState<WeatherSystem | null>(null);
    const [showSystems, setShowSystems] = useState(true);
    const [showSeaState, setShowSeaState] = useState(true);

    const activeWarnings = weatherSystems.filter(s => s.warning_level === 'warning' || s.warning_level === 'emergency');
    const totalSystems = weatherSystems.length;
    const avgWaveHeight = seaConditions.length > 0
        ? (seaConditions.reduce((a, c) => a + c.wave_height_m, 0) / seaConditions.length).toFixed(1)
        : '0.0';

    return (
        <div className="glass-card p-6 rounded-2xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h2 className="text-xl font-bold text-white font-futuristic flex items-center gap-2">
                        <span className="text-2xl">🌊</span> Weather Overlay
                    </h2>
                    <p className="text-sm text-zinc-400 mt-1">Storm systems, wind patterns & sea conditions</p>
                </div>

                {/* Toggle Buttons */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowSystems(!showSystems)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${showSystems ? 'bg-cyan-500 text-black' : 'bg-zinc-800 text-zinc-400'
                            }`}
                    >
                        🌀 Systems
                    </button>
                    <button
                        onClick={() => setShowSeaState(!showSeaState)}
                        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${showSeaState ? 'bg-cyan-500 text-black' : 'bg-zinc-800 text-zinc-400'
                            }`}
                    >
                        🌊 Sea State
                    </button>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-blue-400">{totalSystems}</p>
                    <p className="text-xs text-zinc-400">Active Systems</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-orange-400">{activeWarnings.length}</p>
                    <p className="text-xs text-zinc-400">Active Warnings</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-cyan-400">{avgWaveHeight}m</p>
                    <p className="text-xs text-zinc-400">Avg Wave Height</p>
                </div>
                <div className="bg-zinc-800/50 rounded-xl p-3 text-center">
                    <p className="text-2xl font-bold text-emerald-400">
                        {seaConditions.filter(c => c.condition === 'calm' || c.condition === 'moderate').length}
                    </p>
                    <p className="text-xs text-zinc-400">Clear Regions</p>
                </div>
            </div>

            {/* Weather Systems */}
            {showSystems && (
                <div className="mb-6">
                    <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                        <span>🌀</span> Active Weather Systems
                    </h3>
                    <div className="space-y-3">
                        {weatherSystems.map(system => {
                            const colors = getIntensityColor(system.intensity);
                            const badge = getWarningBadge(system.warning_level);

                            return (
                                <div
                                    key={system.id}
                                    onClick={() => {
                                        setSelectedSystem(selectedSystem?.id === system.id ? null : system);
                                        onWeatherSelect?.(system);
                                    }}
                                    className={`p-4 rounded-xl border cursor-pointer transition-all ${selectedSystem?.id === system.id
                                        ? `border-2 ${colors.ring.replace('ring', 'border')} shadow-lg`
                                        : 'border-zinc-700 hover:border-zinc-600'
                                        } bg-zinc-900/80`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <span className="text-3xl">{getSystemIcon(system.type)}</span>
                                            <div>
                                                <h4 className="font-bold text-white">{system.name}</h4>
                                                <p className="text-xs text-zinc-400">
                                                    {system.lat.toFixed(1)}°N, {system.lng.toFixed(1)}°{system.lng > 0 ? 'E' : 'W'}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2 py-1 text-xs font-bold rounded ${badge.bg} text-white`}>
                                            {badge.text}
                                        </span>
                                    </div>

                                    {/* Stats Row */}
                                    <div className="mt-3 grid grid-cols-4 gap-2 text-xs">
                                        <div className="bg-zinc-800/50 p-2 rounded text-center">
                                            <p className={`font-bold ${colors.text}`}>{system.wind_speed_knots} kts</p>
                                            <p className="text-zinc-500">Wind</p>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded text-center">
                                            <p className="font-bold text-blue-400">{system.wave_height_m}m</p>
                                            <p className="text-zinc-500">Waves</p>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded text-center">
                                            <p className="font-bold text-purple-400">{system.radius_nm} nm</p>
                                            <p className="text-zinc-500">Radius</p>
                                        </div>
                                        <div className="bg-zinc-800/50 p-2 rounded text-center">
                                            <p className="font-bold text-zinc-300">{system.direction}°</p>
                                            <p className="text-zinc-500">Heading</p>
                                        </div>
                                    </div>

                                    {/* Expanded Details */}
                                    {selectedSystem?.id === system.id && (
                                        <div className="mt-3 pt-3 border-t border-zinc-700 animate-fadeIn">
                                            <p className="text-sm text-zinc-300">{system.impact_description}</p>

                                            {system.forecast_path && (
                                                <div className="mt-3">
                                                    <p className="text-xs text-zinc-400 mb-2">Forecast Track:</p>
                                                    <div className="flex items-center gap-2 overflow-x-auto">
                                                        {system.forecast_path.map((point, idx) => (
                                                            <div key={idx} className="flex items-center">
                                                                <div className="px-2 py-1 bg-zinc-800 rounded text-xs">
                                                                    <p className="text-cyan-400">+{point.hours}h</p>
                                                                    <p className="text-zinc-500">{point.lat.toFixed(1)}°N</p>
                                                                </div>
                                                                {idx < system.forecast_path!.length - 1 && (
                                                                    <span className="text-zinc-600 mx-1">→</span>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Sea Conditions */}
            {showSeaState && showConditions && (
                <div>
                    <h3 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
                        <span>🌊</span> Sea Conditions by Region
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {seaConditions.map((condition, idx) => (
                            <div key={idx} className="p-3 bg-zinc-800/50 rounded-xl border border-zinc-700">
                                <h4 className="font-medium text-white text-sm">{condition.region}</h4>
                                <p className={`text-lg font-bold ${getConditionColor(condition.condition)}`}>
                                    {condition.condition.replace('_', ' ').toUpperCase()}
                                </p>
                                <div className="mt-2 space-y-1 text-xs text-zinc-400">
                                    <div className="flex justify-between">
                                        <span>Waves:</span>
                                        <span className="text-blue-400">{condition.wave_height_m}m</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Wind:</span>
                                        <span className="text-zinc-300">{condition.wind_speed_knots} kts @ {condition.wind_direction}°</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Visibility:</span>
                                        <span className={condition.visibility_nm < 5 ? 'text-amber-400' : 'text-emerald-400'}>
                                            {condition.visibility_nm} nm
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Legend */}
            <div className="mt-6 pt-4 border-t border-zinc-700">
                <p className="text-xs text-zinc-500 mb-2">Intensity Legend:</p>
                <div className="flex items-center gap-4 text-xs">
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                        <span className="text-zinc-400">Low</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-amber-500"></div>
                        <span className="text-zinc-400">Medium</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                        <span className="text-zinc-400">High</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full bg-rose-500"></div>
                        <span className="text-zinc-400">Severe</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
