"""
MarketScout: LangGraph Pipeline
==================================
Wires the worker nodes into a linear StateGraph:

    START -> orchestrator -> scout -> analyst -> publisher -> END

This file should not need changes unless you add new nodes or branching logic.
"""

from langgraph.graph import END, START, StateGraph

from agent.state import MarketScoutState
from agent.workers.analyst import analyst_node
from agent.workers.orchestrator import orchestrator_node
from agent.workers.publisher import publisher_node
from agent.workers.scout import scout_node

def build_graph():
    """Build and compile the MarketScout LangGraph pipeline."""
    builder = StateGraph(MarketScoutState)

    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node("scout", scout_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("publisher", publisher_node)

    # NOTE: Add the edges in the order of execution, e.g. when you create a new node, add an edge from the previous node to it, and from it to the next node.
    builder.add_edge(START, "orchestrator")
    builder.add_edge("orchestrator", "scout")
    builder.add_edge("scout", "analyst")
    builder.add_edge("analyst", "publisher")
    builder.add_edge("publisher", END)

    return builder.compile()

graph = build_graph()
