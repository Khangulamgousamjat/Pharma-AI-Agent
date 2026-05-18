"use client";

/**
 * components/PrescriptionApproval.tsx — Pharmacist prescription review card.
 *
 * Displays a single prescription with:
 * - Patient user ID and upload date
 * - Vision Agent extracted medicine info (parsed from JSON)
 * - Raw extracted text
 * - Verify / Approve button → calls pharmacist API
 * - Verified status badge when already approved
 *
 * @param prescription - Prescription record from API
 * @param token - Pharmacist JWT token for verify call
 * @param onVerified - Callback after successful verification
 */

import { useState } from "react";
import { verifyPrescription, type Prescription } from "@/lib/api";
import GlassCard from "@/components/GlassCard";

interface PrescriptionApprovalProps {
    prescription: Prescription;
    token: string;
    onVerified?: (id: number) => void;
}

export default function PrescriptionApproval({
    prescription,
    token,
    onVerified,
}: PrescriptionApprovalProps) {
    const [verifying, setVerifying] = useState(false);
    const [verified, setVerified] = useState(prescription.verified);
    const [error, setError] = useState<string | null>(null);

    /** Parse extracted_medicine JSON for display */
    const extracted = (() => {
        try {
            return prescription.extracted_medicine
                ? JSON.parse(prescription.extracted_medicine)
                : null;
        } catch {
            return null;
        }
    })();

    const handleVerify = async () => {
        setVerifying(true);
        setError(null);
        try {
            await verifyPrescription(prescription.id, token);
            setVerified(true);
            onVerified?.(prescription.id);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Verification failed.");
        } finally {
            setVerifying(false);
        }
    };

    return (
        <GlassCard className="space-y-4" hover={false}>
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className="text-xs text-slate-500 mb-0.5">Prescription #{prescription.id}</p>
                    <p className="text-[var(--text-color)] font-semibold">Patient: User #{prescription.user_id}</p>
                    <p className="text-slate-600 dark:text-slate-400 text-xs mt-0.5">
                        Uploaded:{" "}
                        {prescription.created_at
                            ? new Date(prescription.created_at).toLocaleString()
                            : "Unknown date"}
                    </p>
                </div>
                <span className={verified ? "badge-success" : "badge-warning"}>
                    {verified ? "✅ Verified" : "⏳ Pending"}
                </span>
            </div>

            {/* Extracted info */}
            {extracted && (
                <div className="grid grid-cols-2 gap-2">
                    {[
                        { label: "Medicine", value: extracted.medicine_name ?? "–" },
                        { label: "Dosage", value: extracted.dosage ?? "–" },
                        { label: "Quantity", value: extracted.quantity ?? "–" },
                        { label: "Confidence", value: extracted.confidence ?? "–" },
                    ].map((item) => (
                        <div key={item.label} className="p-2 rounded-lg bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10">
                            <p className="text-xs text-slate-600 dark:text-slate-400">{item.label}</p>
                            <p className="text-sm text-[var(--text-color)] font-medium">{item.value}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Raw text preview */}
            {prescription.extracted_text && (
                <div className="p-3 rounded-xl bg-black/20 border border-black/10 dark:border-white/10">
                    <p className="text-xs text-slate-600 dark:text-slate-400 mb-1 font-medium">Extracted Text</p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed line-clamp-4">
                        {prescription.extracted_text}
                    </p>
                </div>
            )}

            {/* Error state */}
            {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    ⚠️ {error}
                </div>
            )}

            {/* Verify button */}
            {!verified && (
                <button
                    onClick={handleVerify}
                    disabled={verifying}
                    className="btn-primary w-full"
                >
                    {verifying ? (
                        <span className="flex items-center justify-center gap-2">
                            <span className="spinner w-4 h-4 border-2" />
                            Verifying...
                        </span>
                    ) : "✅ Approve Prescription"}
                </button>
            )}

            {verified && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                    <p className="text-sm text-emerald-400 font-medium">
                        ✅ Prescription approved — patient can now order this medicine
                    </p>
                </div>
            )}
        </GlassCard>
    );
}
