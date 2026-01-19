'use client';

import { Route, Prediction } from '@/lib/api';
import { Tooltip } from './Tooltip';

interface RouteCardProps {
    route: Route;
    prediction?: Prediction;
    onSelect?: (route: Route) => void;
}

export function RouteCard({ route, prediction, onSelect }: RouteCardProps) {
    const riskLevel = prediction?.prediction.risk_level || 'unknown';
    const onTimeProb = prediction?.prediction.on_time_probability
        ? Math.round(prediction.prediction.on_time_probability * 100)
        : null;

    const riskConfig = {
        low: { border: 'border-emerald-500', bg: 'bg-gradient-to-br from-white to-emerald-50 dark:from-zinc-900 dark:to-emerald-950/20', badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400', icon: '✓' },
        medium: { border: 'border-amber-500', bg: 'bg-gradient-to-br from-white to-amber-50 dark:from-zinc-900 dark:to-amber-950/20', badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400', icon: '⚠' },
        high: { border: 'border-orange-500', bg: 'bg-gradient-to-br from-white to-orange-50 dark:from-zinc-900 dark:to-orange-950/20', badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-400', icon: '!' },
        critical: { border: 'border-rose-500', bg: 'bg-gradient-to-br from-white to-rose-50 dark:from-zinc-900 dark:to-rose-950/20', badge: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-400', icon: '🚨' },
        unknown: { border: 'border-zinc-300 dark:border-zinc-700', bg: 'bg-white dark:bg-zinc-900', badge: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400', icon: '?' },
    };

    const config = riskConfig[riskLevel as keyof typeof riskConfig] || riskConfig.unknown;

    return (
        <div
            className={`rounded-xl border-2 p-4 sm:p-5 cursor-pointer transition-all duration-300 card-hover animate-fadeIn ${config.border} ${config.bg}`}
            onClick={() => onSelect?.(route)}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-2 sm:gap-3">
                    <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-zinc-200 dark:bg-zinc-700 flex items-center justify-center shadow-inner">
                        <span className="text-base sm:text-lg">🚢</span>
                    </div>
                    <div>
                        <h3 className="font-semibold text-sm sm:text-base text-zinc-900 dark:text-zinc-100">{route.id}</h3>
                        <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400">{route.origin_name} → {route.destination_name}</p>
                    </div>
                </div>
                <Tooltip content={`Risk Level: ${riskLevel.toUpperCase()}`}>
                    <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-medium uppercase flex items-center gap-1 ${config.badge}`}>
                        <span>{config.icon}</span>
                        <span className="hidden sm:inline">{riskLevel}</span>
                    </span>
                </Tooltip>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-2 sm:gap-4 mt-3 sm:mt-4">
                <Tooltip content="Total nautical miles">
                    <div className="text-center sm:text-left">
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">Distance</p>
                        <p className="font-semibold text-xs sm:text-sm text-zinc-900 dark:text-zinc-100">{route.distance_nm.toLocaleString()} nm</p>
                    </div>
                </Tooltip>
                <Tooltip content="Typical transit duration">
                    <div className="text-center sm:text-left">
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">Transit Time</p>
                        <p className="font-semibold text-xs sm:text-sm text-zinc-900 dark:text-zinc-100">{route.typical_days} days</p>
                    </div>
                </Tooltip>
                <Tooltip content="Probability of on-time arrival">
                    <div className="text-center sm:text-left">
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">On-Time</p>
                        <p className={`font-semibold text-xs sm:text-sm ${onTimeProb && onTimeProb >= 90 ? 'text-emerald-600 dark:text-emerald-400' : onTimeProb && onTimeProb >= 70 ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400'}`}>
                            {onTimeProb !== null ? `${onTimeProb}%` : '—'}
                        </p>
                    </div>
                </Tooltip>
            </div>

            {/* Risk Factors */}
            {prediction?.factors && prediction.factors.length > 0 && (
                <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-zinc-200 dark:border-zinc-700">
                    <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-2">Risk Factors</p>
                    <div className="flex flex-wrap gap-1 sm:gap-2">
                        {prediction.factors.slice(0, 3).map((factor, i) => (
                            <Tooltip key={i} content={factor.description}>
                                <span className="text-xs px-2 py-1 rounded-full bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-300 dark:hover:bg-zinc-600 transition-colors cursor-help">
                                    {factor.factor}
                                </span>
                            </Tooltip>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

interface RouteGridProps {
    routes: Route[];
    predictions: Map<string, Prediction>;
    onRouteSelect?: (route: Route) => void;
}

export function RouteGrid({ routes, predictions, onRouteSelect }: RouteGridProps) {
    if (routes.length === 0) {
        return (
            <div className="text-center py-12 bg-zinc-100 dark:bg-zinc-800/50 rounded-xl">
                <span className="text-4xl mb-3 block">🚢</span>
                <p className="text-zinc-500 dark:text-zinc-400">No routes match your filter</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
            {routes.map((route, i) => (
                <div key={route.id} style={{ animationDelay: `${i * 50}ms` }}>
                    <RouteCard
                        route={route}
                        prediction={predictions.get(route.id)}
                        onSelect={onRouteSelect}
                    />
                </div>
            ))}
        </div>
    );
}
