import pytest

from app.api.v1.schemas import KeyClause, PropertyInfo, SpecialTerm

_HEADERS = {
    "X-Internal-Api-Key": "test-secret",
    "X-User-Id": "user-uuid",
    "X-Chatroom-Id": "chatroom-uuid",
    "X-Idempotency-Key": "idem-uuid",
}


@pytest.fixture
def mock_run_pdf_ocr(monkeypatch):
    async def fake(file_bytes: bytes):
        return {
            "page_count": 2,
            "full_text": "추출된 마스킹 텍스트입니다",
            "file_type": "Digital",
            "ocr_accuracy_score": 0.92,
            "processing_ms": 42,
        }

    from app.services import ocr_service

    monkeypatch.setattr(ocr_service, "run_pdf_ocr", fake)
    return fake


@pytest.fixture
def mock_pdf_pipeline(monkeypatch, mock_run_pdf_ocr):
    """OCR 외 추출/인덱싱 서비스도 모두 가짜로 교체"""

    async def fake_extract(full_text: str):
        return (
            PropertyInfo(
                location="서울시 종로구 가상로 1",
                month_rent=700_000,
                deposit=10_000_000,
            ),
            [KeyClause(id=1, section="제1조 (보증금)", content="보증금은 ...")],
        )

    async def fake_special_terms(full_text: str):
        return [SpecialTerm(id=1, content="원상복구 시 ...")]

    async def fake_index(*, full_text, user_id, chatroom_id, contract_id):
        return ["pid-1", "pid-2", "pid-3"], 3

    from app.services import (
        contract_extraction_service,
        contract_index_service,
        special_terms_service,
    )

    monkeypatch.setattr(
        contract_extraction_service,
        "extract_property_and_clauses",
        fake_extract,
    )
    monkeypatch.setattr(
        special_terms_service, "extract_special_terms", fake_special_terms
    )
    monkeypatch.setattr(contract_index_service, "index_contract_text", fake_index)
    return {
        "extract": fake_extract,
        "special_terms": fake_special_terms,
        "index": fake_index,
    }


def _make_pdf_bytes(size: int) -> bytes:
    """PDF 파일처럼 보이는 바이트 시퀀스 생성 (실제 PDF 구조는 아님)"""
    header = b"%PDF-1.4\n"
    return header + b"x" * (size - len(header))


def test_pdf_requires_api_key(client):
    """API 키 없으면 401 Unauthorized"""
    pdf = _make_pdf_bytes(1024)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        headers={"X-User-Id": "u", "X-Chatroom-Id": "c"},
    )
    assert resp.status_code == 401


def test_pdf_requires_context_headers(client, mock_run_pdf_ocr):
    """API 키만 있고 X-User-Id / X-Chatroom-Id 가 없으면 400"""
    pdf = _make_pdf_bytes(1024)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        headers={"X-Internal-Api-Key": "test-secret"},
    )
    assert resp.status_code == 400


def test_pdf_rejects_non_pdf_content_type(client, mock_run_pdf_ocr):
    """PDF가 아닌 파일 업로드 시 415 Unsupported Media Type"""
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers=_HEADERS,
    )
    assert resp.status_code == 415


def test_pdf_rejects_oversized_file(client, mock_run_pdf_ocr):
    """5MB 초과 PDF 업로드 시 413 Payload Too Large"""
    big = _make_pdf_bytes(6 * 1024 * 1024)  # 6MB > 5MB limit (REQ-CHAT-006)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("big.pdf", big, "application/pdf")},
        headers=_HEADERS,
    )
    assert resp.status_code == 413


def test_pdf_returns_spec_response(client, mock_run_pdf_ocr):
    """pii_masked_text,
    property_info, special_terms[], key_clauses[], qdrant.collection, latency_ms 포함."""
    pdf = _make_pdf_bytes(2048)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        headers=_HEADERS,
    )
    assert resp.status_code == 200

    body = resp.json()
    assert 0.0 <= body["ocr_confidence"] <= 1.0
    assert body["pii_masked_text"] == "추출된 마스킹 텍스트입니다"
    assert "property_info" in body
    assert isinstance(body["special_terms"], list)
    assert isinstance(body["key_clauses"], list)
    assert "qdrant" in body
    assert body["qdrant"]["collection"]
    assert body["latency_ms"] >= 0


def test_pdf_returns_filled_response_when_pipeline_succeeds(client, mock_pdf_pipeline):
    """추출/인덱싱 서비스가 모두 성공한 경우, placeholder 가 아닌 실제 결과가 채워짐"""
    pdf = _make_pdf_bytes(2048)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        headers=_HEADERS,
    )
    assert resp.status_code == 200

    body = resp.json()

    # property_info 채워짐 + contract_id 발급
    assert body["property_info"]["location"] == "서울시 종로구 가상로 1"
    assert body["property_info"]["deposit"] == 10_000_000
    assert body["property_info"]["month_rent"] == 700_000
    assert body["property_info"]["contract_id"]  # uuid 자동 발급

    # special_terms / key_clauses 채워짐
    assert len(body["special_terms"]) == 1
    assert body["special_terms"][0]["content"].startswith("원상복구")
    assert len(body["key_clauses"]) == 1
    assert body["key_clauses"][0]["section"] == "제1조 (보증금)"

    # Qdrant chunk_count + ids 채워짐
    assert body["qdrant"]["chunk_count"] == 3
    assert body["qdrant"]["ids"] == ["pid-1", "pid-2", "pid-3"]


def test_pdf_returns_empty_results_when_pipeline_fails(
    client, mock_run_pdf_ocr, monkeypatch
):
    """추출/인덱싱 서비스가 빈 결과를 돌려줘도 200 + 비어있는 placeholder 응답"""

    async def empty_extract(full_text):
        return PropertyInfo(), []

    async def empty_special(full_text):
        return []

    async def empty_index(*, full_text, user_id, chatroom_id, contract_id):
        return [], 0

    from app.services import (
        contract_extraction_service,
        contract_index_service,
        special_terms_service,
    )

    monkeypatch.setattr(
        contract_extraction_service,
        "extract_property_and_clauses",
        empty_extract,
    )
    monkeypatch.setattr(special_terms_service, "extract_special_terms", empty_special)
    monkeypatch.setattr(contract_index_service, "index_contract_text", empty_index)

    pdf = _make_pdf_bytes(2048)
    resp = client.post(
        "/v1/pdf/analyze",
        files={"file": ("a.pdf", pdf, "application/pdf")},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["property_info"]["location"] is None
    assert body["special_terms"] == []
    assert body["key_clauses"] == []
    assert body["qdrant"]["chunk_count"] == 0
    assert body["qdrant"]["ids"] == []
