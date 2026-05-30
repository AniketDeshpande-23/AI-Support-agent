import clsx from 'clsx';
import { BookOpen, FileCode2, Hexagon } from 'lucide-react';
import { API_BASE } from '../api';
import { PIPELINE_STEPS, STATUS_COLORS } from '../constants';
import { useHealth } from '../hooks/useHealth';
import { TabBar } from './TabBar';
import { clockTime } from '../time';
import type { HealthStatus, ViewKey } from '../types';

function deriveStatus(statusText: string, offline: boolean): HealthStatus {
  if (offline) return 'down';
  const s = statusText.toLowerCase();
  if (s.includes('ok') || s.includes('healthy') || s.includes('up')) return 'healthy';
  if (s.includes('degrad') || s.includes('warn')) return 'degraded';
  if (s.includes('down') || s.includes('error') || s.includes('fail')) return 'down';
  return 'healthy';
}

interface SidebarProps {
  active: ViewKey;
  onChange: (k: ViewKey) => void;
}

export function Sidebar({ active, onChange }: SidebarProps) {
  const { health, offline, loading, lastChecked } = useHealth();
  const status = deriveStatus(health?.status ?? '', offline);
  const color = STATUS_COLORS[status];
  const statusLabel = offline ? 'Backend offline' : status;

  return (
    <aside className="flex h-full w-[240px] shrink-0 flex-col border-r border-hairline bg-bg">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <div
          className="flex h-7 w-7 items-center justify-center rounded-md"
          style={{ background: 'linear-gradient(135deg,#6366f1,#818cf8)' }}
        >
          <Hexagon size={16} color="#0f1117" fill="#0f1117" strokeWidth={0} />
        </div>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-tight text-text">Triage</div>
          <div className="font-mono text-[10px] text-faint">support agent console</div>
        </div>
      </div>

      <div className="px-3 pb-2 pt-1">
        <div
          className="flex items-center gap-2 rounded-md border border-hairline bg-card px-2.5 py-2"
          title={lastChecked ? `Last checked ${clockTime(lastChecked)}` : 'Checking…'}
        >
          <span className="relative flex h-2 w-2">
            {status === 'healthy' && !offline && (
              <span
                className="absolute inline-flex h-full w-full rounded-full pulse-dot"
                style={{ backgroundColor: color }}
              />
            )}
            <span
              className="relative inline-flex h-2 w-2 rounded-full"
              style={{ backgroundColor: color }}
            />
          </span>
          <span
            className="text-[12px] font-medium capitalize"
            style={{ color }}
          >
            {loading && !health ? 'Checking…' : statusLabel}
          </span>
          <span className="ml-auto font-mono text-[10px] text-faint">
            {lastChecked ? clockTime(lastChecked) : '—'}
          </span>
        </div>
      </div>

      <div className="px-3 py-3">
        <TabBar active={active} onChange={onChange} />
      </div>

      <div className="mx-3 my-2 border-t border-hairline" />

      <div className="px-4 py-2">
        <div className="label-eyebrow mb-2">Model</div>
        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex justify-between gap-2">
            <span className="text-faint">provider</span>
            <span className="truncate text-muted">{offline ? '—' : health?.provider ?? '…'}</span>
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-faint">model</span>
            <span className="truncate text-muted">{offline ? '—' : health?.model ?? '…'}</span>
          </div>
          <div className="flex justify-between gap-2">
            <span className="text-faint">version</span>
            <span className="truncate text-muted">{offline ? '—' : health?.version ?? '…'}</span>
          </div>
        </div>
      </div>

      <div className="px-4 py-3">
        <div className="label-eyebrow mb-2.5">Pipeline</div>
        <ol className="relative space-y-2.5">
          {PIPELINE_STEPS.map((step, i) => (
            <li key={step} className="flex items-center gap-2.5">
              <span className="tnum flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-hairline bg-card font-mono text-[9px] text-muted">
                {i + 1}
              </span>
              <span className="text-[12px] text-muted">{step}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="mt-auto px-3 py-3">
        <div className="flex gap-2">
          <QuickLink href={`${API_BASE}/docs`} icon={<BookOpen size={13} />} label="Docs" />
          <QuickLink href={`${API_BASE}/redoc`} icon={<FileCode2 size={13} />} label="ReDoc" />
        </div>
      </div>
    </aside>
  );
}

function QuickLink({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={clsx(
        'flex flex-1 items-center justify-center gap-1.5 rounded-md border border-hairline bg-card px-2 py-1.5',
        'text-[12px] text-muted transition-colors duration-150 hover:border-accent hover:text-text',
      )}
    >
      {icon}
      {label}
    </a>
  );
}
