"use client";

/**
 * components/RefillAlertCard.tsx — Refill prediction alert card.
 *
 * Displays a single refill alert with:
 * - Medicine name and predicted refill date
 * - Days until refill (urgency coloring)
 * - Days supply estimation
 * - Status badge (pending/notified/ordered)
 * - Reorder button → redirects to chat with prefilled message
 *
 * @param alert - RefillAlert object from API
 */

import Link from "next/link";
import { type RefillAlert } from "@/lib/api";
import GlassCard from "@/components/GlassCard";

interface RefillAlertCardProps {
    alert: RefillAlert;
}

const STATUS_BADGE: Record<string, string> = {
    pending: "badge-warning",
    notified: "badge-warning",
    ordered: "badge-success",
};

export default function RefillAlertCard({ alert }: RefillAlertCardProps) {
    /** Calculate days until predicted refill date */
    const daysUntil = (() => {
        if (!alert.predicted_refill_date) return null;
        const today = new Date();
        const refill = new Date(alert.predicted_refill_date);
        const diff = Math.ceil((refill.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        return diff;
    })();

    const urgencyColor = (() => {
        if (daysUntil === null) return "text-slate-600 dark:text-slate-400";
        if (daysUntil <= 0) return "text-red-400";
        if (daysUntil <= 3) return "text-red-400";
        if (daysUntil <= 7) return "text-amber-400";
        return "text-emerald-400";
    })();

    const urgencyBg = (() => {
        if (daysUntil === null || daysUntil > 7) return "from-indigo-500/10 to-violet-500/10";
        if (daysUntil <= 3) return "from-red-500/10 to-rose-500/10";
        return "from-amber-500/10 to-orange-500/10";
    })();

    const isOverdue = daysUntil !== null && daysUntil <= 0;

    // Pre-build a chat message for the reorder button
    const chatMessage = `I need to refill ${alert.medicine_name ?? "my medicine"}`;

    return (
        <GlassCard className={`bg-gradient-to-br ${urgencyBg} space-y-3`}>
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-xl">
                        💊
                    </div>
                    <div>
                        <p className="text-[var(--text-color)] font-semibold">
                            {alert.medicine_name ?? `Medicine #${alert.medicine_id}`}
                        </p>
                        <p className="text-xs text-slate-600 dark:text-slate-400">
                            {alert.days_supply} day supply ordered
                        </p>
                    </div>
                </div>
                <span className={STATUS_BADGE[alert.status] ?? "badge-warning"}>
                    {alert.status}
                </span>
            </div>

            {/* Countdown */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-black/20">
                <div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">Predicted Refill Date</p>
                    <p className="text-[var(--text-color)] font-medium text-sm">
                        {alert.predicted_refill_date
                            ? new Date(alert.predicted_refill_date).toLocaleDateString("en-IN", {
                                day: "numeric",
                                month: "short",
                                year: "numeric",
                            })
                            : "Not calculated"}
                    </p>
                </div>
                <div className="text-right">
                    <p className="text-xs text-slate-600 dark:text-slate-400">Time remaining</p>
                    <p className={`font-bold text-lg ${urgencyColor}`}>
                        {daysUntil === null
                            ? "–"
                            : isOverdue
                                ? "Overdue!"
                                : `${daysUntil}d left`}
                    </p>
                </div>
            </div>

            {/* Urgency banner for near-overdue */}
            {daysUntil !== null && daysUntil <= 3 && (
                <div className={`text-xs text-center py-1 px-2 rounded-lg ${isOverdue ? "bg-red-500/20 text-red-300" : "bg-amber-500/20 text-amber-300"}`}>
                    {isOverdue ? "⚠️ Your supply has run out — reorder now!" : "🔔 Running low — consider reordering soon"}
                </div>
            )}

            {/* Reorder button */}
            {alert.status !== "ordered" && (
                <Link
                    href={`/chat`}
                    className="btn-primary block text-center text-sm py-2"
                    onClick={() => {
                        // Store the prefilled message for the chat page to pick up
                        if (typeof window !== "undefined") {
                            localStorage.setItem("chat_prefill", chatMessage);
                        }
                    }}
                >
                    🔄 Reorder {alert.medicine_name ?? "Medicine"}
                </Link>
            )}
        </GlassCard>
    );
}
