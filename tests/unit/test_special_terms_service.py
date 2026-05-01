import asyncio

from app.services import special_terms_service as svc


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_returns_empty_when_input_blank():
    """입력 본문이 빈 문자열일 때, extractor 호출 없이 빈 리스트 반환"""
    assert _run(svc.extract_special_terms("")) == []


def test_returns_empty_when_extractor_signals_no_terms(monkeypatch):
    """extractor가 특약 없음 신호를 보낼 때 빈 리스트 반환"""
    monkeypatch.setattr(
        svc,
        "_invoke_extractor",
        lambda text: "특약 내용을 확인할 수 없습니다. 직접 입력해주세요.",
    )
    assert _run(svc.extract_special_terms("계약서")) == []


def test_parses_numbered_list(monkeypatch):
    """LLM이 만든 번호 매겨진 리스트를 올바르게 파싱하는지 확인"""
    monkeypatch.setattr(
        svc,
        "_invoke_extractor",
        lambda text: (
            "1. 첫 조항 내용입니다.\n2. 둘째 조항 내용입니다.\n3. 셋째 조항 내용입니다."
        ),
    )
    terms = _run(svc.extract_special_terms("계약서"))
    assert [t.id for t in terms] == [1, 2, 3]
    assert terms[0].content == "첫 조항 내용입니다."
    assert terms[2].content == "셋째 조항 내용입니다."
    assert all(t.editable for t in terms)


def test_merges_continuation_lines(monkeypatch):
    """번호 매겨진 조항이 여러 줄로 나뉘어 있을 때, 하나의 조항으로 합쳐지는지 확인"""
    monkeypatch.setattr(
        svc,
        "_invoke_extractor",
        lambda text: "1. 첫 조항\n   여러 줄로 이어짐.\n2. 둘째 조항.",
    )
    terms = _run(svc.extract_special_terms("계약서"))
    assert len(terms) == 2
    assert "이어짐" in terms[0].content


def test_returns_empty_when_extractor_raises(monkeypatch):
    """extractor 호출 중 예외 발생 시 빈 리스트 반환"""

    def boom(text):
        raise RuntimeError("LLM down")

    monkeypatch.setattr(svc, "_invoke_extractor", boom)
    assert _run(svc.extract_special_terms("계약서")) == []
