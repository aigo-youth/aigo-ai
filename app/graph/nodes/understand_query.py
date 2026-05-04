"""intent_understanding + query_summary 통합 노드.

단일 LLM 호출로 (1) 의도 메타데이터, (2) 확답 차단,
(3) 링크 요청 여부, (4) 검색용 질의 요지, (5) 사용자 요청 요약을
한 번에 추출한다.
"""

from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END

from app.graph.state import State
from app.llm import llm


UNDERSTAND_QUERY_SYSTEM_PROMPT = """\
사용자의 질문을 분석해서 아래 JSON만 반환하세요. 설명 없이.

분석 항목:
1. intent_metadata: 벡터 DB 검색에 사용할 필터
   - doc_type: 답변 래퍼런스 카테고리 ("법령" | "법령해석례" | "판례" 중 하나, 모르면 null)
2. is_definitive: 확답을 요구하는 질문인지 여부
   - true 예시: "~이 맞나요?", "반드시 ~해야 하나요?", "~가 100% 맞죠?", "답변에 책임 질 수 있어요?"
   - false 예시: "~에 대해 알려주세요", "~는 어떻게 하나요?"
3. needs_link: 사용자가 링크/출처/참고자료를 요청했는지 여부
4. user_query: 유사도 검색에 쓰기 위한 질문의 핵심 요지 (간결한 한 문장)
5. user_request: 사용자가 원하는 답변 형태/요청 사항 요약

응답 형식 (JSON만, 다른 텍스트 금지):
{
  "intent_metadata": {"doc_type": "법령"},
  "is_definitive": false,
  "needs_link": false,
  "user_query": "...",
  "user_request": "..."
}
"""

_FALLBACK_DEFINITIVE = (
    "해당 질문은 명확한 확답을 드리기 어렵습니다.\n"
    "상황과 조건에 따라 답변이 달라질 수 있어요.\n"
    "더 구체적인 상황을 설명해주시면 더 도움이 될 수 있습니다."
)


def understand_query(state: State) -> dict:
    """intent_understanding + query_summary를 단일 LLM 호출로 통합."""
    user_input = state['user_input']
    last_chat = state.get('messages', [])[-1:]

    response = llm.invoke([
        SystemMessage(content=UNDERSTAND_QUERY_SYSTEM_PROMPT),
        *last_chat,
        HumanMessage(content=user_input),
    ])

    raw = response.content.strip().strip('```json').strip('```').strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "intent_metadata": {"doc_type": None},
            "is_definitive": False,
            "needs_link": False,
            "user_query": user_input,
            "user_request": "",
        }

    if result.get('is_definitive', False):
        return {
            'is_definitive': True,
            'fallback_message': _FALLBACK_DEFINITIVE,
        }

    return {
        'is_definitive': False,
        'intent_metadata': result.get('intent_metadata', {}) or {},
        'needs_link': result.get('needs_link', False),
        'user_query': result.get('user_query') or user_input,
        'user_request': result.get('user_request', ''),
    }


def route_after_understand_query(state: State) -> str:
    """is_definitive면 종료, 아니면 retrieve로."""
    return END if state.get('is_definitive') else 'retrieve'
