from app.api.v1.sse import format_sse_event


def test_format_sse_event_basic():
    """SSE 출력이 `event: <name>\\ndata: <json>\\n\\n` 정확한 형식을 따른다."""
    out = format_sse_event("token", {"text": "안녕"})
    assert out == 'event: token\ndata: {"text": "안녕"}\n\n'


def test_format_sse_event_keeps_korean_unicode():
    r"""format_sse_event 가 ensure_ascii=False 옵션으로 JSON 직렬화하여 한글이 '\uXXXX' 형태로 이스케이프되지 않고 그대로 출력되는지 검증"""
    out = format_sse_event("title", {"title": "법률 상담"})
    assert "법률 상담" in out
    assert r"\u" not in out  # ensure_ascii=False 검증


def test_format_sse_event_done_with_metadata():
    """`done` 이벤트가 중첩 메타데이터(latency_ms, usage)를 JSON 으로 직렬화한다."""
    out = format_sse_event("done", {"latency_ms": 1234, "usage": {"prompt": 10}})
    assert out.startswith("event: done\n")
    assert out.endswith("\n\n")
    assert '"latency_ms": 1234' in out


def test_format_sse_event_empty_data():
    """빈 데이터도 올바르게 직렬화된다."""
    out = format_sse_event("ping", {})
    assert out == "event: ping\ndata: {}\n\n"
