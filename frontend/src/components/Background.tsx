'use client';

import { memo } from 'react';

/* ─── Main export ─── */
const Background = memo(function Background() {
  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      <BgGradient />
      <Orbs />
      <MoleculeLayer />
    </div>
  );
});

export default Background;

/* ─── Gradient base ─── */
function BgGradient() {
  return (
    <>
      {/* Light mode gradient */}
      <style>{`
        .bg-base-light {
          position: absolute;
          inset: 0;
          background:
            radial-gradient(ellipse 80% 80% at 15% 10%, rgba(167,139,250,0.50) 0%, transparent 60%),
            radial-gradient(ellipse 65% 65% at 85% 85%, rgba(6,182,212,0.22) 0%, transparent 55%),
            radial-gradient(ellipse 90% 60% at 50% 50%, rgba(196,181,253,0.35) 0%, transparent 70%),
            #f5f3ff;
        }
        .dark .bg-base-light,
        [data-theme="dark"] .bg-base-light {
          background:
            radial-gradient(ellipse 75% 70% at 15% 15%, rgba(109,40,217,0.40) 0%, transparent 65%),
            radial-gradient(ellipse 55% 55% at 85% 80%, rgba(6,182,212,0.14) 0%, transparent 55%),
            radial-gradient(ellipse 80% 55% at 50% 55%, rgba(76,29,149,0.30) 0%, transparent 70%),
            #07070f;
        }
      `}</style>
      <div className="bg-base-light" />
    </>
  );
}

/* ─── Soft glowing orbs ─── */
function Orbs() {
  return (
    <>
      <style>{`
        @keyframes orbDrift {
          0%   { transform: translate(0px,   0px)   scale(1.00); }
          25%  { transform: translate(25px, -18px)  scale(1.04); }
          50%  { transform: translate(-18px, 25px)  scale(0.97); }
          75%  { transform: translate(15px,  12px)  scale(1.02); }
          100% { transform: translate(0px,   0px)   scale(1.00); }
        }
        .orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(70px);
          will-change: transform;
          animation: orbDrift ease-in-out infinite;
        }
        .orb1 {
          width: 560px; height: 560px;
          top: -140px; left: -100px;
          background: radial-gradient(circle, rgba(196,181,253,0.55), transparent 70%);
          animation-duration: 28s;
        }
        .orb2 {
          width: 480px; height: 480px;
          bottom: -100px; right: -80px;
          background: radial-gradient(circle, rgba(6,182,212,0.30), transparent 70%);
          animation-duration: 22s;
          animation-delay: -7s;
        }
        .orb3 {
          width: 420px; height: 420px;
          top: 38%; left: 48%;
          background: radial-gradient(circle, rgba(167,139,250,0.40), transparent 70%);
          animation-duration: 33s;
          animation-delay: -14s;
        }
        /* Dark orbs are more saturated */
        .dark .orb1, [data-theme="dark"] .orb1 {
          background: radial-gradient(circle, rgba(139,92,246,0.38), transparent 70%);
        }
        .dark .orb2, [data-theme="dark"] .orb2 {
          background: radial-gradient(circle, rgba(6,182,212,0.18), transparent 70%);
        }
        .dark .orb3, [data-theme="dark"] .orb3 {
          background: radial-gradient(circle, rgba(109,40,217,0.28), transparent 70%);
        }
        @media (prefers-reduced-motion: reduce) {
          .orb { animation: none; }
        }
      `}</style>
      <div className="orb orb1" />
      <div className="orb orb2" />
      <div className="orb orb3" />
    </>
  );
}

/* ─── Antigravity molecule + DNA layer ─── */
function MoleculeLayer() {
  return (
    <>
      <style>{`
        @keyframes antigrav {
          0%   { transform: translateY(0px)   rotate(0deg);   }
          30%  { transform: translateY(-22px) rotate(4deg);   }
          65%  { transform: translateY(-10px) rotate(-3deg);  }
          100% { transform: translateY(0px)   rotate(0deg);   }
        }
        @keyframes spin {
          from { transform: rotate(0deg);   }
          to   { transform: rotate(360deg); }
        }
        .mol-wrap {
          position: absolute;
          will-change: transform;
          animation: antigrav ease-in-out infinite;
        }
        .mol-inner {
          animation: spin linear infinite;
          transform-origin: center center;
        }
        /* SVG stroke colors */
        .mol-bond  { stroke: rgba(124,58,237,0.28);  stroke-width: 0.8px; fill: none; }
        .mol-ring  { stroke: rgba(6,182,212,0.32);   stroke-width: 0.5px; fill: none; }
        .mol-node  { fill: rgba(124,58,237,0.55); }
        .mol-hub   { fill: #7c3aed; }
        .dna-s1    { stroke: rgba(139,92,246,0.50); stroke-width: 1.4px; fill: none; }
        .dna-s2    { stroke: rgba(6,182,212,0.40);  stroke-width: 1.4px; fill: none; }
        .dna-rung  { stroke: rgba(196,181,253,0.40); stroke-width: 0.9px; }
        .dark .mol-bond,  [data-theme="dark"] .mol-bond  { stroke: rgba(167,139,250,0.22); }
        .dark .mol-ring,  [data-theme="dark"] .mol-ring  { stroke: rgba(6,182,212,0.25); }
        .dark .mol-node,  [data-theme="dark"] .mol-node  { fill: rgba(167,139,250,0.45); }
        .dark .mol-hub,   [data-theme="dark"] .mol-hub   { fill: #a78bfa; }
        .dark .dna-s1,    [data-theme="dark"] .dna-s1    { stroke: rgba(167,139,250,0.45); }
        .dark .dna-s2,    [data-theme="dark"] .dna-s2    { stroke: rgba(6,182,212,0.32); }
        .dark .dna-rung,  [data-theme="dark"] .dna-rung  { stroke: rgba(167,139,250,0.30); }
        @media (prefers-reduced-motion: reduce) {
          .mol-wrap, .mol-inner { animation: none; }
        }
      `}</style>

      {/* Molecule top-left */}
      <div className="mol-wrap" style={{ top: '6%', left: '4%', width: 220, height: 220, animationDuration: '26s', animationDelay: '0s', opacity: 0.75 }}>
        <div className="mol-inner" style={{ animationDuration: '60s' }}>
          <MolSvg nodes={6} rings />
        </div>
      </div>

      {/* Molecule bottom-right */}
      <div className="mol-wrap" style={{ bottom: '8%', right: '5%', width: 280, height: 280, animationDuration: '32s', animationDelay: '-11s', opacity: 0.65 }}>
        <div className="mol-inner" style={{ animationDuration: '80s', animationDirection: 'reverse' }}>
          <MolSvg nodes={8} rings />
        </div>
      </div>

      {/* Small molecule center-right */}
      <div className="mol-wrap" style={{ top: '52%', right: '8%', width: 160, height: 160, animationDuration: '20s', animationDelay: '-5s', opacity: 0.55 }}>
        <div className="mol-inner" style={{ animationDuration: '45s' }}>
          <MolSvg nodes={4} rings={false} />
        </div>
      </div>

      {/* DNA left */}
      <div className="mol-wrap" style={{ top: '22%', left: '12%', width: 70, height: 180, animationDuration: '24s', animationDelay: '-3s', opacity: 0.60 }}>
        <DnaSvg />
      </div>

      {/* DNA top-right */}
      <div className="mol-wrap" style={{ top: '8%', right: '14%', width: 55, height: 140, animationDuration: '29s', animationDelay: '-16s', opacity: 0.50 }}>
        <DnaSvg />
      </div>
    </>
  );
}

/* Procedural molecule SVG */
function MolSvg({ nodes, rings }: { nodes: number; rings: boolean }) {
  const cx = 50, cy = 50, r = 34;
  const pts = Array.from({ length: nodes }, (_, i) => ({
    x: cx + r * Math.cos((2 * Math.PI * i) / nodes),
    y: cy + r * Math.sin((2 * Math.PI * i) / nodes),
  }));
  return (
    <svg viewBox="0 0 100 100" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      {pts.map((p, i) => <line key={`b${i}`} x1={cx} y1={cy} x2={p.x} y2={p.y} className="mol-bond" />)}
      {rings && pts.map((p, i) => (
        <line key={`r${i}`} x1={p.x} y1={p.y} x2={pts[(i + 1) % nodes].x} y2={pts[(i + 1) % nodes].y} className="mol-ring" />
      ))}
      <circle cx={cx} cy={cy} r={5} className="mol-hub" />
      {pts.map((p, i) => <circle key={`n${i}`} cx={p.x} cy={p.y} r={3} className="mol-node" />)}
    </svg>
  );
}

/* DNA helix SVG */
function DnaSvg() {
  const rungs = [18, 32, 46, 60, 74, 88];
  return (
    <svg viewBox="0 0 40 110" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <path d="M8,5 Q28,20 8,38 Q-12,56 8,74 Q28,92 8,108" className="dna-s1" />
      <path d="M32,5 Q12,20 32,38 Q52,56 32,74 Q12,92 32,108" className="dna-s2" />
      {rungs.map(y => <line key={y} x1="12" y1={y} x2="28" y2={y} className="dna-rung" />)}
    </svg>
  );
}
