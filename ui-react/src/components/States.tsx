import { AlertTriangle, Inbox, Loader2, ServerCrash, Timer } from 'lucide-react';
import type { ReactNode } from 'react';
import { ApiError } from '../types';

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-muted">
      <Loader2 size={22} className="animate-spin text-accent" />
      <span className="text-[13px]">{label}</span>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  hint,
}: {
  icon?: ReactNode;
  title: string;
  hint?: string;
}) {
  return (
    <div className="dot-grid flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-hairline py-14 text-center">
      <div className="text-faint">{icon ?? <Inbox size={26} />}</div>
      <div className="text-[14px] font-medium text-muted">{title}</div>
      {hint && <div className="max-w-xs text-[12px] text-faint">{hint}</div>}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
}: {
  error: ApiError;
  onRetry?: () => void;
}) {
  const isNetwork = error.kind === 'network';
  const Icon = isNetwork ? ServerCrash : error.kind === 'rate_limit' ? Timer : AlertTriangle;
  const title =
    error.kind === 'network'
      ? 'Backend unreachable'
      : error.kind === 'rate_limit'
        ? 'Rate limited'
        : error.kind === 'validation'
          ? 'Invalid request'
          : 'Request failed';
  const tint =
    error.kind === 'rate_limit' || error.kind === 'validation' ? '#fbbf24' : '#f87171';

  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-xl border py-12 text-center"
      style={{ borderColor: `${tint}33`, backgroundColor: `${tint}0d` }}
    >
      <Icon size={24} color={tint} />
      <div className="text-[14px] font-medium text-text">{title}</div>
      <div className="max-w-sm px-4 text-[12px] text-muted">
        {error.message}
        {error.kind === 'network' && ' — is the API running on :8000?'}
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 rounded-md border border-hairline bg-card px-3 py-1.5 text-[12px] font-medium text-text transition-colors duration-150 hover:border-accent"
        >
          Retry
        </button>
      )}
    </div>
  );
}
