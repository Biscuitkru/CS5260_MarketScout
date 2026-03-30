"""
MarketScout: Publisher
==========================
"""
from functools import lru_cache

from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

from agent.config import PUBLISHER_MODEL
from agent.state import MarketScoutState

@lru_cache(maxsize=4)
def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.3)


def publisher_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    # TODO: implement
    # model = config.get("configurable", {}).get("publisher_model", PUBLISHER_MODEL)
    # llm = _get_llm(model)
    return {"report": ""}
