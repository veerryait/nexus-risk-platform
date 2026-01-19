'use client';

import { useState, useRef, useEffect } from 'react';
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
    risk: { icon: '⚠️', color: 'text-rose-500', bg: 'bg-rose-500/10' },
    delay: { icon: '⏰', color: 'text-amber-500', bg: 'bg-amber-500/10' },
    weather: { icon: '🌊', color: 'text-sky-500', bg: 'bg-sky-500/10' },
    news: { icon: '📰', color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
    system: { icon: '⚙️', color: 'text-zinc-500', bg: 'bg-zinc-500/10' },
};

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

export function NotificationsDropdown() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [readIds, setReadIds] = useState<Set<string>>(new Set());
    const [loading, setLoading] = useState(true);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Load read notifications from localStorage
    useEffect(() => {
        setReadIds(getReadNotifications());
    }, []);

    // Fetch notifications from API
    const fetchNotifications = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/v1/notifications?limit=10');
            if (response.ok) {
                const data = await response.json();
                setNotifications(data.notifications || []);
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

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const unreadCount = notifications.filter(n => !readIds.has(n.id)).length;

    const markAsRead = (id: string) => {
        const newReadIds = new Set(readIds);
        newReadIds.add(id);
        setReadIds(newReadIds);
        saveReadNotifications(newReadIds);
    };

    const markAllAsRead = () => {
        const newReadIds = new Set(notifications.map(n => n.id));
        setReadIds(newReadIds);
        saveReadNotifications(newReadIds);
    };

    return (
        <div className="relative" ref={dropdownRef}>
            {/* Bell Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="relative p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                aria-label="Notifications"
            >
                <span className="text-xl">🔔</span>
                {unreadCount > 0 && (
                    <span className="absolute top-0.5 right-0.5 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] font-bold text-white bg-rose-500 rounded-full px-1">
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown Panel */}
            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-zinc-900 rounded-xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden animate-fadeIn z-50">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
                        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100">
                            Notifications
                            <span className="ml-2 text-xs font-normal text-emerald-500">● Live</span>
                        </h3>
                        {unreadCount > 0 && (
                            <button
                                onClick={markAllAsRead}
                                className="text-xs text-sky-500 hover:text-sky-600 font-medium transition-colors"
                            >
                                Mark all as read
                            </button>
                        )}
                    </div>

                    {/* Notifications List */}
                    <div className="max-h-80 overflow-y-auto">
                        {loading ? (
                            <div className="p-8 text-center text-zinc-500">
                                <div className="animate-spin text-2xl mb-2">⏳</div>
                                <p>Loading notifications...</p>
                            </div>
                        ) : notifications.length === 0 ? (
                            <div className="p-8 text-center text-zinc-500">
                                <span className="text-4xl block mb-2">🔕</span>
                                <p>No notifications</p>
                            </div>
                        ) : (
                            notifications.slice(0, 5).map(notification => {
                                const config = typeConfig[notification.type] || typeConfig.system;
                                const isRead = readIds.has(notification.id);

                                return (
                                    <button
                                        key={notification.id}
                                        onClick={() => markAsRead(notification.id)}
                                        className={`w-full text-left px-4 py-3 border-b border-zinc-100 dark:border-zinc-800 last:border-0 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors ${!isRead ? 'bg-sky-50/50 dark:bg-sky-900/10' : ''
                                            }`}
                                    >
                                        <div className="flex gap-3">
                                            <div className={`w-10 h-10 rounded-lg ${config.bg} flex items-center justify-center flex-shrink-0`}>
                                                <span className="text-lg">{config.icon}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-start justify-between gap-2">
                                                    <p className={`text-sm font-medium ${isRead ? 'text-zinc-600 dark:text-zinc-400' : 'text-zinc-900 dark:text-zinc-100'}`}>
                                                        {notification.title}
                                                    </p>
                                                    {!isRead && (
                                                        <span className="w-2 h-2 bg-sky-500 rounded-full flex-shrink-0 mt-1.5" />
                                                    )}
                                                </div>
                                                <p className="text-xs text-zinc-500 dark:text-zinc-500 line-clamp-2 mt-0.5">
                                                    {notification.message}
                                                </p>
                                                <p className="text-xs text-zinc-400 dark:text-zinc-600 mt-1">
                                                    {notification.time_ago}
                                                </p>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })
                        )}
                    </div>

                    {/* Footer */}
                    <div className="px-4 py-3 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/50">
                        <Link
                            href="/notifications"
                            onClick={() => setIsOpen(false)}
                            className="block w-full text-center text-sm font-medium text-sky-500 hover:text-sky-600 transition-colors"
                        >
                            View All Notifications →
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}
