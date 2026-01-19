'use client';

import { useState, useEffect, useCallback } from 'react';
import { Navigation, PageHeader } from '@/components/Navigation';
import { StatsGrid } from '@/components/StatsCard';
import dynamic from 'next/dynamic';
import Link from 'next/link';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const AIInsightsPanel = dynamic(() => import('@/components/AIInsights').then(m => m.AIInsightsPanel), {
  ssr: false,
  loading: () => <div className="h-48 bg-zinc-800 rounded-2xl animate-pulse"></div>
});
const NewsFeed = dynamic(() => import('@/components/NewsFeed').then(m => m.NewsFeed), {
  ssr: false,
  loading: () => <div className="h-48 bg-zinc-800 rounded-2xl animate-pulse"></div>
});

interface Route {
  id: string;
  origin: string;
  destination: string;
}

interface Stats {
  totalRoutes: number;
  activeShipments: number;
  avgOnTime: number;
  highRiskCount: number;
}

export default function OverviewPage() {
  const [stats, setStats] = useState<Stats>({
    totalRoutes: 0,
    activeShipments: 0,
    avgOnTime: 95,
    highRiskCount: 0
  });
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');

  const fetchData = useCallback(async () => {
    try {
      // Check API health
      const healthRes = await fetch(`${API_BASE}/health`);
      const health = await healthRes.json();
      setConnectionStatus(health.status === 'healthy' ? 'connected' : 'disconnected');

      // Fetch routes
      const routesRes = await fetch(`${API_BASE}/api/v1/routes/`);
      const routesData = await routesRes.json();
      const routes = routesData.routes || routesData || [];

      // Calculate stats
      let highRisk = 0;
      let totalDelay = 0;
      let onTime = 0;

      for (const route of routes.slice(0, 5)) {
        try {
          const predRes = await fetch(`${API_BASE}/api/v1/predict/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ route_id: route.id })
          });
          if (predRes.ok) {
            const pred = await predRes.json();
            if (pred.risk_level === 'high' || pred.risk_level === 'critical') highRisk++;
            totalDelay += pred.predicted_delay_days || pred.predicted_delay || 0;
            if ((pred.predicted_delay_days || pred.predicted_delay || 0) < 1) onTime++;
          }
        } catch { }
      }

      setStats({
        totalRoutes: routes.length,
        activeShipments: Math.min(routes.length, 5),
        avgOnTime: routes.length > 0 ? Math.round((onTime / Math.min(routes.length, 5)) * 100) : 95,
        highRiskCount: highRisk
      });
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setConnectionStatus('disconnected');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950">
      <Navigation />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <PageHeader
          icon="📊"
          title="Overview"
          subtitle="Real-time supply chain status and AI-powered insights"
        />

        {loading ? (
          <div className="animate-pulse space-y-6">
            <div className="h-32 bg-zinc-800 rounded-2xl"></div>
            <div className="h-48 bg-zinc-800 rounded-2xl"></div>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <section className="mb-8">
              <StatsGrid stats={stats} />
            </section>

            {/* AI Situation Analysis */}
            <section className="mb-8">
              <AIInsightsPanel />
            </section>

            {/* Quick Links */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <QuickLink
                  href="/routes"
                  icon="🚢"
                  title="Track Routes"
                  value={`${stats.totalRoutes} active`}
                />
                <QuickLink
                  href="/risk"
                  icon="🧠"
                  title="Risk Analysis"
                  value="GNN powered"
                />
                <QuickLink
                  href="/operations"
                  icon="⚙️"
                  title="Operations"
                  value="Ports & weather"
                />
                <QuickLink
                  href="/scenarios"
                  icon="🎯"
                  title="Scenarios"
                  value="What-if analysis"
                />
              </div>
            </section>

            {/* News Feed */}
            <section>
              <h2 className="text-lg font-semibold text-white mb-4">Supply Chain News</h2>
              <NewsFeed maxItems={6} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function QuickLink({ href, icon, title, value }: { href: string; icon: string; title: string; value: string }) {
  return (
    <Link
      href={href}
      className="glass-card p-4 rounded-xl hover:border-cyan-500/50 transition-all hover:scale-[1.02] group"
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl group-hover:scale-110 transition-transform">{icon}</span>
        <div>
          <p className="font-medium text-white">{title}</p>
          <p className="text-xs text-zinc-400">{value}</p>
        </div>
      </div>
    </Link>
  );
}
