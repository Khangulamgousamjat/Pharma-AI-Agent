"use client";

/**
 * components/VoiceRecorder.tsx — Browser-based Speech-to-Text voice input.
 *
 * Phase 3: Voice I/O component using the Web Speech API (SpeechRecognition).
 *
 * Features:
 * - Browser STT recording with interim transcript display
 * - Start/stop via button OR keyboard: Space=toggle, Enter=confirm+send
 * - Automatic language support (en/hi/mr) fed from LanguageSelector
 * - Graceful fallback: if SpeechRecognition unavailable, shows text input
 * - TTS playback via speechSynthesis after agent response
 * - Volume/mute toggle for TTS
 * - Privacy note: browser-mode audio never leaves the device
 *
 * Accessibility:
 * - aria-label on all interactive elements
 * - role="status" for live transcript updates
 * - Keyboard event handling for Space/Enter
 *
 * @param onTranscript - Callback with final transcript (fired on stop/Enter)
 * @param onSend - Callback to send transcript to agent
 * @param language - ISO language code (controls SpeechRecognition language)
 * @param disabled - Disables recording while agent is processing
 * @param agentResponse - Latest agent response text (auto-spoken if TTS enabled)
 */

import { useEffect, useRef, useState, useCallback, KeyboardEvent } from "react";

interface VoiceRecorderProps {
    onTranscript?: (text: string) => void;
    onSend: (text: string) => void;
    language?: string;
    disabled?: boolean;
    agentResponse?: string | null;
}

// Web Speech API type declarations (not included in default TS lib)
// These are safe any-casts — we check for browser support before using
declare global {
    interface Window {
        SpeechRecognition: unknown;
        webkitSpeechRecognition: unknown;
    }
}

// BCP 47 language tags for SpeechRecognition
const SPEECH_LANG_MAP: Record<string, string> = {
    en: "en-IN",
    hi: "hi-IN",
    mr: "mr-IN",
};

export default function VoiceRecorder({
    onTranscript,
    onSend,
    language = "en",
    disabled = false,
    agentResponse,
}: VoiceRecorderProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState("");
    const [interimText, setInterimText] = useState("");
    const [isTtsEnabled, setIsTtsEnabled] = useState(true);
    const [browserSupported, setBrowserSupported] = useState(true);
    const [fallbackText, setFallbackText] = useState("");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);


    // ---------------------------------------------------------------------------
    // Check browser support
    // ---------------------------------------------------------------------------
    useEffect(() => {
        const SpeechRecognitionAPI =
            window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognitionAPI) {
            setTimeout(() => setBrowserSupported(false), 0);
        }
    }, []);

    // ---------------------------------------------------------------------------
    // TTS: Speak agent response when it changes
    // ---------------------------------------------------------------------------
    useEffect(() => {
        if (!agentResponse || !isTtsEnabled) return;
        if (typeof window === "undefined" || !window.speechSynthesis) return;

        // Cancel any pending speech before starting new one
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(agentResponse);
        utterance.lang = SPEECH_LANG_MAP[language] || "en-IN";
        utterance.rate = 0.95;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    }, [agentResponse, isTtsEnabled, language]);

    // ---------------------------------------------------------------------------
    // SpeechRecognition setup
    // ---------------------------------------------------------------------------
    const startRecording = useCallback(() => {
        if (!browserSupported || disabled) return;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRecognitionAPI = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const recognition: any = new SpeechRecognitionAPI();

        recognition.lang = SPEECH_LANG_MAP[language] || "en-IN";
        recognition.interimResults = true;
        recognition.continuous = false;
        recognition.maxAlternatives = 1;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
            let interim = "";
            let final = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const text = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    final += text;
                } else {
                    interim += text;
                }
            }
            if (final) {
                setTranscript((prev) => (prev + " " + final).trim());
                onTranscript?.(final);
            }
            setInterimText(interim);
        };

        recognition.onend = () => {
            setIsRecording(false);
            setInterimText("");
        };

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onerror = (event: any) => {
            console.warn("[VoiceRecorder] SpeechRecognition error:", event.error);
            setIsRecording(false);
        };

        recognitionRef.current = recognition;
        recognition.start();
        setIsRecording(true);
    }, [browserSupported, disabled, language, onTranscript]);

    const stopRecording = useCallback(() => {
        recognitionRef.current?.stop();
        setIsRecording(false);
    }, []);

    const toggleRecording = useCallback(() => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }, [isRecording, startRecording, stopRecording]);

    const handleSend = useCallback(() => {
        const textToSend = browserSupported ? transcript : fallbackText;
        if (!textToSend.trim()) return;
        onSend(textToSend.trim());
        setTranscript("");
        setFallbackText("");
        setInterimText("");
    }, [browserSupported, transcript, fallbackText, onSend]);

    // Keyboard shortcuts: Space = toggle recording, Enter = send
    const handleKeyDown = useCallback(
        (e: KeyboardEvent<HTMLDivElement>) => {
            if (e.code === "Space" && !e.shiftKey) {
                e.preventDefault();
                toggleRecording();
            } else if (e.code === "Enter" && !e.shiftKey && transcript) {
                e.preventDefault();
                handleSend();
            }
        },
        [toggleRecording, handleSend, transcript]
    );

    const stopTts = () => {
        window.speechSynthesis?.cancel();
    };

    // ---------------------------------------------------------------------------
    // Render: Fallback if SpeechRecognition not supported
    // ---------------------------------------------------------------------------
    if (!browserSupported) {
        return (
            <div className="space-y-3">
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">
                    🚫 Your browser doesn&apos;t support voice input. Type your message below instead, or try Chrome/Edge.
                </div>
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={fallbackText}
                        onChange={(e) => setFallbackText(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        placeholder="Type your pharmacy request..."
                        className="flex-1 glass-input"
                        aria-label="Type your pharmacy request"
                        disabled={disabled}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!fallbackText.trim() || disabled}
                        className="btn-primary px-4"
                        aria-label="Send message"
                    >
                        Send
                    </button>
                </div>
            </div>
        );
    }

    // ---------------------------------------------------------------------------
    // Render: Full voice recorder
    // ---------------------------------------------------------------------------
    const displayText = transcript + (interimText ? ` ${interimText}` : "");

    return (
        <div
            className="space-y-4"
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="region"
            aria-label="Voice recorder — press Space to start/stop, Enter to send"
        >
            {/* Mic button */}
            <div className="flex flex-col items-center gap-3">
                <button
                    onClick={toggleRecording}
                    disabled={disabled}
                    aria-label={isRecording ? "Stop recording" : "Start recording"}
                    aria-pressed={isRecording}
                    className={`
                        w-20 h-20 rounded-full flex items-center justify-center text-3xl
                        transition-all duration-200 shadow-lg
                        ${isRecording
                            ? "bg-red-500 shadow-red-500/40 scale-110 animate-pulse"
                            : "bg-indigo-600 hover:bg-indigo-500 hover:scale-105"
                        }
                        ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                    `}
                >
                    {isRecording ? "⏹" : "🎙"}
                </button>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                    {isRecording
                        ? "Recording... press Space or click to stop"
                        : "Click or press Space to start"}
                </p>
            </div>

            {/* Live transcript */}
            <div
                role="status"
                aria-live="polite"
                aria-label="Transcript"
                className="min-h-[60px] p-3 rounded-xl bg-black/20 border border-black/10 dark:border-white/10"
            >
                {displayText ? (
                    <p className="text-slate-200 text-sm leading-relaxed">
                        <span className="text-[var(--text-color)]">{transcript}</span>
                        {interimText && (
                            <span className="text-slate-600 dark:text-slate-400 italic"> {interimText}</span>
                        )}
                    </p>
                ) : (
                    <p className="text-slate-500 text-sm italic">
                        {isRecording ? "Listening..." : "Transcript will appear here"}
                    </p>
                )}
            </div>

            {/* Action row */}
            <div className="flex gap-2 items-center">
                <button
                    onClick={handleSend}
                    disabled={!transcript.trim() || disabled}
                    className="btn-primary flex-1"
                    aria-label="Send transcript to pharmacy agent"
                >
                    {disabled ? (
                        <span className="flex items-center justify-center gap-2">
                            <span className="spinner w-4 h-4 border-2" />
                            Processing...
                        </span>
                    ) : "💬 Send to Agent"}
                </button>

                {transcript && (
                    <button
                        onClick={() => { setTranscript(""); setInterimText(""); }}
                        className="btn-secondary px-3"
                        aria-label="Clear transcript"
                    >
                        ✕
                    </button>
                )}

                {/* TTS toggle */}
                <button
                    onClick={() => { setIsTtsEnabled(!isTtsEnabled); if (isTtsEnabled) stopTts(); }}
                    className={`px-3 py-2 rounded-lg text-sm transition-all border ${isTtsEnabled
                        ? "border-indigo-500/40 text-indigo-300 bg-indigo-500/10"
                        : "border-black/10 dark:border-white/10 text-slate-500"
                        }`}
                    aria-label={isTtsEnabled ? "Disable text-to-speech" : "Enable text-to-speech"}
                    aria-pressed={isTtsEnabled}
                    title="Toggle voice response"
                >
                    {isTtsEnabled ? "🔊" : "🔇"}
                </button>
            </div>

            {/* Privacy note */}
            <p className="text-xs text-slate-500 text-center">
                🔒 Voice processing is local — audio never leaves your device
            </p>
        </div>
    );
}
