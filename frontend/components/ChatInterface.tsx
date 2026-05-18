"use client";

/**
 * components/ChatInterface.tsx — AI pharmacy chat interface.
 *
 * State management:
 *   - messages: Array of {role, content, action, order_id} objects
 *   - input: Current user input string
 *   - loading: Whether the agent is processing
 *
 * API integration:
 *   - Calls sendAgentMessage(userId, message) on submit
 *   - Displays agent response with action badge
 *   - Shows order confirmation when action === 'order_created'
 *
 * Safety feedback:
 *   - Shows prescription warning when action === 'prescription_required'
 *   - Shows stock warning when action === 'out_of_stock'
 */

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Mic, Send, Loader2 } from "lucide-react";
import { sendAgentMessage, processPayment, type AgentChatResponse } from "@/lib/api";

interface Message {
    role: "user" | "agent";
    content: string;
    action?: string | null;
    order_id?: number | null;
    timestamp: Date;
}

interface ChatInterfaceProps {
    userId: number;
}

/** Extract a safe, readable error message from any thrown value */
function getErrorMessage(err: unknown): string {
    if (err instanceof Error) {
        const msg = err.message;
        if (msg && msg !== "[object Object]") return msg;
    }
    if (typeof err === "object" && err !== null && "detail" in err) {
        const d = (err as { detail?: unknown }).detail;
        if (typeof d === "string") return d;
    }
    return "Something went wrong";
}

const ACTION_BADGE: Record<string, { label: string; class: string }> = {
    order_created: { label: "✅ Order Created", class: "badge-success" },
    prescription_required: { label: "⚠️ Prescription Required", class: "badge-warning" },
    out_of_stock: { label: "❌ Out of Stock", class: "badge-error" },
    error: { label: "❌ Error", class: "badge-error" },
};

/** Welcome message shown at the start of every chat session */
const WELCOME_MESSAGE: Message = {
    role: "agent",
    content:
        "👋 Hello! I'm PharmaBot, your AI pharmacy assistant. I can help you:\n• Order over-the-counter medicines\n• Check medicine availability and prices\n• View your order history\n\nJust tell me what you need! For example: *\"I need 2 strips of Paracetamol\"*",
    action: null,
    order_id: null,
    timestamp: new Date(),
};

export default function ChatInterface({ userId }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [payingOrderId, setPayingOrderId] = useState<number | null>(null);
    const [isListening, setIsListening] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom on new messages
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const toggleListening = () => {
        if (isListening) return;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Your browser does not support voice input.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onstart = () => setIsListening(true);

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
            const transcript = Array.from(event.results)
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                .map((result: any) => result[0].transcript)
                .join('');

            setInput(transcript);

            if (event.results[0].isFinal) {
                setIsListening(false);
            }
        };

        recognition.onerror = () => setIsListening(false);
        recognition.onend = () => setIsListening(false);

        try {
            recognition.start();
        } catch (e) {
            console.error("Speech recognition error:", e);
            setIsListening(false);
        }
    };

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;

        // Add user message immediately
        const userMsg: Message = {
            role: "user",
            content: text,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setLoading(true);

        try {
            const res: AgentChatResponse = await sendAgentMessage(userId, text);
            const agentMsg: Message = {
                role: "agent",
                content: res.response,
                action: res.action,
                order_id: res.order_id,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, agentMsg]);
        } catch (err: unknown) {
            const message = getErrorMessage(err);
            const errMsg: Message = {
                role: "agent",
                content: `Sorry, I encountered an error: ${message}. Please try again.`,
                action: "error",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errMsg]);
        } finally {
            setLoading(false);
        }
    };

    /** Handle Enter key (without shift) to send message */
    const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    /** Trigger dummy payment for an order */
    const handlePayment = async (orderId: number, amount: number) => {
        setPayingOrderId(orderId);
        try {
            const res = await processPayment(orderId, amount);
            const payMsg: Message = {
                role: "agent",
                content: `💳 ${res.message}\n\n🧾 Transaction ID: \`${res.transaction_id}\``,
                action: "order_created",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, payMsg]);
        } catch {
            const errMsg: Message = {
                role: "agent",
                content: "Payment processing failed. Please try again.",
                action: "error",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errMsg]);
        } finally {
            setPayingOrderId(null);
        }
    };

    const quickPrompts = [
        "I need 2 Paracetamol strips",
        "Do you have Cough Syrup?",
        "Show my order history",
        "I need Amoxicillin",
    ];

    return (
        <div className="flex flex-col h-full">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        <div className="flex flex-col gap-1 max-w-[78%]">
                            {/* Message bubble */}
                            <div className={msg.role === "user" ? "chat-bubble-user" : "chat-bubble-agent"}>
                                <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                            </div>

                            {/* Action badge */}
                            {msg.action && ACTION_BADGE[msg.action] && (
                                <span className={`${ACTION_BADGE[msg.action].class} w-fit`}>
                                    {ACTION_BADGE[msg.action].label}
                                </span>
                            )}

                            {/* Pay Now button for newly created orders */}
                            {msg.action === "order_created" && msg.order_id && (
                                <button
                                    onClick={() => handlePayment(msg.order_id!, 0)}
                                    disabled={payingOrderId === msg.order_id}
                                    className="btn-primary text-xs py-1.5 px-3 w-fit mt-1"
                                >
                                    {payingOrderId === msg.order_id ? "Processing..." : "💳 Pay Now"}
                                </button>
                            )}

                            {/* Timestamp */}
                            <span className="text-xs text-slate-500 px-1">
                                {msg.timestamp.toLocaleTimeString()}
                            </span>
                        </div>
                    </div>
                ))}

                {/* Typing indicator while agent is responding */}
                {loading && (
                    <div className="flex justify-start">
                        <div className="chat-bubble-agent">
                            <div className="typing-dots flex items-center gap-0.5 h-5">
                                <span /><span /><span />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Quick Prompt Chips */}
            <div className="px-4 pb-2 flex gap-2 flex-wrap">
                {quickPrompts.map((prompt) => (
                    <button
                        key={prompt}
                        onClick={() => { setInput(prompt); }}
                        className="text-xs px-3 py-1.5 rounded-full border border-black/10 dark:border-white/10 text-slate-600 dark:text-slate-400 hover:bg-black/10 dark:bg-white/10 hover:text-[var(--text-color)] transition-colors"
                    >
                        {prompt}
                    </button>
                ))}
            </div>

            {/* Input Bar */}
            <div className="p-4 border-t border-black/10 dark:border-white/10">
                <div className="flex gap-3 items-end">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask PharmaBot... (e.g. 'I need 10 Paracetamol tablets')"
                        rows={1}
                        className="input-glass resize-none flex-1"
                        style={{ minHeight: "48px", maxHeight: "120px" }}
                        disabled={loading}
                    />
                    <button
                        onClick={toggleListening}
                        type="button"
                        className={`p-3 rounded-xl transition-all ${isListening
                                ? "bg-red-500/20 text-red-500 hover:bg-red-500/30 animate-pulse border border-red-500/30"
                                : "bg-black/5 dark:bg-white/5 text-slate-600 dark:text-slate-400 hover:text-[var(--text-color)] hover:bg-black/10 dark:bg-white/10 border border-black/10 dark:border-white/10"
                            }`}
                        title="Voice Input"
                    >
                        <Mic size={20} className={isListening ? "animate-bounce" : ""} />
                    </button>
                    <button
                        onClick={sendMessage}
                        disabled={loading || !input.trim()}
                        className="btn-primary shrink-0 flex items-center justify-center gap-2"
                        style={{ padding: "12px 20px" }}
                    >
                        {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                    </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                    Press Enter to send · Shift+Enter for newline
                </p>
            </div>
        </div>
    );
}
