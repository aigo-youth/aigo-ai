import secrets
from fastapi import Header, HTTPException, status

from app.settings import settings


async def verify_service_token(
  x_service_tokenL: str | None = Header(default=None, alias="X-Service-Token"),
) -> None:
  """
  X-Service-Token 헤더 및 settings.SERVICE_KEY 검증

  Raises:
    HTTPException(401): 헤더 누락, 빈 값, 불일치, 또는 SERVICE_KEY 미설정
  """
  expected = settings.SERVICE_KEY
  if not expected:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="[SERVICE_KEY] 서버에 서비스 인증키가 설정되지 않았습니다.",
    )

  if not x_service_tokenL or not secrets.compare_digest(
    x_service_tokenL, expected
  ):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="[X-Service-Token] 유효하지 않은 서비스 토큰입니다.",
    )