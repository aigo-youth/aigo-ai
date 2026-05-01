import asyncio
import contextlib
import time
from typing import AsyncIterator, Iterable

from app.graph import run_preformat, stream_formatter


def _safe_hit_count(state: dict) -> int:
    """state 에서 검색된 hit 수를 best-effort 로 추출."""
    for key in ("retrieved_docs", "hits", "context_docs", "documents"):
        value = state.get(key)
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            try:
                return len(list(value))
            except TypeError:
                continue
    return 0


async def stream_chat(
    query: str,
    history: list[dict] | None = None,
    contract_context: dict | None = None,
) -> AsyncIterator[dict]:
    """질의에 대한 RAG 응답을 SSE 이벤트 dict 시퀀스로 yield 한다.

    Args:
      query:             사용자 질문 (1~1000자, 한국어).
      history:           최근 대화 N개 (token budget 4K — 호출자 책임).
      contract_context:  계약서 컨텍스트 (has_contract, special_terms_summary 등).

    Yields:
      {"event": "rag_search_done", "data": {"hit_count": int, "latency_ms": int}}
      {"event": "token",           "data": {"delta": str}}
      {"event": "citation",        "data": {"title": str, "url": str, ...}}
      {"event": "message_end",     "data": {"total_tokens": int,
                                             "fallback_triggered": bool,
                                             "latency_ms": int}}
      {"event": "error",           "data": {"code": str, "message": str}}
    """
    start = time.monotonic()

    try:
        state = await asyncio.to_thread(run_preformat, query)
    except Exception:
        yield {
            "event": "error",
            "data": {
                "code": "PIPELINE_FAILED",
                "message": "응답 생성 파이프라인이 실패했습니다.",
            },
        }
        return

    rag_latency_ms = int((time.monotonic() - start) * 1000)
    yield {
        "event": "rag_search_done",
        "data": {
            "hit_count": _safe_hit_count(state),
            "latency_ms": rag_latency_ms,
        },
    }

    fallback_triggered = bool(state.get("fallback_message"))
    total_tokens = 0

    if fallback_triggered:
        fallback = state["fallback_message"]
        total_tokens = len(fallback)
        yield {"event": "token", "data": {"delta": fallback}}
    else:
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | BaseException | None] = asyncio.Queue(maxsize=64)

        def producer():
            try:
                for chunk in stream_formatter(state):
                    if chunk:
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
            except BaseException as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        task = asyncio.create_task(asyncio.to_thread(producer))
        errored = False

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, BaseException):
                    errored = True
                    yield {
                        "event": "error",
                        "data": {
                            "code": "STREAM_FAILED",
                            "message": "응답 스트리밍이 중단되었습니다.",
                        },
                    }
                    break
                total_tokens += len(item)
                yield {"event": "token", "data": {"delta": item}}
        except asyncio.CancelledError:
            task.cancel()
            raise
        finally:
            with contextlib.suppress(Exception):
                await task

        if errored:
            return

    for citation in state.get("citations") or []:
        yield {"event": "citation", "data": dict(citation)}

    yield {
        "event": "message_end",
        "data": {
            "total_tokens": total_tokens,
            "fallback_triggered": fallback_triggered,
            "latency_ms": int((time.monotonic() - start) * 1000),
        },
    }
