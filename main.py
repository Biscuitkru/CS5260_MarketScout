"""
MarketScout: main
==========================
The script runs the full pipeline
"""
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from agent.graph import graph
from agent.state import MarketScoutState

def generate_report(user_query: str) -> str:
    initial_state: MarketScoutState = {
        "user_query": user_query,
        "business_idea": "",
        "target_location": "",
        "search_queries": [],
        "raw_results": [],
        "analysis": {},
        "report": "",
        "clarification_attempts": 0,
    }

    print("=" * 60)
    print("MarketScout: Autonomous Market Research Agent")
    print("=" * 60)
    print(f"Query: {user_query}\n")

    final_state = graph.invoke(initial_state)

    return final_state["report"]

def collect_query() -> str:
    return input("What market are you looking to research?\n> ").strip()

if __name__ == "__main__":
    query = collect_query()
    report = generate_report(query)

    print("\n" + "=" * 60)
    print(report)
