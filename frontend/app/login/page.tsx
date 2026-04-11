"use client";

import { useState, FormEvent, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { loginUser } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import GlassCard from "@/components/GlassCard";

export default function LoginPage() {
    const router = useRouter();
    const [form, setForm] = useState({ email: "", password: "" });
    const [selectedRole, setSelectedRole] = useState("user");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleRoleSelect = (role: string) => {
        setSelectedRole(role);
        setForm({ email: "", password: "" });
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            const res = await loginUser(form);
            saveAuth(res.access_token, {
                id: res.user.id,
                name: res.user.name,
                email: res.user.email,
                role: res.user.role as "user" | "admin" | "pharmacist",
            });

            // Route correctly based on role
            if (res.user.role === "admin") {
                router.push("/admin");
            } else if (res.user.role === "pharmacist") {
                router.push("/pharmacist");
            } else {
                router.push("/chat"); // User goes to chat by default
            }
        } catch (err: unknown) {
            let message = "Login failed. Please try again.";
            if (err instanceof Error && err.message) message = err.message;
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center px-4">
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
                <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
            </div>

            <div className="w-full max-w-md relative z-10 pt-10 pb-10">
                <div className="mb-6">
                    <Link 
                        href="/" 
                        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-indigo-400 transition-colors bg-white/5 px-4 py-2 rounded-full border border-white/10"
                    >
                        <ArrowLeft size={16} />
                        Back to Home
                    </Link>
                </div>

                <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-3xl mb-4 shadow-lg">
                        💉
                    </div>
                    <h1 className="text-3xl font-bold gradient-text">PharmaAgent AI</h1>
                    <p className="text-slate-600 dark:text-slate-400 mt-2 text-sm">Your AI-powered pharmacy assistant</p>
                </div>

                <GlassCard>
                    <h2 className="text-xl font-bold text-[var(--text-color)] mb-2 text-center">Select Role to Login</h2>

                    {/* Role Selector Tabs */}
                    <div className="flex gap-2 p-1 bg-white dark:bg-slate-800/50 rounded-lg mb-6 border border-white/5">
                        {["user", "admin", "pharmacist"].map((role) => (
                            <button
                                key={role}
                                type="button"
                                onClick={() => handleRoleSelect(role)}
                                className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all capitalize ${selectedRole === role
                                    ? "bg-indigo-600 text-[var(--text-color)] shadow-md shadow-indigo-900/20"
                                    : "text-slate-600 dark:text-slate-400 hover:text-[var(--text-color)] hover:bg-black/5 dark:bg-white/5"
                                    }`}
                            >
                                {role}
                            </button>
                        ))}
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
                        <div>
                            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5" htmlFor="email">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                required
                                placeholder="you@example.com"
                                className="input-glass w-full"
                                value={form.email}
                                onChange={(e) => setForm({ ...form, email: e.target.value })}
                            />
                        </div>

                        <div>
                            <label className="block text-sm text-slate-600 dark:text-slate-400 mb-1.5" htmlFor="password">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                required
                                placeholder="••••••••"
                                className="input-glass w-full"
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
                                    Signing in as {selectedRole}...
                                </span>
                            ) : (
                                `Sign In as ${selectedRole.charAt(0).toUpperCase() + selectedRole.slice(1)}`
                            )}
                        </button>
                    </form>

                    {selectedRole !== "admin" && (
                        <p className="text-center text-slate-600 dark:text-slate-400 text-sm mt-6">
                            Don&apos;t have an account?{" "}
                            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
                                Register here
                            </Link>
                        </p>
                    )}
                </GlassCard>
            </div>
        </div>
    );
}
