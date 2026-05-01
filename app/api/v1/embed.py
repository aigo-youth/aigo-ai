import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import EmbedRequest, EmbedResponse
from app.core.auth import verify_internal_api_key
from app.core.logging import get_logger
from app.settings import settings
from app.vectordb.embedder import Embedder, EmbedderProtocol

logger = get_logger(__name__)
router = APIRouter(prefix="/embed", tags=["embed"])


_MAX_TEXT_LENGTH = 2048
_embedder_singleton: EmbedderProtocol | None = None
_embedder_lock = asyncio.Lock()


async def get_embedder() -> EmbedderProtocol:
    """Embedder lazy singleton — 첫 호출 시 한 번만 모델 로드 후 재사용"""
    global _embedder_singleton
    if _embedder_singleton is not None:
        return _embedder_singleton
    async with _embedder_lock:
        if _embedder_singleton is None:
            _embedder_singleton = await asyncio.to_thread(
                Embedder, settings.EMBEDDING_MODEL
            )
    return _embedder_singleton


@router.post(
    "",
    response_model=EmbedResponse,
    dependencies=[Depends(verify_internal_api_key)],
    summary="텍스트 임베딩 (KURE-v1)",
)
async def embed_texts(payload: EmbedRequest) -> EmbedResponse:
    if any(len(t) > _MAX_TEXT_LENGTH for t in payload.texts):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": f"각 텍스트 길이는 {_MAX_TEXT_LENGTH}자 이하여야 합니다.",
            },
        )

    start = time.monotonic()

    try:
        embedder = await get_embedder()
        vectors = await asyncio.to_thread(embedder.embed, payload.texts)
    except Exception as exc:
        logger.error("embed.failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "MODEL_NOT_READY",
                "message": "임베딩 모델이 준비되지 않았습니다.",
            },
        ) from exc

    return EmbedResponse(
        model=payload.model,
        embeddings=vectors,
        latency_ms=int((time.monotonic() - start) * 1000),
    )
