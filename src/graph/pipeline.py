"""LangGraph 파이프라인 조립 및 실행.

노드를 StateGraph에 등록하고 조건부 엣지를 연결한다.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.graph.state import State
from src.graph.nodes.check_sensitive_info import (
  check_sensitive_info,
  route_after_check_sensitive_info,
)
from src.graph.nodes.intent_understanding import (
  intent_understanding,
  route_after_intent_understanding,
)
from src.graph.nodes.query_summary import query_summary
from src.graph.nodes.retrieve import retrieve
from src.graph.nodes.check_relevance import (
  check_relevance,
  route_after_check_relevance,
)
from src.graph.nodes.generator import generator
from src.graph.nodes.resolve_citations import resolve_citations
from src.graph.nodes.expression_revision import expression_revision
from src.graph.nodes.formatter import formatter


def build_graph() -> StateGraph:
  """파이프라인 그래프를 구성하고 컴파일한다."""
  graph = StateGraph(State)

  # ── 노드 등록 ──────────────────────────────────────
  graph.add_node("check_sensitive_info", check_sensitive_info)
  graph.add_node("intent_understanding", intent_understanding)
  graph.add_node("query_summary", query_summary)
  graph.add_node("retrieve", retrieve)
  graph.add_node("check_relevance", check_relevance)
  graph.add_node("generator", generator)
  graph.add_node("resolve_citations", resolve_citations)
  graph.add_node("expression_revision", expression_revision)
  graph.add_node("formatter", formatter)

  # ── 엣지 연결 ──────────────────────────────────────
  graph.set_entry_point("check_sensitive_info")

  graph.add_conditional_edges(
    "check_sensitive_info",
    route_after_check_sensitive_info,
  )
  graph.add_conditional_edges(
    "intent_understanding",
    route_after_intent_understanding,
  )
  graph.add_edge("query_summary", "retrieve")
  graph.add_edge("retrieve", "check_relevance")
  graph.add_conditional_edges(
    "check_relevance",
    route_after_check_relevance,
  )
  graph.add_edge("generator", "resolve_citations")
  graph.add_edge("resolve_citations", "expression_revision")
  graph.add_edge("expression_revision", "formatter")
  graph.add_edge("formatter", END)

  return graph.compile()


# 싱글턴 컴파일된 그래프
_compiled = build_graph()


def run(query: str) -> dict:
  """파이프라인을 실행하여 결과를 반환한다.

  Args:
    query: 사용자 질의 텍스트.

  Returns:
    final_answer 또는 fallback_message를 포함하는 상태 dict.
  """
  result = _compiled.invoke({"user_input": query})
  return result
