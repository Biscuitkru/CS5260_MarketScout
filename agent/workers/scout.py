"""
MarketScout: Scout
==========================
Runs each search query from the Planner against the Tavily API
and accumulates the raw results.

Emits custom stream events via get_stream_writer() so the frontend can
display live tool-call activity (which query is running, what came back).
"""
import os

from langgraph.config import get_stream_writer
from tavily import TavilyClient

from agent.state import MarketScoutState


def scout_node(state: MarketScoutState) -> dict:
    writer = get_stream_writer()
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    raw_results: list[dict] = []

    queries = state["search_queries"]
    total = len(queries)

    writer({
        "agent": "scout",
        "event": "start",
        "msg": f"Starting web research — {total} queries to run",
    })

    for i, query in enumerate(queries, 1):
        print(f"[Scout] Searching: {query}")
        writer({
            "agent": "scout",
            "event": "tool_call",
            "tool": "tavily_search",
            "msg": f"[{i}/{total}] Searching Tavily: {query}",
        })

        response = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        answer = response.get("answer", "") or ""
        results = response.get("results", [])
        print(f"[Scout] Answer: {answer}")

        writer({
            "agent": "scout",
            "event": "tool_result",
            "tool": "tavily_search",
            "msg": (
                f"[{i}/{total}] Got {len(results)} results"
                + (f" — {answer[:140]}{'...' if len(answer) > 140 else ''}" if answer else "")
            ),
        })

        query_results = {
            "query":   query,
            "answer":  answer,
            "results": [],
        }
        for r in results:
            query_results["results"].append({
                "name":    r.get("title", ""),
                "url":     r.get("url", ""),
                "snippet": r.get("content", ""),
                "source":  "tavily",
            })
        raw_results.append(query_results)

    print(f"[Scout] Collected {len(raw_results)} results across {total} queries")
    writer({
        "agent": "scout",
        "event": "done",
        "msg": f"Collected {len(raw_results)} result groups across {total} queries",
    })

    return {"raw_results": raw_results}