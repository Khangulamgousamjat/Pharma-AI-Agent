"use client";

/**
 * components/SymptomFlow.tsx — MCQ-style symptom triage UI component.
 *
 * Phase 3: Renders the step-by-step symptom checking flow powered
 * by the SymptomAgent backend. Shows:
 *
 *   1. Initial symptom input form
 *   2. Sequential MCQ cards with progress bar
 *   3. Final recommendation (OTC / doctor / emergency)
 *      - OTC: shows suggested medicine cards with "Add to Cart" linking to chat
 *      - Doctor: show referral message + find-a-doctor encouragement
 *      - Emergency: large red banner with emergency number
 *
 * SAFETY: Disclaimer shown at every step. Escape button always visible.
 *
 * @param userId - Authenticated user ID
 * @param language - ISO language code for multilingual responses
 */

import { useState } from "react";
import Link from "next/link";
import GlassCard from "@/components/GlassCard";
import {
    startSymptomCheck,
    continueSymptomCheck,
    type SymptomCheckResponse,
    type SuggestedMedicine,
} from "@/lib/api";

interface SymptomFlowProps {
    userId: number;
    language?: string;
}

type FlowState = "idle" | "running" | "complete" | "stopped";

export default function SymptomFlow({ userId, language = "en" }: SymptomFlowProps) {
    const [state, setFlowState] = useState<FlowState>("idle");
    const [symptomInput, setSymptomInput] = useState("");
    const [response, setResponse] = useState<SymptomCheckResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [answerInput, setAnswerInput] = useState("");

    const DISCLAIMER =
        "⚠️ This is not medical advice. For serious concerns, always consult a licensed healthcare professional.";

    const handleStart = async () => {
        if (!symptomInput.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const result = await startSymptomCheck(userId, symptomInput.trim(), language);
            setResponse(result);
            setFlowState(result.is_complete ? "complete" : "running");
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to start check");
        } finally {
            setLoading(false);
        }
    };

    const handleAnswer = async (answer: string) => {
        if (!response?.session_id) return;
        setLoading(true);
        setError(null);
        try {
            const result = await continueSymptomCheck(response.session_id, answer);
            setResponse(result);
            setAnswerInput("");
            if (result.is_complete) setFlowState("complete");
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to submit answer");
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setFlowState("idle");
        setSymptomInput("");
        setResponse(null);
        setError(null);
        setAnswerInput("");
    };

    // ---------------------------------------------------------------------------
    // IDLE — Initial symptom input
    // ---------------------------------------------------------------------------
    if (state === "idle") {
        return (
            <div className="space-y-4">
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                    {DISCLAIMER}
                </div>
                <div className="space-y-3">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="symptom-input">
                        Describe your symptom(s)
                    </label>
                    <textarea
                        id="symptom-input"
                        value={symptomInput}
                        onChange={(e) => setSymptomInput(e.target.value)}
                        placeholder="e.g. I have a headache and mild fever since yesterday morning..."
                        className="w-full glass-input resize-none"
                        rows={3}
                        aria-describedby="symptom-hint"
                        maxLength={1000}
                    />
                    <p id="symptom-hint" className="text-xs text-slate-500">
                        Be as specific as possible — duration, severity, location
                    </p>
                </div>
                {error && (
                    <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                        ⚠️ {error}
                    </div>
                )}
                <button
                    onClick={handleStart}
                    disabled={!symptomInput.trim() || loading}
                    className="btn-primary w-full"
                >
                    {loading
                        ? <span className="flex items-center justify-center gap-2"><span className="spinner w-4 h-4 border-2" /> Analyzing...</span>
                        : "🩺 Start Symptom Check"
                    }
                </button>
            </div>
        );
    }

    // ---------------------------------------------------------------------------
    // RUNNING — MCQ question
    // ---------------------------------------------------------------------------
    if (state === "running" && response) {
        const progress = Math.round((response.question_number / (response.max_questions || 6)) * 100);

        return (
            <div className="space-y-4">
                {/* Disclaimer always visible */}
                <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                    {DISCLAIMER}
                </div>

                {/* Progress bar */}
                <div>
                    <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
                        <span>Question {response.question_number} of {response.max_questions || 6}</span>
                        <span>{progress}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-black/10 dark:bg-white/10 overflow-hidden" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
                        <div
                            className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>

                {/* Question card */}
                <GlassCard hover={false} className="space-y-4">
                    <p className="text-[var(--text-color)] font-medium">{response.question}</p>

                    {/* Quick-answer buttons for common responses */}
                    <div className="grid grid-cols-2 gap-2">
                        {["Yes", "No", "Mild", "Severe"].map((opt) => (
                            <button
                                key={opt}
                                onClick={() => handleAnswer(opt)}
                                disabled={loading}
                                className="py-2 rounded-lg border border-black/10 dark:border-white/10 text-slate-700 dark:text-slate-300 text-sm hover:border-indigo-500/50 hover:text-[var(--text-color)] hover:bg-indigo-500/10 transition-all"
                                aria-label={`Answer: ${opt}`}
                            >
                                {opt}
                            </button>
                        ))}
                    </div>

                    {/* Free-text answer */}
                    <div className="flex gap-2">
                        <input
                            type="text"
                            value={answerInput}
                            onChange={(e) => setAnswerInput(e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && answerInput.trim() && handleAnswer(answerInput.trim())}
                            placeholder="Or type your own answer..."
                            className="flex-1 glass-input"
                            aria-label="Type your answer"
                            disabled={loading}
                        />
                        <button
                            onClick={() => answerInput.trim() && handleAnswer(answerInput.trim())}
                            disabled={!answerInput.trim() || loading}
                            className="btn-primary px-4 py-2"
                        >
                            {loading ? <span className="spinner w-4 h-4 border-2" /> : "→"}
                        </button>
                    </div>
                </GlassCard>

                {error && <div className="p-3 rounded-xl bg-red-500/10 text-red-400 text-sm">{error}</div>}

                {/* Escape hatch */}
                <button
                    onClick={() => setFlowState("stopped")}
                    className="text-xs text-slate-500 hover:text-slate-700 dark:text-slate-300 w-full text-center"
                    aria-label="Stop symptom check"
                >
                    Stop check
                </button>
            </div>
        );
    }

    // ---------------------------------------------------------------------------
    // COMPLETE — Final recommendation
    // ---------------------------------------------------------------------------
    if (state === "complete" && response) {
        const level = response.level;

        return (
            <div className="space-y-4">
                {/* Emergency banner */}
                {level === "emergency" && (
                    <div className="p-4 rounded-2xl bg-red-500/20 border-2 border-red-500/50 space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl animate-pulse">🚨</span>
                            <div>
                                <p className="text-red-300 font-bold text-lg">Medical Emergency Detected</p>
                                <p className="text-red-400 text-sm">Please seek immediate help</p>
                            </div>
                        </div>
                        <p className="text-[var(--text-color)] text-sm leading-relaxed">{response.message}</p>
                        <div className="flex gap-2">
                            <a href="tel:112" className="btn-primary bg-red-600 hover:bg-red-500 flex-1 text-center">
                                📞 Call 112 (India Emergency)
                            </a>
                        </div>
                    </div>
                )}

                {/* Doctor referral */}
                {level === "doctor" && (
                    <GlassCard hover={false} className="space-y-3 border-amber-500/30">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">👨‍⚕️</span>
                            <div>
                                <p className="text-[var(--text-color)] font-bold">Doctor Consultation Recommended</p>
                                <p className="text-slate-600 dark:text-slate-400 text-sm">Non-urgent — within 1-2 days</p>
                            </div>
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{response.message}</p>
                    </GlassCard>
                )}

                {/* OTC recommendation */}
                {level === "otc" && (
                    <GlassCard hover={false} className="space-y-4">
                        <div className="flex items-center gap-3">
                            <span className="text-3xl">💊</span>
                            <div>
                                <p className="text-[var(--text-color)] font-bold">OTC Medicine Suggestions</p>
                                <p className="text-slate-600 dark:text-slate-400 text-sm">Self-care recommended</p>
                            </div>
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{response.message}</p>

                        {/* Medicine cards */}
                        {response.suggested_medicines && response.suggested_medicines.length > 0 && (
                            <div className="space-y-2">
                                {response.suggested_medicines.map((med: SuggestedMedicine) => (
                                    <div key={med.id} className="flex items-center justify-between p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10">
                                        <div>
                                            <p className="text-[var(--text-color)] font-medium text-sm">{med.name}</p>
                                            <p className="text-slate-600 dark:text-slate-400 text-xs">₹{med.price} · {med.unit}</p>
                                        </div>
                                        <Link
                                            href="/chat"
                                            onClick={() => {
                                                if (typeof window !== "undefined") {
                                                    localStorage.setItem("chat_prefill", `I need ${med.name}`);
                                                }
                                            }}
                                            className="btn-primary text-xs py-1.5 px-3"
                                        >
                                            Order →
                                        </Link>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Self-care tips */}
                        {response.self_care_tips && response.self_care_tips.length > 0 && (
                            <div>
                                <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-2">💡 Self-care tips</p>
                                <ul className="space-y-1">
                                    {response.self_care_tips.map((tip: string, i: number) => (
                                        <li key={i} className="text-sm text-slate-700 dark:text-slate-300 flex gap-2">
                                            <span className="text-emerald-400">✓</span> {tip}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </GlassCard>
                )}

                {/* Disclaimer */}
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                    {response.disclaimer || DISCLAIMER}
                </div>

                <button onClick={handleReset} className="btn-secondary w-full text-sm">
                    🔄 Start New Check
                </button>
            </div>
        );
    }

    // Stopped
    return (
        <div className="text-center space-y-4 py-8">
            <p className="text-slate-600 dark:text-slate-400">Symptom check stopped.</p>
            <button onClick={handleReset} className="btn-primary">Start Over</button>
        </div>
    );
}
