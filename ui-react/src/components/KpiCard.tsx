import type { ReactNode } from 'react';

interface KpiCardProps {
  label: string;
  value: ReactNode;
  sub?: string;
  accent?: string;
  loading?: boolean;
}

export function KpiCard({ label, value, sub, accent = '#818cf8', loading }: KpiCardProps) {
  return (
    <div className="rounded-xl border border-hairline bg-card p-4 transition-colors duration-150 hover:border-[#343a4a]">
      <div className="flex items-center gap-2">
        <span className="h-3 w-[3px] rounded-full" style={{ backgroundColor: accent }} aria-hidden />
        <span className="label-eyebrow">{label}</span>
      </div>
      {loading ? (
        <div className="mt-3 h-8 w-20 animate-pulse rounded bg-hairline" />
      ) : (
        <div className="tnum mt-2 font-mono text-[32px] font-bold leading-none text-text">
          {value}
        </div>
      )}
      {sub && !loading && <div className="tnum mt-2 font-mono text-[12px] text-faint">{sub}</div>}
    </div>
  );
}
