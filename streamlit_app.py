"""
Streamlit UI for MarketScout.
"""
from __future__ import annotations

from dotenv import load_dotenv
import streamlit as st

from main import generate_report

load_dotenv()

st.set_page_config(
    page_title="MarketScout",
    page_icon="MS",
    layout="wide",
)

st.title("MarketScout")
st.caption(
    "Generate a market research report from a business idea and target location."
)

if "report" not in st.session_state:
    st.session_state.report = ""

if "submitted_query" not in st.session_state:
    st.session_state.submitted_query = ""

with st.form("market_scout_form"):
    business_idea = st.text_input(
        "Business idea",
        placeholder="Artisan coffee shop",
        help="Describe the business you want to research.",
    )
    target_location = st.text_input(
        "Target location",
        placeholder="Austin, TX",
        help="Enter the city, neighborhood, or market you want to analyze.",
    )
    submitted = st.form_submit_button("Generate report", use_container_width=True)

if submitted:
    if not business_idea.strip() or not target_location.strip():
        st.error("Please enter both a business idea and a target location.")
    else:
        with st.spinner("Researching the market and drafting your report..."):
            try:
                st.session_state.report = generate_report(
                    business_idea + " " + target_location
                )
            except Exception as exc:
                st.session_state.report = ""
                st.error(f"Unable to generate the report: {exc}")

st.subheader("Report")
if st.session_state.report:
    st.markdown(st.session_state.report)
else:
    st.info("Your generated market report will appear here.")
