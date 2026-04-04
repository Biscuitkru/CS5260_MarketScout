"""
MarketScout: Scout
==========================
Runs each search query from the Planner against the Tavily API
and accumulates the raw results.
"""
import os

from tavily import TavilyClient

from agent.state import MarketScoutState


def scout_node(state: MarketScoutState) -> dict:
    """
    Runs each search query from the Planner against the Tavily API.

    Writes to state["raw_results"]: list of query-grouped result objects.

    Output schema (one item per search query):
    [
        {
            "query":   str,          # the original search query string from the Planner
            "answer":  str,          # Tavily's AI-synthesised answer for the query (e.g. "Top 10 complaints")
            "results": [
                {
                    "name":    str,  # page/article title
                    "url":     str,  # source URL
                    "snippet": str,  # relevant excerpt from the page (main signal for sentiment analysis)
                    "source":  str,  # always "tavily"
                },
                ...                  # up to max_results entries per query
            ]
        },
        ...                          # one group per search query
    ]

    Analyst tips:
    - "answer" is a quick summary; use it for high-level context per query angle.
    - "snippet" is the richest field — mine it for competitor mentions, customer
      sentiment, pain points, and market-gap signals.
    - "query" tells you the angle (e.g. complaints, gaps, top-rated) so you can
      weight snippets accordingly when categorising findings.
    """
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    raw_results: list[dict] = []

    for query in state["search_queries"]:
        print(f"[Scout] Searching: {query}")
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        answer = response.get("answer", "")
        print(f"[Scout] Answer: {answer}")
        query_results = {
            "query":        query,
            "answer":       answer,
            "results": []
        }
        for r in response.get("results", []):
            query_results["results"].append({
                "name":         r.get("title", ""),
                "url":          r.get("url", ""),
                "snippet":      r.get("content", ""),
                "source":       "tavily",
            })
        raw_results.append(query_results)

    print(f"[Scout] Collected {len(raw_results)} results across {len(state['search_queries'])} queries")
    return {"raw_results": raw_results}
