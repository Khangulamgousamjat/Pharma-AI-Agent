/**
 * components/GlassCard.tsx — Reusable glassmorphism card component.
 *
 * Renders a frosted glass panel with blur, transparent background,
 * soft shadow, and optional hover lift effect.
 *
 * @param children - Card content
 * @param className - Additional CSS classes
 * @param hover - Enable hover lift animation (default: true)
 * @param padding - Padding size (sm/md/lg, default: md)
 */

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    hover?: boolean;
    padding?: "sm" | "md" | "lg" | "none";
}

const paddingMap = {
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
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
        ${hover ? "hover:-translate-y-1 hover:shadow-2xl" : ""}
        ${className}
      `}
        >
            {children}
        </div>
    );
}
