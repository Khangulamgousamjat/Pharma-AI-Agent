"use client";

/**
 * app/analytics/page.tsx — Admin Analytics Dashboard.
 *
 * Phase 3: Shows KPI cards, top medicines bar chart, daily orders line chart,
 * webhook fulfillment pie chart, and recent webhook events table.
 *
 * Access: Admin only (redirects non-admins to /dashboard).
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import {
    TopMedicinesChart,
    OrdersLineChart,
    WebhookPieChart,
    type TopMedicine,
    type DailyOrder,
    type WebhookStats,
} from "@/components/AnalyticsCharts";
import { getUser } from "@/lib/auth";
import {
    getAnalyticsOverview,
    getTopMedicines,
    getOrdersOverTime,
    getAnalyticsFulfillment,
    retriggerWebhook,
    type AnalyticsOverview,
    type WebhookEvent,
} from "@/lib/api";

export default function AnalyticsPage() {
    const router = useRouter();
    const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
    const [topMeds, setTopMeds] = useState<TopMedicine[]>([]);
    const [ordersTime, setOrdersTime] = useState<DailyOrder[]>([]);
    const [webhookStats, setWebhookStats] = useState<WebhookStats | null>(null);
    const [recentEvents, setRecentEvents] = useState<WebhookEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [retriggering, setRetriggering] = useState<number | null>(null);

    useEffect(() => {
        const user = getUser();
        if (!user || user.role !== "admin") {
            router.push("/dashboard");
            return;
        }
        loadAll();
    }, [router]);

    const loadAll = async () => {
        setLoading(true);
        try {
            const [ov, meds, time, fulfillment] = await Promise.all([
                getAnalyticsOverview(),
                getTopMedicines(10),
                getOrdersOverTime(30),
                getAnalyticsFulfillment(),
            ]);
            setOverview(ov);
            setTopMeds(meds.medicines || []);
            setOrdersTime(time.data || []);
            setWebhookStats({
                total_attempts: fulfillment.total_attempts,
                successful: fulfillment.successful,
                failed: fulfillment.failed,
                success_rate: fulfillment.success_rate,
            });
            setRecentEvents(fulfillment.recent_events || []);
        } catch (e) {
            console.error("Analytics load failed:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleRetrigger = async (orderId: number) => {
        setRetriggering(orderId);
        try {
            await retriggerWebhook(orderId);
            await loadAll();
        } catch (e) {
            console.error("Retrigger failed:", e);
        } finally {
            setRetriggering(null);
        }
    };

    const STATUS_BADGE: Record<string, string> = {
        success: "badge-success",
        failed: "badge-error",
        pending: "badge-warning",
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col">
                <div className="flex-1 flex items-center justify-center">
                    <div className="spinner" />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen">
            <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-[var(--text-color)]">📈 Analytics Dashboard</h1>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">Platform KPIs and agent metrics</p>
                    </div>
                    <button onClick={loadAll} className="btn-secondary text-sm" aria-label="Refresh analytics">
                        🔄 Refresh
                    </button>
                </div>

                {/* KPI Cards */}
                {overview && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { label: "Total Orders", value: overview.total_orders, icon: "📦", color: "from-indigo-500 to-violet-600" },
                            { label: "Total Revenue", value: `₹${overview.total_revenue.toFixed(0)}`, icon: "💰", color: "from-emerald-500 to-teal-600" },
                            { label: "Total Users", value: overview.total_users, icon: "👤", color: "from-blue-500 to-cyan-600" },
                            { label: "Pending Prescriptions", value: overview.pending_prescriptions, icon: "📋", color: "from-amber-500 to-orange-600" },
                        ].map((s) => (
                            <GlassCard key={s.label} padding="md">
                                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center text-xl mb-3`}>
                                    {s.icon}
                                </div>
                                <div className="text-2xl font-bold text-[var(--text-color)]">{s.value}</div>
                                <div className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">{s.label}</div>
                            </GlassCard>
                        ))}
                    </div>
                )}

                {/* Charts row */}
                <div className="grid lg:grid-cols-3 gap-6">
                    {/* Top Medicines */}
                    <GlassCard hover={false} padding="none" className="lg:col-span-2">
                        <div className="p-4 border-b border-black/10 dark:border-white/10">
                            <h2 className="font-bold text-[var(--text-color)] text-sm">💊 Top Medicines (by Orders)</h2>
                        </div>
                        <div className="p-4">
                            <TopMedicinesChart data={topMeds} />
                        </div>
                    </GlassCard>

                    {/* Webhook Pie */}
                    <GlassCard hover={false} padding="none">
                        <div className="p-4 border-b border-black/10 dark:border-white/10">
                            <h2 className="font-bold text-[var(--text-color)] text-sm">📡 Webhook Status</h2>
                        </div>
                        <div className="p-4">
                            {webhookStats && <WebhookPieChart stats={webhookStats} />}
                        </div>
                    </GlassCard>
                </div>

                {/* Orders over time */}
                <GlassCard hover={false} padding="none">
                    <div className="p-4 border-b border-black/10 dark:border-white/10">
                        <h2 className="font-bold text-[var(--text-color)] text-sm">📅 Orders & Revenue (Last 30 days)</h2>
                    </div>
                    <div className="p-4">
                        <OrdersLineChart data={ordersTime} />
                    </div>
                </GlassCard>

                {/* Webhook events table */}
                <GlassCard hover={false} padding="none">
                    <div className="p-4 border-b border-black/10 dark:border-white/10 flex items-center justify-between">
                        <h2 className="font-bold text-[var(--text-color)] text-sm">📡 Recent Webhook Events</h2>
                        <span className="text-xs text-slate-600 dark:text-slate-400">
                            Success rate: <span className="text-emerald-400 font-bold">{webhookStats?.success_rate ?? 0}%</span>
                        </span>
                    </div>
                    <div className="overflow-x-auto">
                        {recentEvents.length === 0 ? (
                            <div className="text-center py-8 text-slate-500 text-sm">No webhook events yet</div>
                        ) : (
                            <table className="table-glass">
                                <thead>
                                    <tr>
                                        <th>Event</th>
                                        <th>Order</th>
                                        <th>Attempt</th>
                                        <th>HTTP</th>
                                        <th>Status</th>
                                        <th>Time</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {recentEvents.map((ev) => (
                                        <tr key={ev.id}>
                                            <td className="text-indigo-400 font-mono text-xs">#{ev.id}</td>
                                            <td className="text-slate-700 dark:text-slate-300">#{ev.order_id}</td>
                                            <td className="text-slate-600 dark:text-slate-400">#{ev.attempt_number}</td>
                                            <td className="font-mono text-xs">{ev.http_status_code ?? "—"}</td>
                                            <td>
                                                <span className={STATUS_BADGE[ev.status] ?? "badge-warning"}>
                                                    {ev.status}
                                                </span>
                                            </td>
                                            <td className="text-slate-500 text-xs">
                                                {ev.created_at ? new Date(ev.created_at).toLocaleString() : "—"}
                                            </td>
                                            <td>
                                                {ev.status === "failed" && (
                                                    <button
                                                        onClick={() => handleRetrigger(ev.order_id)}
                                                        disabled={retriggering === ev.order_id}
                                                        className="text-xs text-indigo-400 hover:text-indigo-300 underline"
                                                        aria-label={`Retry webhook for order ${ev.order_id}`}
                                                    >
                                                        {retriggering === ev.order_id ? "Retrying..." : "↺ Retry"}
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </GlassCard>
            </div>
        </div>
    );
}
