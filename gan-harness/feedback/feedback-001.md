# Evaluation — Iteration 001

Mode: live app (frontend :5173 + backend :8000 both running) + source/build audit.
Backend verified live: `/health` → `{"status":"ok","provider":"ollama","model":"mistral"}`,
`/metrics` and `/tickets` return real rows, `/analyze` returns a full classification + reply_draft.

## Scores

| Criterion | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Design Quality | 9/10 | 0.30 | 2.70 |
| Originality | 8/10 | 0.20 | 1.60 |
| Craft | 9/10 | 0.30 | 2.70 |
| Functionality | 8/10 | 0.20 | 1.60 |
| **TOTAL** | | | **8.60/10** |

## Verdict: PASS (threshold: 7.0)

No hard-fail flags triggered:
- No `any` / non-strict TS — `grep` for `:any|as any|<any>` returns zero matches; `tsc -b` exits 0.
- Correct dark base theme; exact palette in `index.css` `@theme` + `constants.ts`.
- No `transition: all` anywhere — `grep` for `transition:all|transition-all` returns zero; all transitions scoped (`transition-colors` / explicit keyframes).
- No async surface renders a blank screen — every fetch boundary (analyze, health, tickets, metrics, each chart) has distinct loading / error / empty states (`States.tsx`, `AnalyzeView`, `DashboardView`, `LiveFeedView`).
- Dev server on 5173 (HTTP 200). `vite build` exits 0 (`dist/assets/index.js` 593 kB / 178 kB gzip).

## Evidence by Rubric Dimension

### Design Quality — 9/10
- Exact palette confirmed in `src/index.css` `@theme` and `src/constants.ts`: bg `#0f1117`, card `#1a1d27`, hairline `#262a36`, accent `#818cf8`. Borders are 1px hairlines; shadows reserved for hover/drawer only. Matches spec.
- Semantic priority colors exact: Critical `#f87171` / High `#fb923c` / Medium `#fbbf24` / Low `#34d399` (`PRIORITY_COLORS`). Status pill green/amber/red (`STATUS_COLORS`). Grounded green on `rgba(52,211,153,0.12)` vs ungrounded amber on `rgba(251,191,36,0.12)` (`GROUNDED`).
- Typography hierarchy present: Inter UI, mono `tabular-nums` for all numerics/IDs/timestamps (`.tnum`, `font-mono`), 11px uppercase tracked `.label-eyebrow` section labels. Confirmed visually in screenshot.
- Charts themed to dark surface: custom `DarkTooltip`, axis ticks `#9ca3af`/`#6b7280`, hairline axis lines, indigo/semantic fills, no default white Recharts. Donut has dark `#0f1117` cell stroke + center total.
- Confidence arc (`ConfidenceArc.tsx`) is a hand-built SVG open-gauge (90° bottom gap, color band by value, rAF cubic ease-out, drop-shadow glow, mono center %), not a stock progress bar.

### Originality — 8/10
- Reads as serious internal tooling (Linear sidebar density + Vercel KPI surfaces + Stripe-style charts). Dense control-room layout, not a marketing template.
- All three signature touches present: animated confidence arc, urgent-route red pulse dot (`pulse-dot` on routes ending "Urgent", `isUrgentRoute`), word-by-word typewriter reply with blinking caret (`ReplyPanel`).
- Zero AI-slop: no hero gradient, lucide icons (no emoji), left-aligned dense copy, hairline borders over shadow-soup, tinted semantic badges (not flat saturated pills).
- Held at 8 (not 9): the visual identity, while clean, is largely an assembly of the cited references rather than a distinct point of view. The logo tile carries the only real brand mark and it is a generic hexagon on an indigo gradient — the one spot where a more bespoke mark would lift originality.

### Craft — 9/10
- Loading + error + empty on every async boundary: Analyze (skeleton / `ErrorState` per kind / dot-grid empty), Dashboard (LoadingState / ErrorState / per-chart EmptyState), Live Feed (LoadingState / ErrorState / EmptyState), health pill (Checking… / offline).
- Error states are distinct per kind: `ApiError` carries `kind` (validation/rate_limit/server/network) + `retryAfter`; `ErrorState` renders different icon/title/tint and 429 surfaces "Rate limited". `toApiError` maps 422/429/5xx; fetch failure → `network`.
- Scoped transitions only; `prefers-reduced-motion` honored in CSS (`@media` disables feed-in/pulse/caret/drawer/fade) AND in JS (arc + typewriter check `matchMedia` and render final state).
- Polling lifecycle correct: feed polls 5s with `inFlight` guard + abort + `mounted` ref; pause clears the interval (`useLiveFeed` effect keyed on `paused`); health polls 30s with cleanup. Relative timestamps tick every 1s (`useTick`).
- Keyboard: `1/2/3` switch views, `g a/d/f` navigation, `?` cheatsheet, `Esc` closes overlays, `Cmd/Ctrl+Enter` analyze; shortcuts suppressed while typing (`isTyping`). Copy-to-clipboard confirms with a 1.6s "Copied" state.
- Strict TS, no `any`, typed API boundary with runtime narrowing (`asString/asNumber/asPriority/rec`). Build clean.
- Minor deduction only for the bundle: 593 kB single chunk (Recharts) ships with no code-splitting — non-blocking but the one real craft gap on an otherwise senior-level codebase.

### Functionality — 8/10
- End-to-end verified against live API: `POST /analyze` returns `{category, priority, confidence, grounded, route_to, reply_draft}` and the results card + typewriter consume it. Confirmed by direct curl.
- Input validation: `< 10` disables Analyze, hard cap 2000 with amber > 1800 / red at 2000, slice on paste; 422/429/500/network handled distinctly.
- Dashboard: 4 KPI cards + 4 Recharts visuals render from `/metrics` + `/tickets`; grounding % and routing distribution derived client-side (`groundingPct`, `topRoutes`, `bucketConfidence`); empty states per chart.
- Live Feed: polls `/tickets?limit=25` every 5s, newest-first as returned by API, priority-colored 3px left border, relative timestamps, pause/resume stops the timer, manual refresh, detail drawer with `Esc`.
- Backend-down surfaces in sidebar pill ("Backend offline", red) and in each view's `ErrorState` (network kind appends "is the API running on :8000?").

## Critical Issues (must fix)
None. No blocker bugs found in live testing or source audit.

## Major Issues (should fix)
1. Bundle size: single 593 kB JS chunk (Recharts). → Lazy-load `DashboardView` with `React.lazy` + `Suspense`, or `manualChunks` to split recharts into its own chunk. Keeps initial Analyze paint light.
2. Live backend returns `confidence` on a 0–8 scale, not 0–100 (e.g. ticket confidence `8`, `avg_confidence: 8.0`). The UI treats it as a percentage, so the arc and KPI render "8%" and the histogram dumps everything into the 0–20 bucket. → Either normalize at the API boundary (`api.ts`) if the backend scale is fixed, or confirm the contract; right now the headline confidence number is misleading against live data. This is the single most impactful functional fix for iteration 2.

## Minor Issues (nice to fix)
1. `priorityData` filter `.filter((d) => d.value > 0 || true)` is a no-op (always true) — dead code; remove the filter or make it meaningful (`DashboardView.tsx`).
2. Health "degraded" branch in `deriveStatus` can never trigger from this backend (status is `"ok"`); the unknown-status fallback returns `'healthy'` rather than `'degraded'`, which could mask a genuinely odd status string. Consider defaulting unknown → `degraded`.
3. The `⌘`/`CornerDownLeft` hint in the Analyze footer shows a Mac glyph unconditionally; on Windows it should read `Ctrl`. Detect platform for the kbd label.
4. Logo mark is a generic hexagon — a small bespoke glyph would raise originality.

## What's Working Well (do NOT regress)
- Exact palette + hairline-over-shadow discipline and dark-themed Recharts.
- Hand-built SVG confidence arc with rAF easing and reduced-motion handling.
- Typed API layer with `ApiError.kind` and runtime narrowing at every boundary.
- Complete loading/error/empty coverage on all five async surfaces.
- Correct polling lifecycle: 5s feed, 30s health, in-flight guard, pause clears timer, abort + mounted-ref cleanup.
- Full keyboard model (1/2/3, g-nav, ?, Esc, Cmd/Ctrl+Enter) with typing suppression, plus copy confirmation.
- Strict TS, zero `any`, clean `tsc -b` and `vite build`.

## Specific Suggestions for Next Iteration
1. Resolve the confidence-scale mismatch (Major #2) — this is the highest-value fix; normalize or confirm the 0–100 contract so the arc/KPI/histogram reflect live data correctly.
2. Code-split Recharts (Major #1) to drop initial bundle below the 500 kB warning.
3. Remove the no-op priority filter and tighten `deriveStatus` unknown handling (Minor #1, #2).
4. Platform-aware ⌘/Ctrl label (Minor #3).
5. Optional: a bespoke logo glyph to push Originality from 8 to 9.

## Screenshots
- `gan-harness/screenshots/iter-001-initial-load.png` — Analyze view at 1440×900. Confirms dark theme, indigo active-tab accent, mono pipeline stepper, dot-grid empty results state, Docs/ReDoc links. Captured before health resolved, so the pill reads "Checking…" and Model fields show "—"; on live re-check the pill goes green with provider `ollama` / model `mistral`.
