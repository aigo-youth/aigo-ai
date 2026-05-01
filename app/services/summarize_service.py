import asyncio
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.logging import get_logger
from app.llm import llm

logger = get_logger(__name__)

_SYSTEM_PROMPT = """당신은 사용자의 질문을 채팅방 제목으로 쓸 한국어 한 줄로 요약하는 도우미입니다.

규칙:
1. 명사구 위주 (예: "전세 계약 분쟁 상담")
2. 마침표/물음표/이모지 없음
3. 따옴표로 감싸지 말 것
4. 한 줄로만 출력
5. 최대 30자 이내
** 실패하거나 빈 응답 시 질문 앞부분을 최대 30자까지 반환 (예: "전세 계약 관련 문의")"""


def _invoke_llm(messages):
    """LLM 호출 단위 (테스트에서 monkeypatch 가능)."""
    return llm.invoke(messages)


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^[\"'`]+|[\"'`]+$", "", text)
    text = text.split("\n", 1)[0].strip()
    return text


def _fallback(question: str, max_chars: int) -> str:
    fallback = question.strip().split("\n", 1)[0]
    return fallback[:max_chars].strip() or "새 대화"


async def summarize_for_title(question: str, max_chars: int = 30) -> str:
    """질문에서 채팅방 제목 한 줄을 생성한다.

    실패/빈 응답 시 질문 앞부분을 fallback으로 반환한다.
    """
    try:
        response = await asyncio.to_thread(
            _invoke_llm,
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=question),
            ],
        )
        title = _clean(getattr(response, "content", "") or "")
    except Exception as exc:
        logger.warning("summarize.fallback", error=str(exc))
        return _fallback(question, max_chars)

    if not title:
        return _fallback(question, max_chars)

    return title[:max_chars]
