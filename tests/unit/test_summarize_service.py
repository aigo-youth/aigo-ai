import asyncio
from types import SimpleNamespace

from app.services import summarize_service as svc


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _fake_response(text: str):
    return SimpleNamespace(content=text)


def test_returns_clean_title(monkeypatch):
    """LLM이 반환한 제목에서 불필요한 공백과 따옴표가 제거되는지 확인"""
    monkeypatch.setattr(
        svc, "_invoke_llm", lambda msgs: _fake_response("전세 계약 분쟁 상담")
    )
    title = _run(svc.summarize_for_title("집주인이 전세금을 돌려주지 않습니다."))
    assert title == "전세 계약 분쟁 상담"


def test_strips_surrounding_quotes(monkeypatch):
    """LLM이 반환한 제목에서 양쪽 따옴표가 제거되는지 확인"""
    monkeypatch.setattr(
        svc, "_invoke_llm", lambda msgs: _fake_response('"전세 계약 분쟁 상담"')
    )
    assert _run(svc.summarize_for_title("질문")) == "전세 계약 분쟁 상담"


def test_keeps_only_first_line(monkeypatch):
    """LLM이 여러 줄을 반환할 때, 첫 줄만 제목으로 사용하는지 확인"""
    monkeypatch.setattr(
        svc,
        "_invoke_llm",
        lambda msgs: _fake_response("전세 계약 상담\n부가 설명입니다."),
    )
    assert _run(svc.summarize_for_title("질문")) == "전세 계약 상담"


def test_truncates_to_max_chars(monkeypatch):
    """LLM이 반환한 제목이 최대 글자 수로 잘리는지 확인"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda msgs: _fake_response("가" * 50))
    title = _run(svc.summarize_for_title("질문", max_chars=10))
    assert title == "가" * 10


def test_fallback_when_llm_returns_empty(monkeypatch):
    """LLM이 빈 문자열을 반환할 때, 질문 앞부분이 제목으로 사용되는지 확인"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda msgs: _fake_response("   "))
    title = _run(svc.summarize_for_title("전세 계약 관련 문의 드립니다"))
    assert title.startswith("전세 계약 관련 문의")


def test_fallback_when_llm_raises(monkeypatch):
    """LLM 호출 중 예외가 발생할 때, 질문 앞부분이 제목으로 사용되는지 확인"""

    def boom(msgs):
        raise RuntimeError("network down")

    monkeypatch.setattr(svc, "_invoke_llm", boom)
    title = _run(svc.summarize_for_title("계약 갱신 절차 문의"))
    assert "계약 갱신" in title


def test_fallback_truncated_to_max_chars(monkeypatch):
    """LLM이 실패할 때, 질문 앞부분이 최대 글자 수로 잘리는지 확인"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda msgs: _fake_response(""))
    title = _run(svc.summarize_for_title("가" * 100, max_chars=15))
    assert len(title) <= 15
    assert title == "가" * 15


def test_fallback_empty_question_returns_default(monkeypatch):
    """질문이 빈 문자열일 때, fallback이 '새 대화'가 되는지 확인"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda msgs: _fake_response(""))
    title = _run(svc.summarize_for_title("   "))
    assert title == "새 대화"


def test_handles_response_without_content_attr(monkeypatch):
    """LLM 응답이 content 속성이 없는 경우에도 fallback"""
    monkeypatch.setattr(svc, "_invoke_llm", lambda msgs: SimpleNamespace())
    title = _run(svc.summarize_for_title("전세 보증금 반환 청구"))
    assert "전세 보증금 반환" in title
