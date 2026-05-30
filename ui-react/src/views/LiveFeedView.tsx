import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { Pause, Play, RefreshCw, Radio, X } from 'lucide-react';
import { useLiveFeed } from '../hooks/useLiveFeed';
import { CategoryBadge, GroundedBadge, PriorityBadge } from '../components/Badge';
import { EmptyState, ErrorState, LoadingState } from '../components/States';
import { PRIORITY_COLORS, categoryColor, isUrgentRoute } from '../constants';
import { clockTime, relativeTime } from '../time';
import type { Ticket } from '../types';

function hashIdx(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function useTick(ms: number) {
  const [, setN] = useState(0);
  useEffect(() => {
    const id = window.setInterval(() => setN((n) => n + 1), ms);
    return () => window.clearInterval(id);
  }, [ms]);
}

export function LiveFeedView() {
  const [paused, setPaused] = useState(false);
  const { tickets, loading, error, lastUpdated, refresh } = useLiveFeed(paused);
  const [selected, setSelected] = useState<Ticket | null>(null);
  useTick(1000);

  const prevIds = useRef<Set<string | number>>(new Set());
  const newIds = useMemo(() => {
    const next = new Set<string | number>();
    const fresh = new Set<string | number>();
    for (const t of tickets) {
      next.add(t.id);
      if (!prevIds.current.has(t.id)) fresh.add(t.id);
    }
    // first load: don't flag everything as new
    if (prevIds.current.size === 0) {
      prevIds.current = next;
      return new Set<string | number>();
    }
    prevIds.current = next;
    return fresh;
  }, [tickets]);

  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelected(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [selected]);

  return (
    <div className="mx-auto w-full max-w-[920px]">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-[18px] font-semibold tracking-tight text-text">
            Live feed
            {!paused && (
              <span className="relative flex h-2 w-2">
                <span className="pulse-dot absolute inline-flex h-full w-full rounded-full bg-low" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-low" />
              </span>
            )}
          </h2>
          <p className="font-mono text-[11px] text-faint">
            polling /tickets every 5s ·{' '}
            {lastUpdated ? `updated ${clockTime(lastUpdated)}` : 'connecting…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void refresh()}
            className="inline-flex items-center gap-1.5 rounded-md border border-hairline bg-card px-2.5 py-1.5 text-[12px] text-muted transition-colors duration-150 hover:border-accent hover:text-text"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : undefined} />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            className={clsx(
              'inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1.5 text-[12px] font-medium transition-colors duration-150',
              paused
                ? 'border-med/40 bg-[rgba(251,191,36,0.08)] text-med'
                : 'border-hairline bg-card text-muted hover:border-accent hover:text-text',
            )}
          >
            {paused ? <Play size={13} /> : <Pause size={13} />}
            {paused ? 'Resume' : 'Pause'}
          </button>
        </div>
      </div>

      {paused && (
        <div className="mb-3 flex items-center gap-2 rounded-md border border-med/30 bg-[rgba(251,191,36,0.07)] px-3 py-2 text-[12px] text-med">
          <Pause size={13} />
          Paused — feed frozen at {lastUpdated ? clockTime(lastUpdated) : '—'}. Resume or refresh to
          update.
        </div>
      )}

      {loading && tickets.length === 0 && <LoadingState label="Fetching tickets…" />}
      {error && tickets.length === 0 && <ErrorState error={error} onRetry={() => void refresh()} />}
      {!loading && !error && tickets.length === 0 && (
        <EmptyState
          icon={<Radio size={26} />}
          title="No tickets yet"
          hint="Analyzed tickets will stream in here, newest first."
        />
      )}

      <div className="space-y-2">
        {tickets.map((t) => (
          <FeedCard
            key={t.id}
            ticket={t}
            isNew={newIds.has(t.id)}
            onClick={() => setSelected(t)}
          />
        ))}
      </div>

      {selected && <DetailDrawer ticket={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function FeedCard({
  ticket,
  isNew,
  onClick,
}: {
  ticket: Ticket;
  isNew: boolean;
  onClick: () => void;
}) {
  const border = PRIORITY_COLORS[ticket.priority];
  const urgent = isUrgentRoute(ticket.route_to);
  const catColor = categoryColor(ticket.category, hashIdx(ticket.category));

  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'block w-full rounded-lg border border-hairline bg-card text-left transition-colors duration-150 hover:border-[#343a4a]',
        isNew && 'animate-feed-in',
      )}
      style={{ borderLeft: `3px solid ${border}` }}
    >
      <div className="px-3.5 py-3">
        <div className="mb-2 flex items-center gap-2">
          <CategoryBadge category={ticket.category} color={catColor} />
          <PriorityBadge priority={ticket.priority} />
          <GroundedBadge grounded={ticket.grounded} />
          <span className="tnum ml-auto font-mono text-[11px] text-faint">
            {relativeTime(ticket.timestamp)}
          </span>
        </div>
        <p className="line-clamp-2 text-[13px] leading-relaxed text-text">{ticket.ticket_text}</p>
        <div className="mt-2 flex items-center gap-2 text-[12px]">
          {urgent && (
            <span
              className="pulse-dot inline-block h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: '#f87171' }}
            />
          )}
          <span className="text-faint">→</span>
          <span style={{ color: urgent ? '#f87171' : '#9ca3af' }}>{ticket.route_to}</span>
          <span className="tnum ml-auto font-mono text-faint">{ticket.confidence}%</span>
        </div>
      </div>
    </button>
  );
}

function DetailDrawer({ ticket, onClose }: { ticket: Ticket; onClose: () => void }) {
  const catColor = categoryColor(ticket.category, hashIdx(ticket.category));
  const urgent = isUrgentRoute(ticket.route_to);

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="animate-fade-in absolute inset-0 bg-black/50"
      />
      <div className="animate-drawer-in relative flex h-full w-full max-w-[440px] flex-col border-l border-hairline bg-card">
        <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
          <div>
            <div className="label-eyebrow">Ticket</div>
            <div className="tnum font-mono text-[12px] text-muted">#{String(ticket.id)}</div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-hairline p-1.5 text-muted transition-colors duration-150 hover:border-accent hover:text-text"
          >
            <X size={15} />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <CategoryBadge category={ticket.category} color={catColor} />
            <PriorityBadge priority={ticket.priority} />
            <GroundedBadge grounded={ticket.grounded} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Meta label="Confidence" value={`${ticket.confidence}%`} />
            <Meta label="Received" value={relativeTime(ticket.timestamp)} />
            <Meta
              label="Route"
              value={ticket.route_to}
              color={urgent ? '#f87171' : undefined}
              span
            />
          </div>

          <div>
            <div className="label-eyebrow mb-1.5">Ticket text</div>
            <p className="rounded-lg border border-hairline bg-bg px-3 py-2.5 text-[13px] leading-relaxed text-text">
              {ticket.ticket_text}
            </p>
          </div>

          <div>
            <div className="label-eyebrow mb-1.5">Drafted reply</div>
            {ticket.reply ? (
              <p className="whitespace-pre-wrap rounded-lg border border-hairline bg-bg px-3 py-2.5 text-[13px] leading-relaxed text-muted">
                {ticket.reply}
              </p>
            ) : (
              <p className="rounded-lg border border-dashed border-hairline px-3 py-2.5 text-[12px] text-faint">
                No reply on record.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Meta({
  label,
  value,
  color,
  span,
}: {
  label: string;
  value: string;
  color?: string;
  span?: boolean;
}) {
  return (
    <div className={clsx('rounded-lg border border-hairline bg-bg px-3 py-2', span && 'col-span-2')}>
      <div className="label-eyebrow mb-1">{label}</div>
      <div
        className="tnum font-mono text-[13px] font-medium"
        style={{ color: color ?? '#e5e7eb' }}
      >
        {value}
      </div>
    </div>
  );
}
