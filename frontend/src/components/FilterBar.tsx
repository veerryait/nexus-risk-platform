'use client';

import { Tooltip } from './Tooltip';

interface FilterBarProps {
    riskFilter: string;
    onRiskFilterChange: (filter: string) => void;
    sortBy: string;
    onSortChange: (sort: string) => void;
    onRefresh?: () => void;
    refreshing?: boolean;
}

export function FilterBar({ riskFilter, onRiskFilterChange, sortBy, onSortChange, onRefresh, refreshing }: FilterBarProps) {
    const riskOptions = [
        { value: 'all', label: 'All Routes', icon: '🔍' },
        { value: 'low', label: 'Low Risk', icon: '✓' },
        { value: 'medium', label: 'Medium', icon: '⚠' },
        { value: 'high', label: 'High Risk', icon: '!' },
        { value: 'critical', label: 'Critical', icon: '🚨' },
    ];

    const sortOptions = [
        { value: 'risk', label: 'Risk Level', icon: '⚡' },
        { value: 'delay', label: 'Predicted Delay', icon: '⏳' },
        { value: 'ontime', label: 'On-Time Rate', icon: '⏱️' },
        { value: 'distance', label: 'Distance', icon: '📏' },
        { value: 'transit', label: 'Transit Time', icon: '🚢' },
    ];

    return (
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 p-4 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-200 dark:border-zinc-800 animate-fadeIn">
            {/* Risk Filter */}
            <div className="flex items-center gap-2 flex-1">
                <Tooltip content="Filter routes by risk level">
                    <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400 whitespace-nowrap">
                        Risk:
                    </label>
                </Tooltip>
                <div className="flex gap-1 flex-wrap">
                    {riskOptions.map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => onRiskFilterChange(opt.value)}
                            className={`px-2 sm:px-3 py-1.5 rounded-lg text-xs sm:text-sm font-medium transition-all duration-200 ${riskFilter === opt.value
                                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/30'
                                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700'
                                }`}
                        >
                            <span className="sm:hidden">{opt.icon}</span>
                            <span className="hidden sm:inline">{opt.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Sort By */}
            <div className="flex items-center gap-2">
                <Tooltip content="Sort routes by criteria">
                    <label className="text-sm font-medium text-zinc-600 dark:text-zinc-400 whitespace-nowrap">
                        Sort:
                    </label>
                </Tooltip>
                <select
                    value={sortBy}
                    onChange={(e) => onSortChange(e.target.value)}
                    className="px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 text-sm text-zinc-900 dark:text-zinc-100 focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-shadow"
                >
                    {sortOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.icon} {opt.label}</option>
                    ))}
                </select>
            </div>

            {/* Refresh Button */}
            {onRefresh && (
                <Tooltip content="Refresh route data">
                    <button
                        onClick={onRefresh}
                        disabled={refreshing}
                        className="px-4 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-600 disabled:opacity-50 text-white text-sm font-medium transition-all duration-200 flex items-center gap-2 shadow-md shadow-sky-500/20 hover:shadow-lg hover:shadow-sky-500/30"
                    >
                        <span className={refreshing ? 'animate-spin' : ''}>↻</span>
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                </Tooltip>
            )}
        </div>
    );
}
