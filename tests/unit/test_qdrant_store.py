import uuid

import pytest


class _FakeEmbedder:
    vector_size = 4

    def embed(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def embed_question(self, text):
        return [0.1, 0.2, 0.3, 0.4]


class _FakeQdrantClient:
    def __init__(self, *args, **kwargs) -> None:
        self.upsert_calls: list[dict] = []
        self._collections: list = []

    def get_collections(self):
        return type("R", (), {"collections": list(self._collections)})()

    def create_collection(self, **kwargs):
        self._collections.append(type("C", (), {"name": kwargs["collection_name"]})())

    def upsert(self, **kwargs):
        self.upsert_calls.append(kwargs)


@pytest.fixture
def fake_store(monkeypatch):
    from app.vectordb import store as store_module

    fake_client = _FakeQdrantClient()

    def fake_qdrant_factory(*args, **kwargs):
        return fake_client

    monkeypatch.setattr(store_module, "QdrantClient", fake_qdrant_factory)

    store = store_module.QdrantStore(
        collection_name="test_collection",
        embedder=_FakeEmbedder(),
    )
    return store, fake_client


def test_returns_empty_list_when_texts_empty(fake_store):
    """texts 가 빈 리스트일 때, upsert 호출 없이 빈 리스트 반환"""
    store, _client = fake_store
    result = store.add_docs_with_ids([])
    assert result == []


def test_generates_uuid_string_ids_in_input_order(fake_store):
    """생성된 포인트 ID가 UUID 문자열 형식인지, 입력 텍스트 순서대로 반환되는지 확인"""
    store, client = fake_store
    texts = ["청크 A", "청크 B", "청크 C"]
    ids = store.add_docs_with_ids(texts)

    assert len(ids) == 3
    assert all(isinstance(pid, str) for pid in ids)
    for pid in ids:
        uuid.UUID(pid)  # raises ValueError 면 테스트 실패

    call = client.upsert_calls[0]
    points = call["points"]
    assert [p.id for p in points] == ids
    assert [p.payload["text"] for p in points] == texts


def test_passes_metadata_into_payload(fake_store):
    """메타데이터가 올바르게 payload에 포함되는지 확인"""
    store, client = fake_store
    texts = ["A", "B"]
    metadatas = [
        {"chatroom_id": "room1", "chunk_index": 0},
        {"chatroom_id": "room1", "chunk_index": 1},
    ]
    store.add_docs_with_ids(texts, metadatas)

    points = client.upsert_calls[0]["points"]
    assert points[0].payload == {"text": "A", "chatroom_id": "room1", "chunk_index": 0}
    assert points[1].payload == {"text": "B", "chatroom_id": "room1", "chunk_index": 1}


def test_default_metadata_when_omitted(fake_store):
    """메타데이터가 생략될 경우 기본값이 올바르게 설정되는지 확인"""
    store, client = fake_store
    store.add_docs_with_ids(["x", "y"])
    points = client.upsert_calls[0]["points"]
    for point in points:
        assert set(point.payload.keys()) == {"text"}


def test_wait_flag_passed_through(fake_store):
    """wait=True 옵션이 QdrantClient.upsert 호출에 제대로 전달되는지 확인"""
    store, client = fake_store
    store.add_docs_with_ids(["x"], wait=True, timeout=30)
    call = client.upsert_calls[0]
    assert call["wait"] is True
    assert call["timeout"] == 30
    assert call["collection_name"] == "test_collection"


def test_legacy_add_docs_returns_none_but_still_upserts(fake_store):
    """기존 add_docs 시그니처 호환성 — 반환값 None, upsert 는 발생."""
    store, client = fake_store
    result = store.add_docs(["legacy text"], [{"src": "legal"}])
    assert result is None
    assert len(client.upsert_calls) == 1
    assert client.upsert_calls[0]["points"][0].payload["src"] == "legal"
