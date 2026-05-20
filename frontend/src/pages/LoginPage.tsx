"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, ChevronDown, Chrome, Eye, EyeOff } from "lucide-react";
import { signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { fetchMyProfile, registerUser } from "@/lib/api";
import { saveUserLocal } from "@/lib/auth";
import GlassPanel from "@/components/GlassPanel";

export default function LoginPage() {
    const router = useRouter();
    const [form, setForm] = useState({ email: "", password: "" });
    const [selectedRole, setSelectedRole] = useState("user");
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleRoleSelect = (role: string) => {
        setSelectedRole(role);
        setForm({ email: "", password: "" });
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);

        try {
            // 1. Sign in with Firebase Auth
            const userCredential = await signInWithEmailAndPassword(auth, form.email, form.password);
            
            // Wait for auth observer to set token internally
            const token = await userCredential.user.getIdToken();
            
            // 2. Fetch the user profile from our backend (which contains the Role)
            const profile = await fetchMyProfile(token);
            
            saveUserLocal({
                id: profile.id,
                name: profile.name,
                email: profile.email,
                role: profile.role as "user" | "admin" | "pharmacist",
            });

            // Route correctly based on role
            if (profile.role === "admin") {
                router.push("/admin");
            } else if (profile.role === "pharmacist") {
                router.push("/pharmacist");
            } else {
                router.push("/chat");
            }
        } catch (err: any) {
            let message = "Login failed. Please check your credentials.";
            if (err.code === "auth/invalid-credential") {
                 message = "Invalid email or password.";
            } else if (err.message) {
                 message = err.message;
            }
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setError("");
        setLoading(true);
        try {
            const provider = new GoogleAuthProvider();
            const userCredential = await signInWithPopup(auth, provider);
            
            // Force token update
            const token = await userCredential.user.getIdToken(true);
            
            let profile;
            try {
                // Check if user profile already exists
                profile = await fetchMyProfile(token);
            } catch (profileErr) {
                // If profile doesn't exist, auto-register on the backend with "user" role
                profile = await registerUser({
                    name: userCredential.user.displayName || "Google User",
                    email: userCredential.user.email || "",
                    password: "google-auth-placeholder-password",
                    role: "user"
                });
            }

            saveUserLocal({
                id: profile.id,
                name: profile.name,
                email: profile.email,
                role: profile.role as "user" | "admin" | "pharmacist",
            });

            if (profile.role === "admin") {
                router.push("/admin");
            } else if (profile.role === "pharmacist") {
                router.push("/pharmacist");
            } else {
                router.push("/chat");
            }
        } catch (err: any) {
            let message = "Google Sign-In failed.";
            if (err.message) {
                message = err.message;
            }
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

                <GlassPanel variant="modal">
                    <h2 className="text-xl font-bold text-[var(--text-color)] mb-4 text-center">Sign In</h2>

                    {/* Role Dropdown Selector */}
                    <div className="relative mb-6">
                        <label className="block text-xs text-slate-400 uppercase tracking-wider mb-2 font-medium">
                            Select Role
                        </label>
                        <button
                            type="button"
                            onClick={() => setDropdownOpen(!dropdownOpen)}
                            className="w-full input-glass flex items-center justify-between py-2.5 px-4 rounded-lg capitalize border border-white/10 hover:border-indigo-500/50 transition-all text-left bg-slate-900/40 text-slate-200"
                        >
                            <span>{selectedRole}</span>
                            <ChevronDown size={18} className={`transform transition-transform duration-300 ${dropdownOpen ? 'rotate-180' : ''}`} />
                        </button>
                        
                        {dropdownOpen && (
                            <>
                                <div className="fixed inset-0 z-20" onClick={() => setDropdownOpen(false)} />
                                <div className="absolute left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-white/10 rounded-xl shadow-2xl overflow-hidden z-30 transition-all animate-in fade-in slide-in-from-top-2 duration-300">
                                    {["user", "admin", "pharmacist"].map((role) => (
                                        <button
                                            key={role}
                                            type="button"
                                            onClick={() => {
                                                handleRoleSelect(role);
                                                setDropdownOpen(false);
                                            }}
                                            className={`w-full text-left px-4 py-3 text-sm transition-colors capitalize ${selectedRole === role 
                                                ? "bg-indigo-600 text-white font-medium" 
                                                : "text-slate-300 hover:bg-white/5 hover:text-white"
                                            }`}
                                        >
                                            {role}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
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
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors"
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

                    {/* Google Login Separator */}
                    <div className="relative my-6 flex items-center justify-center">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-white/10"></div>
                        </div>
                        <span className="relative bg-transparent px-3 text-xs text-slate-500 uppercase tracking-wider font-semibold z-10">
                            Or continue with
                        </span>
                    </div>

                    {/* Google Sign In Button */}
                    <button
                        type="button"
                        onClick={handleGoogleSignIn}
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-3 bg-white/5 hover:bg-white/10 border border-white/15 hover:border-white/20 text-slate-200 py-3 rounded-xl transition-all duration-300 font-semibold shadow-md active:scale-[0.98]"
                    >
                        <Chrome size={18} className="text-indigo-400" />
                        Sign in with Google
                    </button>

                    {selectedRole !== "admin" && (
                        <p className="text-center text-slate-600 dark:text-slate-400 text-sm mt-6">
                            Don&apos;t have an account?{" "}
                            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-medium">
                                Register here
                            </Link>
                        </p>
                    )}
                </GlassPanel>
            </div>
        </div>
    );
}
