"""LangGraph 파이프라인 조립 및 실행.

노드를 StateGraph에 등록하고 조건부 엣지를 연결한다.

스트리밍 경로:
  run_preformat()로 generator 직전(검색 + 인용 준비)까지 동기 실행한 뒤,
  stream_formatter()가 generator 출력을 직접 token 단위로 스트리밍한다.
  (formatter / expression_revision 노드는 generator 시스템 프롬프트에 흡수됨.)
"""

from __future__ import annotations

from collections.abc import Generator

from langgraph.graph import END, StateGraph

from app.graph.state import State
from app.graph.nodes.check_sensitive_info import (
  check_sensitive_info,
  route_after_check_sensitive_info,
)
from app.graph.nodes.understand_query import (
  understand_query,
  route_after_understand_query,
)
from app.graph.nodes.retrieve import retrieve
from app.graph.nodes.check_relevance import check_relevance
from app.graph.nodes.generator import generator, stream_generator
from app.graph.nodes.resolve_citations import resolve_citations
from app.graph.nodes.formatter import _build_citation_section


def build_graph(*, include_generator: bool = True) -> StateGraph:
  """파이프라인 그래프를 구성하고 컴파일한다.

  Args:
    include_generator: False이면 generator 노드를 제외하고 resolve_citations에서
      종료한다 (스트리밍용 — 외부에서 stream_generator로 직접 LLM 호출).
  """
  graph = StateGraph(State)

  # ── 공통 노드 ───────────────────────────────────────
  graph.add_node("check_sensitive_info", check_sensitive_info)
  graph.add_node("understand_query", understand_query)
  graph.add_node("retrieve", retrieve)
  graph.add_node("check_relevance", check_relevance)
  graph.add_node("resolve_citations", resolve_citations)

  graph.set_entry_point("check_sensitive_info")

  # check_sensitive_info의 라우터는 통과 시 'intent_understanding'을 반환하므로
  # path_map으로 통합 노드 'understand_query'에 매핑.
  graph.add_conditional_edges(
    "check_sensitive_info",
    route_after_check_sensitive_info,
    {END: END, 'intent_understanding': 'understand_query'},
  )
  graph.add_conditional_edges(
    "understand_query",
    route_after_understand_query,
  )
  graph.add_edge("retrieve", "check_relevance")

  if include_generator:
    graph.add_node("generator", generator)
    graph.add_conditional_edges(
      "check_relevance",
      lambda s: 'generator' if s.get('retrieval_passed') else END,
    )
    graph.add_edge("generator", "resolve_citations")
    graph.add_edge("resolve_citations", END)
  else:
    # 스트리밍 경로: generator 직전(인용 준비 완료)에서 종료
    graph.add_conditional_edges(
      "check_relevance",
      lambda s: 'resolve_citations' if s.get('retrieval_passed') else END,
    )
    graph.add_edge("resolve_citations", END)

  return graph.compile()


# 싱글턴 컴파일된 그래프
_compiled = build_graph(include_generator=True)
_compiled_preformat = build_graph(include_generator=False)


def run(query: str) -> dict:
  """파이프라인을 실행하여 결과를 반환한다."""
  return _compiled.invoke({"user_input": query})


def run_preformat(query: str) -> dict:
  """generator 직전까지 동기 실행하여 상태를 반환한다.

  스트리밍 경로에서 검색·필터·인용 준비를 마친 후, stream_formatter로
  generator를 직접 토큰 단위 스트리밍하기 위해 사용된다.
  """
  return _compiled_preformat.invoke({"user_input": query})


def stream_formatter(state: dict) -> Generator[str, None, None]:
  """pre-format 상태를 받아 generator를 토큰 단위로 스트리밍한다.

  과거에는 generator → formatter (별도 LLM) 두 단계였으나,
  formatter 규칙을 generator 시스템 프롬프트에 흡수하여 LLM 호출을
  1회로 줄였다. 함수명은 chat_service 호환을 위해 유지.

  Yields:
    답변 본문 토큰 청크 → 마지막에 인용 섹션(있으면).
  """
  citations = state.get("citations", [])

  yield from stream_generator(state)

  citation_section = _build_citation_section(citations)
  if citation_section:
    yield citation_section
