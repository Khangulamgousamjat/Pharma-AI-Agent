'use client';

/**
 * MedicalCrossLogo — Premium 4-petal healthcare cross SVG
 * Matches the stylized health cross reference design with teal gradient.
 * Used across Login, Register, Navbar, and Footer.
 */

interface MedicalCrossLogoProps {
  size?: number;       // pixel size
  variant?: 'teal' | 'white' | 'indigo';  // color scheme
  className?: string;
}

export default function MedicalCrossLogo({
  size = 32,
  variant = 'teal',
  className = '',
}: MedicalCrossLogoProps) {
  const id = `mcg-${variant}-${size}`;

  const gradients = {
    teal: {
      a: '#5eead4',  // teal-300
      b: '#0d9488',  // teal-600
      c: '#0f766e',  // teal-700
    },
    indigo: {
      a: '#c4b5fd',
      b: '#7c3aed',
      c: '#5b21b6',
    },
    white: {
      a: 'rgba(255,255,255,0.95)',
      b: 'rgba(255,255,255,0.80)',
      c: 'rgba(255,255,255,0.65)',
    },
  };

  const g = gradients[variant];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Medical Cross Logo"
    >
      <defs>
        {/* Main gradient — top-left to bottom-right */}
        <linearGradient id={`${id}-grad`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%"   stopColor={g.a} />
          <stop offset="55%"  stopColor={g.b} />
          <stop offset="100%" stopColor={g.c} />
        </linearGradient>

        {/* Subtle shadow for each petal */}
        <filter id={`${id}-shadow`} x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.18" />
        </filter>
      </defs>

      {/*
        4-petal cross: each petal is a rounded square occupying one quadrant.
        They meet at center (50,50) with a natural gap between petals.
        Outer corners are fully rounded (rx matched to ~35% of petal size).
        Inner corners taper to the center point.
      */}

      {/* ── Top-Left petal ── */}
      <path
        d="M48 48 L48 16 Q48 6 38 6 L16 6 Q6 6 6 16 L6 38 Q6 48 16 48 Z"
        fill={`url(#${id}-grad)`}
        filter={`url(#${id}-shadow)`}
      />

      {/* ── Top-Right petal ── */}
      <path
        d="M52 48 L84 48 Q94 48 94 38 L94 16 Q94 6 84 6 L62 6 Q52 6 52 16 Z"
        fill={`url(#${id}-grad)`}
        filter={`url(#${id}-shadow)`}
        opacity="0.92"
      />

      {/* ── Bottom-Right petal ── */}
      <path
        d="M52 52 L52 84 Q52 94 62 94 L84 94 Q94 94 94 84 L94 62 Q94 52 84 52 Z"
        fill={`url(#${id}-grad)`}
        filter={`url(#${id}-shadow)`}
      />

      {/* ── Bottom-Left petal ── */}
      <path
        d="M48 52 L16 52 Q6 52 6 62 L6 84 Q6 94 16 94 L38 94 Q48 94 48 84 Z"
        fill={`url(#${id}-grad)`}
        filter={`url(#${id}-shadow)`}
        opacity="0.92"
      />
    </svg>
  );
}
