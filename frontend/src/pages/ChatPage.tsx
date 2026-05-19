"use client";

/**
 * app/chat/page.tsx — Chat page wrapper.
 *
 * Loads the logged-in user and renders ChatInterface.
 * Redirects to /login if not authenticated.
 */

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import GlassCard from "@/components/GlassCard";
import ChatInterface from "@/components/ChatInterface";
import { getUser, type User } from "@/lib/auth";

export default function ChatPage() {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        const u = getUser();
        if (!u) {
            router.push("/login");
            return;
        }
        if (u.role === "admin") {
            router.push("/admin");
            return;
        }
        setUser(u);
        setMounted(true);
    }, []);

    if (!mounted || !user) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col">
            <div className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-6 flex flex-col">
                {/* Page Header */}
                <div className="mb-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-[var(--text-color)]">💊 PharmaBot Chat</h1>
                        <p className="text-slate-600 dark:text-slate-400 text-sm mt-0.5">
                            AI-powered pharmacy assistant with prescription safety enforcement
                        </p>
                    </div>
                    <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                        <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-emerald-400 text-xs font-medium">PharmaBot Online</span>
                    </div>
                </div>

                {/* Chat Window */}
                <div className="flex-1" style={{ minHeight: "500px" }}>
                    <GlassCard hover={false} padding="none" className="h-full flex flex-col">
                        <ChatInterface userId={user.id} />
                    </GlassCard>
                </div>

                {/* Safety Notice */}
                <div className="mt-3 p-3 rounded-xl bg-amber-500/5 border border-amber-500/15 flex items-start gap-2">
                    <span className="text-amber-400 text-lg mt-0.5">⚠️</span>
                    <p className="text-xs text-amber-300/80">
                        <span className="font-semibold">Safety Notice:</span> Prescription medicines are automatically blocked.
                        OTC medicines can be ordered directly. Always consult a doctor for prescription medications.
                    </p>
                </div>
            </div>
        </div>
    );
}
