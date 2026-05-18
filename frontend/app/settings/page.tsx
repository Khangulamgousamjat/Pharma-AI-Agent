"use client";

/**
 * app/settings/page.tsx — User settings for theme and language.
 *
 * Phase 3: Persists UI theme (dark/light) and language preference
 * in the database via PUT /settings/preferences.
 * Also syncs to localStorage for instant client-side use.
 *
 * Accessible settings page — not a floating toggle but a dedicated page.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import LanguageSelector from "@/components/LanguageSelector";
import { getUser } from "@/lib/auth";
import { updatePreferences, type UserPreferences } from "@/lib/api";

export default function SettingsPage() {
    const router = useRouter();
    const [userId, setUserId] = useState<number | null>(null);
    const [theme, setTheme] = useState<"dark" | "light">("dark");
    const [language, setLanguage] = useState("en");
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const user = getUser();
        if (!user) { router.push("/login"); return; }
        setUserId(user.id);

        const savedTheme = localStorage.getItem("ui_theme") as "dark" | "light" || "dark";
        const savedLang = localStorage.getItem("preferred_language") || "en";
        setTheme(savedTheme);
        setLanguage(savedLang);
    }, [router]);

    const handleSave = async () => {
        if (!userId) return;
        setSaving(true);
        setError(null);
        setSaved(false);
        try {
            await updatePreferences(userId, { ui_theme: theme, preferred_language: language });
            // Persist locally
            localStorage.setItem("ui_theme", theme);
            localStorage.setItem("preferred_language", language);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to save settings");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="min-h-screen">
            <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--text-color)]">⚙️ Settings</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">Personalize your PharmaAgent experience</p>
                </div>

                {/* Theme */}
                <GlassCard hover={false}>
                    <h2 className="text-[var(--text-color)] font-semibold mb-4">🎨 UI Theme</h2>
                    <div className="grid grid-cols-2 gap-3">
                        {(["dark", "light"] as const).map((t) => (
                            <button
                                key={t}
                                role="radio"
                                aria-checked={theme === t}
                                onClick={() => setTheme(t)}
                                className={`p-4 rounded-xl border transition-all text-left ${theme === t
                                        ? "border-indigo-500/50 bg-indigo-500/10"
                                        : "border-black/10 dark:border-white/10 hover:border-black/20 dark:border-white/20"
                                    }`}
                            >
                                <div className="text-2xl mb-2">{t === "dark" ? "🌙" : "☀️"}</div>
                                <div className="text-[var(--text-color)] font-medium capitalize">{t} Mode</div>
                                <div className="text-slate-600 dark:text-slate-400 text-xs mt-0.5">
                                    {t === "dark" ? "Easy on the eyes" : "Bright and clean"}
                                </div>
                                {theme === t && (
                                    <div className="text-indigo-400 text-xs mt-2 font-medium">✓ Active</div>
                                )}
                            </button>
                        ))}
                    </div>
                    <p className="text-xs text-slate-500 mt-3">
                        Note: Full light mode CSS is available — enable in globals.css for complete theming.
                    </p>
                </GlassCard>

                {/* Language */}
                <GlassCard hover={false}>
                    <h2 className="text-[var(--text-color)] font-semibold mb-4">🌐 Conversation Language</h2>
                    <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
                        The AI will respond in your selected language for voice and text chat.
                    </p>
                    <LanguageSelector
                        currentLanguage={language}
                        onLanguageChange={setLanguage}
                    />
                </GlassCard>

                {/* Privacy note */}
                <GlassCard hover={false} className="bg-white dark:bg-slate-800/30">
                    <h2 className="text-[var(--text-color)] font-semibold mb-3">🔒 Privacy & Data</h2>
                    <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                        <li>• <strong className="text-slate-700 dark:text-slate-300">Voice input:</strong> Processed locally in your browser — audio never sent to servers</li>
                        <li>• <strong className="text-slate-700 dark:text-slate-300">Prescription images:</strong> Stored securely in the backend uploads directory</li>
                        <li>• <strong className="text-slate-700 dark:text-slate-300">Symptom data:</strong> Stored anonymously for your session history only</li>
                        <li>• <strong className="text-slate-700 dark:text-slate-300">LangSmith traces:</strong> Agent reasoning chains logged for observability (see runbook for sharing)</li>
                    </ul>
                </GlassCard>

                {/* Save button */}
                {error && (
                    <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                        {error}
                    </div>
                )}
                {saved && (
                    <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
                        ✅ Settings saved successfully
                    </div>
                )}
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="btn-primary w-full"
                    aria-label="Save settings"
                >
                    {saving
                        ? <span className="flex items-center justify-center gap-2"><span className="spinner w-4 h-4 border-2" /> Saving...</span>
                        : "Save Settings"
                    }
                </button>
            </div>
        </div>
    );
}
