"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, clearAuth, type User } from "@/lib/auth";
import { LogOut } from "lucide-react";

export default function Sidebar() {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        setTimeout(() => {
            setUser(getUser());
        }, 0);
    }, []);

    const isActive = (path: string) => pathname === path;

    const handleLogout = () => {
        clearAuth();
        router.push("/login");
    };

    // Define sidebar links by role
    const getLinks = () => {
        const role = user?.role || "user";

        if (role === "admin") {
            return [
                { href: "/dashboard", label: "Dashboard", icon: "📊" },
                { href: "/admin", label: "Inventory & Orders", icon: "📦" },
                { href: "/analytics", label: "Analytics", icon: "📈" },
            ];
        }

        if (role === "pharmacist") {
            return [
                { href: "/pharmacist", label: "Prescriptions", icon: "📋" },
                { href: "/refill-alerts", label: "Refill Alerts", icon: "🔔" },
            ];
        }

        // Default: User
        return [
            { href: "/chat", label: "Chat", icon: "💬" },
            { href: "/dashboard", label: "My Orders", icon: "📦" },
            { href: "/vision", label: "Vision", icon: "📸" },
            { href: "/voice", label: "Voice", icon: "🎙️" },
            { href: "/symptom", label: "Symptom Check", icon: "🩺" },
            { href: "/settings", label: "Settings", icon: "⚙️" },
        ];
    };

    const links = getLinks();

    return (
        <aside className="w-64 border-r border-[var(--glass-border)] bg-[var(--glass-bg)] backdrop-blur-xl hidden md:flex flex-col shrink-0">
            <div className="p-6">
                <Link href={user?.role === "admin" ? "/admin" : user?.role === "pharmacist" ? "/pharmacist" : "/dashboard"} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg shadow-lg">
                        💊
                    </div>
                    <span className="font-bold text-lg gradient-text tracking-tight">
                        PharmaAgent
                    </span>
                </Link>
            </div>

            <div className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
                {links.map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive(link.href)
                            ? "bg-indigo-600/20 text-indigo-500 dark:text-indigo-300 border border-indigo-500/20 shadow-inner"
                            : "text-slate-600 dark:text-slate-600 dark:text-slate-400 hover:text-black dark:hover:text-[var(--text-color)] hover:bg-black/5 dark:hover:bg-black/5 dark:bg-white/5"
                            }`}
                    >
                        <span className="text-xl">{link.icon}</span>
                        {link.label}
                    </Link>
                ))}
            </div>

            {user && (
                <div className="p-4 space-y-3">
                    <div className="p-3 rounded-2xl bg-black/5 dark:bg-black/5 dark:bg-white/5 border border-black/10 dark:border-black/10 dark:border-white/10 flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold text-[var(--text-color)] shadow-md shrink-0">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[var(--text-color)] truncate">{user.name}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-600 dark:text-slate-400 uppercase tracking-wider">{user.role}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-600 dark:text-slate-400 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-500/10 transition-all"
                    >
                        <LogOut size={16} />
                        Sign Out
                    </button>
                </div>
            )}
        </aside>
    );
}
