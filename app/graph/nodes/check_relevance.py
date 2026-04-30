from langgraph.graph import END

from app.config import RELEVANCE_THRESHOLD
from app.graph.state import State

_FALLBACK_MSG_CR = (
  "죄송합니다, 해당 질문에 대한 정확한 답변을 찾지 못했습니다. "
  "질문을 좀 더 구체적으로 입력해주시겠어요?"
)


def check_relevance(
  state: State,
  threshold: float | None = None,
) -> State:
  """
  검색 결과의 유사도 점수를 기준으로 응답 가능 여부를 판정

  Args:
    state: 파이프라인 상태. retrieved_docs와 similarity_score 필요
    threshold: 유사도 임계값. None이면 config 기본값 사용

  Returns:
    retrieval_passed, fallback_message, is_terminated 키가 갱신된 상태
  """
  threshold = threshold if threshold is not None else RELEVANCE_THRESHOLD
  docs = state.get("retrieved_docs", [])
  similarity_score = state.get("similarity_score", 0.0)

  passed = len(docs) > 0 and similarity_score >= threshold

  if passed:
    return {
      "retrieval_passed": True,   # ↓ 자매품으로 이 친구도 알아보면 좋을 것 같다.
      "fallback_message": None,
      "is_terminated": False,     # 얘는 무슨 의도인지 확인해야할 것 같다.
    }

  return {
    "retrieval_passed": False,
    "fallback_message": _FALLBACK_MSG_CR,
    "is_terminated": True,
  }


### check_relevance의 조건부 엣지 함수
def route_after_check_relevance(state: State) -> str:
    '''
    <소개>
    check_relevance 노드의 조건부 엣지 함수
    
    <기능>
    - retrieval_passed 값에 따라 다음 노드 결정
        - True : 통과(다음 단계로)
        - False : Fallback(-> END)
    '''
    
    if state['retrieval_passed'] == False:
      print(state['fallback_message'])

    return 'generator' if state['retrieval_passed'] else END