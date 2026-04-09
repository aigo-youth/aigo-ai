"""
노트북에서 추출한 청킹 로직.

raw API 데이터 → (text, metadata) 청크로 변환.
- prec: 판례 본문 → RecursiveCharacterTextSplitter(500, 50)
- expc: 질의요지 + 이유 결합 (분할 없음)
"""

import re
from datetime import date
from typing import Any, Iterator

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .loaders import LoadedChunk


# ── 공통 유틸 ─────────────────────────────────────────

def _clean_text(text: str) -> str:
    """HTML 태그 제거 및 공백 정리."""
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _date_type(raw_date: str) -> str:
    """'YYYY.MM.DD' → 'YYYY-MM-DD' ISO 형식 변환."""
    try:
        y, m, d = raw_date.split(".")
        return date(int(y), int(m), int(d)).isoformat()
    except (ValueError, AttributeError):
        return raw_date


# ── prec (판례) ────────────────────────────────────────

_prec_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)


def _clean_prec(text: str) -> str:
    """판례내용에서 【이유】 이후만 추출 후 정리."""
    if not text:
        return ""
    match = re.search(r"【이\s*유】", text)
    if match:
        text = text[match.end():]
    return _clean_text(text)


def chunk_prec(raw_record: dict[str, Any]) -> Iterator[LoadedChunk]:
    """raw API 판례 1건 → 여러 청크로 분할."""
    prec_body = raw_record.get("본문", {})
    if isinstance(prec_body, dict):
        prec_body = prec_body.get("PrecService", prec_body)
    else:
        return

    # 메타데이터
    meta_base = {
        "doc_type": "판례",
        "title": raw_record.get("사건명", ""),
        "source_id": str(raw_record.get("판례일련번호", "")),
        "사건번호": raw_record.get("사건번호", ""),
        "사건종류명": raw_record.get("사건종류명", ""),
        "법원명": raw_record.get("법원명", ""),
        "선고일자": _date_type(raw_record.get("선고일자", "")),
        "판결유형": raw_record.get("판결유형", ""),
    }

    # 본문 텍스트 조합
    content_parts = {
        "판결요지": _clean_text(prec_body.get("판결요지", "")),
        "판례내용": _clean_prec(prec_body.get("판례내용", "")),
    }
    embed_text = "\n\n".join(
        f"{k}: {v}" for k, v in content_parts.items() if v
    )

    if not embed_text:
        return

    # RecursiveCharacterTextSplitter로 분할
    chunks = _prec_splitter.split_text(embed_text)
    for i, chunk_text in enumerate(chunks):
        yield chunk_text, {**meta_base, "chunk_id": i}


# ── expc (법령해석례) ──────────────────────────────────

def chunk_expc(raw_record: dict[str, Any]) -> Iterator[LoadedChunk]:
    """raw API 법령해석례 1건 → 1청크 (분할 불필요)."""
    body = raw_record.get("본문", {})
    if isinstance(body, dict):
        body = body.get("ExpcService", body)
    else:
        return

    질의요지 = _clean_text(body.get("질의요지", ""))
    이유 = _clean_text(body.get("이유", ""))

    page_content = ""
    if 질의요지:
        page_content += f"질의요지: {질의요지}"
    if 이유:
        page_content += f"\n이유: {이유}"

    page_content = page_content.strip()
    if not page_content:
        return

    meta = {
        "doc_type": "법령해석례",
        "chunk_id": raw_record.get("안건번호", ""),
        "title": raw_record.get("안건명", ""),
        "source_id": str(raw_record.get("법령해석례일련번호", "")),
        "회신일자": raw_record.get("회신일자", ""),
    }

    yield page_content, meta
