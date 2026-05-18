"use client";

/**
 * app/symptom/page.tsx — Symptom Checker page.
 *
 * Phase 3: Safe, structured symptom triage powered by SymptomAgent.
 * Uses the SymptomFlow component for the interactive MCQ flow.
 *
 * Features:
 * - Clear safety disclaimers above the fold
 * - Language selection
 * - How-it-works explainer section
 * - Recent sessions history (future enhancement placeholder)
 */

import { useEffect, useState } from "react";
import GlassCard from "@/components/GlassCard";
import SymptomFlow from "@/components/SymptomFlow";
import { getUser } from "@/lib/auth";
import { useRouter } from "next/navigation";

const HOW_IT_WORKS = [
    { icon: "📝", title: "Describe symptoms", desc: "Tell us what you're experiencing in natural language" },
    { icon: "❓", title: "Answer questions", desc: "Up to 6 targeted questions to narrow down your situation" },
    { icon: "💊", title: "Get suggestions", desc: "OTC medicine recommendations or doctor referral advice" },
    { icon: "🛒", title: "Order directly", desc: "Add suggested OTC medicines to your cart instantly" },
];

const LANGUAGE_OPTIONS = [
    { code: "en", label: "English" },
    { code: "hi", label: "हिंदी" },
    { code: "mr", label: "मराठी" },
];

export default function SymptomPage() {
    const router = useRouter();
    const [user, setUser] = useState<{ id: number } | null>(null);
    const [language, setLanguage] = useState("en");

    useEffect(() => {
        const u = getUser();
        if (!u) { router.push("/login"); return; }
        setUser(u);
        const saved = localStorage.getItem("preferred_language");
        if (saved) setLanguage(saved);
    }, [router]);

    if (!user) return null;

    return (
        <div className="min-h-screen">
            <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
                {/* Header */}
                <div>
                    <h1 className="text-3xl font-bold text-[var(--text-color)]">🩺 Symptom Checker</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">AI-guided triage — get OTC recommendations or doctor referral</p>
                </div>

                {/* Safety notice */}
                <GlassCard hover={false} className="border-amber-500/30 bg-amber-500/5">
                    <div className="flex gap-3 items-start">
                        <span className="text-2xl">⚠️</span>
                        <div>
                            <p className="text-amber-300 font-semibold text-sm">Important Health Disclaimer</p>
                            <p className="text-amber-200/70 text-xs mt-1 leading-relaxed">
                                This tool is NOT a substitute for professional medical advice, diagnosis, or treatment.
                                Always consult a licensed healthcare professional for medical concerns.
                                If you have a medical emergency, call <strong>112</strong> immediately.
                            </p>
                        </div>
                    </div>
                </GlassCard>

                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Main checker */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Language selector */}
                        <GlassCard hover={false} padding="sm">
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-slate-600 dark:text-slate-400">Language:</span>
                                {LANGUAGE_OPTIONS.map((l) => (
                                    <button
                                        key={l.code}
                                        onClick={() => { setLanguage(l.code); localStorage.setItem("preferred_language", l.code); }}
                                        aria-pressed={language === l.code}
                                        className={`text-xs px-3 py-1 rounded-lg border transition-all ${language === l.code
                                                ? "border-indigo-500/50 bg-indigo-500/10 text-indigo-300"
                                                : "border-black/10 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:text-[var(--text-color)]"
                                            }`}
                                    >
                                        {l.label}
                                    </button>
                                ))}
                            </div>
                        </GlassCard>

                        <GlassCard hover={false}>
                            <SymptomFlow userId={user.id} language={language} />
                        </GlassCard>
                    </div>

                    {/* How it works */}
                    <div className="space-y-3">
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider">How it works</p>
                        {HOW_IT_WORKS.map((step, i) => (
                            <GlassCard key={i} hover={false} padding="sm" className="flex gap-3 items-start">
                                <span className="text-xl">{step.icon}</span>
                                <div>
                                    <p className="text-[var(--text-color)] text-sm font-medium">{step.title}</p>
                                    <p className="text-slate-600 dark:text-slate-400 text-xs mt-0.5">{step.desc}</p>
                                </div>
                            </GlassCard>
                        ))}

                        <GlassCard hover={false} padding="sm" className="border-red-500/20 bg-red-500/5">
                            <p className="text-xs text-slate-600 dark:text-slate-400 font-medium mb-1">🚨 Emergency?</p>
                            <p className="text-xs text-red-300">
                                Chest pain, difficulty breathing, or loss of consciousness?
                            </p>
                            <a href="tel:112" className="text-red-400 text-xs font-bold mt-1 block hover:text-red-300">
                                Call 112 immediately →
                            </a>
                        </GlassCard>
                    </div>
                </div>
            </div>
        </div>
    );
}
