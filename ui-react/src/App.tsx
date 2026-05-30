import { useCallback, useEffect, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { AnalyzeView } from './views/AnalyzeView';
import { DashboardView } from './views/DashboardView';
import { LiveFeedView } from './views/LiveFeedView';
import type { ViewKey } from './types';
import { Keyboard, X } from 'lucide-react';

const TITLES: Record<ViewKey, { title: string; sub: string }> = {
  analyze: { title: 'Analyze', sub: 'Classify, prioritize, route and draft a reply for a ticket' },
  dashboard: { title: 'Dashboard', sub: 'Operational metrics derived from the agent pipeline' },
  feed: { title: 'Live Feed', sub: 'Real-time stream of analyzed tickets' },
};

function isTyping(): boolean {
  const el = document.activeElement;
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || (el as HTMLElement).isContentEditable;
}

export default function App() {
  const [view, setView] = useState<ViewKey>('analyze');
  const [showHelp, setShowHelp] = useState(false);
  const [gPressed, setGPressed] = useState(false);

  const go = useCallback((v: ViewKey) => setView(v), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowHelp(false);
        return;
      }
      if (isTyping() || e.metaKey || e.ctrlKey || e.altKey) return;

      if (gPressed) {
        if (e.key === 'a') go('analyze');
        else if (e.key === 'd') go('dashboard');
        else if (e.key === 'f') go('feed');
        setGPressed(false);
        return;
      }

      if (e.key === '1') go('analyze');
      else if (e.key === '2') go('dashboard');
      else if (e.key === '3') go('feed');
      else if (e.key === '?') setShowHelp((s) => !s);
      else if (e.key === 'g') {
        setGPressed(true);
        window.setTimeout(() => setGPressed(false), 800);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [gPressed, go]);

  const meta = TITLES[view];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-bg text-text">
      <Sidebar active={view} onChange={go} />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex shrink-0 items-center justify-between border-b border-hairline px-6 py-3.5">
          <div>
            <h1 className="text-[16px] font-semibold tracking-tight text-text">{meta.title}</h1>
            <p className="text-[12px] text-faint">{meta.sub}</p>
          </div>
          <button
            type="button"
            onClick={() => setShowHelp(true)}
            className="inline-flex items-center gap-1.5 rounded-md border border-hairline bg-card px-2.5 py-1.5 text-[12px] text-muted transition-colors duration-150 hover:border-accent hover:text-text"
          >
            <Keyboard size={13} />
            Shortcuts
            <kbd className="tnum rounded border border-hairline px-1 font-mono text-[10px]">?</kbd>
          </button>
        </header>

        <main className="min-h-0 flex-1 overflow-y-auto px-6 py-5">
          {view === 'analyze' && <AnalyzeView />}
          {view === 'dashboard' && <DashboardView />}
          {view === 'feed' && <LiveFeedView />}
        </main>
      </div>

      {showHelp && <ShortcutsModal onClose={() => setShowHelp(false)} />}
    </div>
  );
}

const SHORTCUTS: { keys: string[]; label: string }[] = [
  { keys: ['1'], label: 'Go to Analyze' },
  { keys: ['2'], label: 'Go to Dashboard' },
  { keys: ['3'], label: 'Go to Live Feed' },
  { keys: ['g', 'a'], label: 'Navigate to Analyze' },
  { keys: ['g', 'd'], label: 'Navigate to Dashboard' },
  { keys: ['g', 'f'], label: 'Navigate to Feed' },
  { keys: ['⌘', '↵'], label: 'Run analysis' },
  { keys: ['?'], label: 'Toggle this cheatsheet' },
  { keys: ['Esc'], label: 'Close drawer / dialog' },
];

function ShortcutsModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="animate-fade-in absolute inset-0 bg-black/55"
      />
      <div className="animate-fade-in relative w-full max-w-md rounded-xl border border-hairline bg-card p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-[14px] font-semibold text-text">
            <Keyboard size={15} className="text-accent" />
            Keyboard shortcuts
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-hairline p-1 text-muted transition-colors duration-150 hover:border-accent hover:text-text"
          >
            <X size={14} />
          </button>
        </div>
        <ul className="space-y-2">
          {SHORTCUTS.map((s) => (
            <li key={s.label} className="flex items-center justify-between">
              <span className="text-[13px] text-muted">{s.label}</span>
              <span className="flex items-center gap-1">
                {s.keys.map((k) => (
                  <kbd
                    key={k}
                    className="tnum rounded border border-hairline bg-bg px-1.5 py-0.5 font-mono text-[11px] text-text"
                  >
                    {k}
                  </kbd>
                ))}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
