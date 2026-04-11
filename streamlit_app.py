"""
MarketScout: Streamlit App
==========================
Streamlit UI for MarketScout.
"""
from uuid import uuid4

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from agent.utils.slides import build_pptx, summarize_to_slides

from agent.state import MarketScoutState
from database.sessions import rename_session, save_session
from handlers.followup import handle_followup
from handlers.pipeline import run_pipeline
from handlers.sidebar import render_sidebar

# Page setup
st.set_page_config(page_title="MarketScout", page_icon="MS", layout="wide")
st.title("MarketScout")
st.caption("Your autonomous market research agent. Ask me about any market.")

# Session state
_defaults = {
    "messages": [],
    "thread_id": None,
    "awaiting_clarification": False,
    "report": None,
    "pipeline_context": None,
    "pending_input": None,
    "renaming_session": None,
    "pipeline_error": None,   # error message when pipeline fails
    "error_config": None,     # config to resume from after error
    "slide_data": None,       # pre-computed slide dicts for pptx + terminal
}
for key, val in _defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def _render_report_artifacts():
    ctx = st.session_state.pipeline_context or {}
    report_tables = ctx.get("report_tables", [])
    report_charts = ctx.get("report_charts", [])

    if not report_tables and not report_charts:
        return

    st.divider()
    st.subheader("Report Data")

    for table in report_tables:
        rows = table.get("rows", [])
        if not rows:
            continue
        st.markdown(f"**{table.get('title', 'Table')}**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    for chart in report_charts:
        records = chart.get("data", [])
        x_field = chart.get("x")
        y_field = chart.get("y")
        if not records or not x_field or not y_field:
            continue

        df = pd.DataFrame(records)
        if x_field not in df.columns or y_field not in df.columns:
            continue

        st.markdown(f"**{chart.get('title', 'Chart')}**")
        chart_frame = df.set_index(x_field)
        chart_type = chart.get("type", "bar")

        if chart_type == "line":
            st.line_chart(chart_frame[y_field])
        elif chart_type == "area":
            st.area_chart(chart_frame[y_field])
        else:
            st.bar_chart(chart_frame[y_field])

# strip border + arrow from sidebar popover buttons
st.markdown("""
<style>
section[data-testid="stSidebar"] [data-testid="stPopover"] button {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 4px !important;
}
section[data-testid="stSidebar"] [data-testid="stPopover"] button svg {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


# Session persistence
def _save_current_session():
    tid = st.session_state.thread_id
    if not tid or not st.session_state.messages:
        return
    title = next(
        (m["content"][:60] for m in st.session_state.messages if m["role"] == "user"),
        "Untitled",
    )
    save_session(
        session_id=tid,
        title=title,
        messages=st.session_state.messages,
        pipeline_context=st.session_state.pipeline_context,
        report=st.session_state.report,
    )


# Chat renaming
@st.dialog("Rename this chat")
def _rename_dialog():
    session = st.session_state.renaming_session
    if not session:
        st.rerun()
        return
    new_name = st.text_input("", value=session["title"], label_visibility="collapsed")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cancel", use_container_width=True, type="tertiary"):
            st.session_state.renaming_session = None
            st.rerun()
    with col2:
        if st.button("Rename", use_container_width=True, type="primary"):
            if new_name.strip():
                rename_session(session["id"], new_name.strip())
            st.session_state.renaming_session = None
            st.rerun()


if st.session_state.renaming_session:
    _rename_dialog()

render_sidebar()

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

_render_report_artifacts()

# Download button — shown persistently once a report exists
if st.session_state.report and st.session_state.slide_data:
    pptx_bytes = build_pptx(st.session_state.slide_data)
    st.download_button(
        label="Download Slide Deck (.pptx)",
        data=pptx_bytes,
        file_name="MarketScout_SlideDeck.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

# Retry button — shown when pipeline hit an error
if st.session_state.pipeline_error:
    st.error(st.session_state.pipeline_error)
    if st.button("Retry"):
        st.session_state.pipeline_error = None
        run_pipeline(None, st.session_state.error_config, _save_current_session)

# Input routing
if st.session_state.pending_input is not None:
    placeholder = "Researching your market..."
elif st.session_state.report is not None:
    placeholder = "What else would you like to know about this market?"
elif st.session_state.awaiting_clarification:
    placeholder = "Type your answer..."
else:
    placeholder = "Describe the market you want to research..."

is_busy = st.session_state.pending_input is not None

# Phase 1: capture input + rerun so UI updates before pipeline runs
if prompt := st.chat_input(placeholder, disabled=is_busy):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.pending_input = prompt
    st.rerun()

# Phase 2: on next rerun, execute pipeline
if st.session_state.pending_input is not None:
    prompt = st.session_state.pending_input
    st.session_state.pending_input = None

    if st.session_state.awaiting_clarification:
        config: RunnableConfig = {"configurable": {"thread_id": st.session_state.thread_id}}
        run_pipeline(Command(resume=prompt), config, _save_current_session)

    elif st.session_state.report is not None:
        handle_followup(prompt, _save_current_session)

    else:
        thread_id = str(uuid4())
        st.session_state.thread_id = thread_id
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        initial_state: MarketScoutState = {
            "user_query": prompt,
            "business_idea": "",
            "target_location": "",
            "search_queries": [],
            "raw_results": [],
            "analysis": {},
            "report": "",
            "report_tables": [],
            "report_charts": [],
            "clarification_attempts": 0,
        }
        run_pipeline(initial_state, config, _save_current_session)
