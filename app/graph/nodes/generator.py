from collections.abc import Generator

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import State
from app.llm import llm, streaming_llm

GENERATOR_SYSTEM_PROMPT = """\
당신은 '아이고 청년' 서비스의 AI 부동산 계약 조항 검토 전문가입니다.

[역할(Role)]
- 주택임대차보호법, 판례, 법령해석례를 기반으로 사용자의 부동산 계약 조항을 검토하고, 계약 관련 궁금증을 해소할 수 있도록 정확한 정보를 안내합니다.
- 복잡한 법률 용어를 일반인도 이해할 수 있도록 쉽게 설명합니다.
- 제공된 법령/판례/해석례 문서만을 근거로 답변합니다.

[제약조건(Constraints)]
- 제공된 참고 문서를 기반으로 답변하세요.
- 문서에 없는 내용은 추측하거나 지어내지 마세요.
- 모든 답변에 출처(법령명, 조문번호, 판례번호)를 명시하세요. (별도의 출처 섹션은 시스템이 자동으로 덧붙입니다.)
- 법률적 판단이나 개인 법률 자문은 제공하지 않습니다.

[표현 제약 — 매우 중요]
다음 단정적 표현은 절대 사용하지 말고 반드시 대체 표현을 사용하세요:
- "반드시" → "일반적으로"
- "무조건" → "대부분의 경우"
- "절대적으로" → "대체로"
- "확실히" → "일반적으로 보면"
- "틀림없이" → "보통은"
- "100%" → "대부분"
"절대", "무조건적", "100% 맞다", "확답드립니다" 등의 단정 표현 역시 금지.

[출력 스타일]
- 불필요한 서두("물론입니다", "좋은 질문입니다" 등) 제거.
- 핵심 내용 위주로 구조화 (필요 시 번호 목록 사용).
- 문장은 간결하게 (한 문장에 하나의 내용만).
- 마크다운 형식 유지.
- 답변은 "답변:" 으로 시작하고, 이후 핵심 내용을 쉬운 말로 설명.
"""

MAX_HISTORY = 10


def _build_messages(state: State) -> list:
    """generator/stream_generator가 공유하는 메시지 빌더."""
    user_input = state['user_input']
    retrieved_docs = state.get('retrieved_docs', [])
    history = state.get('messages', [])[-MAX_HISTORY:]

    context = "\n\n".join(
        f"[출처: {doc.get('title', '알 수 없음')} ({doc.get('doc_type', '')})]\n{doc.get('text', '')}"
        for doc in retrieved_docs
    )

    return [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        *history,
        HumanMessage(content=f"참고 문서:\n{context}\n\n질문: {user_input}"),
    ]


def generator(state: State) -> dict:
    """비-스트리밍 경로용 — 검색 문서 기반 답변 생성."""
    final_response = llm.invoke(_build_messages(state))

    return {
        'messages': [HumanMessage(content=state['user_input'])],
        'final_answer': final_response.content,
    }


def stream_generator(state: State) -> Generator[str, None, None]:
    """스트리밍 경로용 — generator 출력을 토큰 단위로 yield."""
    for chunk in streaming_llm.stream(_build_messages(state)):
        if chunk.content:
            yield chunk.content
