"use client";

import { useEffect, useRef } from "react";

export default function DnaBackground() {
    const videoRef = useRef<HTMLVideoElement>(null);

    useEffect(() => {
        const video = videoRef.current;
        if (video) {
            // Force browser to know it is muted to satisfy autoplay policy
            video.muted = true;
            
            // Attempt autoplay programmatically
            const playPromise = video.play();
            if (playPromise !== undefined) {
                playPromise.catch((error) => {
                    console.log("Autoplay blocked by browser. Setting up interaction listeners.", error);
                    
                    // Fallback: Start playing when user interacts with the page
                    const startVideo = () => {
                        video.play()
                            .then(() => {
                                cleanup();
                            })
                            .catch((err) => console.log("Play failed on interaction:", err));
                    };

                    const events = ["click", "touchstart", "scroll", "keydown"];
                    const cleanup = () => {
                        events.forEach((event) => {
                            window.removeEventListener(event, startVideo);
                        });
                    };

                    events.forEach((event) => {
                        window.addEventListener(event, startVideo, { passive: true });
                    });
                });
            }
        }
    }, []);

    return (
        <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0 overflow-hidden">
            <video
                ref={videoRef}
                autoPlay
                loop
                muted
                playsInline
                disablePictureInPicture
                className="absolute top-0 left-0 w-full h-full object-cover"
            >
                <source src="/videoplayback.webm" type="video/webm" />
            </video>
            {/* Ultra-translucent vignette overlay: transparent in the center for 4K video clarity, with subtle dark corners for text contrast */}
            <div className="absolute inset-0 bg-white/10 dark:bg-gradient-to-br dark:from-black/35 dark:via-transparent dark:to-black/45 transition-colors duration-300" />
        </div>
    );
}
