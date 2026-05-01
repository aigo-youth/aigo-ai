import json

import pytest

_HEADERS = {
    "X-Internal-Api-Key": "test-secret",
    "X-User-Id": "user-uuid",
    "X-Chatroom-Id": "chatroom-uuid",
}


@pytest.fixture
def mock_stream_chat(monkeypatch):
    """실제 LLM 호출 없이 chat_service.stream_chat 만 monkeypatch"""

    async def fake_stream(
        query: str,
        history=None,
        contract_context=None,
    ):
        yield {"event": "rag_search_done", "data": {"hit_count": 3, "latency_ms": 42}}
        yield {"event": "token", "data": {"delta": "주택"}}
        yield {"event": "token", "data": {"delta": "임대차"}}
        yield {
            "event": "citation",
            "data": {"title": "주택임대차보호법 제6조", "url": "https://law.go.kr/..."},
        }
        yield {
            "event": "message_end",
            "data": {
                "total_tokens": 6,
                "fallback_triggered": False,
                "latency_ms": 1234,
            },
        }

    from app.services import chat_service

    monkeypatch.setattr(chat_service, "stream_chat", fake_stream)
    return fake_stream


def _parse_sse(text: str) -> list[dict]:
    """SSE 형식의 응답 텍스트를 이벤트 리스트로 파싱"""
    events = []
    for block in text.strip().split("\n\n"):
        if not block:
            continue
        name = ""
        data_str = ""
        for line in block.split("\n"):
            if line.startswith("event:"):
                name = line[len("event:") :].strip()
            elif line.startswith("data:"):
                data_str = line[len("data:") :].strip()
        if name:
            events.append({"event": name, "data": json.loads(data_str)})
    return events


def test_chat_stream_requires_api_key(client):
    """API 키 없으면 401"""
    resp = client.post(
        "/v1/chat/stream",
        json={"query": "안녕"},
        headers={"X-User-Id": "u", "X-Chatroom-Id": "c"},
    )
    assert resp.status_code == 401


def test_chat_stream_requires_user_id(client, mock_stream_chat):
    """사용자 ID 없으면 400"""
    resp = client.post(
        "/v1/chat/stream",
        json={"query": "안녕"},
        headers={"X-Internal-Api-Key": "test-secret"},
    )
    assert resp.status_code == 400


def test_chat_stream_validates_empty_query(client, mock_stream_chat):
    """빈 쿼리 문자열은 422"""
    resp = client.post(
        "/v1/chat/stream",
        json={"query": ""},
        headers=_HEADERS,
    )
    assert resp.status_code == 422


def test_chat_stream_emits_spec_events(client, mock_stream_chat):
    """
    rag_search_done 으로 시작 → token / citation 중간 이벤트 → message_end 로 종료
    message_end 페이로드는 fallback_triggered 를 포함해야함
    """
    resp = client.post(
        "/v1/chat/stream",
        json={"query": "묵시적 갱신이란?"},
        headers={**_HEADERS, "Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    names = [e["event"] for e in events]

    assert names[0] == "rag_search_done"
    assert names[-1] == "message_end"
    assert "token" in names
    assert "citation" in names

    first_token = next(e for e in events if e["event"] == "token")
    assert "delta" in first_token["data"]

    end = events[-1]
    assert end["data"]["fallback_triggered"] is False


def test_chat_stream_emits_keepalive_ping_when_idle(client, monkeypatch):
    """producer 가 이벤트를 늦게 내보내면 SSE 코멘트 ping(`: ping`) 이 흘러야 함"""
    import asyncio as _asyncio

    from app.api.v1 import chat as chat_module
    from app.services import chat_service

    async def slow_stream(query, history=None, contract_context=None):
        await _asyncio.sleep(0.15)
        yield {
            "event": "message_end",
            "data": {"total_tokens": 0, "fallback_triggered": False, "latency_ms": 0},
        }

    monkeypatch.setattr(chat_service, "stream_chat", slow_stream)
    monkeypatch.setattr(chat_module, "_KEEPALIVE_INTERVAL", 0.02)

    resp = client.post(
        "/v1/chat/stream",
        json={"query": "느린 응답"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200
    assert ": ping" in resp.text
    assert "event: message_end" in resp.text


def test_chat_stream_with_full_payload(client, mock_stream_chat):
    """history + contract_context 가 모두 채워진 요청을 수용"""
    resp = client.post(
        "/v1/chat/stream",
        json={
            "query": "더 자세히",
            "history": [
                {"role": "user", "content": "전세 계약 갱신 절차는?"},
                {"role": "assistant", "content": "..."},
            ],
            "contract_context": {
                "has_contract": True,
                "special_terms_summary": "...",
                "qdrant_chunk_filter": {"chatroom_id": "uuid"},
            },
        },
        headers=_HEADERS,
    )
    assert resp.status_code == 200
