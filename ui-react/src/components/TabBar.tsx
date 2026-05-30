import clsx from 'clsx';
import { Inbox, LayoutDashboard, Radio, type LucideIcon } from 'lucide-react';
import type { ViewKey } from '../types';

interface TabDef {
  key: ViewKey;
  label: string;
  icon: LucideIcon;
  hint: string;
}

const TABS: TabDef[] = [
  { key: 'analyze', label: 'Analyze', icon: Inbox, hint: '1' },
  { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, hint: '2' },
  { key: 'feed', label: 'Live Feed', icon: Radio, hint: '3' },
];

interface TabBarProps {
  active: ViewKey;
  onChange: (k: ViewKey) => void;
}

export function TabBar({ active, onChange }: TabBarProps) {
  return (
    <nav className="flex flex-col gap-0.5" aria-label="Primary">
      {TABS.map((t) => {
        const isActive = t.key === active;
        const Icon = t.icon;
        return (
          <button
            key={t.key}
            type="button"
            onClick={() => onChange(t.key)}
            aria-current={isActive ? 'page' : undefined}
            className={clsx(
              'group relative flex items-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] font-medium',
              'transition-colors duration-150',
              isActive
                ? 'bg-[rgba(129,140,248,0.10)] text-text'
                : 'text-muted hover:bg-[rgba(255,255,255,0.03)] hover:text-text',
            )}
          >
            <span
              className={clsx(
                'absolute left-0 top-1/2 h-5 w-[2.5px] -translate-y-1/2 rounded-full transition-opacity duration-150',
                isActive ? 'opacity-100' : 'opacity-0',
              )}
              style={{ backgroundColor: '#818cf8' }}
              aria-hidden
            />
            <Icon
              size={16}
              strokeWidth={isActive ? 2.4 : 2}
              color={isActive ? '#818cf8' : 'currentColor'}
            />
            <span className="flex-1 text-left">{t.label}</span>
            <kbd
              className="tnum rounded border border-hairline px-1 font-mono text-[10px] text-faint opacity-0 transition-opacity duration-150 group-hover:opacity-100"
            >
              {t.hint}
            </kbd>
          </button>
        );
      })}
    </nav>
  );
}
