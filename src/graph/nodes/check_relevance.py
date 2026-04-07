from src.config import RELEVANCE_THRESHOLD
from src.graph.state import PipelineState

_FALLBACK_MSG = (
  "죄송합니다, 해당 질문에 대한 정확한 답변을 찾지 못했습니다. "
  "질문을 좀 더 구체적으로 입력해주시겠어요?"
)


def check_relevance(
  state: PipelineState,
  threshold: float | None = None,
) -> PipelineState:
  """
  검색 결과의 유사도 점수를 기준으로 응답 가능 여부를 판정

  Args:
    state: 파이프라인 상태. retrieved_docs와 top_score 필요
    threshold: 유사도 임계값. None이면 config 기본값 사용

  Returns:
    retrieval_passed, fallback_message, is_terminated 키가 갱신된 상태
  """
  threshold = threshold if threshold is not None else RELEVANCE_THRESHOLD
  docs = state.get("retrieved_docs", [])
  top_score = state.get("top_score", 0.0)

  passed = len(docs) > 0 and top_score >= threshold

  if passed:
    return {
      "retrieval_passed": True,
      "fallback_message": None,
      "is_terminated": False,
    }

  return {
    "retrieval_passed": False,
    "fallback_message": _FALLBACK_MSG,
    "is_terminated": True,
  }
