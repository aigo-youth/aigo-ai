"""LangGraph 파이프라인 전체 상태 스키마."""

from __future__ import annotations

from typing import Literal, TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class Citation(TypedDict):
  """개별 인용 출처."""

  doc_type: str       # "법령" | "판례" | "법령해석례"
  title: str          # 법령명 또는 사건명
  source_id: str      # 법령ID, 판례일련번호 등
  detail: str         # 조문번호, 사건번호 등
  url: str | None     # 법령정보 URL


class State(TypedDict, total=False):
  """LangGraph 파이프라인 전체 상태."""

  # ── 입력 ────────────────────────────────────────────
  user_input: str
  # input_type: Literal["pdf", "text"]
  messages: Annotated[List, add_messages] # 메시지 히스토리 저장 (세션 아이디에 따라 저장하진 않을 것이기 때문에)

  # ── 전처리 ──────────────────────────────────────────
  # user_query: str

  # ── 모더레이션 (입력) ───────────────────────────────
  is_sensitive: bool
  is_definitive: bool 
  # moderation_passed: bool
  # moderation_reason: str | None

  # ── 의도 분류 ───────────────────────────────────────
  intent: Literal["recommend", "dispute", "review", "unknown"]
  intent_metadata: Optional[dict]       # dict[str, str]
  # is_definitive_request: bool >>> 모더레이션에 비슷한 거 있
  needs_link: bool

  # ── 검색 ────────────────────────────────────────────
  retrieved_docs: Optional[List[dict]]  # list[dict]
  similarity_score: Optional[float]  # top_score: float
  retrieval_passed: bool

  # ── 생성 ────────────────────────────────────────────
  # generated_answer: str
  # citations: list[Citation]

  # ── 출력 ────────────────────────────────────────────
  # formatted_answer: str
  final_answer: Optional[str]       # str
  # output_moderation_passed: bool

  # ── 흐름 제어 ───────────────────────────────────────
  fallback_message: str | None
  is_terminated: bool
