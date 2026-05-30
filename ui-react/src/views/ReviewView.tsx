import { useState, useCallback } from 'react';
import { CheckCircle, XCircle, RefreshCw, Inbox } from 'lucide-react';
import { submitFeedback } from '../api';
import { ErrorState, LoadingState } from '../components/States';
import { categoryColor, PRIORITY_COLORS } from '../constants';
import type { Ticket } from '../types';
import { useReviewQueue } from '../hooks/useReviewQueue';

export function ReviewView() {
  const { tickets, loading, error, refresh } = useReviewQueue();

  if (loading && tickets.length === 0) return <LoadingState label="Loading review queue…" />;
  if (error && tickets.length === 0)   return <ErrorState error={error} onRetry={refresh} />;

  return (
    <div className="mx-auto w-full max-w-[1280px] space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[18px] font-semibold tracking-tight text-text">Human Review Queue</h2>
          <p className="font-mono text-[11px] text-faint">
            {tickets.length} ticket{tickets.length !== 1 ? 's' : ''} awaiting review
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-1.5 rounded-lg border border-hairline px-3 py-2 text-[13px] text-muted transition-colors duration-150 hover:text-text"
        >
          <RefreshCw size={13} />
          Refresh
        </button>
      </div>

      {tickets.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20 text-center">
          <Inbox size={40} className="text-faint" />
          <p className="text-[14px] text-muted">Queue is empty</p>
          <p className="text-[12px] text-faint">
            Low-confidence or ungrounded tickets are routed here automatically
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {tickets.map((t) => (
            <ReviewCard key={t.id} ticket={t} onAction={refresh} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewCard({ ticket, onAction }: { ticket: Ticket; onAction: () => void }) {
  const [editing, setEditing]     = useState(false);
  const [corrReply, setCorrReply] = useState(ticket.reply);
  const [corrCat, setCorrCat]     = useState(ticket.category);
  const [busy, setBusy]           = useState(false);
  const [done, setDone]           = useState(false);

  const submit = useCallback(async (approved: boolean) => {
    setBusy(true);
    try {
      await submitFeedback(Number(ticket.id), {
        approved,
        corrected_category: editing ? corrCat  : null,
        corrected_reply:    editing ? corrReply : null,
      });
      setDone(true);
      setTimeout(onAction, 500);
    } finally {
      setBusy(false);
    }
  }, [ticket.id, editing, corrCat, corrReply, onAction]);

  if (done) return null;

  const priColor = PRIORITY_COLORS[ticket.priority] ?? '#94a3b8';
  const catColor = categoryColor(ticket.category, 0);

  return (
    <div
      className="rounded-xl border border-hairline bg-surface p-4 shadow-card"
      style={{ borderLeftWidth: 3, borderLeftColor: priColor }}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="rounded px-2 py-0.5 text-[11px] font-semibold" style={{color:catColor,background:`${catColor}22`}}>{ticket.category}</span>
        <span className="rounded px-2 py-0.5 text-[11px] font-semibold" style={{color:priColor,background:`${priColor}22`}}>{ticket.priority}</span>
        <span className="font-mono text-[11px] text-faint">
          {ticket.timestamp?.slice(0, 16).replace('T', ' ')}
        </span>
        {ticket.customer_id && (
          <span className="font-mono text-[11px] text-faint">· {ticket.customer_id}</span>
        )}
        <span className="ml-auto font-mono text-[11px] text-faint">conf {ticket.confidence}%</span>
      </div>

      <p className="mb-3 text-[13px] leading-relaxed text-muted">{ticket.ticket_text}</p>

      <div className="mb-4 rounded-lg border border-hairline bg-bg p-3">
        {editing ? (
          <div className="space-y-2">
            <select
              value={corrCat}
              onChange={(e) => setCorrCat(e.target.value)}
              className="w-full rounded border border-hairline bg-surface px-2 py-1 text-[12px] text-text"
            >
              {['Account','Billing','Order','Shipping','Technical Support','Feedback','Other'].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
            <textarea
              rows={4}
              value={corrReply}
              onChange={(e) => setCorrReply(e.target.value)}
              className="w-full resize-none rounded border border-hairline bg-surface px-2 py-1.5 text-[12px] text-text"
            />
          </div>
        ) : (
          <p className="text-[12px] leading-relaxed text-muted">{ticket.reply}</p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => void submit(true)}
          disabled={busy}
          className="flex items-center gap-1.5 rounded-lg bg-[#34d399]/15 px-3 py-1.5 text-[13px] font-medium text-[#34d399] transition-colors duration-150 hover:bg-[#34d399]/25 disabled:opacity-50"
        >
          <CheckCircle size={14} /> Approve
        </button>
        <button
          onClick={() => void submit(false)}
          disabled={busy}
          className="flex items-center gap-1.5 rounded-lg bg-[#f87171]/15 px-3 py-1.5 text-[13px] font-medium text-[#f87171] transition-colors duration-150 hover:bg-[#f87171]/25 disabled:opacity-50"
        >
          <XCircle size={14} /> Reject
        </button>
        <button
          onClick={() => setEditing((v) => !v)}
          className="ml-auto text-[12px] text-faint underline-offset-2 hover:text-muted hover:underline"
        >
          {editing ? 'Cancel' : 'Edit reply'}
        </button>
      </div>
    </div>
  );
}
