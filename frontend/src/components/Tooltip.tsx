'use client';

import { useState, ReactNode } from 'react';

interface TooltipProps {
    content: string | ReactNode;
    children: ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
    delay?: number;
}

export function Tooltip({ content, children, position = 'top', delay = 200 }: TooltipProps) {
    const [visible, setVisible] = useState(false);
    const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);

    const show = () => {
        const id = setTimeout(() => setVisible(true), delay);
        setTimeoutId(id);
    };

    const hide = () => {
        if (timeoutId) clearTimeout(timeoutId);
        setVisible(false);
    };

    const positionClasses = {
        top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
        bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
        left: 'right-full top-1/2 -translate-y-1/2 mr-2',
        right: 'left-full top-1/2 -translate-y-1/2 ml-2',
    };

    const arrowClasses = {
        top: 'top-full left-1/2 -translate-x-1/2 border-t-zinc-800 dark:border-t-zinc-200 border-l-transparent border-r-transparent border-b-transparent',
        bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-zinc-800 dark:border-b-zinc-200 border-l-transparent border-r-transparent border-t-transparent',
        left: 'left-full top-1/2 -translate-y-1/2 border-l-zinc-800 dark:border-l-zinc-200 border-t-transparent border-b-transparent border-r-transparent',
        right: 'right-full top-1/2 -translate-y-1/2 border-r-zinc-800 dark:border-r-zinc-200 border-t-transparent border-b-transparent border-l-transparent',
    };

    return (
        <div className="relative inline-block" onMouseEnter={show} onMouseLeave={hide}>
            {children}
            {visible && (
                <div
                    className={`absolute z-50 px-3 py-2 text-sm font-medium text-white dark:text-zinc-900 bg-zinc-800 dark:bg-zinc-200 rounded-lg shadow-lg whitespace-nowrap animate-fadeIn ${positionClasses[position]}`}
                    role="tooltip"
                >
                    {content}
                    <div className={`absolute w-0 h-0 border-4 ${arrowClasses[position]}`} />
                </div>
            )}
        </div>
    );
}

// Info tooltip with icon
export function InfoTooltip({ content }: { content: string }) {
    return (
        <Tooltip content={content}>
            <span className="inline-flex items-center justify-center w-4 h-4 text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 cursor-help transition-colors">
                ⓘ
            </span>
        </Tooltip>
    );
}
