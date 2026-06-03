"use client";

import { useState, FormEvent, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Eye, EyeOff } from "lucide-react";
import { loginUser } from "@/lib/api";
import { saveAuth } from "@/lib/auth";
import { auth, googleProvider } from "@/lib/firebase";
import { signInWithEmailAndPassword, signInWithPopup } from "firebase/auth";
import GlassCard from "@/components/GlassCard";

const GoogleIcon = () => (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
        <path
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            fill="#4285F4"
        />
        <path
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            fill="#34A853"
        />
        <path
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            fill="#FBBC05"
        />
        <path
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            fill="#EA4335"
        />
    </svg>
);

export default function LoginPage() {
    const router = useRouter();
    // Default pre-fill to user credentials
    const [form, setForm] = useState({ email: "john@example.com", password: "user123" });
    const [selectedRole, setSelectedRole] = useState("user");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleRoleSelect = (role: string) => {
        setSelectedRole(role);
        if (role === "admin") {
            setForm({ email: "admin@gmail.com", password: "Kingkhan@12" });
        } else if (role === "pharmacist") {
            setForm({ email: "pharmacist@pharmaagent.com", password: "pharma123" });
        } else {
            setForm({ email: "john@example.com", password: "user123" });
        }
    };

    const handleGoogleLogin = async () => {
        setError("");
        setLoading(true);
        try {
            const result = await signInWithPopup(auth, googleProvider);
            const user = result.user;
            const token = await user.getIdToken();
            saveAuth(token, {
                id: user.uid,
                name: user.displayName || "Google User",
                email: user.email || "",
                role: "user",
            });
            router.push("/chat");
        } catch (err: unknown) {
            let message = "Google Sign-In failed.";
            if (err instanceof Error && err.message) message = err.message;
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            // 1. Try Firebase Auth first
            try {
                const userCredential = await signInWithEmailAndPassword(auth, form.email, form.password);
                const user = userCredential.user;
                const token = await user.getIdToken();
                saveAuth(token, {
                    id: user.uid,
                    name: user.displayName || user.email?.split("@")[0] || "User",
                    email: user.email || "",
                    role: selectedRole as "user" | "admin" | "pharmacist",
                });

                // Route correctly based on role
                if (selectedRole === "admin") {
                    router.push("/admin");
                } else if (selectedRole === "pharmacist") {
                    router.push("/pharmacist");
                } else {
                    router.push("/chat");
                }
                return;
            } catch (fbErr: any) {
                console.log("Firebase login failed, trying local DB backend:", fbErr.message);
                if (fbErr.code === "auth/wrong-password" || fbErr.code === "auth/invalid-credential") {
                    throw new Error("Invalid credentials (Firebase).");
                }
            }

            // 2. Fallback to local Backend API (e.g. for offline seeded database users)
            const res = await loginUser(form);
            saveAuth(res.access_token, {
                id: res.user.id,
                name: res.user.name,
                email: res.user.email,
                role: res.user.role as "user" | "admin" | "pharmacist",
            });

            if (res.user.role === "admin") {
                router.push("/admin");
            } else if (res.user.role === "pharmacist") {
                router.push("/pharmacist");
            } else {
                router.push("/chat");
            }
        } catch (err: unknown) {
            let message = "Login failed. Please verify credentials.";
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

                <div className="text-center mb-6 filter drop-shadow-[0_2px_12px_rgba(0,0,0,0.85)]">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 text-3xl mb-4 shadow-lg">
                        💉
                    </div>
                    <h1 className="text-3xl font-bold gradient-text">PharmaAgent AI</h1>
                    <p className="text-slate-200 font-semibold mt-2 text-sm">Your AI-powered pharmacy assistant</p>
                </div>

                <GlassCard>
                    {/* Role Selector Dropdown (Shutter) */}
                    <div className="mb-6">
                        <label className="block text-sm text-slate-200 font-semibold mb-2" htmlFor="role-select">
                            Select Role to Login
                        </label>
                        <div className="relative">
                            <select
                                id="role-select"
                                value={selectedRole}
                                onChange={(e) => handleRoleSelect(e.target.value)}
                                className="input-glass w-full capitalize appearance-none pr-10 cursor-pointer bg-[#0d0a21] border border-white/10 text-[var(--text-color)] rounded-xl py-3 px-4 focus:border-indigo-500 focus:outline-none transition-all shadow-md"
                            >
                                <option value="user" className="bg-[#0a071b] text-slate-200">User</option>
                                <option value="admin" className="bg-[#0a071b] text-slate-200">Admin</option>
                                <option value="pharmacist" className="bg-[#0a071b] text-slate-200">Pharmacist</option>
                            </select>
                            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-indigo-400">
                                <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                                    <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/>
                                </svg>
                            </div>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4" autoComplete="off">
                        <div>
                            <label className="block text-sm text-slate-200 font-semibold mb-1.5" htmlFor="email">
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
                            <label className="block text-sm text-slate-200 font-semibold mb-1.5" htmlFor="password">
                                Password
                            </label>
                            <div className="relative">
                                <input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    required
                                    placeholder="••••••••"
                                    className="input-glass w-full pr-10"
                                    value={form.password}
                                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[var(--text-color)] transition-colors"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
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

                    {/* Google Login Section */}
                    <div className="mt-6">
                        <div className="relative flex items-center justify-center mb-4">
                            <div className="absolute w-full border-t border-slate-700/50" />
                            <span className="relative z-10 px-3 bg-[#0d0a21] text-xs text-slate-500 font-medium uppercase tracking-wider">
                                Or Continue With
                            </span>
                        </div>

                        <button
                            type="button"
                            onClick={handleGoogleLogin}
                            disabled={loading}
                            className="flex items-center justify-center gap-3 w-full py-3 px-4 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 active:bg-white/15 text-sm font-semibold transition-all hover:scale-[1.02] shadow-lg shadow-black/30"
                        >
                            <GoogleIcon />
                            Sign in with Google
                        </button>
                    </div>

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
