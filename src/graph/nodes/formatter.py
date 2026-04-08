from src.graph.state import State
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

FORMATTER_SYSTEM_PROMPT = """\
당신은 Generation에 대해 답변의 스타일을 정제해 주는 AI 어시스턴트입니다.

규칙:
1. 불필요한 서두("물론입니다", "좋은 질문입니다" 등) 제거
2. 핵심 내용 위주로 구조화 (필요 시 번호 목록 사용)
3. 문장은 간결하게 (한 문장에 하나의 내용만)
4. 마크다운 형식 유지

==================

[출력 형식 (Format)]

답변: (핵심 내용을 쉬운 말로 설명하되 확답의 표현은 자제)

관련 법령/판례:
  - [출처] [법령명 또는 판례번호] : (법령/판례의 핵심 내용)
"""

def formatter(state: State) -> dict:
    """PDF 6번: generator 출력을 사용자에게 노출하기 좋은 형태로 정제"""
    final_answer = state.get('final_answer', '')
    if not final_answer:
        return {}

    response = llm.invoke([
        SystemMessage(content=FORMATTER_SYSTEM_PROMPT),
        HumanMessage(content=final_answer)
    ])

    return {
        'final_answer': response.content,
        'messages': [AIMessage(content=response.content)]
    }