"use client";

import { useEffect, useState } from "react";

export default function DnaBackground() {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    if (!mounted) {
        // Dark placeholder matches the theme color while hydrating
        return <div className="fixed top-0 left-0 w-full h-full bg-[#0f0109] pointer-events-none z-0" />;
    }

    return (
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0 overflow-hidden">
            <video
                src="/videoplayback.webm"
                autoPlay
                loop
                muted
                playsInline
                disablePictureInPicture
                className="absolute top-0 left-0 w-full h-full object-cover"
            />
            {/* Translucent overlay to protect text contrast and adapt to theme modes */}
            <div className="absolute inset-0 bg-white/80 dark:bg-[#090005]/50 transition-colors duration-300" />
        </div>
    );
}
