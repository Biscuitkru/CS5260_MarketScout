"""
MarketScout: main
==========================
CLI entry point — runs the full pipeline with interrupt handling.
"""
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv()

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

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

    thread_id = str(uuid4())
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    print("=" * 60)
    print("MarketScout: Autonomous Market Research Agent")
    print("=" * 60)
    print(f"Query: {user_query}\n")

    result = graph.invoke(initial_state, config)

    # For clarification interrupts
    state = graph.get_state(config)
    while state.next:
        question = state.tasks[0].interrupts[0].value
        answer = input(f"\n{question}\n> ").strip()
        result = graph.invoke(Command(resume=answer), config)
        state = graph.get_state(config)

    return result["report"]

def collect_query() -> str:
    return input("What market are you looking to research?\n> ").strip()

if __name__ == "__main__":
    query = collect_query()
    report = generate_report(query)

    print("\n" + "=" * 60)
    print(report)
