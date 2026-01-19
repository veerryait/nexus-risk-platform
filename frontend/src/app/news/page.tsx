'use client';

import { Header } from '@/components/Header';
import { NewsFeed } from '@/components/NewsFeed';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function NewsPage() {
    return (
        <ErrorBoundary>
            <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
                <Header />
                <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100">Supply Chain News</h1>
                        <p className="text-zinc-600 dark:text-zinc-400 mt-1">
                            Latest news affecting Taiwan → US semiconductor shipping
                        </p>
                    </div>

                    <NewsFeed maxItems={24} />

                    <footer className="mt-12 pt-8 border-t border-zinc-200 dark:border-zinc-800 text-center">
                        <p className="text-sm text-zinc-500 dark:text-zinc-400">
                            Sources: Reuters, Bloomberg, FreightWaves, Lloyd's List, 高雄港务局, 航运界, 中远海运
                        </p>
                    </footer>
                </main>
            </div>
        </ErrorBoundary>
    );
}
