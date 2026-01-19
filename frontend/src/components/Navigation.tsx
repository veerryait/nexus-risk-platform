'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
    name: string;
    href: string;
    icon: string;
    description: string;
}

const navigation: NavItem[] = [
    { name: 'Overview', href: '/', icon: '📊', description: 'Dashboard summary' },
    { name: 'Routes', href: '/routes', icon: '🚢', description: 'Shipping routes & vessels' },
    { name: 'Risk Analysis', href: '/risk', icon: '🧠', description: 'GNN & predictions' },
    { name: 'Model', href: '/model-performance', icon: '📈', description: 'Accuracy tracking' },
    { name: 'Operations', href: '/operations', icon: '⚙️', description: 'Ports & weather' },
    { name: 'Scenarios', href: '/scenarios', icon: '🎯', description: 'What-if simulations' },
];

export function Navigation() {
    const pathname = usePathname();

    return (
        <nav className="bg-zinc-900/80 backdrop-blur-xl border-b border-zinc-800 sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-3">
                        <span className="text-2xl">⚡</span>
                        <span className="text-xl font-bold neon-text">NEXUS</span>
                    </Link>

                    {/* Navigation Links */}
                    <div className="flex items-center gap-1">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${isActive
                                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                                        : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                                        }`}
                                >
                                    <span>{item.icon}</span>
                                    <span>{item.name}</span>
                                </Link>
                            );
                        })}
                    </div>

                    {/* Status Indicator */}
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-zinc-800 rounded-full">
                            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                            <span className="text-xs text-zinc-400">Live</span>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
}

export function PageHeader({
    title,
    subtitle,
    icon
}: {
    title: string;
    subtitle: string;
    icon: string;
}) {
    return (
        <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">{icon}</span>
                <h1 className="text-3xl font-bold text-white">{title}</h1>
            </div>
            <p className="text-zinc-400 ml-12">{subtitle}</p>
        </div>
    );
}

export default Navigation;
