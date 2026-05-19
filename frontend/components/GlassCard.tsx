/**
 * components/GlassCard.tsx — Reusable glassmorphism card component.
 *
 * Now powered by the full Pharma AI design system (design-system.css).
 * Uses the .glass-card class which includes the real glass inner-highlight strip.
 */

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    padding?: "sm" | "md" | "lg" | "none";
}

const paddingMap = {
    sm:   "p-4",
    md:   "p-6",
    lg:   "p-8",
    none: "",
};

export default function GlassCard({
    children,
    className = "",
    hover = true,
    padding = "md",
}: GlassCardProps) {
    return (
        <div
            className={`
                glass-card
                ${paddingMap[padding]}
                ${hover ? "cursor-pointer" : ""}
                ${className}
            `}
        >
            {children}
        </div>
    );
}
