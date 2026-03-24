import streamlit as st
import requests
import plotly.io as pio

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Data Analyst", layout="wide")
st.title("🤖 AI Data Analyst")

col_session, col_refresh = st.columns([3, 1])
with col_session:
    session_id = st.text_input("Enter Session ID")
with col_refresh:
    force_refresh = st.checkbox("🔄 Refresh (re-run analysis)", value=False)

if st.button("Run Analysis") and session_id:

    with st.spinner("Running analysis..."):
        response = requests.get(
            f"{API_URL}/get_full_analysis",
            params={"session_id": session_id, "refresh": str(force_refresh).lower()}
        )

    if response.status_code == 404:
        st.error("Session not found — the server may have restarted. Please re-upload your dataset.")
        st.stop()
    if response.status_code != 200:
        st.error(f"Error {response.status_code}: {response.text}")
        st.stop()

    data = response.json()
    insights = data.get("insights", {})
    general  = insights.get("general", {})
    eda      = data.get("eda", {})

    # ── Summary ──────────────────────────────────────────────────────────
    if general.get("summary"):
        st.info(general["summary"])

    col1, col2 = st.columns(2)

    # ── Key Findings ─────────────────────────────────────────────────────
    with col1:
        st.subheader("🔑 Key Findings")
        for f in insights.get("key_findings", []):
            st.write("•", f)

    # ── Feature Importance ───────────────────────────────────────────────
    with col2:
        st.subheader("📊 Feature Importance")
        for item in insights.get("feature_importance", []):
            corr = item["correlation"]
            bar = "█" * int(abs(corr) * 20)
            sign = "+" if corr > 0 else "-"
            st.write(f"`{item['feature']}` {sign}{abs(corr):.3f}  {bar}")

    # ── Risk Flags ───────────────────────────────────────────────────────
    risk_flags = insights.get("risk_flags", [])
    if risk_flags:
        st.subheader("⚠️ Risk Flags")
        for flag in risk_flags:
            st.warning(flag)

    # ── Missing Values ───────────────────────────────────────────────────
    missing = general.get("missing", [])
    if missing:
        st.subheader("❌ Missing Values")
        for m in missing:
            st.write("•", m)

    # ── Skewness ─────────────────────────────────────────────────────────
    skewness = general.get("skewness", [])
    if skewness:
        st.subheader("📉 Skewness")
        for s in skewness:
            st.write("•", s)

    # ── Correlation Insights ─────────────────────────────────────────────
    correlation_insights = insights.get("correlation", [])
    if correlation_insights:
        st.subheader("🔗 Correlation Insights")
        for c in correlation_insights:
            st.write("•", c)

    # ── Target Analysis ──────────────────────────────────────────────────
    target_analysis = insights.get("target_analysis", [])
    if target_analysis:
        st.subheader("🎯 Target Analysis")
        for t in target_analysis:
            st.write("•", t)

    # ── Recommendations ──────────────────────────────────────────────────
    recommendations = insights.get("recommendations", [])
    if recommendations:
        st.subheader("✅ Recommendations")
        for r in recommendations:
            st.success(r)

    # ── LLM Insights ─────────────────────────────────────────────────────
    llm = insights.get("llm", "")
    if llm:
        with st.expander("🧠 LLM Insights"):
            st.write(llm)

    # ── EDA Plots ────────────────────────────────────────────────────────
    st.subheader("📈 EDA Plots")

    tabs = st.tabs(["Univariate", "Bivariate", "Correlation Matrix", "Target Analysis"])

    with tabs[0]:
        for plot_json in eda.get("univariate", []):
            fig = pio.from_json(plot_json)
            st.plotly_chart(fig)

    with tabs[1]:
        for plot_json in eda.get("bivariate", []):
            fig = pio.from_json(plot_json)
            st.plotly_chart(fig)

    with tabs[2]:
        if eda.get("correlation"):
            fig = pio.from_json(eda["correlation"])
            st.plotly_chart(fig)
        else:
            st.info("Not enough numerical columns for a correlation matrix.")

    with tabs[3]:
        for plot_json in eda.get("target_analysis") or []:
            fig = pio.from_json(plot_json)
            st.plotly_chart(fig)