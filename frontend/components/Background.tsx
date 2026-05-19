'use client';

/**
 * components/Background.tsx — Fixed full-screen animated background.
 *
 * Renders:
 *   1. Radial gradient orb blobs (violet/cyan/purple) that float gently
 *   2. Procedural SVG molecule clusters (antigravity floating nodes + bonds)
 *   3. DNA helix SVG strands drifting in the background
 *
 * Registered once in root layout.tsx and sits at z-index:0 behind all content.
 */

import styles from './Background.module.css';

export default function Background() {
  return (
    <div className={styles.bgRoot} aria-hidden="true">
      {/* Floating gradient orbs */}
      <div className={styles.orb1} />
      <div className={styles.orb2} />
      <div className={styles.orb3} />

      {/* Antigravity molecule SVG clusters */}
      <MoleculeCanvas />
    </div>
  );
}

/* ── Floating DNA / Molecule SVG clusters ── */
function MoleculeCanvas() {
  return (
    <div className={styles.moleculeLayer}>
      <MoleculeCluster
        className={styles.mol1}
        nodes={6}
        rings={true}
        style={{ width: 260, height: 260, animationDelay: '0s', animationDuration: '28s' }}
      />
      <MoleculeCluster
        className={styles.mol2}
        nodes={4}
        rings={false}
        style={{ width: 180, height: 180, animationDelay: '-9s', animationDuration: '22s' }}
      />
      <MoleculeCluster
        className={styles.mol3}
        nodes={8}
        rings={true}
        style={{ width: 320, height: 320, animationDelay: '-5s', animationDuration: '35s' }}
      />
      <DnaHelix
        className={styles.dna1}
        style={{ animationDelay: '0s', animationDuration: '25s' }}
      />
      <DnaHelix
        className={styles.dna2}
        style={{ animationDelay: '-12s', animationDuration: '30s' }}
      />
    </div>
  );
}

/* Procedural molecule cluster via SVG */
function MoleculeCluster({
  nodes,
  rings,
  className,
  style,
}: {
  nodes: number;
  rings: boolean;
  className?: string;
  style?: React.CSSProperties;
}) {
  const cx = 50,
    cy = 50,
    r = 30;
  const pts = Array.from({ length: nodes }, (_, i) => ({
    x: cx + r * Math.cos((2 * Math.PI * i) / nodes),
    y: cy + r * Math.sin((2 * Math.PI * i) / nodes),
  }));

  return (
    <svg
      viewBox="0 0 100 100"
      className={`${styles.moleculeSvg} ${className ?? ''}`}
      style={style}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* bonds from center to each node */}
      {pts.map((p, i) => (
        <line
          key={`b${i}`}
          x1={cx}
          y1={cy}
          x2={p.x}
          y2={p.y}
          className={styles.bond}
          strokeWidth="0.8"
        />
      ))}
      {/* ring bonds between consecutive nodes */}
      {rings &&
        pts.map((p, i) => (
          <line
            key={`r${i}`}
            x1={p.x}
            y1={p.y}
            x2={pts[(i + 1) % pts.length].x}
            y2={pts[(i + 1) % pts.length].y}
            className={styles.bond}
            strokeWidth="0.5"
          />
        ))}
      {/* center node */}
      <circle cx={cx} cy={cy} r={4} className={styles.nodeCenter} />
      {/* outer nodes */}
      {pts.map((p, i) => (
        <circle key={`n${i}`} cx={p.x} cy={p.y} r={2.5} className={styles.node} />
      ))}
    </svg>
  );
}

/* Simple DNA helix using SVG path */
function DnaHelix({
  className,
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  const strand1 = 'M10,10 Q30,25 10,40 Q-10,55 10,70 Q30,85 10,100';
  const strand2 = 'M30,10 Q10,25 30,40 Q50,55 30,70 Q10,85 30,100';

  return (
    <svg
      viewBox="0 0 40 110"
      className={`${styles.dnaSvg} ${className ?? ''}`}
      style={style}
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d={strand1} className={styles.strand1} strokeWidth="1.5" fill="none" />
      <path d={strand2} className={styles.strand2} strokeWidth="1.5" fill="none" />
      {/* rungs connecting the two strands */}
      {[20, 35, 50, 65, 80].map((y) => (
        <line
          key={y}
          x1="14"
          y1={y}
          x2="26"
          y2={y}
          className={styles.rung}
          strokeWidth="1"
        />
      ))}
    </svg>
  );
}
