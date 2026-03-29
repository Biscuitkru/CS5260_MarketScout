"""
MarketScout: Orchestrator Node
==========================================
Parses user's query into structured parameters
to generate targeted search queries for the Scout
"""
from functools import lru_cache

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agent.config import ORCHESTRATOR_MODEL
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

# LLM singleton
@lru_cache(maxsize=4)
def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    """
    Client is created once per unique model string and this will be reused across all graph.invoke() calls
    
    To avoid re-initialising the SDK client on every request.
    """
    return ChatGoogleGenerativeAI(model=model, temperature=0)

SYSTEM_PROMPT = """\
Assume the role of the Orchestrator for MarketScout, an autonomous market research agent \
to help entrepreneurs understand their competitive landscape before launching a business.

Your job is to parse the user's query and extract accordingly with the structured fields required \
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

#####################################################################################
# Node
#####################################################################################
def orchestrator_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    """
    Orchestrator node: parses user intent to plan for the Scout
    """
    model = config.get("configurable", {}).get("orchestrator_model", ORCHESTRATOR_MODEL)
    llm = _get_llm(model).with_structured_output(ResearchPlan)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=state["user_query"]),
    ]

    plan: ResearchPlan = llm.invoke(messages)

    print(f"[Orchestrator] Model         : {model}")
    print(f"[Orchestrator] Business idea : {plan.business_idea}")
    print(f"[Orchestrator] Location      : {plan.target_location}")
    print(f"[Orchestrator] Search queries:")
    for q in plan.search_queries:
        print(f"               • {q}")

    return {
        "business_idea": plan.business_idea,
        "target_location": plan.target_location,
        "search_queries": plan.search_queries,
    }
