"""PDF 텍스트 추출 과정의 LangGraph LangGraph 파이프라인 조립 및 실행.

노드를 StateGraph에 등록하고 조건부 엣지를 연결한다.
"""

# from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from src.pdf_graph.state import PDF_State
from src.pdf_graph.nodes.check_pdf import (
  check_pdf,
  route_after_check_pdf,
)
from src.pdf_graph.nodes.digital_to_text import digital_to_text
from src.pdf_graph.nodes.scan_to_text import scan_to_text
from src.pdf_graph.nodes.masking_text import masking_text
from src.pdf_graph.nodes.extracting_special_terms import extracting_special_terms


def build_graph() -> StateGraph:
  """파이프라인 그래프를 구성하고 컴파일한다.

  Args:
    include_formatter: False이면 formatter 노드를 제외하고
      expression_revision에서 종료한다 (스트리밍용).
  """
  graph = StateGraph(PDF_State)

  # ── 노드 등록 ──────────────────────────────────────
  graph.add_node('check_pdf', check_pdf)
  graph.add_node('digital_to_text', digital_to_text)
  graph.add_node('scan_to_text', scan_to_text)
  graph.add_node('masking_text', masking_text)
  graph.add_node('extracting_special_terms', extracting_special_terms)

  # ── 엣지 연결 ──────────────────────────────────────
  graph.set_entry_point('check_pdf')
    # graph.add_edge(START, 'check_pdf')

  graph.add_conditional_edges(
      'check_pdf', route_after_check_pdf,
      ['digital_to_text', 'scan_to_text']
  )
  graph.add_edge('digital_to_text', 'masking_text')
  graph.add_edge('scan_to_text', 'masking_text')
  graph.add_edge('masking_text', 'extracting_special_terms')
  graph.add_edge('extracting_special_terms', END)

  return graph.compile()


# 싱글턴 컴파일된 그래프
_compiled = build_graph()