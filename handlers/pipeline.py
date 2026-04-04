"""
MarketScout: Pipeline Handler
====================
Runs the LangGraph pipeline and streams progress to the UI.
Handles both initial queries and clarification resumes.
"""
import streamlit as st

from langchain_core.runnables import RunnableConfig

from agent.graph import graph

def run_pipeline(input_data, config: RunnableConfig, save_fn):
    with st.chat_message("assistant"):
        status = st.status("Researching...", expanded=True)
        report = None
        ctx = st.session_state.pipeline_context or {}

        for update in graph.stream(input_data, config, stream_mode="updates"):
            node = list(update.keys())[0]
            data = update[node]

            if node == "planner":
                ctx["business_idea"] = data.get("business_idea", "")
                ctx["target_location"] = data.get("target_location", "")
                ctx["search_queries"] = data.get("search_queries", [])
                status.write(f"**Business:** {ctx['business_idea']}")
                status.write(f"**Location:** {ctx['target_location']}")
                if ctx["search_queries"]:
                    status.write("**Search queries:**")
                    for q in ctx["search_queries"]:
                        status.write(f"- {q}")
            elif node == "scout":
                ctx["raw_results"] = data.get("raw_results", [])
                n = len(ctx["raw_results"])
                status.write(f"Searched the web — {n} result groups collected")
            elif node == "analyst":
                ctx["analysis"] = data.get("analysis", {})
                nc = len(ctx["analysis"].get("competitors", []))
                np_ = len(ctx["analysis"].get("pain_points", []))
                ng = len(ctx["analysis"].get("market_gaps", []))
                status.write(
                    f"Market analysis complete — {nc} competitors, "
                    f"{np_} pain points, {ng} market gaps"
                )
            elif node == "publisher":
                report = data.get("report", "")

        state = graph.get_state(config)
        if state.next:
            question = state.tasks[0].interrupts[0].value
            status.update(label="Need more information", state="complete")
            st.markdown(question)
            st.session_state.messages.append({"role": "assistant", "content": question})
            st.session_state.awaiting_clarification = True
            save_fn()
            st.rerun()
        elif report is not None:
            status.update(label="Research complete!", state="complete")
            st.markdown(report)
            st.session_state.messages.append({"role": "assistant", "content": report})
            st.session_state.report = report
            st.session_state.pipeline_context = ctx
            st.session_state.awaiting_clarification = False
            save_fn()
            st.rerun()
