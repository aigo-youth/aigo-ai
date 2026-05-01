import asyncio
import json
import re
from datetime import date
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.api.v1.schemas import KeyClause, PropertyInfo
from app.core.logging import get_logger
from app.llm import llm

logger = get_logger(__name__)


_EXTRACTION_PROMPT = """당신은 한국 부동산 임대차 계약서 분석 전문가입니다.
계약서 본문에서 아래 두 가지를 추출해 **반드시 JSON 한 객체** 로만 응답하세요.

## 1) property_info (매물 정보)
| 필드 | 설명 |
|---|---|
| location | 소재지 (40자 이내, 없으면 null) |
| start_date | 계약 시작일 (YYYY-MM-DD, 없으면 null) |
| end_date | 계약 종료일 (YYYY-MM-DD, 없으면 null) |
| month_rent | 월세 (정수 원 단위, 없으면 null) |
| deposit | 보증금 (정수 원 단위, 없으면 null) |
| house_cost | 관리비 (10자 이내 문자열, 없으면 null) |

## 2) key_clauses (핵심 조항 배열)
보증금/월세/계약기간/관리비/원상복구/하자보수 등 임차인 보호와 직결되는 핵심 조항만 골라 배열로 반환.
각 항목은 {"section": "조항명", "content": "원문 그대로의 조항 내용"} 형태.
없으면 빈 배열.

## 출력 예시
{"property_info": {"location": "서울시 ...", "start_date": "2024-03-01", "end_date": "2026-02-28", "month_rent": 700000, "deposit": 10000000, "house_cost": "5만원"}, "key_clauses": [{"section": "제1조 (보증금)", "content": "..."}]}

다른 설명, 마크다운 코드 블록, 주석을 일절 포함하지 마세요. JSON 객체만 출력하세요."""


def _strip_code_fence(text: str) -> str:
    """LLM 이 ```json ... ``` 으로 감쌌을 때 본문만 추출."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 2:
            body = parts[1].strip()
            if body.lower().startswith("json"):
                body = body[4:].strip()
            return body
    return text


def _parse_date(value: Any) -> date | None:
    if not value or not isinstance(value, str):
        return None
    match = re.match(r"(\d{4})[-./](\d{1,2})[-./](\d{1,2})", value.strip())
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _parse_amount(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return int(value) if value >= 0 else None
    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        if not digits:
            return None
        try:
            amount = int(digits)
        except ValueError:
            return None
        return amount if amount >= 0 else None
    return None


def _truncate(value: Any, max_len: int) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    return trimmed[:max_len]


def _build_property_info(raw: Any) -> PropertyInfo:
    if not isinstance(raw, dict):
        return PropertyInfo()
    return PropertyInfo(
        location=_truncate(raw.get("location"), 40),
        start_date=_parse_date(raw.get("start_date")),
        end_date=_parse_date(raw.get("end_date")),
        month_rent=_parse_amount(raw.get("month_rent")),
        deposit=_parse_amount(raw.get("deposit")),
        house_cost=_truncate(raw.get("house_cost"), 10),
    )


def _build_key_clauses(raw: Any) -> list[KeyClause]:
    if not isinstance(raw, list):
        return []
    clauses: list[KeyClause] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        section = item.get("section")
        section_str = (
            section.strip()
            if isinstance(section, str) and section.strip()
            else f"제{index}조"
        )
        clauses.append(
            KeyClause(id=index, section=section_str, content=content.strip())
        )
    return clauses


def _invoke_llm(text: str) -> str:
    """LLM 호출 단위 (테스트에서 monkeypatch)"""
    response = llm.invoke(
        [
            SystemMessage(content=_EXTRACTION_PROMPT),
            HumanMessage(content=text),
        ]
    )
    return getattr(response, "content", "") or ""


async def extract_property_and_clauses(
    full_text: str,
) -> tuple[PropertyInfo, list[KeyClause]]:
    """계약서 본문에서 PropertyInfo + KeyClause 목록을 추출한다

    실패하더라도 예외를 전파하지 않고 빈 결과를 돌려준다.
    PDF 분석 자체는 OCR 결과만으로 성공 응답하도록 부분 실패를 허용한다
    """
    if not full_text or not full_text.strip():
        return PropertyInfo(), []

    try:
        raw = await asyncio.to_thread(_invoke_llm, full_text)
    except Exception as exc:
        logger.warning("contract_extraction.llm_failed", error=str(exc))
        return PropertyInfo(), []

    cleaned = _strip_code_fence(raw)
    if not cleaned:
        return PropertyInfo(), []

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning(
            "contract_extraction.parse_failed",
            error=str(exc),
            head=cleaned[:200],
        )
        return PropertyInfo(), []

    if not isinstance(payload, dict):
        return PropertyInfo(), []

    return (
        _build_property_info(payload.get("property_info")),
        _build_key_clauses(payload.get("key_clauses")),
    )
