"use client";

/**
 * app/refill-alerts/page.tsx — Refill prediction alerts page.
 *
 * Displays AI-predicted refill dates from the Refill Agent.
 * Users can trigger prediction manually and reorder via chat.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import RefillAlertCard from "@/components/RefillAlertCard";
import { getUser } from "@/lib/auth";
import { getRefillAlerts, runRefillPrediction, type RefillAlert } from "@/lib/api";

export default function RefillAlertsPage() {
    const router = useRouter();
    const [alerts, setAlerts] = useState<RefillAlert[]>([]);
    const [loading, setLoading] = useState(true);
    const [predicting, setPredicting] = useState(false);
    const [predictionMsg, setPredictionMsg] = useState<string | null>(null);
    const [userId, setUserId] = useState<number | null>(null);

    useEffect(() => {
        const user = getUser();
        if (!user) { router.push("/login"); return; }
        setUserId(user.id);
        loadAlerts(user.id);
    }, []);

    const loadAlerts = async (uid: number) => {
        try {
            const data = await getRefillAlerts(uid);
            setAlerts(data);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    };

    const handleRunPrediction = async () => {
        if (!userId) return;
        setPredicting(true);
        setPredictionMsg(null);
        try {
            const res = await runRefillPrediction(userId);
            setPredictionMsg(res.message);
            await loadAlerts(userId);
        } catch (err: unknown) {
            setPredictionMsg(err instanceof Error ? err.message : "Prediction failed.");
        } finally {
            setPredicting(false);
        }
    };

    const urgentCount = alerts.filter((a) => {
        if (!a.predicted_refill_date) return false;
        const days = Math.ceil(
            (new Date(a.predicted_refill_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
        );
        return days <= 3;
    }).length;

    return (
        <div className="min-h-screen">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">

                {/* Header */}
                <div className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-[var(--text-color)]">🔔 Refill Alerts</h1>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">
                            AI-predicted medicine refill notifications based on your order history
                        </p>
                    </div>
                    <button
                        onClick={handleRunPrediction}
                        disabled={predicting}
                        className="btn-primary whitespace-nowrap"
                    >
                        {predicting ? (
                            <span className="flex items-center gap-2">
                                <span className="spinner w-4 h-4 border-2" />
                                Analyzing...
                            </span>
                        ) : "🤖 Run AI Prediction"}
                    </button>
                </div>

                {/* Prediction result banner */}
                {predictionMsg && (
                    <div className="mb-4 p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm">
                        🤖 {predictionMsg}
                    </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    {[
                        { label: "Total Alerts", value: alerts.length, icon: "📋", color: "from-indigo-500 to-violet-600" },
                        { label: "Urgent (≤3 days)", value: urgentCount, icon: "🔴", color: "from-red-500 to-rose-600" },
                        { label: "Ordered", value: alerts.filter((a) => a.status === "ordered").length, icon: "✅", color: "from-emerald-500 to-teal-600" },
                    ].map((s) => (
                        <GlassCard key={s.label} padding="md">
                            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center text-lg mb-2`}>
                                {s.icon}
                            </div>
                            <div className="text-2xl font-bold text-[var(--text-color)]">{s.value}</div>
                            <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{s.label}</div>
                        </GlassCard>
                    ))}
                </div>

                {/* Alerts Grid */}
                {loading ? (
                    <div className="flex justify-center py-12"><div className="spinner" /></div>
                ) : alerts.length === 0 ? (
                    <GlassCard hover={false} className="text-center py-12">
                        <div className="text-4xl mb-3">💊</div>
                        <p className="text-[var(--text-color)] font-medium">No refill alerts yet</p>
                        <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                            Order some medicines first, then run AI prediction to see alerts.
                        </p>
                        <button onClick={handleRunPrediction} className="btn-primary mt-4">
                            Run Prediction
                        </button>
                    </GlassCard>
                ) : (
                    <div className="grid sm:grid-cols-2 gap-4">
                        {alerts.map((alert) => (
                            <RefillAlertCard key={alert.id} alert={alert} />
                        ))}
                    </div>
                )}

                {/* Explainer */}
                <GlassCard hover={false} className="mt-6">
                    <h3 className="font-semibold text-[var(--text-color)] mb-2">How Refill Prediction Works</h3>
                    <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
                        The AI analyzes your last 90 days of orders. For each medicine, it estimates
                        your daily usage (e.g. 30 tablets = 30 day supply) and predicts when you'll
                        run out. Alerts appear when you have 7 or fewer days of supply remaining.
                    </p>
                </GlassCard>
            </div>
        </div>
    );
}
