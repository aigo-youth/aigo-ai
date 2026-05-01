import asyncio
from uuid import uuid4

import pytest

from app.services import contract_index_service as svc


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class _FakeStore:
    """add_docs_with_ids 만 흉내내는 가짜 store."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def add_docs_with_ids(
        self,
        texts,
        metadatas=None,
        *,
        timeout=120,
        wait=False,
    ):
        self.calls.append(
            {
                "texts": list(texts),
                "metadatas": list(metadatas) if metadatas else None,
                "timeout": timeout,
                "wait": wait,
            }
        )
        return [f"pid-{i}" for i in range(len(texts))]


@pytest.fixture
def reset_singletons():
    svc._store_singleton = None
    yield
    svc._store_singleton = None


@pytest.fixture
def fake_store(monkeypatch, reset_singletons):
    store = _FakeStore()

    async def fake_get_store():
        return store

    monkeypatch.setattr(svc, "_get_store", fake_get_store)
    return store


def test_split_into_chunks_drops_short_paragraphs():
    """짧은 문단은 제거되는지 확인"""
    text = "짧음\n\n" + ("긴문단내용" * 5) + "\n\n" + "또짧"
    chunks = svc._split_into_chunks(text)
    assert len(chunks) == 1
    assert "긴문단내용" in chunks[0]


def test_split_into_chunks_handles_long_paragraph():
    """긴 문단이 여러 청크로 나뉘는지 확인"""
    long_text = "가" * (svc._MAX_CHUNK_CHARS * 2 + 50)
    chunks = svc._split_into_chunks(long_text)
    assert len(chunks) >= 2
    assert all(len(c) <= svc._MAX_CHUNK_CHARS for c in chunks)


def test_returns_empty_when_text_blank():
    """본문이 공백이면 store 호출 없이 빈 결과 반환"""
    ids, count = _run(
        svc.index_contract_text(
            full_text="",
            user_id="u",
            chatroom_id="c",
            contract_id=uuid4(),
        )
    )
    assert ids == []
    assert count == 0


def test_delegates_to_store_with_metadata(fake_store):
    """청크와 메타데이터가 store에 올바르게 전달되는지 확인"""
    contract_id = uuid4()
    text = (
        "보증금 관련 조항: " + "가" * 60 + "\n\n"
        "월세 관련 조항: " + "나" * 60 + "\n\n"
        "관리비 조항: " + "다" * 60
    )
    ids, count = _run(
        svc.index_contract_text(
            full_text=text,
            user_id="user-uuid",
            chatroom_id="chatroom-uuid",
            contract_id=contract_id,
        )
    )

    assert count == 3
    assert ids == ["pid-0", "pid-1", "pid-2"]

    # store.add_docs_with_ids 가 한 번 호출됨
    assert len(fake_store.calls) == 1
    call = fake_store.calls[0]
    assert len(call["texts"]) == 3
    assert call["wait"] is True

    # 각 청크에 chunk_index + 사용자/계약 메타데이터가 들어감
    for index, meta in enumerate(call["metadatas"]):
        assert meta["chunk_index"] == index
        assert meta["user_id"] == "user-uuid"
        assert meta["chatroom_id"] == "chatroom-uuid"
        assert meta["contract_id"] == str(contract_id)


def test_returns_empty_when_store_raises(monkeypatch, reset_singletons):
    """store 호출 중 예외 발생 시 빈 결과 반환"""

    class _BoomStore:
        def add_docs_with_ids(self, texts, metadatas=None, *, timeout=120, wait=False):
            raise RuntimeError("qdrant down")

    async def fake_get_store():
        return _BoomStore()

    monkeypatch.setattr(svc, "_get_store", fake_get_store)

    ids, count = _run(
        svc.index_contract_text(
            full_text="유효한 계약서 청크 본문 가나다라마바사아자차카타파하" * 3,
            user_id="u",
            chatroom_id="c",
            contract_id=uuid4(),
        )
    )
    assert ids == []
    assert count == 0
