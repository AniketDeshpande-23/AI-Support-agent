import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import {
  ArrowRight,
  Check,
  ChevronDown,
  Copy,
  CornerDownLeft,
  Loader2,
  Sparkles,
  Zap,
} from 'lucide-react';
import { useAnalyze } from '../hooks/useAnalyze';
import { CategoryBadge, GroundedBadge, PriorityBadge } from '../components/Badge';
import { ConfidenceArc } from '../components/ConfidenceArc';
import { ErrorState } from '../components/States';
import { SAMPLE_TICKETS, categoryColor, isUrgentRoute } from '../constants';
import type { AnalyzeResult } from '../types';

const MAX = 2000;
const MIN = 10;

const prefersReduced =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

export function AnalyzeView() {
  const [text, setText] = useState('');
  const [sampleIdx, setSampleIdx] = useState<number>(-1);
  const { result, loading, error, run, reset } = useAnalyze();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const len = text.length;
  const tooShort = len < MIN;
  const canSubmit = !loading && len >= MIN && len <= MAX;

  const counterColor =
    len >= MAX ? '#f87171' : len > 1800 ? '#fbbf24' : '#6b7280';

  const submit = () => {
    if (!canSubmit) return;
    void run(text.slice(0, MAX));
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      submit();
    }
  };

  const pickSample = (i: number) => {
    setSampleIdx(i);
    if (i >= 0) {
      setText(SAMPLE_TICKETS[i].text);
      reset();
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
  };

  return (
    <div className="mx-auto grid w-full max-w-[1100px] grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
      {/* Input panel */}
      <section className="rounded-xl border border-hairline bg-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[15px] font-semibold text-text">New ticket</h2>
          <SampleSelect value={sampleIdx} onChange={pickSample} />
        </div>

        <div className="relative">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value.slice(0, MAX));
              setSampleIdx(-1);
            }}
            onKeyDown={onKeyDown}
            placeholder="Paste a customer ticket, or load a sample above…"
            rows={9}
            className={clsx(
              'w-full resize-none rounded-lg border bg-bg px-3 py-2.5 font-sans text-[14px] leading-relaxed text-text',
              'placeholder:text-faint transition-colors duration-150',
              'border-hairline focus:border-accent focus:outline-none',
            )}
          />
          <div className="pointer-events-none absolute bottom-2.5 right-3">
            <span className="tnum font-mono text-[11px]" style={{ color: counterColor }}>
              {len} / {MAX}
            </span>
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            onClick={submit}
            disabled={!canSubmit}
            className={clsx(
              'inline-flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-semibold',
              'transition-colors duration-150 disabled:cursor-not-allowed',
              canSubmit
                ? 'bg-accent text-bg hover:bg-[#9aa3f7]'
                : 'border border-hairline bg-card text-faint',
            )}
          >
            {loading ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                Analyzing…
              </>
            ) : (
              <>
                <Sparkles size={15} />
                Analyze
              </>
            )}
          </button>
          <span className="flex items-center gap-1 font-mono text-[11px] text-faint">
            <kbd className="rounded border border-hairline px-1 py-0.5">
              <CornerDownLeft size={10} className="inline" /> Ctrl
            </kbd>
            to run
          </span>
          {tooShort && len > 0 && (
            <span className="ml-auto text-[11px] text-muted">
              {MIN - len} more chars to analyze
            </span>
          )}
        </div>
      </section>

      {/* Results panel */}
      <section className="min-h-[360px] rounded-xl border border-hairline bg-card p-4">
        {loading && !result && <ResultSkeleton />}
        {error && !loading && <ErrorState error={error} onRetry={submit} />}
        {!loading && !error && !result && <ResultsEmpty />}
        {result && !error && <ResultCard result={result} />}
      </section>
    </div>
  );
}

function SampleSelect({
  value,
  onChange,
}: {
  value: number;
  onChange: (i: number) => void;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="tnum appearance-none rounded-md border border-hairline bg-bg py-1.5 pl-2.5 pr-7 text-[12px] text-muted transition-colors duration-150 hover:border-accent focus:border-accent focus:outline-none"
      >
        <option value={-1}>Load sample…</option>
        {SAMPLE_TICKETS.map((s, i) => (
          <option key={s.label} value={i}>
            {s.label}
          </option>
        ))}
      </select>
      <ChevronDown
        size={13}
        className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-faint"
      />
    </div>
  );
}

function ResultsEmpty() {
  return (
    <div className="dot-grid flex h-full min-h-[330px] flex-col items-center justify-center gap-2 rounded-lg text-center">
      <Sparkles size={24} className="text-faint" />
      <div className="text-[14px] font-medium text-muted">No analysis yet</div>
      <div className="max-w-[240px] text-[12px] text-faint">
        Run a ticket to see category, priority, confidence, grounding, routing, and a drafted reply.
      </div>
    </div>
  );
}

function ResultSkeleton() {
  return (
    <div className="animate-fade-in space-y-4">
      <div className="flex items-center gap-5">
        <div className="h-[132px] w-[132px] shrink-0 animate-pulse rounded-full bg-hairline" />
        <div className="flex-1 space-y-2">
          <div className="h-5 w-24 animate-pulse rounded bg-hairline" />
          <div className="h-5 w-32 animate-pulse rounded bg-hairline" />
          <div className="h-5 w-40 animate-pulse rounded bg-hairline" />
        </div>
      </div>
      <div className="h-px bg-hairline" />
      <div className="space-y-2">
        <div className="h-3 w-full animate-pulse rounded bg-hairline" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-hairline" />
        <div className="h-3 w-4/6 animate-pulse rounded bg-hairline" />
      </div>
    </div>
  );
}

function ResultCard({ result }: { result: AnalyzeResult }) {
  const urgent = isUrgentRoute(result.route_to);
  const catColor = useMemo(() => categoryColor(result.category, hashIdx(result.category)), [result.category]);

  return (
    <div className="animate-fade-in space-y-4">
      <div className="flex items-center gap-5">
        <ConfidenceArc value={result.confidence} />
        <div className="flex flex-1 flex-col gap-2.5">
          <div className="flex flex-wrap items-center gap-2">
            <CategoryBadge category={result.category} color={catColor} />
            <PriorityBadge priority={result.priority} />
            <GroundedBadge grounded={result.grounded} />
          </div>
          <div className="mt-1">
            <div className="label-eyebrow mb-1.5">Route to</div>
            <div className="flex items-center gap-2">
              {urgent && (
                <span
                  className="inline-block h-2 w-2 rounded-full pulse-dot"
                  style={{ backgroundColor: '#f87171' }}
                  aria-label="urgent"
                />
              )}
              <ArrowRight size={14} className="text-accent" />
              <span
                className="text-[14px] font-medium"
                style={{ color: urgent ? '#f87171' : '#e5e7eb' }}
              >
                {result.route_to}
              </span>
              {urgent && <Zap size={13} className="text-crit" />}
            </div>
          </div>
        </div>
      </div>

      <div className="h-px bg-hairline" />

      <ReplyPanel reply={result.reply_draft} key={result.reply_draft} />
    </div>
  );
}

function hashIdx(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function ReplyPanel({ reply }: { reply: string }) {
  const words = useMemo(() => reply.split(/(\s+)/), [reply]);
  const [count, setCount] = useState(prefersReduced ? words.length : 0);
  const [copied, setCopied] = useState(false);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    setCopied(false);
    if (prefersReduced) {
      setCount(words.length);
      return;
    }
    setCount(0);
    let i = 0;
    const step = () => {
      i += 1;
      setCount(i);
      if (i < words.length) timerRef.current = window.setTimeout(step, 28);
    };
    timerRef.current = window.setTimeout(step, 28);
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [words]);

  const done = count >= words.length;
  const shown = words.slice(0, count).join('');

  const skip = () => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    setCount(words.length);
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(reply);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard unavailable */
    }
  };

  if (!reply) {
    return (
      <div className="rounded-lg border border-dashed border-hairline px-3 py-4 text-center text-[12px] text-faint">
        No reply draft returned.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="label-eyebrow">Drafted reply</span>
        <div className="flex items-center gap-2">
          {!done && (
            <button
              type="button"
              onClick={skip}
              className="rounded-md border border-hairline px-2 py-1 text-[11px] text-muted transition-colors duration-150 hover:border-accent hover:text-text"
            >
              Skip animation
            </button>
          )}
          <button
            type="button"
            onClick={copy}
            className={clsx(
              'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] transition-colors duration-150',
              copied
                ? 'border-low/40 text-low'
                : 'border-hairline text-muted hover:border-accent hover:text-text',
            )}
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>
      <div className="rounded-lg border border-hairline bg-bg px-3.5 py-3 text-[13px] leading-relaxed text-text">
        <span className="whitespace-pre-wrap">{shown}</span>
        {!done && (
          <span
            className="caret-blink ml-0.5 inline-block h-[15px] w-[2px] translate-y-[2px] bg-accent align-middle"
            aria-hidden
          />
        )}
      </div>
    </div>
  );
}
