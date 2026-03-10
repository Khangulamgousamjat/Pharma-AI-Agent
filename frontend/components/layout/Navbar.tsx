"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, clearAuth, type User } from "@/lib/auth";
import { useTheme } from "next-themes";
import { Sun, Moon, LogOut } from "lucide-react";

const PAGE_TITLES: Record<string, string> = {
    "/": "Home",
    "/dashboard": "Dashboard",
    "/chat": "Chat",
    "/admin": "Admin",
    "/analytics": "Analytics",
    "/voice": "Voice",
    "/vision": "Vision",
    "/symptom": "Symptom Checker",
    "/settings": "Settings",
    "/pharmacist": "Pharmacist",
    "/register": "Register",
    "/login": "Login",
    "/refill-alerts": "Refill Alerts",
};

export default function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const { theme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        setTimeout(() => {
            setUser(getUser());
        }, 0);
    }, []);

    const handleLogout = () => {
        clearAuth();
        router.push("/login");
    };

    const pageTitle = PAGE_TITLES[pathname] ?? pathname.slice(1).charAt(0).toUpperCase() + pathname.slice(2);

    return (
        <header className="sticky top-0 z-50 bg-[var(--glass-bg)] backdrop-blur-xl border-b border-[var(--glass-border)] flex items-center justify-between px-4 h-16 md:px-6">
            <div className="flex items-center gap-3">
                <div className="md:hidden flex items-center">
                    <Link href="/dashboard" className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-lg shadow-lg">
                        💊
                    </Link>
                </div>
                <h1 className="text-[var(--text-color)] font-semibold hidden md:block">
                    {pageTitle}
                </h1>
            </div>

            <div className="flex items-center gap-2">
                {mounted && (
                    <button
                        onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                        className="p-2 rounded-full bg-black/5 dark:bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-black/10 dark:bg-white/10 text-[var(--text-color)] transition-colors"
                        aria-label="Toggle theme"
                    >
                        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
                    </button>
                )}

                {user && (
                    <div className="flex items-center gap-2">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-[var(--text-color)] leading-tight">{user.name}</p>
                            <p className="text-xs text-slate-600 dark:text-slate-400 capitalize leading-tight">{user.role}</p>
                        </div>
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-sm font-bold text-[var(--text-color)] shadow-md">
                            {user.name.charAt(0).toUpperCase()}
                        </div>
                        <button
                            onClick={handleLogout}
                            className="p-2 rounded-full bg-black/5 dark:bg-black/5 dark:bg-white/5 hover:bg-red-500/20 hover:text-red-400 text-[var(--text-color)] transition-colors md:hidden"
                            aria-label="Logout"
                        >
                            <LogOut size={18} />
                        </button>
                    </div>
                )}
            </div>
        </header>
    );
}
