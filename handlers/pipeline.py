"""
MarketScout: Pipeline Handler
====================================
Runs the LangGraph pipeline and streams progress to the UI.
Handles both initial queries and clarification resumes.
"""
from __future__ import annotations

import streamlit as st

from langchain_core.runnables import RunnableConfig

from agent.graph import graph
from agent.utils.slides import summarize_to_slides


AGENT_LABELS = {
    "planner":   "Planner — parsing intent & drafting queries",
    "clarify":   "Clarifier — asking for missing info",
    "scout":     "Scout — searching the web",
    "analyst":   "Analyst — extracting competitors & pain points",
    "publisher": "Publisher — drafting the final report",
}


def _print_slides(slides: list[dict]):
    print("\n" + "=" * 60)
    print("  SLIDE DECK PREVIEW")
    print("=" * 60)
    for i, slide in enumerate(slides, 1):
        print(f"\n[Slide {i}] {slide['title']}")
        if slide.get("subtitle"):
            print(f"          {slide['subtitle']}")
        print("-" * 40)
        for bullet in slide.get("bullets", []):
            print(f"  • {bullet}")
    print("\n" + "=" * 60 + "\n")


def run_pipeline(input_data, config: RunnableConfig, save_fn):
    with st.chat_message("assistant"):
        outer = st.status("Researching...", expanded=True)
        report = None
        ctx = st.session_state.pipeline_context or {}

        agent_status: dict = {}

        def get_status(node: str):
            if node not in agent_status:
                with outer:
                    agent_status[node] = st.status(
                        AGENT_LABELS.get(node, f"Agent: {node}"),
                        expanded=True,
                    )
            return agent_status[node]

        try:
            for stream_mode, chunk in graph.stream(
                input_data,
                config,
                stream_mode=["updates", "custom"],
            ):
                # Custom events emitted from inside nodes
                if stream_mode == "custom":
                    agent = chunk.get("agent", "system")
                    msg = chunk.get("msg", "")
                    s = get_status(agent)
                    with s:
                        st.write(msg)
                    if chunk.get("event") == "done":
                        s.update(state="complete")
                    continue

                # Final state writes per node
                update = chunk
                node = list(update.keys())[0]
                data = update[node]
                s = get_status(node)

                if node == "planner":
                    ctx["business_idea"] = data.get("business_idea", "")
                    ctx["target_location"] = data.get("target_location", "")
                    ctx["search_queries"] = data.get("search_queries", [])
                    with s:
                        st.write(f"**Business:** {ctx['business_idea']}")
                        st.write(f"**Location:** {ctx['target_location']}")
                        if ctx["search_queries"]:
                            st.write("**Search queries:**")
                            for q in ctx["search_queries"]:
                                st.write(f"- {q}")
                    s.update(state="complete")
                elif node == "scout":
                    ctx["raw_results"] = data.get("raw_results", [])
                    n = len(ctx["raw_results"])
                    with s:
                        st.write(f"Searched the web — {n} result groups collected")
                    s.update(state="complete")
                elif node == "analyst":
                    ctx["analysis"] = data.get("analysis", {})
                    nc = len(ctx["analysis"].get("competitors", []))
                    np_ = len(ctx["analysis"].get("pain_points", []))
                    ng = len(ctx["analysis"].get("market_gaps", []))
                    with s:
                        st.write(
                            f"Market analysis complete — {nc} competitors, "
                            f"{np_} pain points, {ng} market gaps"
                        )
                    s.update(state="complete")
                elif node == "publisher":
                    report = data.get("report", "")
                    ctx["report_tables"] = data.get("report_tables", [])
                    ctx["report_charts"] = data.get("report_charts", [])
                    nt = len(ctx["report_tables"])
                    nc = len(ctx["report_charts"])
                    if nt or nc:
                        with s:
                            st.write(
                                f"Prepared {nt} table(s) and {nc} chart(s) for the report"
                            )
                    s.update(state="complete")

        except Exception as e:
            outer.update(label="Pipeline failed", state="error")
            st.session_state.pipeline_error = str(e)
            st.session_state.error_config = config
            st.session_state.pipeline_context = ctx
            st.rerun()
            return

        state = graph.get_state(config)
        if state.next:
            question = state.tasks[0].interrupts[0].value
            outer.update(label="Need more information", state="complete")
            st.markdown(question)
            st.session_state.messages.append({"role": "assistant", "content": question})
            st.session_state.awaiting_clarification = True
            save_fn()
            st.rerun()
        elif report is not None:
            outer.update(label="Research complete!", state="complete")
            slide_data = summarize_to_slides(report)
            _print_slides(slide_data)
            st.session_state.slide_data = slide_data
            st.markdown(report)
            st.session_state.messages.append({"role": "assistant", "content": report})
            st.session_state.report = report
            st.session_state.pipeline_context = ctx
            st.session_state.awaiting_clarification = False
            save_fn()
            st.rerun()