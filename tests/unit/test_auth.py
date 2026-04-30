import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import verify_service_token


@pytest.fixture
def protected_app():
    """인증이 필요한 테스트 FastAPI 앱 생성"""
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_service_token)])
    async def protected():
        return {"ok": True}

    return TestClient(app)


def test_missing_token_returns_401(protected_app):
    """토큰이 없는 경우 401 반환 테스트"""
    response = protected_app.get("/protected")
    assert response.status_code == 401


def test_invalid_token_returns_401(protected_app):
    """유효하지 않은 토큰인 경우 401 반환 테스트"""
    response = protected_app.get(
        "/protected",
        headers={"X-Service-Token": "wrong-token"},
    )
    assert response.status_code == 401


def test_valid_token_returns_200(protected_app):
    """유효한 토큰인 경우 200 반환 테스트"""
    response = protected_app.get(
        "/protected",
        headers={"X-Service-Token": "test-secret"},
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_empty_token_returns_401(protected_app):
    """빈 토큰인 경우 401 반환 테스트"""
    response = protected_app.get(
        "/protected",
        headers={"X-Service-Token": ""},
    )
    assert response.status_code == 401
