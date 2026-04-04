"""
MarketScout: Publisher
==========================
"""
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.config import PUBLISHER_MODEL
from agent.state import MarketScoutState
import json

@lru_cache(maxsize=4)
def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.3)


def publisher_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    systemPrompt = """\
    You are the Publisher for MarketScout.

    Your job is to turn the outputs of upstream workers into a polished, professional
    market research report in Markdown.

    Requirements:
    - Use only the provided information.
    - Do not invent competitors, reviews, ratings, or market claims.
    - If evidence is weak or incomplete, state that clearly.
    - Be concise but professional.
    - Emphasize actionable business insight, not generic summary.

    Output structure:
    # Market Research Report
    ## Executive Summary
    ## Market Overview
    ## Key Competitors
    ## Customer Pain Points
    ## Market Gaps and Opportunities
    ## Strategic Recommendations
    ## Risks and Unknowns
    ## Conclusion
    """
    #tentative state structure, need to update later
    payload = {
        "business_idea": state.get("business_idea", ""),
        "target_location": state.get("target_location", ""),
        "search_queries": state.get("search_queries", []),
        "analysis": state.get("analysis", {}),
        "raw_results": state.get("raw_results", []),
    }
    messages = [
        SystemMessage(content=systemPrompt),
        HumanMessage(content=json.dumps(payload, indent=2)),
    ]
    model = config.get("configurable", {}).get("publisher_model", PUBLISHER_MODEL)
    llm = _get_llm(model)
    report = llm.invoke(messages).content.strip()
    return {"report": report}
