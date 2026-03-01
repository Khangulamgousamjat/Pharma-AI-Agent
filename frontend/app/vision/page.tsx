"use client";

/**
 * app/vision/page.tsx — Vision Hub page.
 *
 * Allows users to:
 * 1. Upload a prescription image
 * 2. See Vision Agent extraction results
 * 3. View their prescription history with verification status
 *
 * Uses VisionUploader component for the drag-and-drop UI.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import VisionUploader from "@/components/VisionUploader";
import { getUser } from "@/lib/auth";
import { getUserPrescriptions, type Prescription, type PrescriptionUploadResponse } from "@/lib/api";

export default function VisionPage() {
    const router = useRouter();
    const [userId, setUserId] = useState<number | null>(null);
    const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const user = getUser();
        if (!user) { router.push("/login"); return; }
        setUserId(user.id);
        loadPrescriptions(user.id);
    }, []);

    const loadPrescriptions = async (uid: number) => {
        try {
            const data = await getUserPrescriptions(uid);
            setPrescriptions(data);
        } catch { /* ignore */ } finally {
            setLoading(false);
        }
    };

    const handleUploadSuccess = (result: PrescriptionUploadResponse) => {
        // Reload prescriptions list after successful upload
        if (userId) loadPrescriptions(userId);
    };

    return (
        <div className="min-h-screen">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-[var(--text-color)]">🔍 Vision Hub</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">
                        Upload prescription images — our AI extracts medicine info automatically
                    </p>
                </div>

                <div className="grid lg:grid-cols-2 gap-6">
                    {/* Upload Section */}
                    <div>
                        <GlassCard hover={false}>
                            <h2 className="text-lg font-bold text-[var(--text-color)] mb-4 flex items-center gap-2">
                                <span className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">📸</span>
                                Upload Prescription
                            </h2>
                            {userId && (
                                <VisionUploader
                                    userId={userId}
                                    onUploadSuccess={handleUploadSuccess}
                                />
                            )}
                        </GlassCard>

                        {/* How it works */}
                        <GlassCard hover={false} className="mt-4">
                            <h3 className="font-semibold text-[var(--text-color)] mb-3">How Vision AI Works</h3>
                            <div className="space-y-2">
                                {[
                                    { step: "1", text: "Upload your prescription image", icon: "📤" },
                                    { step: "2", text: "Gemini Vision AI extracts medicine details", icon: "🤖" },
                                    { step: "3", text: "Pharmacist reviews and approves", icon: "👨‍⚕️" },
                                    { step: "4", text: "Order Rx medicines through chat", icon: "✅" },
                                ].map((item) => (
                                    <div key={item.step} className="flex items-center gap-3 p-2 rounded-lg">
                                        <span className="text-xl">{item.icon}</span>
                                        <span className="text-sm text-slate-700 dark:text-slate-300">{item.text}</span>
                                    </div>
                                ))}
                            </div>
                        </GlassCard>
                    </div>

                    {/* Prescription History */}
                    <div>
                        <GlassCard hover={false} padding="none">
                            <div className="p-5 border-b border-black/10 dark:border-white/10">
                                <h2 className="font-bold text-[var(--text-color)]">My Prescriptions</h2>
                            </div>
                            {loading ? (
                                <div className="flex justify-center p-8"><div className="spinner" /></div>
                            ) : prescriptions.length === 0 ? (
                                <div className="text-center p-8 text-slate-600 dark:text-slate-400">
                                    <div className="text-3xl mb-2">📄</div>
                                    <p className="text-sm">No prescriptions uploaded yet.</p>
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {prescriptions.map((rx) => {
                                        const extracted = (() => {
                                            try { return rx.extracted_medicine ? JSON.parse(rx.extracted_medicine) : null; }
                                            catch { return null; }
                                        })();
                                        return (
                                            <div key={rx.id} className="p-4 hover:bg-black/5 dark:bg-white/5 transition-colors">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div>
                                                        <p className="text-sm font-medium text-[var(--text-color)]">
                                                            {extracted?.medicine_name ?? "Unknown medicine"}
                                                        </p>
                                                        <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
                                                            {extracted?.dosage ?? ""} · uploaded{" "}
                                                            {rx.created_at ? new Date(rx.created_at).toLocaleDateString() : "–"}
                                                        </p>
                                                    </div>
                                                    <span className={rx.verified ? "badge-success" : "badge-warning"}>
                                                        {rx.verified ? "✅ Verified" : "⏳ Pending"}
                                                    </span>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </GlassCard>
                    </div>
                </div>
            </div>
        </div>
    );
}
