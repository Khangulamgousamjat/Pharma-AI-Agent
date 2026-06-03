"use client";

/**
 * app/voice/page.tsx — Voice Chat interface.
 *
 * Phase 3: Full voice-enabled chat page. Uses VoiceRecorder (browser STT)
 * and sends transcript to POST /agent/voice-message.
 * Agent response is displayed in chat log and spoken via browser TTS.
 *
 * Language: Selected from dropdown, passed to backend + SpeechRecognition.
 */

import { useEffect, useRef, useState } from "react";
import GlassCard from "@/components/GlassCard";
import VoiceRecorder from "@/components/VoiceRecorder";
import { getUser } from "@/lib/auth";
import { sendVoiceMessage, type VoiceMessageResponse } from "@/lib/api";

interface VoiceMessage {
    role: "user" | "agent";
    text: string;
    language: string;
    timestamp: string;
    action?: string | null;
}

const LANGUAGE_LABELS: Record<string, string> = {
    en: "🇬🇧 English",
    hi: "🇮🇳 हिंदी",
    mr: "🇮🇳 मराठी",
};

export default function VoicePage() {
    const [messages, setMessages] = useState<VoiceMessage[]>([]);
    const [language, setLanguage] = useState<string>("en");
    const [loading, setLoading] = useState(false);
    const [lastResponse, setLastResponse] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const user = typeof window !== "undefined" ? getUser() : null;

    // Load saved language preference
    useEffect(() => {
        const saved = localStorage.getItem("preferred_language");
        if (saved) setLanguage(saved);
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendToAgent = async (transcript: string) => {
        if (!user || !transcript.trim()) return;

        const userMsg: VoiceMessage = {
            role: "user",
            text: transcript,
            language,
            timestamp: new Date().toLocaleTimeString(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const result: VoiceMessageResponse = await sendVoiceMessage(user.id, transcript, language);
            const agentMsg: VoiceMessage = {
                role: "agent",
                text: result.response_text,
                language: result.language,
                timestamp: new Date().toLocaleTimeString(),
                action: result.action,
            };
            setMessages((prev) => [...prev, agentMsg]);
            setLastResponse(result.response_text); // triggers TTS in VoiceRecorder
        } catch (e) {
            const errMsg: VoiceMessage = {
                role: "agent",
                text: "Sorry, I encountered an error. Please try again.",
                language,
                timestamp: new Date().toLocaleTimeString(),
            };
            setMessages((prev) => [...prev, errMsg]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen">
            <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
                <div>
                    <h1 className="text-3xl font-bold text-[var(--text-color)]">🎙 Voice Agent</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-1">Speak to your AI pharmacy assistant</p>
                </div>

                {/* Language selector */}
                <GlassCard hover={false} padding="sm">
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-slate-600 dark:text-slate-400">Language:</span>
                        {Object.entries(LANGUAGE_LABELS).map(([code, label]) => (
                            <button
                                key={code}
                                onClick={() => { setLanguage(code); localStorage.setItem("preferred_language", code); }}
                                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${language === code
                                        ? "border-indigo-500/50 bg-indigo-500/10 text-indigo-300"
                                        : "border-black/10 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:border-black/20 dark:border-white/20 hover:text-[var(--text-color)]"
                                    }`}
                                aria-pressed={language === code}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                </GlassCard>

                {/* Chat log */}
                <GlassCard hover={false} padding="none">
                    <div className="p-4 max-h-80 overflow-y-auto space-y-3">
                        {messages.length === 0 ? (
                            <div className="text-center py-8 text-slate-500">
                                <p className="text-2xl mb-2">🎙</p>
                                <p className="text-sm">Press the mic and speak your request</p>
                                <p className="text-xs mt-1 text-slate-600">Example: &quot;I need paracetamol 10 tablets&quot;</p>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <div key={idx} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                                    {msg.role === "agent" && (
                                        <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center text-xs flex-shrink-0">AI</div>
                                    )}
                                    <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${msg.role === "user"
                                            ? "bg-indigo-600/30 text-[var(--text-color)] rounded-tr-sm"
                                            : "bg-black/5 dark:bg-white/5 text-slate-200 rounded-tl-sm"
                                        }`}>
                                        {msg.text}
                                        <div className="text-xs text-slate-500 mt-1">{msg.timestamp}</div>
                                    </div>
                                </div>
                            ))
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </GlassCard>

                {/* Voice recorder */}
                <GlassCard hover={false}>
                    <VoiceRecorder
                        onSend={sendToAgent}
                        language={language}
                        disabled={loading}
                        agentResponse={lastResponse}
                    />
                </GlassCard>
            </div>
        </div>
    );
}
