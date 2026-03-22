import streamlit as st
import requests
import json
import plotly.io as pio

API_URL = "http://127.0.0.1:8000"

st.title("AI Data Analyst")

session_id = st.text_input("Enter Session ID")

if st.button("Run Analysis"):

    response = requests.get(
        f"{API_URL}/get_full_analysis",
        params={"session_id": session_id}
    )

    data = response.json()

    st.subheader("Insights")

    for insight in data["insights"]["general"]:
        st.write("•", insight)

    st.subheader("LLM Insights")
    st.write(data["insights"]["llm"])

    st.subheader("EDA Plots")

    for plot_json in data["eda"]["univariate"]:
        fig = pio.from_json(plot_json)
        st.plotly_chart(fig)

    for plot_json in data["eda"]["bivariate"]:
        fig = pio.from_json(plot_json)
        st.plotly_chart(fig)

    if data["eda"]["correlation"]:
        fig = pio.from_json(data["eda"]["correlation"])
        st.plotly_chart(fig)

    for plot_json in data["eda"]["target_analysis"]:
        fig = pio.from_json(plot_json)
        st.plotly_chart(fig)