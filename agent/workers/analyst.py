"""
MarketScout: Analyst Node
==========================
Reads state["raw_results"] from the Scout, uses an LLM to extract
competitor profiles, customer pain points, and market gaps.
Returns {"analysis": {...}} for the Publisher.
"""
import json
import logging
from functools import lru_cache
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agent.config import ANALYST_MODEL
from agent.state import MarketScoutState

from langgraph.config import get_stream_writer

logger = logging.getLogger(__name__)


# ── pydantic schemas ──────────────────────────────────────────────────
class ExistingBusiness(BaseModel):
    name: str = Field(description="Business name")
    strengths: list[str] = Field(default_factory=list, description="What this business does well based on reviews and ratings")
    weaknesses: list[str] = Field(default_factory=list, description="Where this business falls short based on reviews and ratings")
    avg_rating: Optional[float] = Field(default=None, description="Average star rating (1.0–5.0)")
    review_count: Optional[int] = Field(default=None, description="Total number of reviews")


class MarketAnalysis(BaseModel):
    competitors: list[ExistingBusiness] = Field(
        default_factory=list,
        description="Existing businesses in the target market that would compete with the user's proposed business idea",
    )
    pain_points: list[str] = Field(
        default_factory=list,
        description="Recurring customer complaints found across existing businesses in the target market",
    )
    market_gaps: list[str] = Field(
        default_factory=list,
        description="Unmet customer needs or opportunities that the user's proposed business could fill",
    )
    summary: str = Field(
        default="",
        description="2-3 paragraph narrative summarising the competitive landscape, "
        "key pain points, and the most promising market gaps",
    )


# ── cached model ──────────────────────────────────────────────────────
@lru_cache(maxsize=4)
def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.1)


# ── prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a senior market research analyst.

Context: A user is planning to start a new business. You will receive their \
business idea, their target location, and raw search results containing \
existing businesses that operate in the same market. These existing businesses \
are potential competitors to the user's proposed business.

Your task:
1. Profile each existing business — identify their strengths and weaknesses \
based on ratings, review snippets, and any available context.
2. Identify recurring customer pain points across these existing businesses — \
what do customers consistently complain about?
3. Identify market gaps — what needs are unmet by the current businesses that \
the user's proposed business could address?
4. Write a 2-3 paragraph summary of the competitive landscape.

Guidelines:
- Deduplicate businesses that appear under slight name variations.
- Be specific: "slow service during weekday lunch rush" is better than "bad service".
- If data is insufficient for a field, use null or an empty list — never fabricate data.
"""


def _build_user_prompt(state: MarketScoutState) -> str:
    """Format the raw results + context into a clear prompt for the LLM."""
    business_idea = state.get("business_idea", "unknown business")
    location = state.get("target_location", "unknown location")
    raw_results = state.get("raw_results", [])

    results_text = json.dumps(raw_results, indent=2, default=str)

    return (
        f"Proposed business idea: {business_idea}\n"
        f"Target location: {location}\n\n"
        f"Existing businesses found ({len(raw_results)} results):\n"
        f"{results_text}\n\n"
        "Produce the market analysis now."
    )


# ── node ──────────────────────────────────────────────────────────────
def analyst_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    """
    LangGraph node: analyse raw scout results and return structured insights.
    """
    writer = get_stream_writer()
    raw_results = state.get("raw_results", [])
    logger.info("Analyst: starting analysis of %d raw results", len(raw_results))
    writer({"agent": "analyst", "event": "start", "msg": f"Analysing {len(raw_results)} result groups"})


    model = config.get("configurable", {}).get("analyst_model", ANALYST_MODEL)
    llm = _get_llm(model)

    structured_llm = llm.with_structured_output(MarketAnalysis)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_user_prompt(state)),
    ]
    
    writer({"agent": "analyst", "event": "thinking", "msg": "Calling LLM to extract competitors, pain points, and market gaps"})


    analysis: MarketAnalysis = structured_llm.invoke(messages, config=config)

    logger.info(
        "Analyst: identified %d competitors, %d pain points, %d market gaps",
        len(analysis.competitors),
        len(analysis.pain_points),
        len(analysis.market_gaps),
    )
    
    writer({"agent": "analyst", "event": "done", "msg": (
        f"Identified {len(analysis.competitors)} competitors, "
        f"{len(analysis.pain_points)} pain points, "
        f"{len(analysis.market_gaps)} market gaps"
    )})

    return {"analysis": analysis.model_dump()}