def _patch_qdrant(monkeypatch, ok: bool) -> None:
    from app.api import health as health_mod

    monkeypatch.setattr(health_mod, "_qdrant_connected", lambda: ok)
    monkeypatch.setattr(health_mod, "_qdrant_probe_cache", (0.0, ok))


def test_healthz_returns_ready_when_qdrant_up(client, monkeypatch):
    _patch_qdrant(monkeypatch, True)

    resp = client.get("/healthz")
    assert resp.status_code == 200

    body = resp.json()
    assert body["status"] == "ready"
    assert "model" in body
    assert "embedding_model" in body
    assert body["qdrant_connected"] is True


def test_healthz_returns_loading_when_qdrant_down(client, monkeypatch):
    _patch_qdrant(monkeypatch, False)

    resp = client.get("/healthz")
    assert resp.status_code == 503

    body = resp.json()
    assert body["status"] == "loading"
    assert body["ready_in_seconds"] >= 0
