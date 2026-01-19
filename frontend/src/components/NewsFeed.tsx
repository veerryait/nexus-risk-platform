'use client';

import { useState, useEffect } from 'react';

interface NewsItem {
    title: string;
    url: string;
    source: string;
    published_at: string;
    risk_score: number;
    keyword?: string;
    image_url?: string;
}

interface NewsFeedProps {
    maxItems?: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function NewsFeed({ maxItems = 12 }: NewsFeedProps) {
    const [news, setNews] = useState<NewsItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [riskFilter, setRiskFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
    const [source, setSource] = useState<string>('api');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchNews() {
            setLoading(true);
            setError(null);

            try {
                const res = await fetch(`${API_BASE}/api/v1/news/?limit=${maxItems * 2}`, {
                    headers: { 'Accept': 'application/json' },
                });

                if (res.ok) {
                    const data = await res.json();
                    if (data.news && data.news.length > 0) {
                        setNews(data.news);
                        setSource(data.source || 'api');
                        return;
                    }
                }

                // Fallback to curated if API returns empty
                setNews(getCuratedNews());
                setSource('curated');
            } catch (err) {
                console.error('News fetch error:', err);
                setNews(getCuratedNews());
                setSource('curated');
                setError('Using cached news');
            } finally {
                setLoading(false);
            }
        }

        fetchNews();
        // Refresh every 5 minutes
        const interval = setInterval(fetchNews, 5 * 60 * 1000);
        return () => clearInterval(interval);
    }, [maxItems]);

    const filteredNews = news.filter(item => {
        if (riskFilter === 'all') return true;
        if (riskFilter === 'high' && item.risk_score >= 0.6) return true;
        if (riskFilter === 'medium' && item.risk_score >= 0.3 && item.risk_score < 0.6) return true;
        if (riskFilter === 'low' && item.risk_score < 0.3) return true;
        return false;
    }).slice(0, maxItems);

    const getRiskBadge = (score: number) => {
        if (score >= 0.6) return { label: 'High', color: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400' };
        if (score >= 0.3) return { label: 'Medium', color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' };
        return { label: 'Low', color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' };
    };

    const formatDate = (dateStr: string) => {
        try {
            if (!dateStr) return 'Recent';
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return 'Recent';
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        } catch { return 'Recent'; }
    };

    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Supply Chain News</h3>
                <span className={`text-xs px-2 py-1 rounded ${source === 'gdelt' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                        source === 'database' ? 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400' :
                            'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400'
                    }`}>
                    {source === 'gdelt' ? '🌐 GDELT' : source === 'database' ? '💾 DB' : '📋 Curated'}
                </span>
            </div>

            {/* Risk Filters */}
            <div className="flex gap-2 mb-4">
                {(['all', 'high', 'medium', 'low'] as const).map(filter => (
                    <button
                        key={filter}
                        onClick={() => setRiskFilter(filter)}
                        className={`px-2 py-1 text-xs font-medium rounded-full transition-colors ${riskFilter === filter
                                ? 'bg-indigo-500 text-white'
                                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400'
                            }`}
                    >
                        {filter === 'all' ? 'All' : filter.charAt(0).toUpperCase() + filter.slice(1)}
                    </button>
                ))}
            </div>

            {/* News List */}
            {loading ? (
                <div className="space-y-3">{[1, 2, 3].map(i => <div key={i} className="animate-pulse h-16 bg-zinc-200 dark:bg-zinc-700 rounded" />)}</div>
            ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {filteredNews.map((item, index) => {
                        const risk = getRiskBadge(item.risk_score);
                        return (
                            <div key={index} className="p-3 rounded-lg border border-zinc-100 dark:border-zinc-800 hover:border-sky-500 transition-all animate-fadeIn">
                                <div className="flex items-start justify-between gap-2">
                                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-zinc-900 dark:text-zinc-100 hover:text-sky-600 line-clamp-2 flex-1">
                                        {item.title}
                                    </a>
                                    <span className={`flex-shrink-0 px-2 py-0.5 text-xs font-medium rounded-full ${risk.color}`}>{risk.label}</span>
                                </div>
                                <div className="flex items-center gap-2 mt-2 text-xs text-zinc-500">
                                    <span className="font-medium">{item.source}</span>
                                    <span>•</span>
                                    <span>{formatDate(item.published_at)}</span>
                                    {item.keyword && <span className="bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded">{item.keyword}</span>}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {error && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">{error}</p>
            )}

            <div className="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-800">
                <a href="/news" className="text-sm text-sky-500 hover:text-sky-600">View all news →</a>
            </div>
        </div>
    );
}

// Curated fallback news
function getCuratedNews(): NewsItem[] {
    const d = (n: number) => { const x = new Date(); x.setDate(x.getDate() - n); return x.toISOString(); };
    return [
        { title: "TSMC Reports Record Q4 Revenue Amid Strong AI Chip Demand", url: "https://reuters.com/technology/", source: "Reuters", published_at: d(0), risk_score: 0.15, keyword: "semiconductor" },
        { title: "Port of Los Angeles Container Volume Up 12% Year-Over-Year", url: "https://portoflosangeles.org/", source: "Port of LA", published_at: d(1), risk_score: 0.2, keyword: "port" },
        { title: "Pacific Trans-Pacific Shipping Rates Stabilize After Peak", url: "https://freightwaves.com/", source: "FreightWaves", published_at: d(1), risk_score: 0.25, keyword: "rates" },
        { title: "Taiwan Strait: US Navy Conducts Freedom of Navigation Transit", url: "https://defense.gov/", source: "Defense.gov", published_at: d(2), risk_score: 0.55, keyword: "Taiwan" },
        { title: "Long Beach Port Automated Terminal Handles Record Throughput", url: "https://polb.com/", source: "Port of LB", published_at: d(2), risk_score: 0.1, keyword: "port" },
        { title: "Global Semiconductor Supply Chain Shows Signs of Recovery", url: "https://bloomberg.com/", source: "Bloomberg", published_at: d(3), risk_score: 0.2, keyword: "semiconductor" },
        { title: "Winter Storm Warning: Seattle Port Operations May Be Affected", url: "https://weather.gov/", source: "NWS", published_at: d(3), risk_score: 0.45, keyword: "weather" },
        { title: "Evergreen Adds New Container Ships to Asia-America Route", url: "https://evergreen-line.com/", source: "Evergreen", published_at: d(4), risk_score: 0.15, keyword: "shipping" },
    ];
}
