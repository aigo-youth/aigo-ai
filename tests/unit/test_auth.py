"""verify_internal_api_key 의존성 테스트 (API 명세 0.1 / 6.x)."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import verify_internal_api_key


@pytest.fixture
def protected_app():
    """X-Internal-Api-Key 검증이 필요한 테스트용 FastAPI 앱."""
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_internal_api_key)])
    async def protected():
        return {"ok": True}

    return TestClient(app)


def test_missing_header_returns_401(protected_app):
    resp = protected_app.get("/protected")
    assert resp.status_code == 401


def test_invalid_key_returns_401(protected_app):
    resp = protected_app.get(
        "/protected",
        headers={"X-Internal-Api-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_valid_key_returns_200(protected_app):
    resp = protected_app.get(
        "/protected",
        headers={"X-Internal-Api-Key": "test-secret"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_empty_key_returns_401(protected_app):
    resp = protected_app.get(
        "/protected",
        headers={"X-Internal-Api-Key": ""},
    )
    assert resp.status_code == 401
