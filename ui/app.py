"""
ui/app.py — AI Support Agent · Professional Dashboard v3

Tabs:
  🎫 Analyze Ticket  — sample picker, streaming reply animation, metadata card
  📊 Analytics       — KPI row + 4 Plotly charts (dark theme)
  📡 Live Feed       — auto-refreshing ticket stream with priority-coded rows

Design: ecc make-interfaces-feel-better principles applied throughout
  • Concentric radius (outer = inner + padding)
  • tabular-nums on all numeric displays
  • text-wrap: balance on headings, pretty on body copy
  • Explicit CSS transitions (never transition: all)
  • enter animations: opacity + translateY
  • Tactile button press: scale(0.97)
  • will-change only on transform/opacity
  • ≥ 44px hit areas on interactive controls
"""

import html
import os
import time

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Design tokens ─────────────────────────────────────────────────────────────

PRIORITY_HEX = {
    "Critical": "#ef4444",
    "High":     "#f97316",
    "Medium":   "#eab308",
    "Low":      "#22c55e",
}
CATEGORY_HEX = {
    "Account":           "#818cf8",
    "Billing":           "#34d399",
    "Order":             "#60a5fa",
    "Shipping":          "#fb923c",
    "Technical Support": "#f472b6",
    "Feedback":          "#a78bfa",
    "Other":             "#94a3b8",
    # legacy
    "Login Issue":       "#818cf8",
    "Bug Report":        "#f472b6",
    "Feature Request":   "#a78bfa",
}
CATEGORY_ICON = {
    "Account": "👤", "Billing": "💳", "Order": "📦",
    "Shipping": "🚚", "Technical Support": "🔧",
    "Feedback": "💬", "Other": "📌",
    "Login Issue": "🔐", "Bug Report": "🐛", "Feature Request": "💡",
}
ROUTE_ICON = {
    "Engineering": "⚙️", "Engineering — Urgent": "🚨",
    "Finance": "💰", "Finance — Urgent": "🚨",
    "Order Management": "📋", "Order Management — Urgent": "🚨",
    "Account Support": "👤", "Logistics": "🚚",
    "Product": "💡", "Senior Support": "⚡",
    "Human Review": "🧑", "General Support": "💬",
}
SAMPLE_TICKETS = {
    "— pick a sample ticket —": "",
    "💳 Charged twice for last order":
        "I was charged twice for order #78432. Both transactions appear on my bank statement but I only authorised one payment. I need an immediate refund for the duplicate charge.",
    "👤 Can't login after email change":
        "I updated my email address last week but now I cannot log in. The password reset link is sent to my old address which I no longer have access to. Please help me recover my account.",
    "🚚 Package marked delivered but missing":
        "My tracking shows the parcel was delivered yesterday but I never received it. I've checked with neighbours and the building front desk — nobody has it. Order #99201.",
    "📦 Cancel order placed 10 minutes ago":
        "I placed order #55678 by mistake — I selected the wrong size. Can you cancel it before it ships? I placed it about 10 minutes ago.",
    "🔧 App crashes on iOS 17":
        "Your mobile app crashes every time I open the Orders section on iOS 17.4. This started after your last update. I've reinstalled twice but the issue persists.",
    "💬 Feature request: dark mode":
        "I'd love to see a dark mode option in the app. Many users have requested this and it would make the interface much more comfortable for night-time use.",
}


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
/* ── Fonts & base ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300..800&display=swap');

*, *::before, *::after {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  box-sizing: border-box;
}

/* ── Design tokens ────────────────────────────────────────── */
:root {
  --accent:       #818cf8;
  --accent-glow:  rgba(129,140,248,0.25);
  --success:      #34d399;
  --warning:      #fbbf24;
  --danger:       #f87171;
  --card-bg:      rgba(255,255,255,0.045);
  --card-border:  rgba(255,255,255,0.09);
  --r-xl:  20px;
  --r-lg:  14px;
  --r-md:  10px;
  --r-sm:   6px;
  --r-xs:   4px;
  /* shadow stacked for depth without harshness */
  --shadow-card:  0 1px 2px rgba(0,0,0,.4), 0 4px 14px rgba(0,0,0,.3);
  --shadow-btn:   0 2px 8px rgba(129,140,248,.35);
}

/* ── Hide Streamlit chrome ────────────────────────────────── */
footer, #MainMenu, .stDeployButton,
[data-testid="stToolbar"] { visibility: hidden; height: 0; }

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar       { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.15); border-radius: 99px; }

/* ── Tab bar ──────────────────────────────────────────────── */
/* outer radius 14 → inner tab radius = 14 - 4 (padding) = 10 */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-lg);
  padding: 4px;
  backdrop-filter: blur(12px);
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--r-md);   /* 14 - 4 = 10 ✓ concentric */
  padding: 8px 20px;
  font-size: 0.875rem;
  font-weight: 500;
  min-height: 40px;
  transition-property: background-color, color, box-shadow;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
}
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: #fff !important;
  box-shadow: 0 2px 8px rgba(129,140,248,.4);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* ── Card (HTML component) ────────────────────────────────── */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-xl);
  padding: 22px 24px;
  box-shadow: var(--shadow-card);
  animation: fadeUp .22s ease-out both;
}

/* ── KPI card ─────────────────────────────────────────────── */
.kpi {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-xl);
  padding: 20px;
  text-align: center;
  box-shadow: var(--shadow-card);
  animation: fadeUp .2s ease-out both;
}
.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  margin-bottom: 4px;
}
.kpi-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .07em;
  opacity: .5;
}

/* ── Badge ────────────────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: .03em;
  text-transform: uppercase;
  font-variant-numeric: tabular-nums;
}

/* ── Confidence bar ───────────────────────────────────────── */
.conf-track {
  background: rgba(255,255,255,.08);
  border-radius: 99px;
  height: 7px;
  overflow: hidden;
}
.conf-fill {
  height: 100%;
  border-radius: 99px;
  /* animated on paint — no JS needed */
  transition-property: width, background-color;
  transition-duration: 700ms;
  transition-timing-function: cubic-bezier(.4,0,.2,1);
}

/* ── Streaming reply box ──────────────────────────────────── */
.reply-stream {
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 0.9rem;
  line-height: 1.72;
  white-space: pre-wrap;
  text-wrap: pretty;
  padding: 16px 18px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  /* inner radius = outer(14) - padding equivalent → 10 ✓ */
  border-radius: var(--r-lg);
  min-height: 110px;
  box-shadow: var(--shadow-card);
}
/* blinking cursor */
.cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--accent);
  border-radius: 1px;
  vertical-align: text-bottom;
  margin-left: 1px;
  animation: blink .85s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* ── Feed rows ────────────────────────────────────────────── */
.feed-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-left: 3px solid transparent;
  border-radius: var(--r-lg);
  margin-bottom: 7px;
  animation: fadeUp .16s ease-out both;
  transition-property: background-color, border-left-color;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
}
.feed-row:hover {
  background: rgba(255,255,255,.065);
  border-left-color: var(--accent);
}
.feed-icon {
  width: 40px; min-width: 40px;
  text-align: center;
}
.feed-icon-emoji  { font-size: 1.2rem; line-height: 1; }
.feed-icon-conf   { font-size: 0.65rem; opacity: .45;
                    font-variant-numeric: tabular-nums; }
.feed-body        { flex: 1; min-width: 0; }
.feed-ticket      { font-size: 0.85rem; text-wrap: pretty; opacity: .75; }
.feed-badges      { display: flex; gap: 5px; flex-wrap: wrap;
                    align-items: center; margin-top: 5px; }
.feed-route       { font-size: 0.75rem; opacity: .45; }
.feed-ts          { font-size: 0.72rem; opacity: .4; white-space: nowrap;
                    font-variant-numeric: tabular-nums; }

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  border-right: 1px solid var(--card-border);
}
.stat-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--card-border);
  font-size: 0.82rem;
  font-variant-numeric: tabular-nums;
}
.stat-row:last-child { border-bottom: none; }

/* ── Plotly chart containers ──────────────────────────────── */
[data-testid="stPlotlyChart"] {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--r-xl);
  padding: 10px 12px;
  box-shadow: var(--shadow-card);
}

/* ── Textarea ─────────────────────────────────────────────── */
.stTextArea textarea {
  font-family: 'Inter', system-ui, sans-serif !important;
  font-size: 0.88rem !important;
  line-height: 1.68 !important;
  border-radius: var(--r-md) !important;
}

/* ── Primary button ───────────────────────────────────────── */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #818cf8, #6d63f5);
  border: none;
  border-radius: var(--r-md);
  font-weight: 600;
  font-size: 0.9rem;
  min-height: 44px;           /* 44px hit area */
  box-shadow: var(--shadow-btn);
  transition-property: transform, box-shadow;
  transition-duration: 150ms;
  transition-timing-function: ease-out;
  will-change: transform;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(129,140,248,.45);
}
.stButton > button[kind="primary"]:active {
  transform: scale(0.97);
  box-shadow: 0 1px 4px rgba(129,140,248,.3);
}
/* secondary buttons */
.stButton > button:not([kind="primary"]) {
  border-radius: var(--r-md);
  min-height: 44px;
  font-size: 0.875rem;
  font-weight: 500;
  transition-property: background-color, border-color;
  transition-duration: 130ms;
  transition-timing-function: ease-out;
}

/* ── Section labels ───────────────────────────────────────── */
.field-label {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .07em;
  opacity: .5;
  margin-bottom: 6px;
}

/* ── Headings ─────────────────────────────────────────────── */
h3 { text-wrap: balance; font-weight: 700 !important; }

/* ── Animations ───────────────────────────────────────────── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0);    }
}
</style>
"""


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def backend_health():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.ok, r.json() if r.ok else {}
    except Exception:
        return False, {}


def badge(text: str, color: str, prefix: str = "") -> str:
    label = f"{prefix} {text}".strip()
    return (
        f'<span class="badge" '
        f'style="background:{color}20;color:{color};border:1px solid {color}40">'
        f'{label}</span>'
    )


def conf_bar(score: int) -> str:
    pct   = score * 10
    color = ("#22c55e" if score >= 7 else
             "#eab308" if score >= 5 else "#ef4444")
    return (
        f'<div class="conf-track">'
        f'<div class="conf-fill" style="width:{pct}%;background:{color}"></div>'
        f'</div>'
    )


def kpi(value, label: str, color: str = "#818cf8") -> str:
    return (
        f'<div class="kpi">'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'</div>'
    )


def plotly_base() -> dict:
    """Shared dark layout settings for all Plotly figures."""
    return dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#94a3b8"),
        margin=dict(l=0, r=0, t=36, b=0),
    )


# ── Session state ─────────────────────────────────────────────────────────────

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False


# ── Sidebar ───────────────────────────────────────────────────────────────────

online, health_data = backend_health()

with st.sidebar:
    st.markdown("## 🎫 AI Support Agent")
    st.caption("Bitext KB · FAISS RAG · v3")
    st.divider()

    if online:
        st.success("● Backend Online", icon="✅")
        prov  = health_data.get("provider", "—")
        model = health_data.get("model", "—")
        st.caption(f"Provider `{prov}` · Model `{model}`")
    else:
        st.error("● Backend Offline")
        st.code("uvicorn app.main:app --reload", language="bash")

    st.divider()

    # Live stats mini-dashboard
    try:
        m     = requests.get(f"{BACKEND_URL}/metrics", timeout=3).json()
        total = m.get("total", 0)
        avg_c = m.get("avg_confidence", 0)
        by_p  = m.get("by_priority", {})
        urgent = by_p.get("Critical", 0) + by_p.get("High", 0)
        st.markdown(f"""
<div class="stat-row"><span>Total tickets</span>
  <strong style="font-variant-numeric:tabular-nums">{total}</strong></div>
<div class="stat-row"><span>Avg confidence</span>
  <strong style="font-variant-numeric:tabular-nums">{avg_c:.1f} / 10</strong></div>
<div class="stat-row"><span>High / Critical</span>
  <strong style="color:#f97316;font-variant-numeric:tabular-nums">{urgent}</strong></div>
""", unsafe_allow_html=True)
    except Exception:
        st.caption("No data yet.")

    st.divider()
    st.markdown("""
**Pipeline**
1. FAISS vector search → top‑3 docs
2. Single LLM call → classify + reply
3. Confidence & grounding check
4. Route to team
5. SQLite log
""")
    st.divider()
    st.caption(
        "📖 [Swagger](http://localhost:8000/docs) · "
        "[Health](http://localhost:8000/health)"
    )


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_analyze, tab_analytics, tab_feed = st.tabs([
    "🎫  Analyze Ticket",
    "📊  Analytics",
    "📡  Live Feed",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYZE
# ═══════════════════════════════════════════════════════════════════════════════

with tab_analyze:
    st.markdown("### Submit a Support Ticket")

    # ── Sample picker ─────────────────────────────────────────────────────────
    sample_key = st.selectbox(
        "Quick examples",
        options=list(SAMPLE_TICKETS.keys()),
        label_visibility="collapsed",
    )
    prefill = SAMPLE_TICKETS[sample_key]

    ticket_text = st.text_area(
        "Ticket",
        value=prefill,
        placeholder=(
            "Paste the customer's message here…\n\n"
            "Example: 'I was charged twice for my subscription this month "
            "and cannot log in to request a refund.'"
        ),
        height=150,
        label_visibility="collapsed",
    )

    # ── Controls row ──────────────────────────────────────────────────────────
    char_count = len(ticket_text)
    btn_col, char_col = st.columns([2, 7])
    with btn_col:
        go_btn = st.button(
            "Analyze →",
            type="primary",
            disabled=(not ticket_text.strip() or not online or char_count > 2000),
            use_container_width=True,
        )
    with char_col:
        c_color = "#ef4444" if char_count > 2000 else "#94a3b8"
        st.markdown(
            f'<p style="line-height:2.7;font-size:0.78rem;color:{c_color};'
            f'font-variant-numeric:tabular-nums;margin:0">'
            f'{char_count} / 2 000 characters</p>',
            unsafe_allow_html=True,
        )

    if not online:
        st.warning("Backend is offline — start it with `uvicorn app.main:app --reload`.", icon="⚠️")

    # ── Analysis ──────────────────────────────────────────────────────────────
    if go_btn and ticket_text.strip():
        with st.spinner("Calling LLM pipeline…"):
            try:
                t0  = time.perf_counter()
                res = requests.post(
                    f"{BACKEND_URL}/analyze",
                    json={"text": ticket_text},
                    timeout=120,
                )
                elapsed = time.perf_counter() - t0

                if res.status_code == 422:
                    st.error(f"Validation error: {res.json().get('detail')}")
                    st.stop()
                elif res.status_code == 429:
                    st.warning("Rate limit reached — wait a moment and try again.", icon="⏳")
                    st.stop()
                elif not res.ok:
                    st.error(f"Backend error {res.status_code}: "
                             f"{res.json().get('detail', 'unknown')}")
                    st.stop()

                data = res.json()

            except requests.exceptions.Timeout:
                st.error("Request timed out — the model may still be loading. Try again.")
                st.stop()
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the backend.")
                st.stop()

        st.toast(f"Analysis complete in {elapsed:.1f}s", icon="✅")
        st.divider()

        cat      = data.get("category",   "Other")
        pri      = data.get("priority",   "Medium")
        conf     = int(data.get("confidence", 5))
        grounded = data.get("grounded",   False)
        route    = data.get("route_to",   "General Support")
        reply    = data.get("reply_draft", "")

        cat_color  = CATEGORY_HEX.get(cat, "#94a3b8")
        cat_icon   = CATEGORY_ICON.get(cat, "📌")
        pri_color  = PRIORITY_HEX.get(pri, "#94a3b8")
        route_icon = ROUTE_ICON.get(route, "📨")
        g_color    = "#34d399" if grounded else "#f97316"
        g_icon     = "✓" if grounded else "⚠"
        g_label    = "Grounded in docs" if grounded else "Not grounded"

        meta_col, reply_col = st.columns([1, 2], gap="large")

        with meta_col:
            st.markdown(f"""
<div class="card">
  <div style="margin-bottom:18px">
    <div class="field-label">Category</div>
    {badge(cat, cat_color, cat_icon)}
  </div>
  <div style="margin-bottom:18px">
    <div class="field-label">Priority</div>
    {badge(pri, pri_color)}
  </div>
  <div style="margin-bottom:18px">
    <div class="field-label">Confidence &nbsp;
      <span style="font-variant-numeric:tabular-nums;font-weight:700;
                   font-size:.9rem;opacity:.9">{conf} / 10</span>
    </div>
    {conf_bar(conf)}
  </div>
  <div style="margin-bottom:18px">
    <div class="field-label">Source check</div>
    {badge(g_label, g_color, g_icon)}
  </div>
  <div>
    <div class="field-label">Routed to</div>
    <span style="font-weight:600;font-size:.9rem">{route_icon}&nbsp;{route}</span>
  </div>
  <div style="margin-top:20px;padding-top:14px;
              border-top:1px solid var(--card-border);
              font-size:.72rem;opacity:.38;font-variant-numeric:tabular-nums">
    ⏱&nbsp;{elapsed:.1f} s
  </div>
</div>
""", unsafe_allow_html=True)

        with reply_col:
            st.markdown('<div class="field-label">Draft Reply</div>',
                        unsafe_allow_html=True)

            # ── Streaming text animation ──────────────────────────────────────
            # Escape once; render chunk by chunk so HTML stays intact.
            safe_reply = html.escape(reply)
            placeholder = st.empty()
            chunk = 4                       # chars per frame
            for i in range(0, len(safe_reply), chunk):
                partial = safe_reply[:i + chunk]
                placeholder.markdown(
                    f'<div class="reply-stream">{partial}'
                    f'<span class="cursor"></span></div>',
                    unsafe_allow_html=True,
                )
                time.sleep(0.01)
            # Final state — no cursor
            placeholder.markdown(
                f'<div class="reply-stream">{safe_reply}</div>',
                unsafe_allow_html=True,
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # Editable copy
            st.text_area(
                "edit_reply",
                value=reply,
                height=190,
                label_visibility="collapsed",
                help="Edit the AI draft before sending to the customer.",
                key="editable_reply",
            )
            st.caption("✏️ Review and edit above before sending to the customer.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_analytics:
    st.markdown("### Analytics Dashboard")

    if st.button("🔄 Refresh data"):
        st.rerun()

    try:
        m_res = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        t_res = requests.get(f"{BACKEND_URL}/tickets?limit=500", timeout=5)
        if not m_res.ok or not t_res.ok:
            st.info("No data yet — analyse some tickets first.", icon="📊")
            st.stop()

        m       = m_res.json()
        tickets = t_res.json()

        if not tickets:
            st.info("No tickets yet — go to **Analyze Ticket** to get started.", icon="🎫")
            st.stop()

        df = pd.DataFrame(tickets)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # ── KPI row ───────────────────────────────────────────────────────────
        by_p    = m.get("by_priority", {})
        urgent  = by_p.get("Critical", 0) + by_p.get("High", 0)
        hr_mask = df["route_to"].str.contains("Human Review", na=False)
        hr_rate = hr_mask.mean() if len(df) else 0
        gr_rate = df["grounded"].mean() if len(df) else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(kpi(m.get("total", 0),          "Total Tickets",       "#818cf8"), unsafe_allow_html=True)
        k2.markdown(kpi(f"{m.get('avg_confidence', 0):.1f}", "Avg Confidence", "#34d399"), unsafe_allow_html=True)
        k3.markdown(kpi(urgent,                     "High / Critical",     "#f97316"), unsafe_allow_html=True)
        k4.markdown(kpi(f"{gr_rate:.0%}",           "Grounding Rate",      "#60a5fa"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Category pie + Priority bar ───────────────────────────────
        c1, c2 = st.columns(2)

        with c1:
            by_cat    = df["category"].value_counts().reset_index()
            cat_cols  = [CATEGORY_HEX.get(c, "#94a3b8") for c in by_cat["category"]]
            fig_pie   = go.Figure(go.Pie(
                labels=by_cat["category"],
                values=by_cat["count"],
                marker=dict(colors=cat_cols,
                            line=dict(color="rgba(0,0,0,0)", width=0)),
                hole=0.58,
                textinfo="label+percent",
                textfont=dict(size=11),
                hovertemplate="%{label}: %{value} tickets<extra></extra>",
            ))
            fig_pie.update_layout(
                title=dict(text="Tickets by Category", font=dict(size=14, color="#e2e8f0")),
                showlegend=False,
                height=320,
                **plotly_base(),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            pri_order = ["Critical", "High", "Medium", "Low"]
            by_pri    = (df["priority"].value_counts()
                         .reindex(pri_order, fill_value=0)
                         .reset_index())
            p_cols    = [PRIORITY_HEX.get(p, "#94a3b8") for p in by_pri["priority"]]
            fig_bar   = go.Figure(go.Bar(
                x=by_pri["priority"],
                y=by_pri["count"],
                marker=dict(color=p_cols, line=dict(width=0)),
                text=by_pri["count"],
                textposition="outside",
                textfont=dict(size=12, color="#e2e8f0"),
                hovertemplate="%{x}: %{y} tickets<extra></extra>",
            ))
            fig_bar.update_layout(
                title=dict(text="Tickets by Priority", font=dict(size=14, color="#e2e8f0")),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True,
                           gridcolor="rgba(255,255,255,.06)",
                           zeroline=False),
                height=320,
                **plotly_base(),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Row 2: Confidence histogram + Routing bar ─────────────────────────
        c3, c4 = st.columns(2)

        with c3:
            fig_hist = go.Figure(go.Histogram(
                x=df["confidence"],
                nbinsx=10,
                marker=dict(color="#818cf8",
                            line=dict(width=0),
                            opacity=0.85),
                hovertemplate="Score %{x}: %{y} tickets<extra></extra>",
            ))
            fig_hist.update_layout(
                title=dict(text="Confidence Score Distribution",
                           font=dict(size=14, color="#e2e8f0")),
                xaxis=dict(range=[0.5, 10.5], dtick=1,
                           showgrid=False, title="Score"),
                yaxis=dict(showgrid=True,
                           gridcolor="rgba(255,255,255,.06)",
                           zeroline=False, title="Count"),
                bargap=0.12,
                height=300,
                **plotly_base(),
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        with c4:
            by_route  = df["route_to"].value_counts().reset_index().head(8)
            fig_route = go.Figure(go.Bar(
                x=by_route["count"],
                y=by_route["route_to"],
                orientation="h",
                marker=dict(color="#60a5fa", line=dict(width=0), opacity=0.9),
                text=by_route["count"],
                textposition="outside",
                textfont=dict(size=11, color="#e2e8f0"),
                hovertemplate="%{y}: %{x} tickets<extra></extra>",
            ))
            fig_route.update_layout(
                title=dict(text="Routing Distribution",
                           font=dict(size=14, color="#e2e8f0")),
                xaxis=dict(showgrid=True,
                           gridcolor="rgba(255,255,255,.06)",
                           zeroline=False),
                yaxis=dict(showgrid=False, autorange="reversed"),
                height=300,
                **plotly_base(),
            )
            st.plotly_chart(fig_route, use_container_width=True)

        # ── Row 3: Grounding + Human review ───────────────────────────────────
        if len(df) >= 5:
            c5, c6 = st.columns(2)

            with c5:
                g_vals   = [gr_rate * 100, (1 - gr_rate) * 100]
                g_labels = ["Grounded", "Not grounded"]
                g_colors = ["#34d399", "#f87171"]
                fig_g    = go.Figure(go.Bar(
                    x=g_labels, y=g_vals,
                    marker=dict(color=g_colors, line=dict(width=0)),
                    text=[f"{v:.0f}%" for v in g_vals],
                    textposition="inside",
                    textfont=dict(size=13, color="#fff"),
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
                ))
                fig_g.update_layout(
                    title=dict(text="Grounding Rate",
                               font=dict(size=14, color="#e2e8f0")),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(range=[0, 115], showgrid=True,
                               gridcolor="rgba(255,255,255,.06)",
                               zeroline=False),
                    height=260,
                    **plotly_base(),
                )
                st.plotly_chart(fig_g, use_container_width=True)

            with c6:
                hr_pct    = hr_rate * 100
                ok_pct    = 100 - hr_pct
                fig_hr    = go.Figure(go.Bar(
                    x=["Auto-resolved", "Human Review"],
                    y=[ok_pct, hr_pct],
                    marker=dict(color=["#34d399", "#f97316"], line=dict(width=0)),
                    text=[f"{ok_pct:.0f}%", f"{hr_pct:.0f}%"],
                    textposition="inside",
                    textfont=dict(size=13, color="#fff"),
                    hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
                ))
                fig_hr.update_layout(
                    title=dict(text="Auto-resolve vs Human Review",
                               font=dict(size=14, color="#e2e8f0")),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(range=[0, 115], showgrid=True,
                               gridcolor="rgba(255,255,255,.06)",
                               zeroline=False),
                    height=260,
                    **plotly_base(),
                )
                st.plotly_chart(fig_hr, use_container_width=True)

    except Exception as e:
        st.error(f"Could not load analytics: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LIVE FEED
# ═══════════════════════════════════════════════════════════════════════════════

with tab_feed:
    st.markdown("### Live Ticket Feed")

    ctrl1, ctrl2, _ = st.columns([2, 3, 5])
    with ctrl1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with ctrl2:
        auto = st.toggle("Auto-refresh every 5 s",
                         value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto

    st.markdown("<br>", unsafe_allow_html=True)

    try:
        feed_res = requests.get(f"{BACKEND_URL}/tickets?limit=50", timeout=5)
        if not feed_res.ok:
            st.error("Could not fetch ticket feed.")
            st.stop()

        feed = feed_res.json()

        if not feed:
            st.info(
                "No tickets yet — go to **🎫 Analyze Ticket** to process some.",
                icon="🎫",
            )
        else:
            st.caption(
                f"Showing {len(feed)} most recent tickets · "
                f"{'auto-refresh on' if st.session_state.auto_refresh else 'manual refresh'}"
            )

            for t in feed:
                cat      = t.get("category",    "Other")
                pri      = t.get("priority",    "Medium")
                conf     = t.get("confidence",  5)
                route    = t.get("route_to",    "General Support")
                ts_raw   = t.get("timestamp",   "")
                text     = t.get("ticket_text", "—")
                grounded = t.get("grounded",    False)

                ts       = ts_raw[:16].replace("T", " ") if ts_raw else "—"
                excerpt  = text[:130] + ("…" if len(text) > 130 else "")

                cat_color  = CATEGORY_HEX.get(cat, "#94a3b8")
                cat_icon   = CATEGORY_ICON.get(cat, "📌")
                pri_color  = PRIORITY_HEX.get(pri, "#94a3b8")
                route_icon = ROUTE_ICON.get(route, "📨")
                g_icon     = "✓" if grounded else "⚠"
                g_color    = "#34d399" if grounded else "#f97316"

                safe_excerpt = html.escape(excerpt)

                st.markdown(f"""
<div class="feed-row" style="border-left-color:{pri_color}">
  <div class="feed-icon">
    <div class="feed-icon-emoji">{cat_icon}</div>
    <div class="feed-icon-conf">{conf}/10</div>
  </div>
  <div class="feed-body">
    <div class="feed-ticket">{safe_excerpt}</div>
    <div class="feed-badges">
      {badge(cat, cat_color)}
      {badge(pri, pri_color)}
      <span class="feed-route">{route_icon}&nbsp;{html.escape(route)}</span>
      <span style="font-size:.72rem;color:{g_color};opacity:.75">{g_icon}</span>
    </div>
  </div>
  <div class="feed-ts">{ts}</div>
</div>
""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Backend unavailable: {e}")

    # Auto-refresh loop
    if st.session_state.auto_refresh:
        time.sleep(5)
        st.rerun()
