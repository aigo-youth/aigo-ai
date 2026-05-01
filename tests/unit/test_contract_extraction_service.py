import asyncio
from datetime import date

from app.services import contract_extraction_service as svc


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_returns_empty_when_text_blank():
    """입력 본문이 빈 문자열일 때, extractor 호출 없이 빈 결과 반환"""
    prop, clauses = _run(svc.extract_property_and_clauses("   "))
    assert prop.location is None
    assert clauses == []


def test_parses_clean_json_response(monkeypatch):
    """LLM이 반환한 깔끔한 JSON을 올바르게 파싱하는지 확인"""
    payload = (
        '{"property_info": {"location": "서울시 가상로 1",'
        ' "start_date": "2024-03-01", "end_date": "2026-02-28",'
        ' "month_rent": 700000, "deposit": "10,000,000원",'
        ' "house_cost": "5만원"}, "key_clauses": ['
        '{"section": "제1조", "content": "보증금은 ..."},'
        '{"section": "제2조 (월세)", "content": "월세는 ..."}]}'
    )
    monkeypatch.setattr(svc, "_invoke_llm", lambda text: payload)

    prop, clauses = _run(svc.extract_property_and_clauses("계약서 본문"))

    assert prop.location == "서울시 가상로 1"
    assert prop.start_date == date(2024, 3, 1)
    assert prop.end_date == date(2026, 2, 28)
    assert prop.month_rent == 700000
    assert prop.deposit == 10_000_000  # "10,000,000원" → digits-only
    assert prop.house_cost == "5만원"

    assert len(clauses) == 2
    assert clauses[0].id == 1 and clauses[0].section == "제1조"
    assert clauses[1].section == "제2조 (월세)"


def test_strips_code_fence(monkeypatch):
    """LLM이 JSON을 ```json ... ``` 으로 감싸서 반환할 때 본문만 추출하는지 확인"""
    payload = '```json\n{"property_info": {"location": "강남"}, "key_clauses": []}\n```'
    monkeypatch.setattr(svc, "_invoke_llm", lambda text: payload)

    prop, clauses = _run(svc.extract_property_and_clauses("계약서"))
    assert prop.location == "강남"
    assert clauses == []


def test_returns_empty_on_invalid_json(monkeypatch):
    """LLM이 JSON이 아닌 문자열을 반환할 때 빈 결과 반환"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda text: "not a json")
    prop, clauses = _run(svc.extract_property_and_clauses("계약서"))
    assert prop.location is None
    assert clauses == []


def test_returns_empty_when_llm_raises(monkeypatch):
    """LLM 호출 중 예외 발생 시 빈 결과 반환"""

    def boom(text):
        raise RuntimeError("network")

    monkeypatch.setattr(svc, "_invoke_llm", boom)
    prop, clauses = _run(svc.extract_property_and_clauses("계약서"))
    assert prop.location is None
    assert clauses == []


def test_skips_invalid_clause_entries(monkeypatch):
    """LLM이 반환한 JSON에서 유효하지 않은 조항 항목을 건너뛰는지 확인"""
    payload = (
        '{"property_info": {}, "key_clauses": ['
        '{"section": "유효", "content": "내용 있음"},'
        '"문자열 항목",'
        '{"section": "빈 콘텐츠", "content": ""}]}'
    )
    monkeypatch.setattr(svc, "_invoke_llm", lambda text: payload)
    _, clauses = _run(svc.extract_property_and_clauses("계약서"))
    assert len(clauses) == 1
    assert clauses[0].section == "유효"


def test_truncates_overlong_strings(monkeypatch):
    """LLM이 반환한 JSON에서 과도하게 긴 문자열이 최대 길이로 잘리는지 확인"""
    long_location = "강남구 " * 20  # > 40 chars
    payload = (
        '{"property_info": {"location": "' + long_location + '",'
        ' "house_cost": "관리비매우매우매우매우긴문자열"},'
        ' "key_clauses": []}'
    )
    monkeypatch.setattr(svc, "_invoke_llm", lambda text: payload)
    prop, _ = _run(svc.extract_property_and_clauses("계약서"))
    assert prop.location is not None and len(prop.location) <= 40
    assert prop.house_cost is not None and len(prop.house_cost) <= 10
