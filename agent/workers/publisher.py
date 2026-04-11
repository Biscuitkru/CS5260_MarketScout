"""
MarketScout: Publisher
==========================
"""
from functools import lru_cache
import json
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from agent.config import PUBLISHER_MODEL
from agent.state import MarketScoutState


class ReportTable(BaseModel):
    title: str = Field(description="Short title for the table.")
    columns: list[str] = Field(
        default_factory=list,
        description="Ordered list of column names used in the rows.",
    )
    rows: list[dict] = Field(
        default_factory=list,
        description="Table rows. Keys should match the declared columns.",
    )


class ReportChart(BaseModel):
    title: str = Field(description="Short chart title.")
    type: Literal["bar", "line", "area"] = Field(
        description="Chart type to render in Streamlit.",
    )
    data: list[dict] = Field(
        default_factory=list,
        description="Flat chart records with numeric values.",
    )
    x: str = Field(description="Field name to use for the x-axis.")
    y: str = Field(description="Field name to use for the y-axis.")


class PublisherOutput(BaseModel):
    report_markdown: str = Field(
        description="Polished market research report in Markdown.",
    )
    tables: list[ReportTable] = Field(
        default_factory=list,
        description="Useful compact tables when supported by the input data.",
    )
    charts: list[ReportChart] = Field(
        default_factory=list,
        description="Useful simple charts when supported by the input data.",
    )

@lru_cache(maxsize=4)
def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=model, temperature=0.3)


def publisher_node(state: MarketScoutState, config: RunnableConfig) -> dict:
    system_prompt = """\
You are the Publisher for MarketScout.

Your job is to turn the outputs of upstream workers into a polished, professional
market research report in Markdown, plus optional structured tables and charts.

Requirements:
- Use only the provided information.
- Do not invent competitors, reviews, ratings, market claims, or statistics.
- If evidence is weak or incomplete, say that clearly in the report.
- Be concise but professional.
- Emphasize actionable business insight, not generic summary.

Report structure:
# Market Research Report
## Executive Summary
## Market Overview
## Key Competitors
## Customer Pain Points
## Market Gaps and Opportunities
## Strategic Recommendations
## Risks and Unknowns
## Conclusion

Table and chart rules:
- Create tables only when they help summarize concrete data already present in the input.
- Create charts only when there is trustworthy numeric evidence such as ratings, review counts,
  competitor counts, percentages, or other explicit statistics.
- Prefer simple bar charts for comparisons; use line or area charts only if the data clearly implies them.
- Keep tables compact and decision-useful.
- If there is not enough reliable numeric evidence, return no charts.
- Rows in tables and records in charts must be valid JSON objects.
"""
    payload = {
        "business_idea": state.get("business_idea", ""),
        "target_location": state.get("target_location", ""),
        "search_queries": state.get("search_queries", []),
        "analysis": state.get("analysis", {}),
        "raw_results": state.get("raw_results", []),
    }
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=json.dumps(payload, indent=2)),
    ]
    model = config.get("configurable", {}).get("publisher_model", PUBLISHER_MODEL)
    llm = _get_llm(model).with_structured_output(PublisherOutput)
    output: PublisherOutput = llm.invoke(messages)

    return {
        "report": output.report_markdown.strip(),
        "report_tables": [table.model_dump() for table in output.tables],
        "report_charts": [chart.model_dump() for chart in output.charts],
    }
