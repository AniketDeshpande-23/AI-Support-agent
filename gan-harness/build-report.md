# GAN Harness Build Report

**Brief:** Production-quality React + Vite + TypeScript + Tailwind CSS frontend for AI Support Ticket Agent  
**Result:** ✅ PASS  
**Iterations:** 1 / 15 (passed first try)  
**Final Score:** 8.60 / 10  
**Post-eval fixes applied:** 4 (confidence scale, dead filter, Ctrl/Cmd label, avg_confidence scale)

---

## Score Progression

| Iter | Design | Originality | Craft | Functionality | Total |
|------|--------|-------------|-------|---------------|-------|
| 1    | 9/10   | 8/10        | 9/10  | 8/10          | **8.60** |

---

## What Was Built

**App name:** Triage  
**Stack:** React 19 + Vite 8 + TypeScript (strict) + Tailwind v4 + Recharts + Lucide  
**Location:** `ui-react/`  
**Port:** 5173

### Features Shipped

| Feature | Status |
|---|---|
| Dark theme (#0f1117 / #1a1d27 / #818cf8) | ✅ |
| Sidebar: status pill, model info, pipeline steps, keyboard shortcuts | ✅ |
| Tab navigation (Analyze / Dashboard / Live Feed) + keyboard shortcuts | ✅ |
| Sample ticket dropdown (6 real examples) | ✅ |
| Textarea with live char counter, 2000-char cap | ✅ |
| Analyze button + Ctrl+Enter shortcut | ✅ |
| Results card: SVG confidence arc, category/priority badges, grounded chip, route | ✅ |
| Typewriter reply animation (word-by-word, skip button, reduced-motion) | ✅ |
| 422 / 429 / 500 / network error states | ✅ |
| Dashboard: 4 KPI cards | ✅ |
| Dashboard: category donut, priority bar, confidence histogram, routing bar | ✅ |
| Grounding % derived client-side from /tickets | ✅ |
| Live Feed: 5s auto-poll, pause/resume toggle | ✅ |
| Live Feed: priority-coloured cards with excerpt, badges, timestamp | ✅ |
| Live Feed: slide-over detail drawer (Esc to close) | ✅ |
| TypeScript strict — zero `any` | ✅ |
| No `transition: all` — all transitions scoped | ✅ |
| Reduced-motion respected in arc animation and typewriter | ✅ |

---

## Post-Eval Fixes (applied after 8.60 score)

| Fix | File | Change |
|---|---|---|
| Confidence scale (0-10 → 0-100) | `api.ts` | `× 10` at API boundary for both `/analyze` and `/tickets` |
| avg_confidence scale | `api.ts` | `× 10` for `/metrics` avg_confidence |
| Dead `\|\| true` filter | `DashboardView.tsx` | Removed always-true condition |
| Windows Ctrl key label | `AnalyzeView.tsx`, `App.tsx` | `⌘` → `Ctrl` |

---

## Remaining Non-Blockers

- Recharts bundle is 594 kB (above Vite's 500 kB warning). Can be fixed with dynamic `import()` on the Dashboard route — not urgent for a dev/internal tool.
- Unreachable "degraded" health branch in `useHealth.ts` — cosmetic dead code.

---

## Files Created

```
ui-react/
├── src/
│   ├── types.ts
│   ├── api.ts
│   ├── constants.ts
│   ├── time.ts
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   ├── components/
│   │   ├── Badge.tsx
│   │   ├── ConfidenceArc.tsx
│   │   ├── KpiCard.tsx
│   │   ├── Sidebar.tsx
│   │   ├── States.tsx
│   │   └── TabBar.tsx
│   ├── hooks/
│   │   ├── useAnalyze.ts
│   │   ├── useHealth.ts
│   │   ├── useLiveFeed.ts
│   │   └── useMetrics.ts
│   └── views/
│       ├── AnalyzeView.tsx
│       ├── DashboardView.tsx
│       └── LiveFeedView.tsx
gan-harness/
├── spec.md
├── eval-rubric.md
├── generator-state.md
├── feedback/feedback-001.md
├── screenshots/iter-001-initial-load.png
└── build-report.md
```
