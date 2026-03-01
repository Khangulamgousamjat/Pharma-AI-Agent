"use client";

/**
 * components/VisionUploader.tsx — Prescription image upload component.
 *
 * Features:
 * - Drag-and-drop or click-to-browse image upload
 * - Image preview before upload
 * - Upload progress indication
 * - Displays Vision Agent extraction results:
 *     - Medicine name, dosage, quantity, confidence badge
 *     - Raw extracted text (expandable)
 * - Error handling for invalid files and API failures
 *
 * @param userId - ID of the logged-in user
 * @param onUploadSuccess - Callback fired after successful upload
 */

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { uploadPrescription, type PrescriptionUploadResponse } from "@/lib/api";
import GlassCard from "@/components/GlassCard";

interface VisionUploaderProps {
    userId: number;
    onUploadSuccess?: (result: PrescriptionUploadResponse) => void;
}

const CONFIDENCE_BADGE: Record<string, string> = {
    high: "badge-success",
    medium: "badge-warning",
    low: "badge-error",
};

export default function VisionUploader({ userId, onUploadSuccess }: VisionUploaderProps) {
    const [dragOver, setDragOver] = useState(false);
    const [preview, setPreview] = useState<string | null>(null);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<PrescriptionUploadResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [showRaw, setShowRaw] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    /** Handle drag events to highlight drop zone */
    const handleDragOver = (e: DragEvent) => {
        e.preventDefault();
        setDragOver(true);
    };
    const handleDragLeave = () => setDragOver(false);

    /** Process file from drag-drop or file input */
    const handleFile = (selectedFile: File) => {
        if (!selectedFile.type.startsWith("image/")) {
            setError("Please select an image file (jpg, png, webp).");
            return;
        }
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError("File too large. Maximum size is 10MB.");
            return;
        }
        setError(null);
        setResult(null);
        setFile(selectedFile);

        // Show preview using FileReader
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target?.result as string);
        reader.readAsDataURL(selectedFile);
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped) handleFile(dropped);
    };

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const selected = e.target.files?.[0];
        if (selected) handleFile(selected);
    };

    /** Upload the selected image to the backend Vision Agent */
    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setError(null);

        try {
            const res = await uploadPrescription(userId, file);
            setResult(res);
            onUploadSuccess?.(res);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Upload failed. Please try again.");
        } finally {
            setUploading(false);
        }
    };

    const handleReset = () => {
        setFile(null);
        setPreview(null);
        setResult(null);
        setError(null);
        if (inputRef.current) inputRef.current.value = "";
    };

    return (
        <div className="space-y-4">
            {/* Drop Zone */}
            {!result && (
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    onClick={() => inputRef.current?.click()}
                    className={`
                        relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
                        ${dragOver
                            ? "border-indigo-400 bg-indigo-500/10"
                            : "border-black/20 dark:border-white/20 hover:border-indigo-400/50 hover:bg-black/5 dark:bg-white/5"
                        }
                    `}
                >
                    <input
                        ref={inputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={handleInputChange}
                    />

                    {/* Preview if file selected */}
                    {preview ? (
                        <div className="space-y-3">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                                src={preview}
                                alt="Prescription preview"
                                className="max-h-48 mx-auto rounded-xl object-contain"
                            />
                            <p className="text-sm text-slate-600 dark:text-slate-400">{file?.name}</p>
                            <p className="text-xs text-indigo-400">Click to change image</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="text-5xl">📄</div>
                            <p className="text-[var(--text-color)] font-medium">Drop prescription image here</p>
                            <p className="text-slate-600 dark:text-slate-400 text-sm">or click to browse</p>
                            <p className="text-xs text-slate-500">JPG, PNG, WebP — max 10MB</p>
                        </div>
                    )}
                </div>
            )}

            {/* Error */}
            {error && (
                <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                    ⚠️ {error}
                </div>
            )}

            {/* Upload / Reset buttons */}
            {file && !result && (
                <div className="flex gap-3">
                    <button onClick={handleUpload} disabled={uploading} className="btn-primary flex-1">
                        {uploading ? (
                            <span className="flex items-center justify-center gap-2">
                                <span className="spinner w-4 h-4 border-2" />
                                Scanning with Vision AI...
                            </span>
                        ) : "🔍 Scan Prescription"}
                    </button>
                    <button onClick={handleReset} className="btn-secondary">Remove</button>
                </div>
            )}

            {/* Extraction Results */}
            {result && (
                <GlassCard hover={false} className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-bold text-[var(--text-color)] flex items-center gap-2">
                            ✅ Extraction Complete
                        </h3>
                        <span className="badge-success">Uploaded</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        {[
                            { label: "Medicine", value: result.extracted.medicine_name ?? "Not detected" },
                            { label: "Dosage", value: result.extracted.dosage ?? "Not detected" },
                            { label: "Quantity", value: result.extracted.quantity ? String(result.extracted.quantity) : "Not detected" },
                            { label: "Confidence", value: result.extracted.confidence ?? "low", isBadge: true },
                        ].map((item) => (
                            <div key={item.label} className="p-3 rounded-xl bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10">
                                <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">{item.label}</p>
                                {item.isBadge ? (
                                    <span className={CONFIDENCE_BADGE[item.value] ?? "badge-warning"}>
                                        {item.value}
                                    </span>
                                ) : (
                                    <p className="text-[var(--text-color)] font-medium text-sm">{item.value}</p>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* Status */}
                    <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                        <p className="text-amber-300 text-sm">
                            ⏳ <strong>Pending pharmacist verification</strong> —
                            Your prescription (ID: #{result.prescription_id}) has been submitted.
                            A pharmacist will review and approve it shortly.
                        </p>
                    </div>

                    {/* Raw text toggle */}
                    {result.extracted.raw_text && (
                        <div>
                            <button
                                onClick={() => setShowRaw(!showRaw)}
                                className="text-xs text-indigo-400 hover:text-indigo-300"
                            >
                                {showRaw ? "▼ Hide" : "▶ Show"} raw extracted text
                            </button>
                            {showRaw && (
                                <pre className="mt-2 p-3 rounded-xl bg-black/30 text-xs text-slate-600 dark:text-slate-400 overflow-auto max-h-32">
                                    {result.extracted.raw_text}
                                </pre>
                            )}
                        </div>
                    )}

                    <button onClick={handleReset} className="btn-secondary w-full text-sm">
                        Upload Another Prescription
                    </button>
                </GlassCard>
            )}
        </div>
    );
}
