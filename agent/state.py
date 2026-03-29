"""
MarketScout: State
======================================
Source of truth for all data flowing through the LangGraph pipeline.
Ideally the worker node reads from and writes to this structure.

Pipeline order:  orchestrator -> scout -> analyst -> publisher
"""
import operator
from typing import Annotated
from typing_extensions import TypedDict

class MarketScoutState(TypedDict):
    # 1. INPUT (set once by main.py before graph.invoke())
    user_query: str
    # Example: "I want to open an artisan coffee shop in Austin, Texas"

    # 2. ORCHESTRATOR OUTPUTS (written by orchestrator.py)
    business_idea: str
    # Normalized business concept, e.g. "artisan coffee shop"
    target_location: str
    # Geographic target market, e.g. "Austin, TX"
    search_queries: list[str]
    # 4–6 targeted queries for the Scout to run, e.g.:
    #   ["coffee shops Austin TX", "best cafes Austin TX reviews", ...]
    # Replacement semantics: orchestrator sets this once and Scout reads it.

    # 3. SCOUT OUTPUTS (written by scout.py)
    raw_results: Annotated[list[dict], operator.add]
    # Accumulated search results from Tavily, change the schema as needed based on actual API response.
    # {
    #     "name":         str,
    #     "url":          str,
    #     "address":      str,
    #     "rating":       float | None,   # 1.0–5.0 star rating
    #     "review_count": int | None,
    #     "snippet":      str,            # short description or review excerpt
    #     "source":       str,            # e.g. "google_maps", "yelp", "tavily"
    # }

    # 4. ANALYST OUTPUTS (written by analyst.py)
    analysis: dict
    # Structured market intelligence, e.g. competitor profiles, customer pain points, market gaps, do add as you see fit.
    # This will be the main input for the Publisher, so design it with the final report in mind. Example schema:
    # {
    #     "competitors": [
    #         {
    #             "name":         str,
    #             "strengths":    list[str],
    #             "weaknesses":   list[str],
    #             "avg_rating":   float | None,
    #             "review_count": int | None,
    #         }
    #     ],
    #     "pain_points":  list[str],  # what customers hate about existing options
    #     "market_gaps":  list[str],  # unmet needs the new business could fill
    #     "summary":      str,        # 2–3 paragraph narrative for the publisher
    # }

    # 5. PUBLISHER OUTPUTS (written by publisher.py)
    report: str
    # Final market research report. Markdown string by default. Change output format as you see fit.
