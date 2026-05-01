import asyncio
from uuid import UUID

from app.core.logging import get_logger
from app.settings import settings
from app.vectordb import Embedder, QdrantStore

logger = get_logger(__name__)


_MAX_CHUNK_CHARS = 800
_MIN_CHUNK_CHARS = 20
_MAX_CHUNKS = 64

_store_singleton: QdrantStore | None = None
_init_lock = asyncio.Lock()


def _split_into_chunks(text: str) -> list[str]:
    """본문을 문단 단위로 나누되 너무 긴 문단은 추가로 잘라낸다"""
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        if len(para) <= _MAX_CHUNK_CHARS:
            chunks.append(para)
            continue
        for start in range(0, len(para), _MAX_CHUNK_CHARS):
            piece = para[start : start + _MAX_CHUNK_CHARS].strip()
            if piece:
                chunks.append(piece)

    trimmed = [c for c in chunks if len(c) >= _MIN_CHUNK_CHARS]
    return trimmed[:_MAX_CHUNKS]


async def _get_store() -> QdrantStore:
    """QdrantStore 싱글톤 — 첫 호출 시 한 번만 로드 (Embedder 포함)"""
    global _store_singleton
    if _store_singleton is not None:
        return _store_singleton

    async with _init_lock:
        if _store_singleton is None:
            embedder = await asyncio.to_thread(Embedder, settings.EMBEDDING_MODEL)
            _store_singleton = await asyncio.to_thread(
                QdrantStore,
                settings.COLLECTION_CONTRACTS,
                embedder,
            )
    return _store_singleton


async def index_contract_text(
    *,
    full_text: str,
    user_id: str,
    chatroom_id: str,
    contract_id: UUID,
) -> tuple[list[str], int]:
    """마스킹된 계약서 본문을 청킹·임베딩·upsert

    Returns:
      (point_ids, chunk_count). 청킹 결과가 비거나 인덱싱이 실패하면 ([], 0)
    """
    chunks = _split_into_chunks(full_text)
    if not chunks:
        return [], 0

    metadatas = [
        {
            "user_id": user_id,
            "chatroom_id": chatroom_id,
            "contract_id": str(contract_id),
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    try:
        store = await _get_store()
        point_ids = await asyncio.to_thread(
            store.add_docs_with_ids, chunks, metadatas, wait=True
        )
    except Exception as exc:
        logger.warning(
            "contract_index.failed",
            error=str(exc),
            chatroom_id=chatroom_id,
            chunk_count=len(chunks),
        )
        return [], 0

    return point_ids, len(point_ids)
