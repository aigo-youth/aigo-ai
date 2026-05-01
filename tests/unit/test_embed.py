import pytest

from app.api.v1 import embed as embed_module

_HEADERS = {"X-Internal-Api-Key": "test-secret"}


class _FakeEmbedder:
    vector_size = 4

    def embed(self, texts):
        return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

    def embed_question(self, text):
        return [0.1, 0.2, 0.3, 0.4]


@pytest.fixture
def reset_embedder_singleton():
    """모듈 글로벌 캐시를 테스트마다 초기화"""
    embed_module._embedder_singleton = None
    yield
    embed_module._embedder_singleton = None


@pytest.fixture
def fake_embedder_factory(monkeypatch, reset_embedder_singleton):
    """Embedder 팩토리를 카운트하는 가짜로 교체"""
    call_count = {"n": 0}

    def fake_embedder(model_name=None):
        call_count["n"] += 1
        return _FakeEmbedder()

    monkeypatch.setattr(embed_module, "Embedder", fake_embedder)
    return call_count


def test_embed_requires_api_key(client):
    """API 키 없으면 401 Unauthorized"""
    resp = client.post("/v1/embed", json={"texts": ["hi"]})
    assert resp.status_code == 401


def test_embed_rejects_text_over_max_length(client, fake_embedder_factory):
    """본문이 최대 길이보다 길면 400 Bad Request"""
    long = "x" * (embed_module._MAX_TEXT_LENGTH + 1)
    resp = client.post(
        "/v1/embed",
        headers=_HEADERS,
        json={"texts": [long]},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_REQUEST"


def test_embed_returns_vectors(client, fake_embedder_factory):
    """임베딩 벡터가 사양에 맞게 반환되는지 확인"""
    resp = client.post(
        "/v1/embed",
        headers=_HEADERS,
        json={"texts": ["보증금", "월세"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["model"] == "kure-v1"
    assert len(body["embeddings"]) == 2
    assert body["embeddings"][0] == [0.1, 0.2, 0.3, 0.4]
    assert body["latency_ms"] >= 0


def test_embedder_loaded_only_once_across_requests(client, fake_embedder_factory):
    """싱글톤 — 여러 요청에 걸쳐 Embedder 팩토리는 한 번만 호출되어야 함"""
    for _ in range(3):
        resp = client.post(
            "/v1/embed",
            headers=_HEADERS,
            json={"texts": ["hi"]},
        )
        assert resp.status_code == 200
    assert fake_embedder_factory["n"] == 1


def test_embed_returns_503_when_embedder_fails(
    client, monkeypatch, reset_embedder_singleton
):
    """Embedder 가 예외를 던지면 MODEL_NOT_READY 503"""

    def broken_embedder(model_name=None):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(embed_module, "Embedder", broken_embedder)

    resp = client.post(
        "/v1/embed",
        headers=_HEADERS,
        json={"texts": ["hi"]},
    )
    assert resp.status_code == 503
    assert resp.json()["detail"]["code"] == "MODEL_NOT_READY"
