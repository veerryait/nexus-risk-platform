'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Notification {
    id: string;
    type: 'risk' | 'delay' | 'weather' | 'news' | 'system';
    title: string;
    message: string;
    details?: string;
    timestamp: string;
    time_ago: string;
    severity: 'high' | 'medium' | 'low';
    url?: string;
}

const typeConfig = {
    risk: { icon: '⚠️', label: 'Risk Alert', color: 'text-rose-500', bg: 'bg-rose-500/10', border: 'border-rose-500/20' },
    delay: { icon: '⏰', label: 'Delay', color: 'text-amber-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
    weather: { icon: '🌊', label: 'Weather', color: 'text-sky-500', bg: 'bg-sky-500/10', border: 'border-sky-500/20' },
    news: { icon: '📰', label: 'News', color: 'text-indigo-500', bg: 'bg-indigo-500/10', border: 'border-indigo-500/20' },
    system: { icon: '⚙️', label: 'System', color: 'text-zinc-500', bg: 'bg-zinc-500/10', border: 'border-zinc-500/20' },
};

type FilterType = 'all' | 'risk' | 'delay' | 'weather' | 'news' | 'system';

const STORAGE_KEY = 'nexus-read-notifications';

function getReadNotifications(): Set<string> {
    if (typeof window === 'undefined') return new Set();
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
        return new Set();
    }
}

function saveReadNotifications(ids: Set<string>) {
    if (typeof window === 'undefined') return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

export default function NotificationsPage() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [readIds, setReadIds] = useState<Set<string>>(new Set());
    const [filter, setFilter] = useState<FilterType>('all');
    const [expandedId, setExpandedId] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdated, setLastUpdated] = useState<string>('');

    // Load read notifications from localStorage
    useEffect(() => {
        setReadIds(getReadNotifications());
    }, []);

    // Fetch notifications from API
    const fetchNotifications = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/notifications?limit=50');
            if (response.ok) {
                const data = await response.json();
                setNotifications(data.notifications || []);
                setLastUpdated(new Date().toLocaleTimeString());
            }
        } catch (error) {
            console.error('Failed to fetch notifications:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();

        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchNotifications, 60000);
        return () => clearInterval(interval);
    }, []);

    const unreadCount = notifications.filter(n => !readIds.has(n.id)).length;

    const filteredNotifications = filter === 'all'
        ? notifications
        : notifications.filter(n => n.type === filter);

    const markAsRead = (id: string) => {
        const newReadIds = new Set(readIds);
        newReadIds.add(id);
        setReadIds(newReadIds);
        saveReadNotifications(newReadIds);
    };

    const markAllAsRead = () => {
        const newReadIds = new Set([...readIds, ...notifications.map(n => n.id)]);
        setReadIds(newReadIds);
        saveReadNotifications(newReadIds);
    };

    const clearReadState = () => {
        setReadIds(new Set());
        saveReadNotifications(new Set());
    };

    const filterButtons: { value: FilterType; label: string; icon: string }[] = [
        { value: 'all', label: 'All', icon: '📋' },
        { value: 'risk', label: 'Risk Alerts', icon: '⚠️' },
        { value: 'delay', label: 'Delays', icon: '⏰' },
        { value: 'weather', label: 'Weather', icon: '🌊' },
        { value: 'news', label: 'News', icon: '📰' },
        { value: 'system', label: 'System', icon: '⚙️' },
    ];

    return (
        <main className="min-h-screen bg-gradient-to-br from-zinc-50 via-zinc-100 to-zinc-50 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950 py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div>
                        <div className="flex items-center gap-2 text-sm text-zinc-500 mb-2">
                            <Link href="/" className="hover:text-sky-500 transition-colors">Dashboard</Link>
                            <span>/</span>
                            <span className="text-zinc-900 dark:text-zinc-100">Notifications</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">
                                Notifications
                            </h1>
                            <span className="text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-full">
                                ● Live
                            </span>
                        </div>
                        <p className="text-zinc-600 dark:text-zinc-400 mt-1">
                            {loading ? 'Loading...' : unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
                            {lastUpdated && <span className="text-xs text-zinc-400 ml-2">Updated {lastUpdated}</span>}
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={fetchNotifications}
                            className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg transition-colors"
                        >
                            🔄 Refresh
                        </button>
                        {unreadCount > 0 && (
                            <button
                                onClick={markAllAsRead}
                                className="px-4 py-2 text-sm font-medium text-sky-600 hover:text-sky-700 dark:text-sky-400 dark:hover:text-sky-300 bg-sky-50 dark:bg-sky-900/20 hover:bg-sky-100 dark:hover:bg-sky-900/30 rounded-lg transition-colors"
                            >
                                ✓ Mark all as read
                            </button>
                        )}
                        {readIds.size > 0 && (
                            <button
                                onClick={clearReadState}
                                className="px-4 py-2 text-sm font-medium text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 bg-rose-50 dark:bg-rose-900/20 hover:bg-rose-100 dark:hover:bg-rose-900/30 rounded-lg transition-colors"
                            >
                                🔄 Reset read state
                            </button>
                        )}
                    </div>
                </div>

                {/* Filter Tabs */}
                <div className="flex flex-wrap gap-2 mb-6">
                    {filterButtons.map(btn => (
                        <button
                            key={btn.value}
                            onClick={() => setFilter(btn.value)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${filter === btn.value
                                    ? 'bg-sky-500 text-white shadow-lg shadow-sky-500/25'
                                    : 'bg-white dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-700 border border-zinc-200 dark:border-zinc-700'
                                }`}
                        >
                            <span>{btn.icon}</span>
                            <span className="hidden sm:inline">{btn.label}</span>
                            {btn.value === 'all' && (
                                <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${filter === btn.value
                                        ? 'bg-white/20 text-white'
                                        : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-400'
                                    }`}>
                                    {notifications.length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Notifications List */}
                <div className="space-y-3">
                    {loading ? (
                        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-12 text-center">
                            <div className="animate-spin text-4xl mb-4">⏳</div>
                            <h3 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
                                Loading notifications...
                            </h3>
                            <p className="text-zinc-500 dark:text-zinc-400">
                                Fetching real-time data from the server
                            </p>
                        </div>
                    ) : filteredNotifications.length === 0 ? (
                        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-12 text-center">
                            <span className="text-6xl block mb-4">🔕</span>
                            <h3 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100 mb-2">
                                No notifications
                            </h3>
                            <p className="text-zinc-500 dark:text-zinc-400">
                                {filter === 'all'
                                    ? "You're all caught up! Check back later for updates."
                                    : `No ${filter} notifications at the moment.`}
                            </p>
                        </div>
                    ) : (
                        filteredNotifications.map(notification => {
                            const config = typeConfig[notification.type] || typeConfig.system;
                            const isExpanded = expandedId === notification.id;
                            const isRead = readIds.has(notification.id);

                            return (
                                <div
                                    key={notification.id}
                                    className={`bg-white dark:bg-zinc-900 rounded-xl border transition-all ${!isRead
                                            ? 'border-sky-500/30 shadow-lg shadow-sky-500/5'
                                            : 'border-zinc-200 dark:border-zinc-800'
                                        }`}
                                >
                                    <button
                                        onClick={() => {
                                            setExpandedId(isExpanded ? null : notification.id);
                                            if (!isRead) markAsRead(notification.id);
                                        }}
                                        className="w-full text-left p-4 sm:p-5"
                                    >
                                        <div className="flex gap-4">
                                            <div className={`w-12 h-12 rounded-xl ${config.bg} flex items-center justify-center flex-shrink-0`}>
                                                <span className="text-2xl">{config.icon}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div>
                                                        <div className="flex items-center gap-2 mb-1">
                                                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${config.bg} ${config.color}`}>
                                                                {config.label}
                                                            </span>
                                                            {!isRead && (
                                                                <span className="w-2 h-2 bg-sky-500 rounded-full" />
                                                            )}
                                                        </div>
                                                        <h3 className={`font-semibold ${isRead ? 'text-zinc-600 dark:text-zinc-400' : 'text-zinc-900 dark:text-zinc-100'}`}>
                                                            {notification.title}
                                                        </h3>
                                                    </div>
                                                    <span className="text-xs text-zinc-400 dark:text-zinc-500 whitespace-nowrap">
                                                        {notification.time_ago}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
                                                    {notification.message}
                                                </p>
                                            </div>
                                            <div className="flex-shrink-0 self-center">
                                                <svg
                                                    className={`w-5 h-5 text-zinc-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                                                    fill="none"
                                                    viewBox="0 0 24 24"
                                                    stroke="currentColor"
                                                >
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                </svg>
                                            </div>
                                        </div>
                                    </button>

                                    {/* Expanded Details */}
                                    {isExpanded && notification.details && (
                                        <div className="px-4 sm:px-5 pb-4 sm:pb-5 pt-0">
                                            <div className="ml-16 pl-4 border-l-2 border-zinc-200 dark:border-zinc-700">
                                                <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-3">
                                                    {notification.details}
                                                </p>
                                                {notification.url && (
                                                    <a
                                                        href={notification.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-xs text-sky-500 hover:text-sky-600 font-medium transition-colors"
                                                    >
                                                        Read full article →
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Back to Dashboard */}
                <div className="mt-8 text-center">
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-sky-500 transition-colors"
                    >
                        ← Back to Dashboard
                    </Link>
                </div>
            </div>
        </main>
    );
}
