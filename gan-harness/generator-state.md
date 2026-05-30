# Generator State — Iteration 001

## What Was Built
A production-quality React 19 + Vite + TypeScript (strict) + Tailwind v4 SPA: **Triage**, a dark operator-grade AI support-ticket console. Three views switched by tab state (no router).

### App shell
- Fixed 240px `Sidebar` with logo, live health pill, tab nav, model info (provider/model/version in mono), numbered pipeline stepper, and Docs/ReDoc quick links.
- Header with view title/subtitle and a Shortcuts button.
- Keyboard: `1/2/3` switch views, `g a / g d / g f` navigate, `?` opens shortcuts cheatsheet, `Esc` closes overlays. Shortcuts ignored while typing.

### Analyze view (`AnalyzeView.tsx`)
- Sample dropdown with 6 realistic tickets (one per category).
- Textarea: live `n / 2000` counter (amber > 1800, red at 2000 hard cap), disabled Analyze < 10 chars, `Cmd/Ctrl+Enter` submits.
- Lifecycle: inline spinner "Analyzing…", disabled in flight; skeleton; distinct error states for 422 / 429 / 500 / network via `ErrorState`.
- Results card: category + priority + grounded badges, signature animated SVG `ConfidenceArc` (open gauge, 700ms ease-out cubic, color by confidence band), route with urgent red pulse dot + Zap icon.
- Reply panel: word-by-word typewriter (~28ms), blinking caret, "Skip animation", "Copy" with copied confirmation. Respects `prefers-reduced-motion`.

### Dashboard view (`DashboardView.tsx`)
- 4 KPI cards: Total, Avg confidence, High+Critical (from `by_priority`), Grounding % (derived client-side from `/tickets`).
- 4 themed Recharts visuals on dark surface with custom `DarkTooltip`: category donut (center total + legend), priority bar (semantic colors, Critical→Low), confidence histogram (0-20…80-100 indigo bars derived from tickets), top-routes horizontal bar (urgent routes tinted red, derived from tickets).
- Manual refresh + optional 15s auto-refresh toggle. Loading / error / empty states throughout.

### Live Feed view (`LiveFeedView.tsx`)
- Polls `/tickets?limit=25` every 5s; priority-colored 3px left border cards, 2-line clamp, badges, route, relative timestamps that tick every 1s.
- Newest items fade+slide in (diff against previous IDs; first load not flagged).
- Pause/Resume actually stops the timer; paused banner with frozen timestamp; always-available manual refresh.
- Click a card → right slide-over detail drawer (full text, full reply, metadata); `Esc` closes.

### Data layer
- `api.ts`: typed fetch wrappers for all 4 endpoints, `API_BASE = http://localhost:8000`, runtime narrowing at boundaries, typed `ApiError` with kind (validation/rate_limit/server/network) + retry-after.
- Hooks: `useAnalyze`, `useMetrics`, `useLiveFeed`, `useHealth` — all with abort/cleanup and proper lifecycle.

## Design notes / trade-offs
- Confidence treated as 0–100 integer per the corrections (arc, avg, histogram all on that scale).
- `/metrics` returns only total/avg/by_category/by_priority; grounding % and routing distribution derived from `/tickets` (200-row sample on Dashboard).
- Palette uses the spec hairline `#262a36` for borders (within design tokens); bg `#0f1117`, card `#1a1d27`, accent `#818cf8`.
- No `transition: all` anywhere — all transitions are scoped (`transition-colors`/`transition-opacity` + explicit keyframes).
- No `any`; strict TS build is clean.
- Recharts pulls bundle over 500kB (warning only, not an error) — acceptable for an internal tool; could code-split later.

## Known Issues
- Backend on :8000 was not running during build; all views were verified to render their loading/error/empty states. End-to-end data paths depend on the live API.
- Recharts bundle size warning (non-blocking).

## Dev Server
- URL: http://localhost:5173
- Status: running (verified HTTP 200)
- Command: npm run dev (strictPort 5173)
