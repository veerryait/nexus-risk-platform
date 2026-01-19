'use client';

import { Header } from '@/components/Header';

export default function ContactPage() {
    return (
        <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
            <Header />

            <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                {/* Hero Section */}
                <div className="text-center mb-12">
                    <h1 className="text-4xl font-bold text-zinc-900 dark:text-zinc-100 mb-4">
                        Get in Touch
                    </h1>
                    <p className="text-zinc-600 dark:text-zinc-400 text-lg">
                        Have questions about Nexus Risk Platform? I&apos;d love to hear from you.
                    </p>
                </div>

                {/* Profile Card */}
                <div className="max-w-2xl mx-auto">
                    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden shadow-xl">
                        {/* Gradient Header */}
                        <div className="h-32 bg-gradient-to-br from-sky-500 via-indigo-500 to-purple-600" />

                        {/* Profile Content */}
                        <div className="px-8 pb-8 -mt-16">
                            {/* Avatar */}
                            <div className="w-32 h-32 rounded-2xl bg-gradient-to-br from-sky-400 to-indigo-600 flex items-center justify-center text-white text-5xl font-bold shadow-xl border-4 border-white dark:border-zinc-900 mb-6">
                                VR
                            </div>

                            {/* Name & Title */}
                            <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">
                                Veer Ryait
                            </h2>
                            <p className="text-sky-600 dark:text-sky-400 font-medium mb-6">
                                Data Scientist & Developer
                            </p>

                            {/* Bio */}
                            <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-xl p-6 mb-8">
                                <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed">
                                    Data Scientist and Developer specializing in real-time analytics, predictive modeling,
                                    and data visualization. Creator of Nexus Risk Platform - leveraging machine learning
                                    and big data to deliver actionable supply chain intelligence and risk insights.
                                </p>
                            </div>

                            {/* Contact Info */}
                            <div className="space-y-4">
                                <h3 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">
                                    Contact Information
                                </h3>

                                {/* Email */}
                                <a
                                    href="mailto:ryaitveersingh0@gmail.com"
                                    className="flex items-center gap-4 p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 hover:bg-sky-50 dark:hover:bg-sky-900/20 transition-colors group"
                                >
                                    <div className="w-12 h-12 rounded-xl bg-sky-100 dark:bg-sky-900/30 flex items-center justify-center text-sky-600 dark:text-sky-400 group-hover:scale-110 transition-transform">
                                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                        </svg>
                                    </div>
                                    <div>
                                        <p className="text-sm text-zinc-500 dark:text-zinc-400">Email</p>
                                        <p className="text-zinc-900 dark:text-zinc-100 font-medium">ryaitveersingh0@gmail.com</p>
                                    </div>
                                </a>
                            </div>

                            {/* Project Info */}
                            <div className="mt-8 pt-8 border-t border-zinc-200 dark:border-zinc-700">
                                <h3 className="text-sm font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider mb-4">
                                    About This Project
                                </h3>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 text-center">
                                        <p className="text-2xl font-bold text-sky-600 dark:text-sky-400">15+</p>
                                        <p className="text-sm text-zinc-500 dark:text-zinc-400">Active Vessels</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 text-center">
                                        <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">Real-time</p>
                                        <p className="text-sm text-zinc-500 dark:text-zinc-400">Data Updates</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 text-center">
                                        <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">3D</p>
                                        <p className="text-sm text-zinc-500 dark:text-zinc-400">Globe Tracking</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 text-center">
                                        <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">AI</p>
                                        <p className="text-sm text-zinc-500 dark:text-zinc-400">Risk Analytics</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer Note */}
                    <p className="text-center text-zinc-500 dark:text-zinc-400 text-sm mt-8">
                        Built with Next.js, Python, and ❤️
                    </p>
                </div>
            </main>
        </div>
    );
}
