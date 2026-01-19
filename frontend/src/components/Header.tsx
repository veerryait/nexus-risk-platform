'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from './ThemeProvider';
import { Tooltip } from './Tooltip';
import { NotificationsDropdown } from './NotificationsDropdown';

export function Header() {
    const [isConnected] = useState(true);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const pathname = usePathname();

    const navLinks = [
        { href: '/', label: 'Dashboard', icon: '📊' },
        { href: '/scenarios', label: 'Scenarios', icon: '🎮' },
        { href: '/routes', label: 'Routes', icon: '🛳️' },
        { href: '/vessels', label: 'Vessels', icon: '🚢' },
        { href: '/news', label: 'News', icon: '📰' },
        { href: '/contact', label: 'Contact', icon: '📧' },
    ];

    const isActive = (href: string) => {
        if (href === '/') return pathname === '/';
        return pathname.startsWith(href);
    };

    return (
        <header className="sticky top-0 z-50 glass border-b border-zinc-200 dark:border-zinc-800">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
                            <span className="text-white font-bold text-lg">N</span>
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">Nexus Risk</h1>
                            <p className="text-xs text-zinc-500 dark:text-zinc-400 hidden sm:block">Supply Chain Intelligence</p>
                        </div>
                    </div>

                    {/* Desktop Navigation */}
                    <nav className="hidden md:flex items-center gap-1">
                        {navLinks.map(link => (
                            <a
                                key={link.href}
                                href={link.href}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${isActive(link.href)
                                    ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                                    : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100'
                                    }`}
                            >
                                {link.label}
                            </a>
                        ))}
                    </nav>

                    {/* Right Section */}
                    <div className="flex items-center gap-2 sm:gap-4">
                        {/* Connection Status */}
                        <Tooltip content={isConnected ? 'Connected to backend API' : 'Backend offline - using cached data'} position="bottom">
                            <div className="flex items-center gap-2 px-2 sm:px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800">
                                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                                <span className="text-xs sm:text-sm font-medium text-zinc-600 dark:text-zinc-400">
                                    {isConnected ? 'Live' : 'Offline'}
                                </span>
                            </div>
                        </Tooltip>

                        {/* Theme Toggle */}
                        <ThemeToggle />

                        {/* Notifications */}
                        <NotificationsDropdown />

                        {/* Mobile Menu Button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="md:hidden p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
                        >
                            <svg className="w-6 h-6 text-zinc-600 dark:text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                {mobileMenuOpen ? (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                ) : (
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                                )}
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Mobile Menu */}
                {mobileMenuOpen && (
                    <div className="md:hidden py-4 border-t border-zinc-200 dark:border-zinc-800 animate-slideUp">
                        <nav className="flex flex-col gap-2">
                            {navLinks.map(link => (
                                <a
                                    key={link.href}
                                    href={link.href}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${isActive(link.href)
                                        ? 'bg-sky-100 dark:bg-sky-900/30 text-sky-600 dark:text-sky-400'
                                        : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800'
                                        }`}
                                >
                                    <span>{link.icon}</span>
                                    {link.label}
                                </a>
                            ))}
                        </nav>
                    </div>
                )}
            </div>
        </header>
    );
}
