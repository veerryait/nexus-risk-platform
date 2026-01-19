'use client';

import { Tooltip } from './Tooltip';

interface StatCardProps {
    title: string;
    value: string | number;
    subtitle?: string;
    trend?: 'up' | 'down' | 'neutral';
    color?: 'green' | 'yellow' | 'red' | 'blue';
    tooltip?: string;
}

export function StatCard({ title, value, subtitle, trend, color = 'blue', tooltip }: StatCardProps) {
    const colorClasses = {
        green: 'text-emerald-500 dark:text-emerald-400',
        yellow: 'text-amber-500 dark:text-amber-400',
        red: 'text-rose-500 dark:text-rose-400',
        blue: 'text-sky-500 dark:text-sky-400',
    };

    const bgClasses = {
        green: 'bg-gradient-to-br from-emerald-50 to-emerald-100/50 dark:from-emerald-900/20 dark:to-emerald-800/10',
        yellow: 'bg-gradient-to-br from-amber-50 to-amber-100/50 dark:from-amber-900/20 dark:to-amber-800/10',
        red: 'bg-gradient-to-br from-rose-50 to-rose-100/50 dark:from-rose-900/20 dark:to-rose-800/10',
        blue: 'bg-gradient-to-br from-sky-50 to-sky-100/50 dark:from-sky-900/20 dark:to-sky-800/10',
    };

    const iconBgClasses = {
        green: 'bg-emerald-100 dark:bg-emerald-900/30',
        yellow: 'bg-amber-100 dark:bg-amber-900/30',
        red: 'bg-rose-100 dark:bg-rose-900/30',
        blue: 'bg-sky-100 dark:bg-sky-900/30',
    };

    const icons = {
        green: '✓',
        yellow: '⚠',
        red: '!',
        blue: '📊',
    };

    const content = (
        <div className={`rounded-2xl border border-zinc-200 dark:border-zinc-800 p-4 sm:p-6 ${bgClasses[color]} card-hover animate-fadeIn`}>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs sm:text-sm font-medium text-zinc-500 dark:text-zinc-400">{title}</p>
                    <p className={`text-2xl sm:text-3xl font-bold mt-1 sm:mt-2 ${colorClasses[color]}`}>{value}</p>
                </div>
                <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-xl ${iconBgClasses[color]} flex items-center justify-center`}>
                    <span className="text-sm sm:text-lg">{icons[color]}</span>
                </div>
            </div>
            {subtitle && (
                <p className="text-xs sm:text-sm text-zinc-500 dark:text-zinc-400 mt-2 sm:mt-3 flex items-center gap-1">
                    {trend === 'up' && <span className="text-emerald-500 font-medium">↑</span>}
                    {trend === 'down' && <span className="text-rose-500 font-medium">↓</span>}
                    {subtitle}
                </p>
            )}
        </div>
    );

    return tooltip ? <Tooltip content={tooltip}>{content}</Tooltip> : content;
}

interface StatsGridProps {
    stats: {
        totalRoutes: number;
        activeShipments: number;
        avgOnTime: number;
        highRiskCount: number;
    };
}

export function StatsGrid({ stats }: StatsGridProps) {
    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <StatCard
                title="Active Routes"
                value={stats.totalRoutes}
                subtitle="Taiwan to US West Coast"
                color="blue"
                tooltip="Number of monitored shipping routes"
            />
            <StatCard
                title="Active Shipments"
                value={stats.activeShipments}
                subtitle="Currently in transit"
                trend="up"
                color="green"
                tooltip="Vessels currently en route"
            />
            <StatCard
                title="On-Time Rate"
                value={`${stats.avgOnTime}%`}
                subtitle="Last 30 days"
                trend="up"
                color="green"
                tooltip="Percentage of on-time arrivals"
            />
            <StatCard
                title="High Risk Routes"
                value={stats.highRiskCount}
                subtitle="Require attention"
                color={stats.highRiskCount > 0 ? 'red' : 'green'}
                tooltip="Routes with elevated delay risk"
            />
        </div>
    );
}
