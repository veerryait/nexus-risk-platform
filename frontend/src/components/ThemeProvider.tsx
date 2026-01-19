'use client';

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
    theme: Theme;
    resolvedTheme: 'light' | 'dark';
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
    const [theme, setTheme] = useState<Theme>('system');
    const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');

    useEffect(() => {
        // Load saved theme
        const saved = localStorage.getItem('theme') as Theme | null;
        if (saved) setTheme(saved);
    }, []);

    useEffect(() => {
        // Resolve theme
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const resolved = theme === 'system' ? (systemDark ? 'dark' : 'light') : theme;
        setResolvedTheme(resolved);

        // Apply to document
        document.documentElement.classList.toggle('dark', resolved === 'dark');
        localStorage.setItem('theme', theme);

        // Listen for system changes
        const media = window.matchMedia('(prefers-color-scheme: dark)');
        const handler = (e: MediaQueryListEvent) => {
            if (theme === 'system') {
                setResolvedTheme(e.matches ? 'dark' : 'light');
                document.documentElement.classList.toggle('dark', e.matches);
            }
        };
        media.addEventListener('change', handler);
        return () => media.removeEventListener('change', handler);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) throw new Error('useTheme must be used within ThemeProvider');
    return context;
}

// Theme toggle button
export function ThemeToggle() {
    const { theme, setTheme } = useTheme();

    const themes: Theme[] = ['light', 'dark', 'system'];
    const icons = { light: '☀️', dark: '🌙', system: '💻' };

    const cycleTheme = () => {
        const idx = themes.indexOf(theme);
        setTheme(themes[(idx + 1) % themes.length]);
    };

    return (
        <button
            onClick={cycleTheme}
            className="p-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all duration-200 group"
            title={`Theme: ${theme}`}
        >
            <span className="text-lg group-hover:scale-110 transition-transform inline-block">
                {icons[theme]}
            </span>
        </button>
    );
}
