# Evaluation Rubric: Triage — AI Support Ticket Console

Total: **10 points**. Score each criterion, sum, and note specific evidence. Penalize any AI-slop pattern listed below regardless of category.

## 1. Design Quality — 3.0 pts
- (0.7) Exact dark palette: bg `#0f1117`, card `#1a1d27`, accent `#818cf8`; hairline borders not heavy shadows.
- (0.7) Semantic colors correct: Critical red / High orange / Medium amber / Low green; status pill green/amber/red; grounded green vs ungrounded amber.
- (0.6) Typography hierarchy with `Inter` + mono `tabular-nums` numerics, uppercase tracked section labels.
- (0.6) Charts themed to dark surface (no default white Recharts), indigo/semantic fills, readable legends/tooltips.
- (0.4) Confidence arc reads as a designed SVG instrument, not a stock progress bar.

## 2. Originality — 2.0 pts
- (0.8) Reads as serious internal tooling (Linear/Vercel/Stripe lineage), not a generic template.
- (0.7) Signature touches present: animated confidence arc, urgent-route pulse, word-by-word typewriter reply.
- (0.5) Zero AI-slop patterns (no purple→pink hero gradient, no emoji icons, no center-aligned marketing copy, no uniform shadow cards).

## 3. Craft — 3.0 pts
- (0.7) Loading + error + empty states on EVERY async boundary (analyze, health, tickets, metrics, charts).
- (0.6) Smooth scoped CSS transitions; no `transition: all` anywhere.
- (0.5) `prefers-reduced-motion` respected by typewriter + arc.
- (0.5) Polling lifecycle correct: 5s feed poll, cleanup on unmount, pause/resume actually stops timers.
- (0.4) Keyboard support (tab switch 1/2/3, Cmd/Ctrl+Enter analyze) + copy-to-clipboard confirmation.
- (0.3) TypeScript strict, no `any`, typed API boundary; build clean.

## 4. Functionality — 2.0 pts
- (0.5) Sample → Analyze → results + streamed reply works end-to-end against live API.
- (0.4) Input validation: <10 char blocked, 2000 cap, 422/429/500 handled distinctly.
- (0.5) Dashboard: 4 KPI cards + 4 charts render from `/metrics` + `/tickets`; grounding % & routing derived client-side; graceful empty.
- (0.4) Live Feed: polls every 5s, newest-first, priority-colored borders, relative timestamps, pause/resume.
- (0.2) Backend-down state surfaces in sidebar pill and per-view error states.

## Scoring
- 9.0–10.0 — Ship-quality, indistinguishable from senior internal tooling.
- 7.0–8.9 — Strong; minor polish/state gaps.
- 5.0–6.9 — Functional but generic or missing several states.
- < 5.0 — Incomplete, off-palette, or AI-slop aesthetics.

## Hard-fail flags (cap score at 5.0 if any present)
- Uses `any` types or non-strict TS.
- Wrong base theme (light, or off-palette).
- A `transition: all` rule present.
- Any async surface with no error/empty handling that renders a blank screen.
- Dev server not on port 5173.
