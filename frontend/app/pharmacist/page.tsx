"use client";

/**
 * app/pharmacist/page.tsx — Pharmacist dashboard for prescription review.
 *
 * Shows pending prescriptions (pharmacist queue) and allows approval.
 * Access restricted to pharmacist and admin roles only.
 *
 * Demo login: pharmacist@pharmaagent.com / pharma123
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import PrescriptionApproval from "@/components/PrescriptionApproval";
import { getUser, getToken } from "@/lib/auth";
import { getPendingPrescriptions, type Prescription } from "@/lib/api";

export default function PharmacistPage() {
    const router = useRouter();
    const [pendingRx, setPendingRx] = useState<Prescription[]>([]);
    const [verifiedIds, setVerifiedIds] = useState<Set<number>>(new Set());
    const [loading, setLoading] = useState(true);
    const [role, setRole] = useState<string>("user");
    const [token, setToken] = useState<string>("");

    useEffect(() => {
        const user = getUser();
        if (!user) { router.push("/login"); return; }
        if (user.role !== "pharmacist" && user.role !== "admin") {
            router.push("/dashboard");
            return;
        }
        setRole(user.role);
        const t = getToken() ?? "";
        setToken(t);
        loadPrescriptions();
    }, []);

    const loadPrescriptions = async () => {
        try {
            const data = await getPendingPrescriptions();
            setPendingRx(data);
        } catch { /* ignore */ }
        finally { setLoading(false); }
    };

    const handleVerified = (id: number) => {
        setVerifiedIds((prev) => new Set([...prev, id]));
    };

    const handleExportInventory = async () => {
        try {
            const t = getToken();
            if (!t) return;
            const res = await fetch("http://localhost:8000/medicines/export", {
                headers: { Authorization: `Bearer ${t}` }
            });
            if (!res.ok) throw new Error("Export failed");
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "medicine_inventory.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (e) {
            console.error(e);
            alert("Export failed. Please try again.");
        }
    };

    const pendingCount = pendingRx.filter((rx) => !verifiedIds.has(rx.id)).length;

    return (
        <div className="min-h-screen">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">

                {/* Header */}
                <div className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-[var(--text-color)]">👨‍⚕️ Pharmacist Dashboard</h1>
                        <p className="text-slate-600 dark:text-slate-400 mt-1">Review and approve patient prescriptions</p>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20">
                        <span className="w-2 h-2 rounded-full bg-violet-400" />
                        <span className="text-violet-300 text-xs font-medium capitalize">{role}</span>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                    {[
                        { label: "Pending Review", value: pendingCount, color: "from-amber-500 to-orange-600", icon: "⏳" },
                        { label: "Approved Today", value: verifiedIds.size, color: "from-emerald-500 to-teal-600", icon: "✅" },
                        { label: "Total in Queue", value: pendingRx.length, color: "from-indigo-500 to-violet-600", icon: "📋" },
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

                {/* Prescription Queue */}
                <div className="mb-4 flex items-center justify-between">
                    <h2 className="font-bold text-[var(--text-color)] text-lg">
                        Prescription Queue
                        {pendingCount > 0 && (
                            <span className="ml-2 px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-normal">
                                {pendingCount} pending
                            </span>
                        )}
                    </h2>
                    <div className="flex gap-2">
                        <button onClick={handleExportInventory} className="btn-secondary text-sm py-1.5 px-3">
                            📥 Export Inventory
                        </button>
                        <button onClick={loadPrescriptions} className="btn-secondary text-sm py-1.5 px-3">
                            🔄 Refresh
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center py-12"><div className="spinner" /></div>
                ) : pendingRx.length === 0 ? (
                    <GlassCard hover={false} className="text-center py-12">
                        <div className="text-4xl mb-3">🎉</div>
                        <p className="text-[var(--text-color)] font-medium">All caught up!</p>
                        <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">No pending prescriptions to review.</p>
                    </GlassCard>
                ) : (
                    <div className="space-y-4">
                        {pendingRx.map((rx) => (
                            <PrescriptionApproval
                                key={rx.id}
                                prescription={rx}
                                token={token}
                                onVerified={handleVerified}
                            />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
