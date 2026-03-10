"use client";

/**
 * app/register/page.tsx — Registration page.
 *
 * Features:
 * - Name, email, password form
 * - Calls POST /auth/register
 * - Auto-login: saves JWT + user, redirects to /dashboard
 */

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerUser } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import GlassCard from "@/components/GlassCard";

export default function RegisterPage() {
    const router = useRouter();
    const [form, setForm] = useState({ name: "", email: "", password: "" });
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        if (form.password.length < 6) {
            setError("Password must be at least 6 characters.");
            return;
        }
        setLoading(true);
        try {
            const res = await registerUser(form);
            saveAuth(res.access_token, {
                id: res.user.id,
                name: res.user.name,
                email: res.user.email,
                role: res.user.role as "user" | "admin",
            });
            router.push("/dashboard");
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Registration failed.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
            </div>

            <div className="w-full max-w-md relative z-10">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-3xl mb-4 shadow-lg">
                        💉
                    </div>
                    <h1 className="text-3xl font-bold gradient-text">PharmaAgent AI</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2 text-sm">Create your pharmacy account</p>
                </div>

                <GlassCard>
                    <h2 className="text-xl font-bold text-[var(--text-color)] mb-6">Create Account</h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5" htmlFor="name">Full Name</label>
                            <input
                                id="name"
                                type="text"
                                required
                                placeholder="John Doe"
                                className="input-glass"
                                value={form.name}
                                onChange={(e) => setForm({ ...form, name: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5" htmlFor="email">Email Address</label>
                            <input
                                id="email"
                                type="email"
                                required
                                placeholder="you@example.com"
                                className="input-glass"
                                value={form.email}
                                onChange={(e) => setForm({ ...form, email: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5" htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                required
                                placeholder="Min 6 characters"
                                className="input-glass"
                                value={form.password}
                                onChange={(e) => setForm({ ...form, password: e.target.value })}
                            />
                        </div>

                        {error && (
                            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                                ⚠️ {error}
                            </div>
                        )}

                        <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <span className="spinner w-4 h-4 border-2" />
                                    Creating account...
                                </span>
                            ) : "Create Account"}
                        </button>
                    </form>

                    <p className="text-center text-slate-600 dark:text-slate-400 text-sm mt-6">
                        Already have an account?{" "}
                        <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
                            Sign in
                        </Link>
                    </p>
                </GlassCard>
            </div>
        </div>
    );
}
