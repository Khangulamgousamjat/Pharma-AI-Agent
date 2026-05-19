"use client";

/**
 * components/LanguageSelector.tsx — Language preference picker.
 *
 * Phase 3: Used on the Settings page to change UI/agent language.
 * Calls PUT /settings/preferences to persist choice in DB.
 * Also updates localStorage for instant client-side availability.
 *
 * @param currentLanguage - Currently selected language code
 * @param onLanguageChange - Callback when user picks a new language
 * @param className - Optional extra CSS classes
 */

interface LanguageSelectorProps {
    currentLanguage: string;
    onLanguageChange: (code: string) => void;
    className?: string;
}

const LANGUAGES = [
    { code: "en", name: "English", flag: "🇬🇧" },
    { code: "hi", name: "हिंदी", flag: "🇮🇳" },
    { code: "mr", name: "मराठी", flag: "🇮🇳" },
];

export default function LanguageSelector({
    currentLanguage,
    onLanguageChange,
    className = "",
}: LanguageSelectorProps) {
    return (
        <div className={`space-y-2 ${className}`} role="radiogroup" aria-label="Select language">
            {LANGUAGES.map((lang) => (
                <button
                    key={lang.code}
                    role="radio"
                    aria-checked={currentLanguage === lang.code}
                    onClick={() => onLanguageChange(lang.code)}
                    className={`
                        w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left
                        ${currentLanguage === lang.code
                            ? "border-indigo-500/50 bg-indigo-500/10 text-[var(--text-color)]"
                            : "border-black/10 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:border-black/20 dark:border-white/20 hover:text-[var(--text-color)] hover:bg-black/5 dark:bg-white/5"
                        }
                    `}
                >
                    <span className="text-xl">{lang.flag}</span>
                    <span className="font-medium">{lang.name}</span>
                    {currentLanguage === lang.code && (
                        <span className="ml-auto text-indigo-400 text-xs font-medium">✓ Active</span>
                    )}
                </button>
            ))}
        </div>
    );
}
