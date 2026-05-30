import {
  ApiError,
  type AnalyzeResult,
  type HealthResponse,
  type Metrics,
  type Priority,
  type Ticket,
} from './types';

export const API_BASE = 'http://localhost:8000';

const VALID_PRIORITIES: Priority[] = ['Critical', 'High', 'Medium', 'Low'];

function asPriority(value: unknown): Priority {
  if (typeof value === 'string') {
    const match = VALID_PRIORITIES.find((p) => p.toLowerCase() === value.toLowerCase());
    if (match) return match;
  }
  return 'Medium';
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function asBool(value: unknown): boolean {
  return value === true;
}

async function toApiError(res: Response): Promise<ApiError> {
  let detail = res.statusText;
  try {
    const body: unknown = await res.json();
    if (body && typeof body === 'object' && 'detail' in body) {
      const d = (body as { detail: unknown }).detail;
      if (typeof d === 'string') detail = d;
    }
  } catch {
    /* ignore non-json */
  }
  if (res.status === 422) return new ApiError('validation', 422, detail || 'Validation failed');
  if (res.status === 429) {
    const ra = Number(res.headers.get('retry-after'));
    return new ApiError(
      'rate_limit',
      429,
      detail || 'Rate limit reached',
      Number.isFinite(ra) && ra > 0 ? ra : undefined,
    );
  }
  return new ApiError('server', res.status, detail || `Server error (${res.status})`);
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
  } catch {
    throw new ApiError('network', 0, 'Backend unreachable');
  }
}

function parseAnalyzeResult(raw: unknown): AnalyzeResult {
  const r = (raw ?? {}) as Record<string, unknown>;
  return {
    ticket_id:   typeof r.ticket_id === 'number' ? r.ticket_id : 0,
    category:    asString(r.category, 'Uncategorized'),
    priority:    asPriority(r.priority),
    confidence:  Math.round(asNumber(r.confidence) * 10), // backend 0-10 -> UI 0-100
    grounded:    asBool(r.grounded),
    route_to:    asString(r.route_to, 'Unassigned'),
    reply_draft: asString(r.reply_draft),
  };
}

export async function analyze(
  text: string,
  options?: { customer_id?: string; thread_id?: string; signal?: AbortSignal },
): Promise<AnalyzeResult> {
  const res = await request('/analyze', {
    method: 'POST',
    body: JSON.stringify({
      text,
      customer_id: options?.customer_id ?? '',
      thread_id:   options?.thread_id   ?? '',
    }),
    signal: options?.signal,
  });
  if (!res.ok) throw await toApiError(res);
  return parseAnalyzeResult(await res.json());
}

export function analyzeStream(
  text: string,
  opts: {
    customer_id?: string;
    thread_id?: string;
    onEvent: (event: string, payload: Record<string, unknown>) => void;
    signal?: AbortSignal;
  },
): void {
  fetch(`${API_BASE}/analyze/stream`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, customer_id: opts.customer_id ?? '', thread_id: opts.thread_id ?? '' }),
    signal: opts.signal,
  })
    .then(async (res) => {
      if (!res.ok || !res.body) throw new Error('Stream failed');
      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let   buf     = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n\n');
        buf = lines.pop() ?? '';
        for (const line of lines) {
          const data = line.replace(/^data:\s*/, '').trim();
          if (!data) continue;
          try {
            const p = JSON.parse(data) as Record<string, unknown>;
            opts.onEvent(typeof p.event === 'string' ? p.event : 'unknown', p);
          } catch { /* skip */ }
        }
      }
    })
    .catch((err) => {
      if ((err as Error).name !== 'AbortError') opts.onEvent('error', { message: String(err) });
    });
}

export async function submitFeedback(
  ticketId: number,
  body: import('./types').FeedbackRequest,
): Promise<void> {
  const res = await request(`/tickets/${ticketId}/feedback`, {
    method: 'POST', body: JSON.stringify(body),
  });
  if (!res.ok) throw await toApiError(res);
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await request('/health', { signal });
  if (!res.ok) throw await toApiError(res);
  const raw: unknown = await res.json();
  const r = (raw ?? {}) as Record<string, unknown>;
  return {
    status:   asString(r.status, 'unknown'),
    version:  asString(r.version, '—'),
    provider: asString(r.provider, '—'),
    model:    asString(r.model, '—'),
    auth:     asBool(r.auth),
  };
}

export async function getTickets(
  limit = 25,
  offset = 0,
  route?: string,
  signal?: AbortSignal,
): Promise<Ticket[]> {
  const qs = route
    ? `/tickets?limit=${limit}&offset=${offset}&route=${encodeURIComponent(route)}`
    : `/tickets?limit=${limit}&offset=${offset}`;
  const res = await request(qs, { signal });
  if (!res.ok) throw await toApiError(res);
  const raw: unknown = await res.json();
  if (!Array.isArray(raw)) return [];
  return raw.map((item): Ticket => {
    const r = (item ?? {}) as Record<string, unknown>;
    return {
      id: typeof r.id === 'number' || typeof r.id === 'string' ? r.id : crypto.randomUUID(),
      timestamp: asString(r.timestamp, new Date().toISOString()),
      ticket_text: asString(r.ticket_text),
      category: asString(r.category, 'Uncategorized'),
      priority: asPriority(r.priority),
      confidence: Math.round(asNumber(r.confidence) * 10), // backend: 0-10 → UI: 0-100
      grounded: asBool(r.grounded),
      route_to: asString(r.route_to, 'Unassigned'),
      reply: asString(r.reply),
    };
  });
}

export async function getMetrics(signal?: AbortSignal): Promise<Metrics> {
  const res = await request('/metrics', { signal });
  if (!res.ok) throw await toApiError(res);
  const raw: unknown = await res.json();
  const r = (raw ?? {}) as Record<string, unknown>;
  const rec = (v: unknown): Record<string, number> => {
    const out: Record<string, number> = {};
    if (v && typeof v === 'object') {
      for (const [k, val] of Object.entries(v as Record<string, unknown>)) {
        if (typeof val === 'number' && Number.isFinite(val)) out[k] = val;
      }
    }
    return out;
  };
  return {
    total: asNumber(r.total),
    avg_confidence:     asNumber(r.avg_confidence) * 10,
    human_review_count: asNumber(r.human_review_count),
    grounding_rate:     asNumber(r.grounding_rate),
    by_category: rec(r.by_category),
    by_priority: rec(r.by_priority),
  };
}
