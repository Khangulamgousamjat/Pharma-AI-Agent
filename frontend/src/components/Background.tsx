'use client';

import { useEffect, useRef, memo } from 'react';

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
        background: 'var(--bg-light)',
      }}
    >
      <DnaCanvas />
      <GlowOrbs />
    </div>
  );
});

export default Background;

/* ═══════════════════════════════════════════════
   CANVAS — Full-screen animated DNA double helix
   ═══════════════════════════════════════════════ */
function DnaCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef    = useRef<number>(0);
  const tRef      = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    /* Resize handler */
    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    /* ── DNA Config ── */
    const STRANDS    = 2;          // double helix
    const NODES      = 28;         // base pairs visible
    const AMPLITUDE  = 120;        // how wide the helix spreads
    const WAVELENGTH = 220;        // vertical distance for one full rotation
    const SPEED      = 0.0004;     // rotation speed
    const PARTICLE_COUNT = 180;    // background bokeh particles

    /* ── Bokeh particles ── */
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:    Math.random() * window.innerWidth,
      y:    Math.random() * window.innerHeight,
      r:    Math.random() * 3.5 + 0.5,
      a:    Math.random() * 0.7 + 0.1,
      vx:   (Math.random() - 0.5) * 0.25,
      vy:   (Math.random() - 0.5) * 0.18,
      hue:  Math.random() > 0.7 ? 0 : 220, // red or blue
    }));

    /* ── Draw a glowing dot ── */
    const glowDot = (x: number, y: number, r: number, color: string, alpha: number) => {
      const grad = ctx.createRadialGradient(x, y, 0, x, y, r * 3);
      grad.addColorStop(0, color.replace('A', `${alpha}`));
      grad.addColorStop(0.4, color.replace('A', `${alpha * 0.6}`));
      grad.addColorStop(1, color.replace('A', '0'));
      ctx.beginPath();
      ctx.arc(x, y, r * 3, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();
      /* solid core */
      ctx.beginPath();
      ctx.arc(x, y, r * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = color.replace('A', `${Math.min(alpha + 0.3, 1)}`);
      ctx.fill();
    };

    /* ── Draw one DNA strand ── */
    const drawHelix = (
      cx: number,    // center X of this helix column
      phaseOffset: number,
      t: number,
    ) => {
      const W = canvas.width;
      const H = canvas.height;

      /* Calculate all node positions for both strands */
      const strand: Array<{x1:number; y1:number; x2:number; y2:number; depth:number}> = [];

      for (let i = 0; i < NODES; i++) {
        const yFrac = i / (NODES - 1);
        const y     = yFrac * (H + 100) - 50;
        const angle = (yFrac * Math.PI * 2 * (H / WAVELENGTH)) + t + phaseOffset;
        const depth = Math.sin(angle); // -1 to 1 for z-depth

        const x1 = cx + Math.cos(angle) * AMPLITUDE;
        const x2 = cx - Math.cos(angle) * AMPLITUDE;

        strand.push({ x1, y1: y, x2, y2: y, depth });
      }

      /* Draw rungs (base pairs) back-to-front based on depth */
      const sorted = [...strand].sort((a, b) => a.depth - b.depth);
      sorted.forEach(({ x1, y1, x2, depth }) => {
        const alpha = (depth + 1) / 2;   // 0..1
        const brightness = 0.3 + alpha * 0.7;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y1);
        ctx.strokeStyle = `rgba(100, 180, 255, ${brightness * 0.55})`;
        ctx.lineWidth   = 0.8 + alpha * 0.6;
        ctx.stroke();

        /* Node dots on each end of rung */
        const nodeColor = depth > 0
          ? `rgba(140, 200, 255, A)`   // front — bright blue
          : `rgba(60,  120, 220, A)`;  // back  — deeper blue
        glowDot(x1, y1, 3 + alpha * 2, nodeColor, 0.5 + alpha * 0.5);
        glowDot(x2, y1, 3 + alpha * 2, nodeColor, 0.5 + alpha * 0.5);
      });

      /* Draw two backbone curves */
      [0, 1].forEach(strandIdx => {
        ctx.beginPath();
        strand.forEach(({ x1, x2, y1 }, i) => {
          const x = strandIdx === 0 ? x1 : x2;
          if (i === 0) ctx.moveTo(x, y1);
          else         ctx.lineTo(x, y1);
        });
        ctx.strokeStyle = strandIdx === 0
          ? 'rgba(120, 200, 255, 0.70)'
          : 'rgba(80,  160, 255, 0.55)';
        ctx.lineWidth = 1.8;
        ctx.shadowColor = 'rgba(100, 180, 255, 0.90)';
        ctx.shadowBlur  = 8;
        ctx.stroke();
        ctx.shadowBlur  = 0;
      });
    };

    /* ── Animation loop ── */
    const draw = (ts: number) => {
      const delta = ts - tRef.current;
      tRef.current = ts;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const t = ts * SPEED;

      /* Draw bokeh particles */
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -10) p.x = canvas.width + 10;
        if (p.x > canvas.width + 10) p.x = -10;
        if (p.y < -10) p.y = canvas.height + 10;
        if (p.y > canvas.height + 10) p.y = -10;

        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 4);
        const col  = p.hue === 0
          ? `rgba(255, 80, 80, ${p.a * 0.7})`
          : `rgba(80, 160, 255, ${p.a * 0.7})`;
        grad.addColorStop(0, col);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 4, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      });

      /* Draw 2 DNA helixes at different X positions */
      drawHelix(canvas.width * 0.25, 0,           t);
      drawHelix(canvas.width * 0.75, Math.PI,      t);

      rafRef.current = requestAnimationFrame(draw);
    };

    tRef.current = performance.now();
    rafRef.current = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        inset: 0,
        width: '100%',
        height: '100%',
        opacity: 0.85,
      }}
    />
  );
}

/* ═══════════════════════════
   Soft glow orbs (background)
   ═══════════════════════════ */
function GlowOrbs() {
  return (
    <>
      <style>{`
        @keyframes orbFloat {
          0%   { transform: translate(0px,   0px);   }
          33%  { transform: translate(20px, -15px);  }
          66%  { transform: translate(-15px, 20px);  }
          100% { transform: translate(0px,   0px);   }
        }
        .bg-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          will-change: transform;
          animation: orbFloat ease-in-out infinite;
          pointer-events: none;
        }
        @media (prefers-reduced-motion: reduce) {
          .bg-orb { animation: none; }
        }
      `}</style>

      {/* Violet orb — top left */}
      <div className="bg-orb" style={{
        width: 500, height: 500,
        top: -120, left: -80,
        background: 'radial-gradient(circle, rgba(109,40,217,0.45), transparent 70%)',
        animationDuration: '28s',
      }} />

      {/* Cyan orb — bottom right */}
      <div className="bg-orb" style={{
        width: 420, height: 420,
        bottom: -100, right: -60,
        background: 'radial-gradient(circle, rgba(6,182,212,0.22), transparent 70%)',
        animationDuration: '22s',
        animationDelay: '-9s',
      }} />

      {/* Red accent — mid left (matches reference bokeh) */}
      <div className="bg-orb" style={{
        width: 280, height: 280,
        top: '35%', left: '5%',
        background: 'radial-gradient(circle, rgba(239,68,68,0.12), transparent 70%)',
        animationDuration: '18s',
        animationDelay: '-5s',
      }} />
    </>
  );
}
