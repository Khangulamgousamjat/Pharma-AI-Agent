"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, clearAuth, type User } from "@/lib/auth";
import { useTheme } from "@/components/ThemeProvider";
import { Sun, Moon, LogOut } from "lucide-react";
import GlassPanel from "@/components/GlassPanel";

const PAGE_TITLES: Record<string, string> = {
    "/":             "Home",
    "/dashboard":    "Dashboard",
    "/chat":         "Chat",
    "/admin":        "Admin",
    "/analytics":    "Analytics",
    "/voice":        "Voice",
    "/vision":       "Vision",
    "/symptom":      "Symptom Checker",
    "/settings":     "Settings",
    "/pharmacist":   "Pharmacist",
    "/register":     "Register",
    "/login":        "Login",
    "/refill-alerts":"Refill Alerts",
};

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        setTimeout(() => { setUser(getUser()); }, 0);
    }, []);

    const handleLogout = async () => {
        await clearAuth();
        router.push("/login");
    };

    const pageTitle =
        PAGE_TITLES[pathname] ??
        pathname.slice(1).charAt(0).toUpperCase() + pathname.slice(2);

    return (
        <GlassPanel
            variant="navbar"
            className="sticky top-0 z-50 flex items-center justify-between px-4 h-16 md:px-6"
            style={{ position: "sticky", top: 0, zIndex: 50, width: "100%" }}
        >
            {/* Left — page title / mobile logo */}
            <div className="flex items-center gap-3">
                <div className="md:hidden flex items-center">
                    <Link
                        href="/dashboard"
                        className="w-8 h-8 rounded-xl flex items-center justify-center text-lg shadow-lg"
                        style={{
                            background: "linear-gradient(135deg, var(--color-primary), #9333ea)",
                            boxShadow: "0 4px 12px rgba(124,58,237,0.4), inset 0 1px 0 rgba(255,255,255,0.3)",
                        }}
                    >
                        💊
                    </Link>
                </div>
                <h1
                    className="font-semibold hidden md:block text-base"
                    style={{ color: "var(--text-primary-light)" }}
                >
                    {pageTitle}
                </h1>
            </div>

            {/* Right — theme toggle + user */}
            <div className="flex items-center gap-2">
                {mounted && (
                    <button
                        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                        className="p-2 rounded-full transition-all duration-200"
                        style={{
                            background: "rgba(124,58,237,0.08)",
                            border: "1px solid rgba(167,139,250,0.2)",
                            color: "var(--color-primary)",
                        }}
                        aria-label="Toggle theme"
                    >
                        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                )}

                {user && (
                    <div className="flex items-center gap-2">
                        <div className="text-right hidden sm:block">
                            <p
                                className="text-sm font-medium leading-tight"
                                style={{ color: "var(--text-primary-light)" }}
                            >
                                {user.name}
                            </p>
                            <p
                                className="text-xs capitalize leading-tight font-semibold"
                                style={{ color: "var(--color-primary-light)" }}
                            >
                                {user.role}
                            </p>
                        </div>
                        <div
                            className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-md"
                            style={{
                                background: "linear-gradient(135deg, var(--color-primary), #9333ea)",
                                boxShadow: "0 3px 10px rgba(124,58,237,0.4), inset 0 1px 0 rgba(255,255,255,0.3)",
                            }}
                        >
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 rounded-full transition-all duration-200 md:hidden"
                            style={{
                                background: "rgba(239,68,68,0.08)",
                                border: "1px solid rgba(239,68,68,0.15)",
                                color: "#f87171",
                            }}
                            aria-label="Logout"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                )}
            </div>
        </GlassPanel>
    );
}
