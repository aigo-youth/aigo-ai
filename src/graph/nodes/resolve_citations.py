"""검색 문서의 출처 URL을 결정론적으로 구성하는 노드.

raw 데이터의 URL 패턴을 그대로 활용한다:
- 판례: /DRF/lawService.do?OC=skn24&target=prec&ID={판례일련번호}&type=HTML
- 법령해석례: /DRF/lawService.do?OC=skn24&target=expc&ID={법령해석례일련번호}&type=HTML
- 법령: /법령/{법령명} (국가법령정보센터 검색)
"""

from __future__ import annotations

from typing import Any

from src.graph.state import Citation, State

_BASE_URL = "https://www.law.go.kr"


def _build_url(doc: dict[str, Any]) -> str:
    """doc_type과 source_id로 법령정보센터 상세 페이지 URL을 구성한다."""
    doc_type = doc.get("doc_type", "")
    source_id = str(doc.get("source_id", ""))

    if doc_type == "판례" and source_id:
        return f"{_BASE_URL}/precInfoP.do?precSeq={source_id}"

    if doc_type == "법령해석례" and source_id:
        return f"{_BASE_URL}/expcInfoP.do?expcSeq={source_id}"

    if doc_type == "법령" and source_id:
        return f"{_BASE_URL}/lsInfoP.do?lsiSeq={source_id}"

    return _BASE_URL


def _extract_detail(doc: dict[str, Any]) -> str:
    """doc_type별 부가 정보 문자열을 생성한다."""
    doc_type = doc.get("doc_type", "")

    if doc_type == "법령":
        parts = [doc.get("조문번호", ""), doc.get("조문제목", "")]
        return " ".join(p for p in parts if p)

    if doc_type == "판례":
        return doc.get("사건번호", "")

    if doc_type == "법령해석례":
        return doc.get("chunk_id", "")  # 안건번호

    return ""


def _deduplicate(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """source_id 기준으로 중복을 제거한다."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for doc in docs:
        sid = str(doc.get("source_id", ""))
        if sid and sid in seen:
            continue
        seen.add(sid)
        unique.append(doc)
    return unique


def resolve_citations(state: State) -> dict:
    """retrieved_docs에서 출처를 추출하고 URL을 확보한다."""
    retrieved_docs = state.get("retrieved_docs", [])
    if not retrieved_docs:
        return {"citations": []}

    unique_docs = _deduplicate(retrieved_docs)

    citations: list[Citation] = []
    for doc in unique_docs:
        citations.append(
            Citation(
                doc_type=doc.get("doc_type", ""),
                title=doc.get("title", ""),
                source_id=str(doc.get("source_id", "")),
                detail=_extract_detail(doc),
                url=_build_url(doc),
            )
        )

    return {"citations": citations}
