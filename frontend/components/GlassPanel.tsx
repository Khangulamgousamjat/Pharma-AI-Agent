import { ReactNode, CSSProperties } from 'react';

type Variant = 'default' | 'card' | 'modal' | 'navbar' | 'sidebar';

interface GlassPanelProps {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  variant?: Variant;
  hover?: boolean;
  onClick?: () => void;
}

const variantStyles: Record<Variant, CSSProperties> = {
  default: { padding: '20px',  borderRadius: '20px' },
  card:    { padding: '24px',  borderRadius: '20px' },
  modal:   { padding: '32px',  borderRadius: '24px' },
  navbar:  { padding: '0 24px', borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderTop: 'none' },
  sidebar: { padding: '16px',  borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none' },
};

export default function GlassPanel({
  children, className = '', style, variant = 'default', hover = false, onClick,
}: GlassPanelProps) {
  return (
    <>
      <style>{`
        .glass-panel {
          position: relative;
          background: var(--gl-bg);
          backdrop-filter: var(--gl-blur);
          -webkit-backdrop-filter: var(--gl-blur);
          border: 1px solid var(--gl-border);
          box-shadow: var(--gl-shadow);
          overflow: hidden;
          transition: var(--transition);
        }
        .dark .glass-panel,
        [data-theme="dark"] .glass-panel {
          background: var(--gld-bg);
          backdrop-filter: var(--gld-blur);
          -webkit-backdrop-filter: var(--gld-blur);
          border-color: var(--gld-border);
          box-shadow: var(--gld-shadow);
        }
        .glass-panel::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            var(--gl-top) 30%,
            var(--gl-top) 70%,
            transparent 100%
          );
          pointer-events: none;
          z-index: 1;
        }
        .dark .glass-panel::before,
        [data-theme="dark"] .glass-panel::before {
          background: linear-gradient(
            90deg,
            transparent 0%,
            var(--gld-top) 30%,
            var(--gld-top) 70%,
            transparent 100%
          );
        }
        .glass-hover:hover {
          border-color: rgba(167,139,250,0.55);
          box-shadow: var(--gl-shadow), 0 0 0 1px rgba(167,139,250,0.25), 0 20px 44px rgba(124,58,237,0.18);
          transform: translateY(-2px);
        }
        .dark .glass-hover:hover,
        [data-theme="dark"] .glass-hover:hover {
          border-color: rgba(167,139,250,0.22);
          box-shadow: var(--gld-shadow), 0 0 0 1px rgba(167,139,250,0.18), 0 20px 44px rgba(0,0,0,0.50);
          transform: translateY(-2px);
        }
        /* Fallback for browsers without backdrop-filter */
        @supports not (backdrop-filter: blur(1px)) {
          .glass-panel { background: rgba(240,236,255,0.92); }
          .dark .glass-panel, [data-theme="dark"] .glass-panel { background: rgba(15,10,30,0.92); }
        }
      `}</style>
      <div
        className={`glass-panel ${hover ? 'glass-hover' : ''} ${className}`}
        style={{ ...variantStyles[variant], ...style }}
        onClick={onClick}
      >
        {children}
      </div>
    </>
  );
}
