import os
import threading
import time
from typing import Literal

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.settings import settings

logger = get_logger(__name__)
router = APIRouter(tags=["health"])


class GpuInfo(BaseModel):
    name: str
    memory_used_mb: int
    memory_total_mb: int


class HealthReadyResponse(BaseModel):
    status: Literal["ready"] = "ready"
    model: str
    embedding_model: str
    qdrant_connected: bool
    gpu: GpuInfo | None = None


class HealthLoadingResponse(BaseModel):
    status: Literal["loading"] = "loading"
    ready_in_seconds: int = Field(..., ge=0)


_QDRANT_PROBE_TTL = 10.0
_qdrant_probe_lock = threading.Lock()
_qdrant_probe_cache: tuple[float, bool] = (0.0, False)


def _ping_qdrant_cloud(url: str, api_key: str | None) -> bool:
    try:
        from qdrant_client import QdrantClient
    except Exception:
        return False

    client = QdrantClient(url=url, api_key=api_key or None, timeout=2.0)
    try:
        client.get_collections()
        return True
    except Exception as exc:
        logger.warning("healthz.qdrant_ping_failed", url=url, error=str(exc))
        return False
    finally:
        try:
            client.close()
        except Exception:
            pass


def _qdrant_connected() -> bool:
    global _qdrant_probe_cache

    now = time.monotonic()
    cached_at, cached = _qdrant_probe_cache
    if now - cached_at < _QDRANT_PROBE_TTL:
        return cached

    with _qdrant_probe_lock:
        now = time.monotonic()
        cached_at, cached = _qdrant_probe_cache
        if now - cached_at < _QDRANT_PROBE_TTL:
            return cached

        if settings.QDRANT_URL:
            ok = _ping_qdrant_cloud(settings.QDRANT_URL, settings.QDRANT_API_KEY)
        elif settings.QDRANT_PATH:
            ok = os.path.isdir(settings.QDRANT_PATH)
        else:
            ok = False

        _qdrant_probe_cache = (now, ok)
        return ok


def _gpu_info() -> GpuInfo | None:
    try:
        import torch  # type: ignore
    except Exception:
        return None

    try:
        if not torch.cuda.is_available() or torch.cuda.device_count() == 0:
            return None

        idx = 0
        name = torch.cuda.get_device_name(idx)
        props = torch.cuda.get_device_properties(idx)
        total_bytes = int(getattr(props, "total_memory", 0))

        used_bytes = 0
        try:
            free, total = torch.cuda.mem_get_info(idx)
            used_bytes = int(total) - int(free)
            total_bytes = int(total)
        except Exception:
            used_bytes = int(torch.cuda.memory_reserved(idx))

        mib = 1024 * 1024
        return GpuInfo(
            name=name,
            memory_used_mb=used_bytes // mib,
            memory_total_mb=total_bytes // mib,
        )
    except Exception:
        return None


@router.get(
    "/healthz",
    summary="AI 헬스체크",
    responses={
        200: {"model": HealthReadyResponse},
        503: {"model": HealthLoadingResponse},
    },
)
async def healthz() -> JSONResponse:
    if not _qdrant_connected():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=HealthLoadingResponse(ready_in_seconds=30).model_dump(),
        )

    payload = HealthReadyResponse(
        model=settings.LLM_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
        qdrant_connected=True,
        gpu=_gpu_info(),
    )
    return JSONResponse(status_code=200, content=payload.model_dump())
