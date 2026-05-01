import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.main import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


@pytest.fixture
def isolated_client():
    """전역 app을 오염시키지 않도록 별도 FastAPI 인스턴스에 핸들러 등록"""
    from fastapi.exceptions import RequestValidationError

    isolated_app = FastAPI()
    isolated_app.add_exception_handler(HTTPException, http_exception_handler)
    isolated_app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
    isolated_app.add_exception_handler(Exception, unhandled_exception_handler)

    @isolated_app.get("/raise-dict")
    async def raise_dict():
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "필수 필드 누락"},
        )

    @isolated_app.get("/raise-string")
    async def raise_string():
        raise HTTPException(status_code=400, detail="plain string detail")

    @isolated_app.get("/raise-unhandled")
    async def raise_unhandled():
        raise RuntimeError("boom")

    return TestClient(isolated_app, raise_server_exceptions=False)


def test_http_exception_with_dict_detail_passthrough(isolated_client):
    """HTTPException(detail=dict) → detail 그대로 응답 확인 (핸들러에서 변형하지 않음)"""
    response = isolated_client.get("/raise-dict")
    assert response.status_code == 400
    body = response.json()
    assert body == {"detail": {"code": "INVALID_REQUEST", "message": "필수 필드 누락"}}


def test_http_exception_with_string_detail_wrapped(isolated_client):
    """HTTPException(detail=str) → detail dict로 래핑 확인"""
    response = isolated_client.get("/raise-string")
    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "HTTP_ERROR"
    assert body["detail"]["message"] == "plain string detail"


def test_unhandled_exception_returns_500_internal_error(isolated_client):
    """Unhandled Exception → 500 INTERNAL_ERROR 응답 확인"""
    response = isolated_client.get("/raise-unhandled")
    assert response.status_code == 500
    body = response.json()
    assert body["detail"]["code"] == "INTERNAL_ERROR"
    assert "서버 내부 오류" in body["detail"]["message"]


def test_validation_error_returns_invalid_request(client):
    """RequestValidationError → 422 INVALID_REQUEST 응답 확인"""
    response = client.post(
        "/v1/chat/stream",
        headers={
            "X-Internal-Api-Key": "test-secret",
            "X-User-Id": "user-uuid",
            "Content-Type": "application/json",
        },
        json={"history": []},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "INVALID_REQUEST"
    assert "errors" in body["detail"]
