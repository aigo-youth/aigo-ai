import asyncio
import re

from app.api.v1.schemas import SpecialTerm
from app.core.logging import get_logger
from app.pdf_graph.nodes.extracting_special_terms import extracting_special_terms

logger = get_logger(__name__)


_NOT_FOUND_MARKER = "특약 내용을 확인할 수 없습니다"
_LEAD_NUMBER_RE = re.compile(r"^\s*(\d+)\s*[\.\)]\s*(.*)$", re.DOTALL)


def _parse_numbered_terms(raw: str) -> list[SpecialTerm]:
    """LLM 이 만든 "1. ...\\n2. ..." 문자열을 SpecialTerm 리스트로 변환"""
    text = (raw or "").strip()
    if not text or _NOT_FOUND_MARKER in text:
        return []

    buckets: list[list[str]] = []
    for line in text.split("\n"):
        stripped = line.rstrip()
        match = _LEAD_NUMBER_RE.match(stripped)
        if match:
            remainder = match.group(2).strip()
            buckets.append([remainder] if remainder else [])
        elif buckets and stripped.strip():
            buckets[-1].append(stripped.strip())

    terms: list[SpecialTerm] = []
    for index, lines in enumerate(buckets, start=1):
        content = " ".join(line for line in lines if line).strip()
        if not content:
            continue
        terms.append(SpecialTerm(id=index, section=None, content=content))
    return terms


def _invoke_extractor(masked_text: str) -> str:
    """기존 LangGraph 노드 호출 (테스트에서 monkeypatch 가능)"""
    result = extracting_special_terms({"masked_text": masked_text})
    return result.get("special_term", "") if isinstance(result, dict) else ""


async def extract_special_terms(masked_text: str) -> list[SpecialTerm]:
    """마스킹된 계약서 본문에서 특약 조항 list 를 추출

    추출 실패는 부분 실패로 간주해 빈 list 를 반환
    PDF 분석 자체는 OCR 결과만으로 성공 응답하도록 부분 실패를 허용
    """
    if not masked_text or not masked_text.strip():
        return []

    try:
        raw = await asyncio.to_thread(_invoke_extractor, masked_text)
    except Exception as exc:
        logger.warning("special_terms.llm_failed", error=str(exc))
        return []

    return _parse_numbered_terms(raw)
