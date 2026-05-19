"use client";

/**
 * components/Navbar.tsx — Top navigation bar.
 *
 * Shows pharmacy app logo, navigation links, and user info.
 * Highlights the active page. Shows admin link only for admin users.
 * Handles logout by clearing localStorage and redirecting to /login.
 */

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, clearAuth, type User } from "@/lib/auth";

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);

    // Load user from localStorage on mount
    useEffect(() => {
        setTimeout(() => {
            setUser(getUser());
        }, 0);
    }, []);

    const handleLogout = () => {
        clearAuth();
        router.push("/login");
    };

    /** Determine if a nav link is currently active */
    const isActive = (path: string) => pathname === path;

    const navLinks = [
        { href: "/dashboard", label: "Dashboard", icon: "🏠", roles: null },
        { href: "/chat", label: "Chat", icon: "💊", roles: null },
        { href: "/voice", label: "Voice", icon: "🎙", roles: null },
        { href: "/vision", label: "Vision", icon: "📸", roles: null },
        { href: "/symptom", label: "Symptom", icon: "🩺", roles: null },
        { href: "/refill-alerts", label: "Refills", icon: "🔔", roles: null },
        {
            href: "/pharmacist",
            label: "Pharmacist",
            icon: "👨‍⚕️",
            roles: ["pharmacist", "admin"],
        },
        {
            href: "/analytics",
            label: "Analytics",
            icon: "📈",
            roles: ["admin"],
        },
        {
            href: "/admin",
            label: "Admin",
            icon: "🛠",
            roles: ["admin"],
        },
        { href: "/settings", label: "Settings", icon: "⚙️", roles: null },
    ].filter((link) => !link.roles || (user?.role && link.roles.includes(user.role)));

    return (
        <nav className="navbar sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
                {/* Brand Logo */}
                <Link href="/dashboard" className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg">
                        💉
                    </div>
                    <span className="font-bold text-lg gradient-text hidden sm:block">
                        PharmaAgent AI
                    </span>
                </Link>

                {/* Nav Links */}
                <div className="flex items-center gap-1">
                    {navLinks.map((link) => (
                        <Link
                            key={link.href}
                            href={link.href}
                            className={`
                flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${isActive(link.href)
                                    ? "bg-indigo-600/40 text-indigo-200 border border-indigo-500/40"
                                    : "text-slate-600 dark:text-slate-400 hover:text-[var(--text-color)] hover:bg-black/10 dark:bg-white/10"
                                }
              `}
                        >
                            <span>{link.icon}</span>
                            <span className="hidden sm:block">{link.label}</span>
                        </Link>
                    ))}
                </div>

                {/* User Info + Logout */}
                <div className="flex items-center gap-3">
                    {user && (
                        <div className="hidden sm:flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-xs font-bold text-[var(--text-color)]">
                                {user.name[0].toUpperCase()}
                            </div>
                            <span className="text-sm text-slate-700 dark:text-slate-300">{user.name}</span>
                            {user.role === "admin" && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                    Admin
                                </span>
                            )}
                            {user.role === "pharmacist" && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 border border-violet-500/30">
                                    Pharmacist
                                </span>
                            )}
                        </div>
                    )}
                    <button
                        onClick={handleLogout}
                        className="btn-secondary text-sm py-2 px-3"
                    >
                        Logout
                    </button>
                </div>
            </div>
        </nav>
    );
}
