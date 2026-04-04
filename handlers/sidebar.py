"""
MarketScout: Sidebar
====================================
Renders the sidebar: new-chat button, past sessions list, and session actions.
"""
from datetime import datetime, timezone

import streamlit as st

from database.sessions import delete_session, list_sessions, load_session

def render_sidebar():
    with st.sidebar:
        st.markdown(
            "This Agent Product is entirely derived from work conducted "
            "as part of the **NUS CS5260** course."
        )
        if st.button("New research", use_container_width=True):
            st.session_state.messages = []
            st.session_state.thread_id = None
            st.session_state.awaiting_clarification = False
            st.session_state.report = None
            st.session_state.pipeline_context = None
            st.session_state.pending_input = None
            st.rerun()

        st.divider()
        st.caption("PAST SESSIONS")
        past = list_sessions()
        if not past:
            st.caption("No saved sessions yet.")

        for s in past:
            try:
                updated = datetime.fromisoformat(s["updated_at"])
                diff = datetime.now(timezone.utc) - updated
                if diff.days == 0:
                    hours = diff.seconds // 3600
                    time_label = "Just now" if hours == 0 else f"{hours}h ago"
                elif diff.days == 1:
                    time_label = "Yesterday"
                elif diff.days < 7:
                    time_label = f"{diff.days}d ago"
                else:
                    time_label = updated.strftime("%b %d")
            except (ValueError, TypeError):
                time_label = ""

            title = s["title"][:30] + ("..." if len(s["title"]) > 30 else "")
            is_active = s["id"] == st.session_state.thread_id

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col1:
                if st.button(
                    title,
                    key=f"load_{s['id']}",
                    use_container_width=True,
                    disabled=is_active,
                    type="tertiary",
                ):
                    data = load_session(s["id"])
                    if data:
                        st.session_state.messages = data["messages"]
                        st.session_state.thread_id = data["id"]
                        st.session_state.pipeline_context = data["pipeline_context"]
                        st.session_state.report = data["report"]
                        st.session_state.awaiting_clarification = False
                        st.session_state.pending_input = None
                        st.rerun()
            with col2:
                with st.popover("\u22EE"):
                    if st.button("Rename", key=f"rename_{s['id']}", use_container_width=True, type="tertiary"):
                        st.session_state.renaming_session = {"id": s["id"], "title": s["title"]}
                        st.rerun()
                    if st.button("Delete", key=f"del_{s['id']}", use_container_width=True, type="tertiary"):
                        delete_session(s["id"])
                        if is_active:
                            st.session_state.messages = []
                            st.session_state.thread_id = None
                            st.session_state.report = None
                            st.session_state.pipeline_context = None
                        st.rerun()
