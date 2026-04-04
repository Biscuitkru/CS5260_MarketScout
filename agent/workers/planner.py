"""
MarketScout: Planner
==========================================
Parses user's query into structured parameters
to generate targeted search queries for the Scout
"""
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from agent.config import PLANNER_MODEL
from agent.state import MarketScoutState

# Output schema
class ResearchPlan(BaseModel):
    business_idea: str = Field(
        description="Core business concept, e.g. 'artisan coffee shop'"
    )
    target_location: str = Field(
        description="The geographic target market, e.g. 'Austin, TX'"
    )
    search_queries: list[str] = Field(
        description=(
            "x – y targeted web search queries to find local competitors and market data."
            "Angle should be varied: direct competitors, review-focused, pain-point-focused, gap-focused."
        ),
        min_length=4,
        max_length=6,
    )

MAX_CLARIFICATION_ATTEMPTS = 3

@lru_cache(maxsize=8)
def _get_llm(model: str, temperature: float) -> ChatGoogleGenerativeAI:
    """
    Cached per (model, temperature) pair — created once and reused across
    all graph.invoke() calls to avoid reinitialising the SDK client.
    """
    return ChatGoogleGenerativeAI(model=model, temperature=temperature)


SYSTEM_PROMPT = """\
You are the Planner for MarketScout, an autonomous market research agent \
to help entrepreneurs understand their competitive landscape before launching a business.

Your job is to parse the user's query and extract the structured fields required \
to search for local competitors.

With reference to the user's query, extract:
1. business_idea - the core business concept, normalised and concise
   (e.g. "specialty pour-over coffee shop", "plant-based bakery")
2. target_location - the specific geographic market
   (e.g. "Austin, TX", "East Nashville", "Singapore CBD")
3. search_queries - x to y targeted queries that will help the Scout find:
   - Direct competitors ("coffee shops in Austin TX")
   - Review-rich sources ("best coffee shops Austin TX Yelp")
   - Customer sentiment ("coffee shop complaints Austin TX Reddit")
   - Market gap signals ("what's missing coffee scene Austin TX")

Be specific. Generic queries like "business in city" produce poor results.
"""


def needs_clarification(state: MarketScoutState) -> str:
    if state["clarification_attempts"] >= MAX_CLARIFICATION_ATTEMPTS:
        return "scout"
    if not state["business_idea"] or not state["target_location"]:
        return "clarify"
    return "scout"


def clarify_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    missing = []
    if not state["business_idea"]:
        missing.append("the type of business")
    if not state["target_location"]:
        missing.append("the target location")

    model = config.get("configurable", {}).get("planner_model", PLANNER_MODEL)
    llm = _get_llm(model, 0.3)

    # Direct string construction — avoids .format() crashing on user input with curly braces
    prompt = (
        "You are a conversational assistant for MarketScout, a market research tool.\n"
        f'The user provided this query: "{state["user_query"]}"\n'
        f"From this query, the following could not be determined: {' and '.join(missing)}.\n"
        "Ask for the missing information in a single, natural sentence. Return only the question."
    )

    question = llm.invoke(prompt).content.strip()
    answer = interrupt(question)

    return {
        "user_query": f"{state['user_query']} {answer}",
        "clarification_attempts": state["clarification_attempts"] + 1,
    }


def planner_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    model = config.get("configurable", {}).get("planner_model", PLANNER_MODEL)
    llm = _get_llm(model, 0.0).with_structured_output(ResearchPlan)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_query"]),
    ]

    plan: ResearchPlan = llm.invoke(messages)

    print(f"[Planner] Business idea : {plan.business_idea}")
    print(f"[Planner] Location      : {plan.target_location}")
    print(f"[Planner] Search queries:")
    for q in plan.search_queries:
        print(f"          • {q}")

    return {
        "business_idea": plan.business_idea,
        "target_location": plan.target_location,
        "search_queries": plan.search_queries,
    }
