"use client";

/**
 * app/dashboard/page.tsx — User dashboard overview.
 *
 * Shows:
 * - Welcome card with user name and quick stats
 * - Recent orders for the logged-in user
 * - Quick action buttons to chat or view inventory
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import GlassCard from "@/components/GlassCard";
import { getUser } from "@/lib/auth";
import { getUserOrders, BASE_URL, type Order } from "@/lib/api";

const STATUS_BADGE: Record<string, string> = {
    confirmed: "badge-success",
    paid: "badge-success",
    pending: "badge-warning",
    cancelled: "badge-error",
};

export default function DashboardPage() {
    const router = useRouter();
    const user = typeof window !== "undefined" ? getUser() : null;
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            router.push("/login");
            return;
        }
        getUserOrders(user.id)
            .then(setOrders)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const handleExportMyOrders = async () => {
        if (!user) return;
        try {
            const token = localStorage.getItem("pharmaagent_token");
            if (!token) return;
            const res = await fetch(`${BASE_URL}/orders/export-user/${user.id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Export failed");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `my_orders.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert("Export failed. Please try again.");
        }
    };

    const stats = [
        {
            label: "Total Orders",
            value: orders.length,
            icon: "📦",
            color: "from-indigo-500 to-violet-600",
        },
        {
            label: "Completed",
            value: orders.filter((o) => o.status === "paid" || o.status === "confirmed").length,
            icon: "✅",
            color: "from-emerald-500 to-teal-600",
        },
        {
            label: "Total Spent",
            value: `₹${orders.reduce((s, o) => s + o.total_price, 0).toFixed(2)}`,
            icon: "💰",
            color: "from-amber-500 to-orange-600",
        },
        {
            label: "Pending",
            value: orders.filter((o) => o.status === "pending").length,
            icon: "⏳",
            color: "from-blue-500 to-cyan-600",
        },
    ];

    return (
        <div className="min-h-screen">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">

                {/* Welcome Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-[var(--text-color)]">
                        Welcome back, <span className="gradient-text">{user?.name ?? "User"}</span> 👋
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">Your AI-powered pharmacy dashboard</p>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {stats.map((stat) => (
                        <GlassCard key={stat.label} padding="md">
                            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center text-xl mb-3`}>
                                {stat.icon}
                            </div>
                            <div className="text-2xl font-bold text-[var(--text-color)]">{stat.value}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">{stat.label}</div>
                        </GlassCard>
                    ))}
                </div>

                {/* Quick Actions */}
                <div className="grid md:grid-cols-2 gap-4 mb-8">
                    {user?.role !== "admin" && (
                        <GlassCard className="flex items-center gap-4" hover={false}>
                            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-2xl shrink-0">
                                💬
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-[var(--text-color)]">Chat with PharmaBot</h3>
                                <p className="text-slate-600 dark:text-slate-400 text-sm">Order medicines using natural language</p>
                            </div>
                            <Link href="/chat" className="btn-primary text-sm py-2 px-4">
                                Start Chat
                            </Link>
                        </GlassCard>
                    )}

                    <GlassCard className="flex items-center gap-4" hover={false}>
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-2xl shrink-0">
                            🏪
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-[var(--text-color)]">Browse Inventory</h3>
                            <p className="text-slate-600 dark:text-slate-400 text-sm">View all available medicines</p>
                        </div>
                        {user?.role === "admin" && (
                            <Link href="/admin" className="btn-secondary text-sm py-2 px-4">
                                Admin View
                            </Link>
                        )}
                    </GlassCard>
                </div>

                <GlassCard hover={false} padding="none">
                    <div className="p-6 border-b border-black/10 dark:border-white/10 flex items-center justify-between">
                        <h2 className="font-bold text-[var(--text-color)] text-lg">Recent Orders</h2>
                        <div className="flex items-center gap-3">
                            <span className="text-sm text-slate-600 dark:text-slate-400">{orders.length} total</span>
                            {orders.length > 0 && (
                                <button
                                    onClick={handleExportMyOrders}
                                    className="text-xs px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-600/30 transition-colors"
                                >
                                    📥 Export
                                </button>
                            )}
                        </div>
                    </div>

                    {loading ? (
                        <div className="flex justify-center p-12">
                            <div className="spinner" />
                        </div>
                    ) : orders.length === 0 ? (
                        <div className="text-center p-12 text-slate-600 dark:text-slate-400">
                            <div className="text-4xl mb-3">📭</div>
                            <p>No orders yet. <Link href="/chat" className="text-indigo-400 hover:underline">Place your first order →</Link></p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="table-glass">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>Medicine</th>
                                        <th>Qty</th>
                                        <th>Total</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders.slice(0, 8).map((order) => (
                                        <tr key={order.id}>
                                            <td className="text-indigo-400 font-mono text-xs">#{order.id}</td>
                                            <td className="text-[var(--text-color)] font-medium">
                                                {order.medicine?.name ?? `Medicine #${order.medicine_id}`}
                                            </td>
                                            <td>{order.quantity} {order.medicine?.unit ?? "units"}</td>
                                            <td className="font-medium">₹{order.total_price.toFixed(2)}</td>
                                            <td>
                                                <span className={STATUS_BADGE[order.status] ?? "badge-warning"}>
                                                    {order.status}
                                                </span>
                                            </td>
                                            <td className="text-slate-500 text-xs">
                                                {order.created_at ? new Date(order.created_at).toLocaleDateString() : "—"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </GlassCard>
            </div>
        </div>
    );
}
