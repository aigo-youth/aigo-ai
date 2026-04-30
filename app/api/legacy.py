from fastapi import APIRouter, HTTPException, status

from app.api.v1.schemas import LegacyChatRequest, LegacyChatResponse
from app.core.logging import get_logger
from app.services.chat_service import ChatServiceError, run_legacy_chat

logger = get_logger(__name__)
legacy_router = APIRouter(tags=["legacy"])


@legacy_router.post(
  "/chat",
  response_model=LegacyChatResponse,
  summary="레거시 챗봇 엔드포인트 (aigo-server 호환)",
)
async def legacy_chat(payload: LegacyChatRequest) -> LegacyChatResponse:
  logger.info("legacy_chat.received", question_len=len(payload.question))

  try:
    answer = await run_legacy_chat(payload.question)
  except ChatServiceError as exc:
    logger.error("legacy_chat.failed", error=str(exc))
    raise HTTPException(
      status_code=status.HTTP_502_BAD_GATEWAY,
      detail="AI 처리 중 오류가 발생했습니다.",
    ) from exc

  return LegacyChatResponse(answer=answer)
