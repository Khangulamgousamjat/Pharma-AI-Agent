"use client";

import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import { usePathname } from "next/navigation";
import DnaBackground from "./DnaBackground";

export default function Layout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const noLayout = ["/login", "/register", "/"];

    if (noLayout.includes(pathname)) {
        return (
            <div className="bg-slate-50 dark:bg-slate-950 min-h-screen text-slate-200 relative">
                <DnaBackground />
                <div className="relative z-10">{children}</div>
            </div>
        );
    }

    return (
        <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-200 overflow-hidden font-sans relative">
            <DnaBackground />
            <div className="flex h-full w-full relative z-10 overflow-hidden">
                <Sidebar />
                <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                    <Navbar />
                    <main className="flex-1 overflow-y-auto">
                        {children}
                    </main>
                </div>
            </div>
        </div>
    );
}

