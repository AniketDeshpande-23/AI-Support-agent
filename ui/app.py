import streamlit as st
import requests

st.set_page_config(page_title="AI Support Agent", layout="centered")

st.title("AI Support Ticket Agent")

ticket = st.text_area("Enter Support Ticket")

if st.button("Analyze"):

    if not ticket.strip():
        st.warning("Please enter a support ticket.")
        st.stop()

    with st.spinner("Analyzing..."):
        try:
            res = requests.post(
                "http://localhost:8000/analyze",
                json={"text": ticket},
                timeout=60
            )

            if res.status_code != 200:
                st.error("Backend error")
                st.stop()

            data = res.json()

        except requests.exceptions.RequestException:
            st.error("Cannot connect to backend.")
            st.stop()

    st.divider()

    st.write(f"**Category:** {data.get('category')}")
    st.write(f"**Priority:** {data.get('priority')}")
    st.write(f"**Confidence:** {data.get('confidence')}/10")
    st.write(f"**Grounded:** {data.get('grounded')}")
    st.write(f"**Route To:** {data.get('route_to')}")

    st.divider()

    st.subheader("Support Response")
    st.write(data.get("reply_draft"))
