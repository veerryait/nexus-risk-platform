'use client';

import { Component, ReactNode } from 'react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('ErrorBoundary caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback || (
                <div className="bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-xl p-6 text-center">
                    <div className="text-3xl mb-3">⚠️</div>
                    <h3 className="text-lg font-semibold text-rose-700 dark:text-rose-400 mb-2">
                        Something went wrong
                    </h3>
                    <p className="text-sm text-rose-600 dark:text-rose-500 mb-4">
                        {this.state.error?.message || 'An unexpected error occurred'}
                    </p>
                    <button
                        onClick={() => this.setState({ hasError: false, error: undefined })}
                        className="px-4 py-2 bg-rose-600 text-white rounded-lg text-sm font-medium hover:bg-rose-700 transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            );
        }

        return this.props.children;
    }
}

// API Error display component
export function ApiError({ message, onRetry }: { message: string; onRetry?: () => void }) {
    return (
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 flex items-center gap-3">
            <span className="text-xl">⚡</span>
            <div className="flex-1">
                <p className="text-sm font-medium text-amber-700 dark:text-amber-400">Backend Unavailable</p>
                <p className="text-xs text-amber-600 dark:text-amber-500">{message}</p>
            </div>
            {onRetry && (
                <button
                    onClick={onRetry}
                    className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-medium hover:bg-amber-700"
                >
                    Retry
                </button>
            )}
        </div>
    );
}

// Loading skeleton components
export function LoadingSkeleton({ className = '' }: { className?: string }) {
    return <div className={`animate-pulse bg-zinc-200 dark:bg-zinc-700 rounded ${className}`} />;
}

export function CardSkeleton() {
    return (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 p-6">
            <LoadingSkeleton className="h-6 w-1/2 mb-4" />
            <LoadingSkeleton className="h-4 w-full mb-2" />
            <LoadingSkeleton className="h-4 w-3/4 mb-2" />
            <LoadingSkeleton className="h-4 w-1/2" />
        </div>
    );
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            {/* Stats skeleton */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                    <div key={i} className="bg-white dark:bg-zinc-900 rounded-xl p-4 border border-zinc-200 dark:border-zinc-800">
                        <LoadingSkeleton className="h-4 w-20 mb-2" />
                        <LoadingSkeleton className="h-8 w-16" />
                    </div>
                ))}
            </div>

            {/* Map skeleton */}
            <LoadingSkeleton className="h-80 w-full rounded-2xl" />

            {/* Cards skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => <CardSkeleton key={i} />)}
            </div>
        </div>
    );
}
