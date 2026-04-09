from src.graph.state import State
from src.llm import llm
from langchain_core.messages import HumanMessage, SystemMessage

FORMATTER_SYSTEM_PROMPT = """\
당신은 Generation에 대해 답변의 스타일을 정제해 주는 AI 어시스턴트입니다.

규칙:
1. 불필요한 서두("물론입니다", "좋은 질문입니다" 등) 제거
2. 핵심 내용 위주로 구조화 (필요 시 번호 목록 사용)
3. 문장은 간결하게 (한 문장에 하나의 내용만)
4. 마크다운 형식 유지
5. 출처 관련 내용은 수정하지 말 것 (별도로 추가됨)

==================

[출력 형식 (Format)]

답변: (핵심 내용을 쉬운 말로 설명하되 확답의 표현은 자제)
"""


def _build_citation_section(citations: list[dict]) -> str:
    """citations 리스트를 마크다운 출처 섹션으로 변환한다."""
    if not citations:
        return ""

    lines = ["\n\n---\n**관련 법령/판례:**"]
    for c in citations:
        doc_type = c.get("doc_type", "")
        title = c.get("title", "")
        detail = c.get("detail", "")
        url = c.get("url", "")

        label = title
        if detail:
            label += f" {detail}"

        if url:
            lines.append(f"- [{doc_type}] [{label}]({url})")
        else:
            lines.append(f"- [{doc_type}] {label}")

    return "\n".join(lines)


def formatter(state: State) -> dict:
    """generator 출력을 정제하고 출처 링크를 추가한다."""
    final_answer = state.get('final_answer', '')
    citations = state.get('citations', [])

    if not final_answer:
        return {}

    response = llm.invoke([
        SystemMessage(content=FORMATTER_SYSTEM_PROMPT),
        HumanMessage(content=final_answer)
    ])

    formatted = response.content
    citation_section = _build_citation_section(citations)

    return {
        'final_answer': formatted + citation_section,
    }
