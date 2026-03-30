"""
MarketScout: LangGraph Pipeline
==================================
Wires the worker nodes into a StateGraph:

    START -> planner -> scout -> analyst -> publisher -> END
                 ^    (if fields missing, up to 3 attempts)
                 |
              clarify

This file should not need changes unless you add new nodes or branching logic.
"""

from langgraph.graph import END, START, StateGraph

from agent.state import MarketScoutState
from agent.workers.analyst import analyst_node
from agent.workers.planner import clarify_node, needs_clarification, planner_node
from agent.workers.publisher import publisher_node
from agent.workers.scout import scout_node

def build_graph():
    """Build and compile the MarketScout LangGraph pipeline."""
    builder = StateGraph(MarketScoutState)

    builder.add_node("planner", planner_node)
    builder.add_node("clarify", clarify_node)
    builder.add_node("scout", scout_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("publisher", publisher_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner",
        needs_clarification,
        {"clarify": "clarify", "scout": "scout"},
    )
    builder.add_edge("clarify", "planner")
    builder.add_edge("scout", "analyst")
    builder.add_edge("analyst", "publisher")
    builder.add_edge("publisher", END)

    return builder.compile()

graph = build_graph()
