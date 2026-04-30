import secrets

from fastapi import Header, HTTPException, status

from app.settings import settings


async def verify_internal_api_key(
    x_internal_api_key: str | None = Header(
        default=None,
        alias="X-Internal-Api-Key",
    ),
) -> None:
    """X-Internal-Api-Key 헤더와 settings.INTERNAL_API_KEY를 비교

    Raises:
      HTTPException(401, INVALID_API_KEY):
        INTERNAL_API_KEY 미설정, 헤더 누락, 빈 값, 또는 불일치
    """
    expected = settings.INTERNAL_API_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_API_KEY",
                "message": "서버에 내부 API Key가 설정되지 않았습니다.",
            },
        )

    if not x_internal_api_key or not secrets.compare_digest(
        x_internal_api_key, expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_API_KEY",
                "message": "유효하지 않은 X-Internal-Api-Key입니다.",
            },
        )
