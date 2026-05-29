"""
ui/app.py — Streamlit frontend for the AI Support Agent.

Two tabs:
  🎫 Analyze Ticket  — submit a ticket and see results with colour-coded badges
  📋 Ticket History  — metrics overview + filterable table of all past tickets
"""

import os
import time

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Styling maps ──────────────────────────────────────────────────────────────

PRIORITY_COLOR = {
    "Critical": "#dc2626",
    "High":     "#ea580c",
    "Medium":   "#ca8a04",
    "Low":      "#16a34a",
}
PRIORITY_EMOJI = {
    "Critical": "🔴",
    "High":     "🟠",
    "Medium":   "🟡",
    "Low":      "🟢",
}
ROUTE_EMOJI = {
    "Engineering":   "🔧",
    "Finance":       "💰",
    "Product":       "📦",
    "Senior Support":"⚡",
    "Human Review":  "👤",
    "General Support":"💬",
}
CATEGORY_EMOJI = {
    "Billing":         "💳",
    "Login Issue":     "🔐",
    "Bug Report":      "🐛",
    "Feature Request": "💡",
    "Other":           "📌",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_backend():
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return r.status_code == 200, r.json() if r.ok else {}
    except Exception:
        return False, {}


def colored_badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:3px 11px;'
        f'border-radius:12px;font-size:0.82em;font-weight:700;'
        f'letter-spacing:0.02em">{label}</span>'
    )


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Support Agent",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide the default Streamlit menu / footer for a cleaner look
st.markdown(
    "<style>footer{visibility:hidden} #MainMenu{visibility:hidden}</style>",
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🎫 AI Support Agent")
    st.caption("v2.0 · Production Ready")
    st.divider()

    online, health_data = check_backend()

    if online:
        st.success("✅ Backend Online")
        provider = health_data.get("provider", "—")
        model    = health_data.get("model", "—")
        st.caption(f"Provider: `{provider}`")
        st.caption(f"Model:    `{model}`")
    else:
        st.error("❌ Backend Offline")
        st.caption("Start the server first:")
        st.code("uvicorn app.main:app --reload", language="bash")

    st.divider()
    st.markdown("""
**Pipeline (single LLM call):**
1. Retrieve docs via RAG (FAISS)
2. Classify + prioritise + draft reply
3. Confidence & grounding check
4. Auto-route to right team
5. Log to SQLite
""")
    st.divider()
    st.caption("API docs → [localhost:8000/docs](http://localhost:8000/docs)")


# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_analyze, tab_history = st.tabs(["🎫 Analyze Ticket", "📋 Ticket History"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Analyze
# ═══════════════════════════════════════════════════════════════════════════════

with tab_analyze:
    st.markdown("### Submit a Support Ticket")

    ticket_text = st.text_area(
        "ticket_input",
        placeholder=(
            "Paste the customer's message here…\n\n"
            "Example: 'I was charged twice for my subscription this month "
            "and cannot log in to request a refund.'"
        ),
        height=160,
        label_visibility="collapsed",
    )

    char_count = len(ticket_text)
    st.caption(f"{char_count} / 2000 characters")

    btn_col, _ = st.columns([1, 6])
    with btn_col:
        analyze_btn = st.button(
            "Analyze →",
            type="primary",
            disabled=(not ticket_text.strip() or not online or char_count > 2000),
            use_container_width=True,
        )

    if not online:
        st.warning("Start the FastAPI backend to enable ticket analysis.")

    # ── Results ───────────────────────────────────────────────────────────────
    if analyze_btn and ticket_text.strip():
        with st.spinner("Analysing ticket…"):
            try:
                t0 = time.perf_counter()
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
                    st.warning("Rate limit reached — wait a moment and try again.")
                    st.stop()
                elif not res.ok:
                    st.error(f"Backend error ({res.status_code}): {res.json().get('detail', 'unknown')}")
                    st.stop()

                data = res.json()

            except requests.exceptions.Timeout:
                st.error("Request timed out. The model may still be loading — try again.")
                st.stop()
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend.")
                st.stop()

        st.success(f"Analysis complete in **{elapsed:.1f}s**")
        st.divider()

        # Layout: metadata left | reply right
        meta_col, reply_col = st.columns([1, 2], gap="large")

        with meta_col:
            st.markdown("#### Classification")

            cat      = data.get("category", "—")
            pri      = data.get("priority", "—")
            conf     = int(data.get("confidence", 0))
            grounded = data.get("grounded", False)
            route    = data.get("route_to", "—")

            # Category
            cat_emoji = CATEGORY_EMOJI.get(cat, "📌")
            st.markdown(f"**Category** &nbsp; {cat_emoji} {cat}", unsafe_allow_html=True)

            # Priority badge
            pri_color = PRIORITY_COLOR.get(pri, "#6b7280")
            pri_emoji = PRIORITY_EMOJI.get(pri, "⚪")
            st.markdown(
                f"**Priority** &nbsp; "
                + colored_badge(f"{pri_emoji} {pri}", pri_color),
                unsafe_allow_html=True,
            )
            st.write("")  # spacer

            # Confidence meter
            st.markdown(f"**Confidence** &nbsp; `{conf}/10`")
            st.progress(conf / 10)

            # Grounding
            g_icon  = "✅" if grounded else "⚠️"
            g_label = "Grounded in docs" if grounded else "Not fully grounded"
            g_color = "#15803d" if grounded else "#b45309"
            st.markdown(
                f"**Source Check** &nbsp; "
                + colored_badge(f"{g_icon} {g_label}", g_color),
                unsafe_allow_html=True,
            )
            st.write("")

            # Route
            route_emoji = ROUTE_EMOJI.get(route, "📨")
            st.markdown(f"**Routed To** &nbsp; {route_emoji} **{route}**", unsafe_allow_html=True)

        with reply_col:
            st.markdown("#### Draft Response")
            reply = data.get("reply_draft", "No response generated.")
            st.text_area(
                "reply_output",
                value=reply,
                height=260,
                label_visibility="collapsed",
                help="AI-generated reply — review before sending.",
            )
            st.caption("Review and edit before sending to the customer.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — History
# ═══════════════════════════════════════════════════════════════════════════════

with tab_history:
    st.markdown("### Ticket History")

    if st.button("🔄 Refresh"):
        st.rerun()

    # ── Metrics row ───────────────────────────────────────────────────────────
    try:
        m_res = requests.get(f"{BACKEND_URL}/metrics", timeout=5)
        if m_res.ok:
            m = m_res.json()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Tickets", m.get("total", 0))
            c2.metric("Avg Confidence", f"{m.get('avg_confidence', 0)}/10")

            by_pri       = m.get("by_priority", {})
            critical_high = by_pri.get("Critical", 0) + by_pri.get("High", 0)
            c3.metric("Critical / High", critical_high)

            by_cat = m.get("by_category", {})
            top_cat = max(by_cat, key=by_cat.get) if by_cat else "—"
            c4.metric("Top Category", top_cat)
    except Exception:
        st.info("Metrics unavailable — is the backend running?")

    st.divider()

    # ── Ticket table ──────────────────────────────────────────────────────────
    try:
        t_res = requests.get(f"{BACKEND_URL}/tickets?limit=200", timeout=5)
        if t_res.ok:
            tickets = t_res.json()
            if not tickets:
                st.info("No tickets yet. Analyse a ticket to see it here.")
            else:
                df = pd.DataFrame(tickets)
                df = df[["id", "timestamp", "category", "priority", "confidence", "grounded", "route_to"]]
                df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d %H:%M")
                df.rename(columns={
                    "id": "ID",
                    "timestamp": "Time",
                    "category": "Category",
                    "priority": "Priority",
                    "confidence": "Confidence",
                    "grounded": "Grounded",
                    "route_to": "Routed To",
                }, inplace=True)

                # Filter controls
                f1, f2, _ = st.columns([2, 2, 4])
                with f1:
                    cat_filter = st.multiselect(
                        "Category", df["Category"].dropna().unique().tolist()
                    )
                with f2:
                    pri_filter = st.multiselect(
                        "Priority", ["Critical", "High", "Medium", "Low"]
                    )

                if cat_filter:
                    df = df[df["Category"].isin(cat_filter)]
                if pri_filter:
                    df = df[df["Priority"].isin(pri_filter)]

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Confidence": st.column_config.ProgressColumn(
                            "Confidence",
                            min_value=0,
                            max_value=10,
                            format="%d/10",
                        ),
                        "Grounded": st.column_config.CheckboxColumn("Grounded"),
                    },
                )
                st.caption(f"Showing {len(df)} ticket(s)")
        else:
            st.error("Could not fetch ticket history from backend.")
    except Exception:
        st.error("Backend unavailable — cannot load ticket history.")
