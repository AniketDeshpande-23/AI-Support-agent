# Product Specification: Triage — AI Support Ticket Console

> Generated from brief: "Build a production-quality React + Vite + TypeScript + Tailwind CSS single-page frontend for an AI Support Ticket Agent dashboard."

## Vision

**Triage** is an operator-grade console for an AI support agent that classifies, prioritizes, routes, and drafts replies to customer tickets in real time. It should feel like a piece of serious internal tooling — the kind of dense, confident, dark-themed control surface you'd expect inside Linear, Vercel, or a Stripe ops dashboard — not a marketing landing page. Every pixel signals "this is a working instrument," and the AI's reasoning is made legible: confidence, grounding, and routing are first-class visual citizens, never buried in JSON.

## Design Direction

- **Color palette**:
  - Background base `#0f1117`, elevated card surface `#1a1d27`, hairline borders `#262a36`.
  - Primary accent indigo `#818cf8`; deep indigo for fills `#6366f1`; muted indigo glow `rgba(129,140,248,0.12)`.
  - Text: primary `#e5e7eb`, secondary `#9ca3af`, tertiary/labels `#6b7280`.
  - Priority semantics — Critical `#f87171`, High `#fb923c`, Medium `#fbbf24`, Low `#34d399`.
  - Status semantics — healthy `#34d399`, degraded `#fbbf24`, down `#f87171`.
  - Grounded chip green `#34d399` on `rgba(52,211,153,0.12)`; ungrounded amber `#fbbf24` on `rgba(251,191,36,0.12)`.
- **Typography**: UI in `Inter` (system fallback `-apple-system, Segoe UI, sans-serif`). Numerics, IDs, timestamps, model strings in a mono face (`ui-monospace, "JetBrains Mono", monospace`) with `tabular-nums`. Hierarchy: page titles 20px/600, section labels 11px/600 uppercase tracking-wider `#6b7280`, KPI numbers 32px/700 tabular, body 14px/400.
- **Layout philosophy**: Dense control-room dashboard. Fixed 240px left sidebar + fluid main column. Generous internal padding inside cards but tight outer rhythm. 12-column implicit grid on Dashboard. Content max-width 1440px, centered above that.
- **Visual identity**: Hairline 1px borders instead of heavy shadows; soft single-layer shadows only on hover. Subtle indigo focus rings. A faint dotted/grid texture allowed on empty states only. Animated confidence arc as the signature element. Monospace metadata gives the "instrument" feel.
- **Inspiration**: Linear (sidebar + density), Vercel dashboard (dark surfaces, KPI cards), Stripe Sigma (charts), Raycast (keyboard-first polish).

### Anti-AI-slop directives (hard rules)
- No purple-to-pink hero gradients. No `transition: all`. No emoji as iconography (use `lucide-react`).
- No generic uniform "3 floating cards with a shadow" hero. No stock illustrations or undraw-style blobs.
- No center-aligned marketing copy. Every async surface must have distinct loading / error / empty states — never a bare spinner that resolves into a blank screen.
- Badges must use semantic color + subtle tinted background, not flat saturated pills.

## API Contract (verified against backend)

- `POST /analyze` body `{ text: string }` (10–2000 chars) → `{ category, priority, confidence:number(0-100), grounded:boolean, route_to, reply_draft }`. Rate-limited 10/min (handle 429). Returns 500 on failure, 422 on validation.
- `GET /health` → `{ status, version, provider, model }`.
- `GET /tickets?limit=N&offset=0` → array of `{ id, timestamp(ISO), ticket_text, category, priority, confidence, grounded, route_to, reply }` newest-first.
- `GET /metrics` → `{ total, avg_confidence, by_category: Record<string,number>, by_priority: Record<string,number> }`.
- Note: `/metrics` does NOT return grounding % or routing breakdown — derive grounding % and routing distribution client-side from `/tickets`.

## Features (prioritized)

### Must-Have (Sprint 1-2)
1. **App shell + tab navigation**: Fixed sidebar; three views Analyze / Dashboard / Live Feed switched via tab state (no router required). Active tab indicated by indigo left-accent + filled icon. Keyboard `1/2/3` switch views.
2. **Sidebar — backend status pill**: Polls `/health` on mount + every 30s. Pill shows healthy/degraded/down with colored dot; tooltip shows last-checked time. On failure → red "Backend offline."
3. **Sidebar — model info + pipeline + quick links**: Shows `provider` / `model` in mono from `/health`. Static pipeline steps list (Classify → Retrieve context → Ground-check → Prioritize → Route → Draft reply) rendered as a numbered vertical stepper. Quick links to `/docs` and `/redoc` (open new tab).
4. **Analyze — input panel**: Sample dropdown with 6 realistic tickets (one per major category). Textarea with live char counter `n / 2000`, turning amber > 1800 and red at 2000 (hard cap). Disabled Analyze button if < 10 chars. Cmd/Ctrl+Enter submits.
5. **Analyze — request lifecycle**: Analyze button shows inline spinner + "Analyzing…" while pending; disabled during flight. Handle 422 (too short/long), 429 (rate limited — show cooldown message), 500/network (retryable error card).
6. **Analyze — results card**: Category badge, priority badge (semantic color), animated confidence arc (SVG circular, 0→value ease-out ~700ms) with center % in mono, grounded/ungrounded chip, and route destination with a routing icon. Route urgency (routes ending "— Urgent") get a red pulse dot.
7. **Analyze — reply panel typewriter**: `reply_draft` revealed word-by-word (~28ms/word) with a blinking caret. "Copy" button (with copied confirmation), and "Skip animation" to reveal instantly. Respects `prefers-reduced-motion` (renders full text).
8. **Live Feed — polling list**: Polls `/tickets?limit=25` every 5s. Cards with priority-colored 3px left border, ticket excerpt (2-line clamp), category + priority + grounded badges, route, and relative timestamp ("2m ago", updating). Newest items animate in (fade + slide).
9. **Live Feed — pause/resume**: Toggle stops/starts polling; paused state shows a "Paused" banner with last-updated time. Manual refresh button always available.

### Should-Have (Sprint 3-4)
10. **Dashboard — 4 KPI cards**: Total tickets, Avg confidence (from `/metrics`), High+Critical count (sum from `by_priority`), Grounding % (derived from `/tickets` sample). Each card: label, big tabular number, tiny mono sublabel/context.
11. **Dashboard — category donut** (Recharts): `by_category` as donut with legend, category colors, center showing total. Empty state when no data.
12. **Dashboard — priority bar** (Recharts): Vertical/horizontal bar of `by_priority` using priority semantic colors, ordered Critical→Low.
13. **Dashboard — confidence histogram** (Recharts): Buckets of confidence (0-20,…,80-100) computed from `/tickets`, indigo bars.
14. **Dashboard — routing horizontal bar** (Recharts): Top routes by volume (derived from `/tickets`), urgent routes tinted red.

### Nice-to-Have (Sprint 5+)
15. **Live Feed detail drawer**: Click a feed card → right-side slide-over drawer with full ticket text, full reply, all metadata. `Esc` closes.
16. **Command palette / shortcuts**: `?` opens a shortcuts cheatsheet; `g a / g d / g f` navigation. Small but high-signal polish.
17. **Dashboard auto-refresh + density toggle**: Manual refresh + optional 15s auto-refresh; comfortable/compact spacing toggle persisted to localStorage.

## Technical Stack
- **Frontend**: React 18 + Vite + TypeScript (strict). Tailwind CSS v4 via `@tailwindcss/vite`.
- **Charts**: `recharts`. **Icons**: `lucide-react`. **Class merge**: `clsx`.
- **Data layer**: a thin typed `api.ts` (typed fetch wrappers, shared types, `API_BASE` const = `http://localhost:8000`); custom `usePolling` hook for Live Feed + health; no extra state lib.
- **No `any`**; all API responses typed; runtime narrowing at boundaries.
- Dev server port **5173**.

## Evaluation Criteria

### Design Quality (weight: 0.3)
Dark theme matches the exact palette; hairline-border density over shadow-soup; correct semantic priority/status colors; typographic hierarchy with mono numerics; charts themed to match (dark grid, indigo/semantic fills, no default Recharts white). The confidence arc reads as a designed instrument, not a default progress bar.

### Originality (weight: 0.2)
Feels like real internal tooling (Linear/Vercel/Stripe lineage), not a template dashboard. Signature confidence arc, urgent-route pulse, and typewriter reply give it a distinct identity. Avoids all listed AI-slop patterns.

### Craft (weight: 0.3)
Every async boundary has loading + error + empty states. Smooth, scoped CSS transitions (no `transition:all`). Typewriter + arc animations honor `prefers-reduced-motion`. Polling cleans up on unmount/pause. Keyboard shortcuts work. Copy-to-clipboard confirms. Relative timestamps tick.

### Functionality (weight: 0.2)
Critical flows: (a) select sample → analyze → see results + streamed reply; (b) short/invalid input blocked or 422-handled; (c) Dashboard renders all 4 charts from live data and degrades gracefully when empty; (d) Live Feed polls every 5s, pause/resume works, newest-first ordering; (e) backend-down state surfaces in sidebar + each view.

## Sprint Plan

### Sprint 1: Shell & Analyze core
- Goals: App boots on 5173, sidebar + tabs, typed `api.ts`, health pill, Analyze input + results card + arc.
- Features: #1, #2, #3, #4, #5, #6.
- Definition of done: Can analyze a sample ticket end-to-end with loading/error states and an animated confidence arc; sidebar shows live health/model.

### Sprint 2: Reply streaming & Live Feed
- Goals: Typewriter reply, full Live Feed with polling + pause.
- Features: #7, #8, #9.
- Definition of done: Reply streams word-by-word with copy; Live Feed polls every 5s, color-bordered cards, pause/resume, empty + offline states.

### Sprint 3: Dashboard
- Goals: KPI cards + all four Recharts visuals, client-derived metrics.
- Features: #10, #11, #12, #13, #14.
- Definition of done: Dashboard renders from `/metrics` + `/tickets` with themed charts and empty states; numbers reconcile with Live Feed.

### Sprint 4: Polish & extras
- Goals: Detail drawer, shortcuts, density/auto-refresh, accessibility + responsive ≥1280 pass.
- Features: #15, #16, #17.
- Definition of done: Drawer + shortcuts work; reduced-motion respected; strict TS build clean with zero `any`.
