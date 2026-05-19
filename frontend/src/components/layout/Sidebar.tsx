"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, clearAuth, type User } from "@/lib/auth";
import { LogOut } from "lucide-react";
import GlassPanel from "@/components/GlassPanel";

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

    const handleLogout = async () => {
        await clearAuth();
        router.push("/login");
    };

    const getLinks = () => {
        const role = user?.role || "user";

        if (role === "admin") {
            return [
                { href: "/dashboard", label: "Dashboard",          icon: "📊" },
                { href: "/admin",     label: "Inventory & Orders", icon: "📦" },
                { href: "/analytics", label: "Analytics",          icon: "📈" },
            ];
        }

        if (role === "pharmacist") {
            return [
                { href: "/pharmacist",    label: "Prescriptions", icon: "📋" },
                { href: "/refill-alerts", label: "Refill Alerts",  icon: "🔔" },
            ];
        }

        return [
            { href: "/chat",          label: "Chat",         icon: "💬" },
            { href: "/dashboard",     label: "My Orders",    icon: "📦" },
            { href: "/vision",        label: "Vision",       icon: "📸" },
            { href: "/voice",         label: "Voice",        icon: "🎙️" },
            { href: "/symptom",       label: "Symptom Check",icon: "🩺" },
            { href: "/settings",      label: "Settings",     icon: "⚙️" },
        ];
    };

    const links = getLinks();

    return (
        <GlassPanel
            variant="sidebar"
            className="w-64 hidden md:flex flex-col shrink-0 relative"
            style={{ height: "100%" }}
        >
            {/* Logo */}
            <div className="p-6 border-b border-[rgba(167,139,250,0.12)]">
                <Link
                    href={
                        user?.role === "admin"
                            ? "/admin"
                            : user?.role === "pharmacist"
                            ? "/pharmacist"
                            : "/dashboard"
                    }
                    className="flex items-center gap-3"
                >
                    <div
                        className="w-9 h-9 rounded-xl flex items-center justify-center text-lg shadow-lg"
                        style={{
                            background: "linear-gradient(135deg, var(--color-primary), #9333ea)",
                            boxShadow: "0 4px 12px rgba(124,58,237,0.4), inset 0 1px 0 rgba(255,255,255,0.3)",
                        }}
                    >
                        💊
                    </div>
                    <span className="font-bold text-lg gradient-text tracking-tight">
                        PharmaAgent
                    </span>
                </Link>
            </div>

            {/* Nav Links */}
            <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
                {links.map((link) => (
                    <Link
                        key={link.href}
                        href={link.href}
                        className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                        style={
                            isActive(link.href)
                                ? {
                                    background: "rgba(124,58,237,0.15)",
                                    color: "var(--color-primary-light)",
                                    border: "1px solid rgba(124,58,237,0.25)",
                                    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.1), 0 2px 8px rgba(124,58,237,0.12)",
                                  }
                                : {
                                    color: "var(--text-secondary-light)",
                                    border: "1px solid transparent",
                                  }
                        }
                    >
                        <span className="text-xl">{link.icon}</span>
                        {link.label}
                    </Link>
                ))}
            </div>

            {/* User card + logout */}
            {user && (
                <div className="p-4 border-t border-[rgba(167,139,250,0.12)] space-y-3">
                    <div
                        className="p-3 rounded-2xl flex items-center gap-3"
                        style={{
                            background: "rgba(124,58,237,0.08)",
                            border: "1px solid rgba(167,139,250,0.15)",
                        }}
                    >
                        <div
                            className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-md shrink-0"
                            style={{ background: "linear-gradient(135deg, var(--color-primary), #9333ea)" }}
                        >
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-[var(--text-primary-light)] dark:text-[var(--text-primary-dark)] truncate">
                                {user.name}
                            </p>
                            <p
                                className="text-xs uppercase tracking-wider font-semibold"
                                style={{ color: "var(--color-primary-light)" }}
                            >
                                {user.role}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200"
                        style={{ color: "var(--text-muted-light)" }}
                        onMouseEnter={(e) => {
                            (e.currentTarget as HTMLButtonElement).style.color = "#f87171";
                            (e.currentTarget as HTMLButtonElement).style.background = "rgba(239,68,68,0.08)";
                        }}
                        onMouseLeave={(e) => {
                            (e.currentTarget as HTMLButtonElement).style.color = "var(--text-muted-light)";
                            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
                        }}
                    >
                        <LogOut size={16} />
                        Sign Out
                    </button>
                </div>
            )}
        </GlassPanel>
    );
}
