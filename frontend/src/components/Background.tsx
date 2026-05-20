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
        background: 'radial-gradient(ellipse 120% 100% at 50% 0%, #0d1f3c 0%, #0a1628 40%, #060e1a 100%)',
      }}
    >
      <DnaCanvas />
    </div>
  );
});

export default Background;

/* ════════════════════════════════════════════════════════════
   CANVAS — 5-6 real 3D twisted DNA helix pieces scattered
   across entire screen, each floating independently
   ════════════════════════════════════════════════════════════ */
function DnaCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef    = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    /* ── Resize ── */
    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    /* ════════════════════════════════════════
       DNA HELIX PIECE DEFINITIONS
       Each piece: position, size, tilt, speed
       ════════════════════════════════════════ */
    const helixes = [
      // { x, y } = center position as fraction of screen
      // size = scale multiplier
      // tilt = rotation angle in radians
      // speed = rotation speed
      // driftX/driftY = floating direction
      // opacity = brightness (0.3 = background, 1.0 = foreground)
      // segments = how many base pairs to draw
      {
        xFrac: 0.10, yFrac: 0.30, size: 1.10,
        tilt: -0.45, speed: 0.00025, driftX: 0.12, driftY: -0.06,
        opacity: 0.85, segments: 10, phase: 0,
      },
      {
        xFrac: 0.88, yFrac: 0.22, size: 0.90,
        tilt: 0.40, speed: 0.00030, driftX: -0.10, driftY: 0.08,
        opacity: 0.80, segments: 9, phase: 1.2,
      },
      {
        xFrac: 0.75, yFrac: 0.72, size: 1.20,
        tilt: -0.30, speed: 0.00018, driftX: 0.08, driftY: -0.10,
        opacity: 0.75, segments: 11, phase: 2.4,
      },
      {
        xFrac: 0.22, yFrac: 0.78, size: 0.80,
        tilt: 0.55, speed: 0.00035, driftX: -0.07, driftY: 0.05,
        opacity: 0.65, segments: 8, phase: 0.8,
      },
      {
        xFrac: 0.50, yFrac: 0.10, size: 0.70,
        tilt: 0.20, speed: 0.00022, driftX: 0.05, driftY: 0.07,
        opacity: 0.55, segments: 7, phase: 3.6,
      },
      {
        xFrac: 0.60, yFrac: 0.50, size: 0.55,
        tilt: -0.65, speed: 0.00040, driftX: -0.06, driftY: -0.04,
        opacity: 0.40, segments: 6, phase: 1.8,
      },
    ];

    /* ── Particle dust ── */
    const PARTICLE_COUNT = 220;
    const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
      x:   Math.random() * window.innerWidth,
      y:   Math.random() * window.innerHeight,
      r:   Math.random() * 2.2 + 0.3,
      a:   Math.random() * 0.55 + 0.08,
      vx:  (Math.random() - 0.5) * 0.20,
      vy:  (Math.random() - 0.5) * 0.15,
      hue: Math.random() > 0.75 ? 'red' : 'blue',
    }));

    /* ════════════════════════════════════════
       DRAW ONE DNA HELIX PIECE
       cx, cy     = center of this piece
       size       = scale
       t          = current time angle
       tilt       = screen rotation
       segments   = number of base pairs
       alpha      = overall opacity
       ════════════════════════════════════════ */
    const drawDna = (
      cx: number, cy: number,
      size: number, t: number,
      tilt: number, segments: number, alpha: number
    ) => {
      const W  = 48  * size;   // strand spread width (how wide the helix is)
      const SH = 38  * size;   // vertical spacing between base pairs
      const totalH = SH * segments;

      /* Save canvas state and apply tilt rotation around center */
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(tilt);

      const halfH = totalH / 2;

      /* Collect all points for both strands */
      type Pt = { x: number; y: number; depth: number };
      const strand1: Pt[] = [];
      const strand2: Pt[] = [];

      for (let i = 0; i <= segments; i++) {
        const prog  = i / segments;
        const y     = prog * totalH - halfH;
        const angle = prog * Math.PI * 3 + t; // 3 full twists per piece

        const depth = Math.sin(angle); // -1..1 simulates Z depth

        strand1.push({
          x:     Math.cos(angle) * W,
          y,
          depth,
        });
        strand2.push({
          x:     -Math.cos(angle) * W,
          y,
          depth: -depth,
        });
      }

      /* ── Draw backbone ribbons (thick smooth curves) ── */
      const drawRibbon = (pts: Pt[], colorFront: string, colorBack: string) => {
        /* Split into segments and color by depth */
        for (let i = 0; i < pts.length - 1; i++) {
          const p  = pts[i];
          const q  = pts[i + 1];
          const d  = (p.depth + 1) / 2;  // 0..1

          /* Interpolate color: back = deep blue, front = bright cyan */
          const r = Math.round(0   + d * 0);
          const g = Math.round(80  + d * 140);
          const b = Math.round(180 + d * 75);
          const a = (0.30 + d * 0.70) * alpha;

          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = `rgba(${r},${g},${b},${a})`;
          ctx.lineWidth   = (2.5 + d * 3.5) * size;  // thicker in front
          ctx.lineCap     = 'round';

          /* Glow effect on front strands */
          if (d > 0.6) {
            ctx.shadowColor = `rgba(0, 210, 255, ${d * alpha * 0.8})`;
            ctx.shadowBlur  = 10 * size;
          } else {
            ctx.shadowBlur = 0;
          }
          ctx.stroke();
        }
        ctx.shadowBlur = 0;
      };

      drawRibbon(strand1, '#00d4ff', '#005588');
      drawRibbon(strand2, '#0099ee', '#003366');

      /* ── Draw rungs (base pairs connecting the two strands) ── */
      /* Sort by average depth so back rungs draw first */
      const rungs = strand1.map((p, i) => ({
        p1: p,
        p2: strand2[i],
        avgDepth: (p.depth + strand2[i].depth) / 2,
      }));
      rungs.sort((a, b) => a.avgDepth - b.avgDepth);

      rungs.forEach(({ p1, p2, avgDepth }) => {
        const d = (avgDepth + 1) / 2;
        const a = (0.15 + d * 0.55) * alpha;

        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.strokeStyle = `rgba(100, 200, 255, ${a})`;
        ctx.lineWidth   = (0.8 + d * 1.0) * size;
        ctx.stroke();

        /* Glowing node dots at each end of the rung */
        [[p1.x, p1.y, p1.depth], [p2.x, p2.y, p2.depth]].forEach(([nx, ny, nd]) => {
          const nd01  = ((nd as number) + 1) / 2;
          const nodeA = (0.3 + nd01 * 0.7) * alpha;
          const nodeR = (2.0 + nd01 * 3.5) * size;

          /* Outer glow */
          const grad = ctx.createRadialGradient(
            nx as number, ny as number, 0,
            nx as number, ny as number, nodeR * 3
          );
          grad.addColorStop(0,   `rgba(180, 240, 255, ${nodeA})`);
          grad.addColorStop(0.4, `rgba(0,   180, 255, ${nodeA * 0.6})`);
          grad.addColorStop(1,   `rgba(0,   120, 200, 0)`);
          ctx.beginPath();
          ctx.arc(nx as number, ny as number, nodeR * 3, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();

          /* Solid core */
          ctx.beginPath();
          ctx.arc(nx as number, ny as number, nodeR * 0.55, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(220, 245, 255, ${Math.min(nodeA + 0.2, 1)})`;
          ctx.fill();
        });
      });

      ctx.restore();
    };

    /* ════════════════════════════════════
       ANIMATION LOOP
       ════════════════════════════════════ */
    const startTime = performance.now();

    const draw = (now: number) => {
      const elapsed = (now - startTime) * 0.001; // seconds
      const W = canvas.width;
      const H = canvas.height;

      ctx.clearRect(0, 0, W, H);

      /* ── Particle dust ── */
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -5)    p.x = W + 5;
        if (p.x > W + 5) p.x = -5;
        if (p.y < -5)    p.y = H + 5;
        if (p.y > H + 5) p.y = -5;

        const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 5);
        if (p.hue === 'red') {
          grad.addColorStop(0,  `rgba(255, 80,  80,  ${p.a})`);
        } else {
          grad.addColorStop(0,  `rgba(80,  180, 255, ${p.a})`);
        }
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 5, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      });

      /* ── Draw each DNA helix piece ── */
      helixes.forEach(h => {
        /* Slow independent drift */
        const driftRange = 35;
        const driftX = Math.sin(elapsed * h.driftX + h.phase) * driftRange;
        const driftY = Math.cos(elapsed * h.driftY + h.phase) * driftRange;

        const cx = h.xFrac * W + driftX;
        const cy = h.yFrac * H + driftY;
        const t  = elapsed * h.speed * 1000 + h.phase;

        drawDna(cx, cy, h.size, t, h.tilt, h.segments, h.opacity);
      });

      rafRef.current = requestAnimationFrame(draw);
    };

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
      }}
    />
  );
}
