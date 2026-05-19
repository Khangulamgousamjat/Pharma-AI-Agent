/**
 * components/GlassPanel.tsx — Unified glassmorphism panel system.
 *
 * Replaces all card/panel/modal/navbar/sidebar divs with proper
 * frosted glass aesthetics for both light and dark modes.
 *
 * Usage:
 *   <GlassPanel variant="card" hover>...</GlassPanel>
 *   <GlassPanel variant="modal">...</GlassPanel>
 *   <GlassPanel variant="navbar">...</GlassPanel>
 */

import styles from './GlassPanel.module.css';

type Variant = 'default' | 'card' | 'modal' | 'sidebar' | 'navbar';

type GlassPanelProps = {
  children: React.ReactNode;
  className?: string;
  variant?: Variant;
  hover?: boolean;
  style?: React.CSSProperties;
};

export default function GlassPanel({
  children,
  className = '',
  variant = 'default',
  hover = false,
  style,
}: GlassPanelProps) {
  const classes = [
    styles.glass,
    styles[variant],
    hover ? styles.hoverEffect : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} style={style}>
      {/* Inner top-edge highlight — makes it look like real glass catching light */}
      <div className={styles.glassHighlight} aria-hidden="true" />
      {children}
    </div>
  );
}
