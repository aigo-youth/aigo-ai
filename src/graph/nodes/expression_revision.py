from src.graph.state import State
import re
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# 1차 정규식 감지 패턴
DEFINITIVE_PATTERNS = [
    r'반드시',
    r'무조건',
    r'절대적으로',
    r'확실히',
    r'틀림없이',
    r'100\s*%',
    r'무조건적',
]

MODERATOR_3_SYSTEM_PROMPT = """\
아래 텍스트에서 확답을 주는 단정적 표현을 부드러운 표현으로 교체하세요.

교체 기준:
- "반드시" → "일반적으로"
- "무조건" → "대부분의 경우"
- "절대적으로" → "대체로"
- "확실히" → "일반적으로 보면"
- "틀림없이" → "보통은"
- "100%" → "대부분"

내용과 맥락은 유지하고, 단정적 표현만 교체하세요.
수정된 텍스트만 반환하세요."""


def expression_revision(state: State) -> dict:
    """PDF 7번: 정규식 1차 감지 → 확답 표현 있을 때만 LLM으로 교체"""
    final_answer = state.get('final_answer', '')
    if not final_answer:
        return {}

    # 1차: 정규식 — 확답 표현 없으면 LLM 호출 생략 (비용 절감)
    has_definitive = any(re.search(p, final_answer) for p in DEFINITIVE_PATTERNS)

    if not has_definitive:
        return {'messages': [AIMessage(content=final_answer)]}

    # 2차: LLM — 문맥을 유지하며 자연스럽게 표현 교체
    response = llm.invoke([
        SystemMessage(content=MODERATOR_3_SYSTEM_PROMPT),
        HumanMessage(content=final_answer)
    ])

    return {
        'final_answer': response.content,
        'messages': [AIMessage(content=response.content)]
    }