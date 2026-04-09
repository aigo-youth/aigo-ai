from src.graph.state import State
from src.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage

GENERATOR_SYSTEM_PROMPT = """\
당신은 사용자의 질문에 대해 주어진 context에 기반해 답변하는 부동산 전문가입니다.

[역할(Role)]
- 주택임대차보호법, 판례, 법령해석례를 기반으로 사용자가 계약 관련 궁금증을 해소할 수 있도록 정확한 정보를 안내합니다.
- 복잡한 법률 용어를 일반인도 이해할 수 있도록 쉽게 설명합니다.
- 제공된 법령/판례/해석례 문서만을 근거로 답변합니다.

[제약조건(Constraints)]
- 제공된 참고 문서를 기반으로 답변하세요.
- 문서에 없는 내용은 추측하거나 지어내지 마세요.
- 모든 답변에 반드시 출처(법령명, 조문번호, 판례번호)를 명시하세요.
- 확답 표현(반드시, 무조건, 절대적으로, 100% 등)은 사용하지 마세요.
- 법률적 판단이나 개인 법률 자문은 제공하지 않습니다.
- 간결하고 명확하게 답변하세요."""

MAX_HISTORY = 10


def generator(state: State) -> dict:
    """검색 문서 기반 답변 생성. 출처 URL은 resolve_citations 노드에서 처리."""
    user_input = state['user_input']
    retrieved_docs = state.get('retrieved_docs', [])
    history = state.get('messages', [])[-MAX_HISTORY:]

    context = "\n\n".join(
        f"[출처: {doc.get('title', '알 수 없음')} ({doc.get('doc_type', '')})]\n{doc.get('text', '')}"
        for doc in retrieved_docs
    )

    messages = [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        *history,
        HumanMessage(content=f"참고 문서:\n{context}\n\n질문: {user_input}")
    ]

    final_response = llm.invoke(messages)

    return {
        'messages': [HumanMessage(content=state['user_input'])],
        'final_answer': final_response.content,
    }
