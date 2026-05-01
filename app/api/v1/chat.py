import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.v1.schemas import ChatStreamRequest
from app.api.v1.sse import format_sse_event
from app.core.auth import verify_internal_api_key
from app.core.logging import get_logger
from app.services import chat_service

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}

# 클라이언트(프록시) 연결 유지를 위한 heartbeat 주기
# — 코멘트 라인은 SSE 파서가 무시
_KEEPALIVE_INTERVAL = 30.0
_PING_FRAME = ": ping\n\n"


@router.post(
    "/stream",
    dependencies=[Depends(verify_internal_api_key)],
    summary="채팅 RAG SSE 스트리밍 (Django → FastAPI 내부 호출)",
)
async def chat_stream(
    request: Request,
    payload: ChatStreamRequest,
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_chatroom_id: str | None = Header(default=None, alias="X-Chatroom-Id"),
) -> StreamingResponse:
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": "X-User-Id 헤더가 필요합니다.",
            },
        )

    logger.info(
        "chat_stream.received",
        user_id=x_user_id,
        chatroom_id=x_chatroom_id,
        query_len=len(payload.query),
        history_len=len(payload.history),
        has_contract=bool(
            payload.contract_context and payload.contract_context.has_contract
        ),
    )

    history = [m.model_dump() for m in payload.history]
    contract_context = (
        payload.contract_context.model_dump() if payload.contract_context else None
    )

    async def _producer(queue: asyncio.Queue) -> None:
        try:
            async for ev in chat_service.stream_chat(
                query=payload.query,
                history=history,
                contract_context=contract_context,
            ):
                await queue.put(("event", ev))
            await queue.put(("done", None))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("chat_stream.failed", error=str(exc))
            await queue.put(("error", None))

    async def event_stream():
        queue: asyncio.Queue = asyncio.Queue()
        producer_task = asyncio.create_task(_producer(queue))
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("chat_stream.client_disconnected", user_id=x_user_id)
                    break
                try:
                    kind, ev = await asyncio.wait_for(
                        queue.get(), timeout=_KEEPALIVE_INTERVAL
                    )
                except asyncio.TimeoutError:
                    yield _PING_FRAME
                    continue

                if kind == "event":
                    yield format_sse_event(ev["event"], ev["data"])
                elif kind == "done":
                    break
                elif kind == "error":
                    yield format_sse_event(
                        "error",
                        {
                            "code": "INTERNAL_ERROR",
                            "message": "응답 생성 중 오류가 발생했습니다.",
                        },
                    )
                    break
        finally:
            if not producer_task.done():
                producer_task.cancel()
                try:
                    await producer_task
                except asyncio.CancelledError:
                    pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
