"use client";

import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import { usePathname } from "next/navigation";

export default function Layout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const noLayout = ["/login", "/register", "/"];

    if (noLayout.includes(pathname)) {
        return (
            // Transparent — Background component (fixed) handles the visuals
            <div className="min-h-screen relative overflow-hidden transition-colors duration-300">
                <div className="relative z-10">
                    {children}
                </div>
            </div>
        );
    }

    return (
        <div className="flex h-screen overflow-hidden relative transition-colors duration-300">
            {/* Content above Background (which is fixed at z-0) */}
            <div className="relative z-10 flex w-full h-full overflow-hidden">
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
