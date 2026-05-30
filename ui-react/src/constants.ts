import type { Priority } from './types';

export const PRIORITY_COLORS: Record<Priority, string> = {
  Critical: '#f87171',
  High: '#fb923c',
  Medium: '#fbbf24',
  Low: '#34d399',
};

export const PRIORITY_ORDER: Priority[] = ['Critical', 'High', 'Medium', 'Low'];

// Deterministic palette for categories (indigo-leaning, semantic-neutral).
export const CATEGORY_PALETTE = [
  '#818cf8',
  '#34d399',
  '#fbbf24',
  '#f472b6',
  '#60a5fa',
  '#fb923c',
  '#a78bfa',
  '#2dd4bf',
];

export function categoryColor(_name: string, index: number): string {
  return CATEGORY_PALETTE[index % CATEGORY_PALETTE.length] ?? '#818cf8';
}

export const GROUNDED = {
  yes: { fg: '#34d399', bg: 'rgba(52,211,153,0.12)' },
  no: { fg: '#fbbf24', bg: 'rgba(251,191,36,0.12)' },
};

export const STATUS_COLORS = {
  healthy: '#34d399',
  degraded: '#fbbf24',
  down: '#f87171',
};

export const PIPELINE_STEPS = [
  'Classify',
  'Retrieve context',
  'Ground-check',
  'Prioritize',
  'Route',
  'Draft reply',
];

export interface SampleTicket {
  label: string;
  category: string;
  text: string;
}

export const SAMPLE_TICKETS: SampleTicket[] = [
  {
    label: 'Billing — double charge',
    category: 'Billing',
    text: "I was charged twice for my Pro subscription this month — invoice #INV-20418 and #INV-20419 both hit my card on the same day for $49 each. I only have one account. Please refund the duplicate and confirm it won't recur next cycle.",
  },
  {
    label: 'Outage — API 503s',
    category: 'Outage',
    text: 'Our production integration started returning 503s from your /v2/ingest endpoint about 20 minutes ago. Roughly 40% of requests are failing and our queue is backing up. Is there an active incident? We need an ETA — this is impacting live customers.',
  },
  {
    label: 'Bug — export corrupts CSV',
    category: 'Bug',
    text: 'When I export a report to CSV with more than ~5,000 rows, the file is truncated and the last column gets mangled with stray commas. Smaller exports are fine. Reproduced on Chrome and Firefox, latest build. Sample file attached in the ticket.',
  },
  {
    label: 'Feature request — SSO',
    category: 'Feature Request',
    text: "We're rolling you out to 200 seats but our security team requires SAML SSO with Okta before we can go company-wide. Is this on the roadmap? A rough timeline would help us plan the procurement review.",
  },
  {
    label: 'Account — locked out',
    category: 'Account',
    text: "I've been locked out of my account after too many 2FA attempts — my authenticator app reset when I changed phones and the backup codes are on the old device. Can you help me regain access? I'm the workspace owner so nobody else can let me back in.",
  },
  {
    label: 'How-to — webhook retries',
    category: 'How-To',
    text: 'Quick question on webhook behavior: if our endpoint returns a 500, how many times do you retry and over what window? And is there a way to manually replay a failed webhook delivery from the dashboard?',
  },
];

export function isUrgentRoute(route: string): boolean {
  return /urgent/i.test(route) || /—\s*urgent$/i.test(route);
}
