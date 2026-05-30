import clsx from 'clsx';
import type { ReactNode } from 'react';
import type { Priority } from '../types';
import { GROUNDED, PRIORITY_COLORS } from '../constants';

function hexToTint(hex: string, alpha: number): string {
  const n = hex.replace('#', '');
  const r = parseInt(n.slice(0, 2), 16);
  const g = parseInt(n.slice(2, 4), 16);
  const b = parseInt(n.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

interface BaseBadgeProps {
  children: ReactNode;
  fg: string;
  bg: string;
  icon?: ReactNode;
  className?: string;
  title?: string;
}

export function Badge({ children, fg, bg, icon, className, title }: BaseBadgeProps) {
  return (
    <span
      title={title}
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[12px] font-medium leading-5',
        className,
      )}
      style={{ color: fg, backgroundColor: bg, border: `1px solid ${hexToTint(fg, 0.22)}` }}
    >
      {icon}
      {children}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  const color = PRIORITY_COLORS[priority];
  return (
    <Badge fg={color} bg={hexToTint(color, 0.12)}>
      <span
        className="inline-block h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: color }}
        aria-hidden
      />
      {priority}
    </Badge>
  );
}

export function CategoryBadge({ category, color }: { category: string; color: string }) {
  return (
    <Badge fg={color} bg={hexToTint(color, 0.12)}>
      {category}
    </Badge>
  );
}

export function GroundedBadge({ grounded }: { grounded: boolean }) {
  const c = grounded ? GROUNDED.yes : GROUNDED.no;
  return (
    <Badge fg={c.fg} bg={c.bg}>
      {grounded ? 'Grounded' : 'Ungrounded'}
    </Badge>
  );
}
