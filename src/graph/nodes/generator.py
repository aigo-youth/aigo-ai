from langchain_tavily import TavilySearch
from src.graph.state import State
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

# Tavily 검색 도구 — PDF 5번: 링크 요청 시에만 사용
tavily_tool = TavilySearch(max_results=3)

# Tool이 바인딩된 LLM — tool_calls 응답을 낼 수 있는 버전
llm_with_tools = llm.bind_tools([tavily_tool])

GENERATOR_SYSTEM_PROMPT = """\
당신은 사용자의 질문에 대해 주어진 context에 기반해 답변하는 부동산 전문가입니다.
사용자가 링크를 요청하면 'tavily' 도구를 호출하여 URL을 확보한 뒤 답변에 포함하세요.

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


def generator(state: State) -> dict:
    """PDF 5번: 검색 문서 기반 답변 생성 + needs_link일 때만 Tavily Tool 사용"""
    user_input     = state['user_input']
    retrieved_docs = state.get('retrieved_docs', [])
    needs_link     = state.get('needs_link', False)

    # 검색된 문서를 컨텍스트로 조합
    context = "\n\n".join(
        f"[출처: {doc['metadata'].get('source', '알 수 없음')}]\n{doc['content']}"
        for doc in retrieved_docs
    )

    messages = [
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=f"참고 문서:\n{context}\n\n질문: {user_input}")
    ]

    # generator 내장된 Tavily tool이라서 이렇게 되면 독립된 Tavily tool 노드는 없게 되는 듯 합니다...
    if needs_link:
        # PDF 5번 Tool: 링크 요청 시에만 Tavily 실행
        ai_response = llm_with_tools.invoke(messages)

        if hasattr(ai_response, 'tool_calls') and ai_response.tool_calls:
            tool_call   = ai_response.tool_calls[0]
            tool_result = tavily_tool.invoke(tool_call['args'])

            # 툴 결과를 대화에 추가 후 최종 응답 생성
            messages.append(ai_response)
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call['id']
            ))
            final_response = llm.invoke(messages)
        else:
            final_response = ai_response
    else:
        # 링크 불필요 → 일반 LLM 호출 (비용 절감)
        final_response = llm.invoke(messages)

    return {
        'final_answer': final_response.content,
        'messages': [final_response]
    }