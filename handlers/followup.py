"""
MarketScout: Followup Handler
====================
Handles follow-up questions after a report is generated.
Builds full context before the invoke call for an answer.
"""
import json
import streamlit as st

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.config import PUBLISHER_MODEL

def handle_followup(question: str, save_fn):
    ctx = st.session_state.pipeline_context or {}

    context_parts = [
        f"Business idea: {ctx.get('business_idea', 'N/A')}",
        f"Target location: {ctx.get('target_location', 'N/A')}",
        f"Search queries used: {json.dumps(ctx.get('search_queries', []))}",
    ]

    raw_results = ctx.get("raw_results", [])
    if raw_results:
        context_parts.append("\nRaw search results (with source URLs):")
        for group in raw_results:
            context_parts.append(f"\nQuery: {group.get('query', '')}")
            context_parts.append(f"Answer: {group.get('answer', '')}")
            for r in group.get("results", []):
                context_parts.append(
                    f"  - {r.get('name', '')} ({r.get('url', '')}): "
                    f"{r.get('snippet', '')}"
                )

    analysis = ctx.get("analysis", {})
    if analysis:
        context_parts.append(
            f"\nStructured analysis:\n{json.dumps(analysis, indent=2, default=str)}"
        )

    context_parts.append(f"\nFinal report:\n{st.session_state.report}")

    system_prompt = (
        "You are MarketScout, an autonomous market research assistant. "
        "The user has received a market research report and is now asking "
        "follow-up questions. You have access to the full research context "
        "below — including raw search results with source URLs, the structured "
        "analysis, and the final report.\n\n"
        "Guidelines:\n"
        "- Reference specific data, competitors, or sources when answering.\n"
        "- Cite source URLs when referencing specific findings.\n"
        "- If the user asks you to refine or rewrite a section, produce the "
        "updated section directly.\n"
        "- Be concise but thorough. Use markdown formatting.\n"
        "- If the data doesn't support an answer, say so honestly.\n\n"
        "Research context:\n" + "\n".join(context_parts)
    )

    llm_messages: list = [SystemMessage(content=system_prompt)]
    for msg in st.session_state.messages:
        # Report is already included in full inside the system prompt
        if msg["content"] == st.session_state.report:
            llm_messages.append(
                HumanMessage(content="[Report was generated and shown to the user]")
            )
            continue
        if msg["role"] == "user":
            llm_messages.append(HumanMessage(content=msg["content"]))
        else:
            llm_messages.append(
                HumanMessage(content=f"[Your previous response]: {msg['content']}")
            )

    llm_messages.append(HumanMessage(content=question))

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            llm = ChatGoogleGenerativeAI(model=PUBLISHER_MODEL, temperature=0.3)
            response = str(llm.invoke(llm_messages).content).strip()
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        save_fn()
        st.rerun()
