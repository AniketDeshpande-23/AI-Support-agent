import { useEffect, useRef, useState } from 'react';

interface ConfidenceArcProps {
  value: number; // 0-100
  size?: number;
  stroke?: number;
}

function arcColor(v: number): string {
  if (v >= 75) return '#34d399';
  if (v >= 50) return '#818cf8';
  if (v >= 30) return '#fbbf24';
  return '#f87171';
}

const prefersReduced =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function ConfidenceArc({ value, size = 132, stroke = 10 }: ConfidenceArcProps) {
  const target = Math.max(0, Math.min(100, value));
  const [display, setDisplay] = useState(prefersReduced ? target : 0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    if (prefersReduced) {
      setDisplay(target);
      return;
    }
    const start = performance.now();
    const from = 0;
    const duration = 700;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (target - from) * eased);
      if (t < 1) rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target]);

  const r = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;
  const gapDeg = 90; // open gauge at bottom
  const sweepDeg = 360 - gapDeg;
  const startAngle = 90 + gapDeg / 2;
  const circumference = 2 * Math.PI * r;
  const arcLength = (sweepDeg / 360) * circumference;
  const filled = (display / 100) * arcLength;
  const color = arcColor(target);

  return (
    <div className="relative inline-flex" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90 transform">
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke="#262a36"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
          transform={`rotate(${startAngle - 90} ${cx} ${cy})`}
        />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          transform={`rotate(${startAngle - 90} ${cx} ${cy})`}
          style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="tnum font-mono text-[28px] font-bold leading-none" style={{ color }}>
          {Math.round(display)}
          <span className="text-[15px] text-faint">%</span>
        </span>
        <span className="label-eyebrow mt-1.5">confidence</span>
      </div>
    </div>
  );
}
