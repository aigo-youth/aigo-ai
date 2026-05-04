"""intent_understanding + query_summary 통합 노드.

단일 LLM 호출로 (1) 의도 메타데이터, (2) 확답 차단,
(3) 링크 요청 여부, (4) 검색용 질의 요지, (5) 사용자 요청 요약을
한 번에 추출한다.

확답 차단 정책:
  통합 LLM 판단만 사용하면 false-positive가 빈번했던 경험을 반영,
  결정론적 정규식 1차 검사를 추가해 확답 회피를 우선 보장한다.
  (정규식 매칭 OR LLM 판단 → 차단)
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END

from app.core.logging import get_logger
from app.graph.state import State
from app.llm import llm

logger = get_logger(__name__)


# ── 결정론적 확답 차단 패턴 ─────────────────────────────
# 사용자가 "법적 책임을 동반한 단정 답변"을 명시적으로 요구할 때만 매칭되도록
# 보수적으로 구성. 일반 정보·확인 질문("맞나요?", "어떻게 되나요?")은 매칭 X.
DEFINITIVE_REGEX_PATTERNS: list[str] = [
    r"확답",                                    # "확답 부탁드립니다"
    r"100\s*%\s*(?:맞|보장|확실|확답|정답)",    # "100% 맞다", "100% 보장"
    r"단언",                                    # "단언컨대"
    r"장담",                                    # "장담할 수 있"
    r"보장(?:해|할|이|을)\s*(?:수\s*있|드릴|줄)",  # "보장해 줄 수 있"
    r"책임(?:지|질|을\s*지)\s*(?:실|수\s*있)",  # "책임지실 수 있나요"
    r"(?:반드시|꼭|무조건)\s*(?:이|그|맞|틀|유효|무효).{0,8}(?:다고|라고|이라고)\s*(?:답변|말씀|확인)",
    r"확실(?:한|히)\s*(?:답|답변|결론|말씀)",   # "확실한 답"
]

_compiled_definitive_patterns = [re.compile(p) for p in DEFINITIVE_REGEX_PATTERNS]


def _matches_definitive_regex(text: str) -> str | None:
    """매칭된 패턴 문자열을 반환, 없으면 None."""
    for pattern in _compiled_definitive_patterns:
        if pattern.search(text):
            return pattern.pattern
    return None


UNDERSTAND_QUERY_SYSTEM_PROMPT = """\
사용자의 질문을 분석해서 아래 JSON만 반환하세요. 설명 없이.

분석 항목:
1. intent_metadata: 벡터 DB 검색에 사용할 필터
   - doc_type: 답변 래퍼런스 카테고리 ("법령" | "법령해석례" | "판례" 중 하나, 모르면 null)
2. is_definitive: 사용자가 "법적 책임을 동반한 단정적 확답"을 명시적으로 요구하는지 여부
   - **기본값은 false. 대부분의 일반 질문은 false 입니다.**
   - true 조건: 단순 정보·상담 요청이 아니라 "100%", "확답", "장담", "보장",
     "책임지실 수 있나요" 같이 단정 답변을 명시적으로 요구하는 표현이 포함되어야 함.
   - true 예시 (드뭅니다):
     * "이게 100% 맞다고 답변해 주실 수 있나요?"
     * "반드시 무효라고 단정해서 답변해 주세요"
     * "확답 부탁드립니다. 책임지실 수 있나요?"
   - false 예시 (모두 false — 일반 정보·확인·상담 질문):
     * "전세보증금 반환은 어떻게 되나요?"
     * "이 조항이 유효한가요?"
     * "이게 맞나요?"
     * "월세 인상 한도가 어떻게 되나요?"
     * "임대차 보호법 적용 받을 수 있을까요?"
     * "특약이 효력이 있나요?"
     * "반드시 ~해야 하나요?"  ← 의무 여부를 묻는 일반 질문은 false
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
    """intent_understanding + query_summary를 단일 LLM 호출로 통합.

    확답 차단은 정규식 1차 + LLM 2차의 OR 결합으로 보수적 차단을 보장한다.
    """
    user_input = state['user_input']
    last_chat = state.get('messages', [])[-1:]

    matched_pattern = _matches_definitive_regex(user_input)

    response = llm.invoke([
        SystemMessage(content=UNDERSTAND_QUERY_SYSTEM_PROMPT),
        *last_chat,
        HumanMessage(content=user_input),
    ])

    raw = response.content.strip().strip('```json').strip('```').strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(
            "understand_query.json_parse_failed",
            user_input=user_input[:200],
            raw=raw[:300],
        )
        result = {
            "intent_metadata": {"doc_type": None},
            "is_definitive": False,
            "needs_link": False,
            "user_query": user_input,
            "user_request": "",
        }

    llm_definitive = bool(result.get('is_definitive', False))
    is_definitive = bool(matched_pattern) or llm_definitive

    if is_definitive:
        logger.info(
            "understand_query.definitive_blocked",
            user_input=user_input[:200],
            matched_pattern=matched_pattern,
            llm_definitive=llm_definitive,
        )
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
