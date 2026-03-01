"use client";

/**
 * app/admin/page.tsx — Admin dashboard for medicine inventory and order management.
 *
 * Features:
 * - Medicine inventory table (name, stock, price, prescription_required)
 * - All orders table with user and status info
 * - Admin-only access guard (redirects if not admin)
 * - Glassmorphism design with colored status badges
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import { getUser } from "@/lib/auth";
import { getMedicines, getAllOrders, type Medicine, type Order } from "@/lib/api";

export default function AdminPage() {
    const router = useRouter();
    const [medicines, setMedicines] = useState<Medicine[]>([]);
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"inventory" | "orders">("inventory");

    useEffect(() => {
        const user = getUser();
        if (!user || user.role !== "admin") {
            router.push("/dashboard");
            return;
        }
        // Load both medicines and orders in parallel
        Promise.all([getMedicines(), getAllOrders()])
            .then(([meds, ords]) => {
                setMedicines(meds);
                setOrders(ords);
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const lowStockCount = medicines.filter((m) => m.stock < 50).length;

    const handleExport = async () => {
        try {
            const token = localStorage.getItem("token");
            if (!token) return;
            const res = await fetch("http://localhost:8000/orders/export", {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!res.ok) throw new Error("Export failed");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "orders_export.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert("Export failed");
        }
    };
    const rxCount = medicines.filter((m) => m.prescription_required).length;
    const otcCount = medicines.filter((m) => !m.prescription_required).length;
    const totalRevenue = orders.reduce((s, o) => s + o.total_price, 0);

    const STATUS_BADGE: Record<string, string> = {
        confirmed: "badge-success",
        paid: "badge-success",
        pending: "badge-warning",
        cancelled: "badge-error",
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
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">

                {/* Header */}
                <div className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-[var(--text-color)]">⚙️ Admin Dashboard</h1>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">Manage inventory and monitor all orders</p>
                    </div>
                    <button onClick={handleExport} className="btn-secondary flex items-center gap-2">
                        <span>📥</span> Export Orders
                    </button>
                </div>

                {/* Summary Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    {[
                        { label: "Total Medicines", value: medicines.length, icon: "💊", color: "from-indigo-500 to-violet-600" },
                        { label: "OTC Medicines", value: otcCount, icon: "✅", color: "from-emerald-500 to-teal-600" },
                        { label: "Rx Medicines", value: rxCount, icon: "📋", color: "from-red-500 to-rose-600" },
                        { label: "⚠️ Low Stock", value: lowStockCount, icon: "⚠️", color: "from-amber-500 to-orange-600" },
                    ].map((s) => (
                        <GlassCard key={s.label} padding="md">
                            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${s.color} flex items-center justify-center text-xl mb-3`}>
                                {s.icon}
                            </div>
                            <div className="text-2xl font-bold text-[var(--text-color)]">{s.value}</div>
                            <div className="text-sm text-slate-600 dark:text-slate-400 mt-0.5">{s.label}</div>
                        </GlassCard>
                    ))}
                </div>

                {/* Revenue Card */}
                <GlassCard hover={false} padding="md" className="mb-6 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center text-2xl">
                        💰
                    </div>
                    <div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">Total Revenue</div>
                        <div className="text-3xl font-bold gradient-text">₹{totalRevenue.toFixed(2)}</div>
                    </div>
                    <div className="ml-auto text-right">
                        <div className="text-sm text-slate-600 dark:text-slate-400">Total Orders</div>
                        <div className="text-2xl font-bold text-[var(--text-color)]">{orders.length}</div>
                    </div>
                </GlassCard>

                {/* Tab Switcher */}
                <div className="flex gap-2 mb-4">
                    {(["inventory", "orders"] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === tab
                                ? "bg-indigo-600/40 text-indigo-200 border border-indigo-500/40"
                                : "text-slate-600 dark:text-slate-400 hover:text-[var(--text-color)] hover:bg-black/10 dark:bg-white/10"
                                }`}
                        >
                            {tab === "inventory" ? "💊 Inventory" : "📦 Orders"}
                        </button>
                    ))}
                </div>

                {/* Inventory Table */}
                {activeTab === "inventory" && (
                    <GlassCard hover={false} padding="none">
                        <div className="p-5 border-b border-black/10 dark:border-white/10">
                            <h2 className="font-bold text-[var(--text-color)]">Medicine Inventory</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="table-glass">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Stock</th>
                                        <th>Unit</th>
                                        <th>Price</th>
                                        <th>Type</th>
                                        <th>Expiry</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {medicines.map((med) => (
                                        <tr key={med.id}>
                                            <td className="text-indigo-400 font-mono text-xs">#{med.id}</td>
                                            <td className="text-[var(--text-color)] font-medium">{med.name}</td>
                                            <td>
                                                <span className={med.stock < 50 ? "text-amber-400 font-semibold" : "text-slate-700 dark:text-slate-300"}>
                                                    {med.stock}
                                                </span>
                                                {med.stock < 50 && <span className="text-amber-400 ml-1 text-xs">⚠️ Low</span>}
                                            </td>
                                            <td className="text-slate-600 dark:text-slate-400">{med.unit}</td>
                                            <td>₹{med.price.toFixed(2)}</td>
                                            <td>
                                                {med.prescription_required
                                                    ? <span className="badge-rx">Rx</span>
                                                    : <span className="badge-otc">OTC</span>}
                                            </td>
                                            <td className="text-slate-500 text-xs">{med.expiry_date ?? "—"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </GlassCard>
                )}

                {/* Orders Table */}
                {activeTab === "orders" && (
                    <GlassCard hover={false} padding="none">
                        <div className="p-5 border-b border-black/10 dark:border-white/10">
                            <h2 className="font-bold text-[var(--text-color)]">All Orders</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="table-glass">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>User ID</th>
                                        <th>Medicine</th>
                                        <th>Qty</th>
                                        <th>Total</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {orders.map((order) => (
                                        <tr key={order.id}>
                                            <td className="text-indigo-400 font-mono text-xs">#{order.id}</td>
                                            <td className="text-slate-600 dark:text-slate-400">User #{order.user_id}</td>
                                            <td className="text-[var(--text-color)]">{order.medicine?.name ?? `Medicine #${order.medicine_id}`}</td>
                                            <td>{order.quantity} {order.medicine?.unit ?? ""}</td>
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
                            {orders.length === 0 && (
                                <div className="text-center p-10 text-slate-600 dark:text-slate-400">
                                    <div className="text-3xl mb-2">📭</div>
                                    <p>No orders yet.</p>
                                </div>
                            )}
                        </div>
                    </GlassCard>
                )}
            </div>
        </div>
    );
}
