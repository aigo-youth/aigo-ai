"""LangGraph 파이프라인 전체 상태 스키마."""

from __future__ import annotations

from typing import Literal, TypedDict


class Citation(TypedDict):
  """개별 인용 출처."""

  doc_type: str       # "법령" | "판례" | "법령해석례"
  title: str          # 법령명 또는 사건명
  source_id: str      # 법령ID, 판례일련번호 등
  detail: str         # 조문번호, 사건번호 등
  url: str | None     # 법령정보 URL


class PipelineState(TypedDict, total=False):
  """LangGraph 파이프라인 전체 상태."""

  # ── 입력 ────────────────────────────────────────────
  raw_input: str
  input_type: Literal["pdf", "text"]

  # ── 전처리 ──────────────────────────────────────────
  user_query: str

  # ── 모더레이션 (입력) ───────────────────────────────
  moderation_passed: bool
  moderation_reason: str | None

  # ── 의도 분류 ───────────────────────────────────────
  intent: Literal["recommend", "dispute", "review", "unknown"]
  intent_metadata: dict[str, str]
  is_definitive_request: bool

  # ── 검색 ────────────────────────────────────────────
  retrieved_docs: list[dict]
  top_score: float
  retrieval_passed: bool

  # ── 생성 ────────────────────────────────────────────
  generated_answer: str
  citations: list[Citation]

  # ── 출력 ────────────────────────────────────────────
  formatted_answer: str
  final_answer: str
  output_moderation_passed: bool

  # ── 흐름 제어 ───────────────────────────────────────
  fallback_message: str | None
  is_terminated: bool
