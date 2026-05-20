import { ReactNode, CSSProperties } from 'react';

type Variant = 'default' | 'card' | 'modal' | 'navbar' | 'sidebar';

const variants: Record<Variant, CSSProperties> = {
  default: { padding: '20px', borderRadius: '20px' },
  card:    { padding: '24px', borderRadius: '20px' },
  modal:   { padding: '32px', borderRadius: '24px' },
  navbar:  { padding: '0 24px', borderRadius: 0, borderLeft: 'none', borderRight: 'none', borderTop: 'none' },
  sidebar: { padding: '16px', borderRadius: 0, borderTop: 'none', borderBottom: 'none', borderLeft: 'none' },
};

interface Props {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  variant?: Variant;
  hover?: boolean;
  onClick?: () => void;
}

export default function GlassPanel({ children, className = '', style, variant = 'default', hover = false, onClick }: Props) {
  return (
    <>
      <style>{`
        .gp {
          position: relative;
          overflow: hidden;
          /* CLEAR GLASS — see DNA through it */
          background: rgba(255, 255, 255, 0.07);
          backdrop-filter: blur(10px) saturate(160%);
          -webkit-backdrop-filter: blur(10px) saturate(160%);
          border: 1px solid rgba(255, 255, 255, 0.18);
          box-shadow:
            0 4px 24px rgba(0, 0, 0, 0.35),
            0 1px 0 rgba(255,255,255,0.12) inset;
          transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
        }
        /* Top-edge catch light — makes it look like real glass */
        .gp::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(90deg,
            transparent 0%,
            rgba(255,255,255,0.70) 25%,
            rgba(255,255,255,0.70) 75%,
            transparent 100%
          );
          pointer-events: none;
          z-index: 2;
        }
        /* Left-edge glint */
        .gp::after {
          content: '';
          position: absolute;
          top: 0; left: 0; bottom: 0;
          width: 1px;
          background: linear-gradient(180deg,
            rgba(255,255,255,0.55) 0%,
            rgba(255,255,255,0.10) 60%,
            transparent 100%
          );
          pointer-events: none;
          z-index: 2;
        }
        /* Hover lift */
        .gp-hover:hover {
          background: rgba(255,255,255,0.10);
          border-color: rgba(167,139,250,0.45);
          box-shadow:
            0 8px 36px rgba(0,0,0,0.45),
            0 0 0 1px rgba(167,139,250,0.20),
            0 1px 0 rgba(255,255,255,0.15) inset;
          transform: translateY(-2px);
        }
        /* Fallback — no backdrop-filter support */
        @supports not (backdrop-filter: blur(1px)) {
          .gp { background: rgba(10, 8, 30, 0.88); }
        }
      `}</style>
      <div
        className={`gp ${hover ? 'gp-hover' : ''} ${className}`}
        style={{ ...variants[variant], ...style }}
        onClick={onClick}
      >
        {children}
      </div>
    </>
  );
}
