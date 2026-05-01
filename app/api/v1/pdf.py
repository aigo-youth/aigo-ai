import asyncio
import os
import time
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    UploadFile,
    status,
)

from app.api.v1.schemas import (
    PdfAnalyzeResponse,
    QdrantInfo,
)
from app.core.auth import verify_internal_api_key
from app.core.logging import get_logger
from app.services import (
    contract_extraction_service,
    contract_index_service,
    ocr_service,
    special_terms_service,
)
from app.services.ocr_service import OCRServiceError
from app.settings import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/pdf", tags=["pdf"])


def _http_error(code: str, message: str, http_status: int) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={"code": code, "message": message},
    )


@router.post(
    "/analyze",
    response_model=PdfAnalyzeResponse,
    dependencies=[Depends(verify_internal_api_key)],
    summary="계약서 PDF 분석 (OCR + 구조화 추출 + Qdrant upsert)",
)
async def analyze_pdf(
    file: UploadFile = File(...),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_chatroom_id: str | None = Header(default=None, alias="X-Chatroom-Id"),
    x_idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
) -> PdfAnalyzeResponse:
    if not x_user_id or not x_chatroom_id:
        raise _http_error(
            "INVALID_REQUEST",
            "X-User-Id 와 X-Chatroom-Id 헤더가 필요합니다.",
            status.HTTP_400_BAD_REQUEST,
        )

    if file.content_type != "application/pdf":
        raise _http_error(
            "UNSUPPORTED_MEDIA",
            "PDF 파일만 업로드할 수 있습니다.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    max_bytes = settings.MAX_PDF_BYTES
    start = time.monotonic()

    try:
        contents = bytearray()
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            contents.extend(chunk)
            if len(contents) > max_bytes:
                raise _http_error(
                    "PAYLOAD_TOO_LARGE",
                    f"파일 크기가 한도({max_bytes // (1024 * 1024)}MB)를 초과합니다.",
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

        if not contents.startswith(b"%PDF"):
            raise _http_error(
                "OCR_FAILED",
                "유효하지 않은 PDF 파일입니다.",
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        safe_filename = os.path.basename(file.filename or "")[:64]
        logger.info(
            "pdf_analyze.received",
            user_id=x_user_id,
            chatroom_id=x_chatroom_id,
            idempotency_key=x_idempotency_key,
            filename=safe_filename,
            size=len(contents),
        )

        try:
            ocr_result = await ocr_service.run_pdf_ocr(bytes(contents))
        except OCRServiceError as exc:
            logger.error("pdf_analyze.ocr_failed", error=str(exc))
            raise _http_error(
                "OCR_FAILED",
                "PDF 파일을 처리할 수 없습니다.",
                status.HTTP_422_UNPROCESSABLE_CONTENT,
            ) from exc
    finally:
        await file.close()

    full_text: str = ocr_result.get("full_text") or ""
    raw_score = ocr_result.get("ocr_accuracy_score")
    ocr_confidence = float(raw_score) if isinstance(raw_score, (int, float)) else 1.0

    contract_id = uuid4()

    extraction_task = asyncio.create_task(
        contract_extraction_service.extract_property_and_clauses(full_text)
    )
    special_terms_task = asyncio.create_task(
        special_terms_service.extract_special_terms(full_text)
    )
    index_task = asyncio.create_task(
        contract_index_service.index_contract_text(
            full_text=full_text,
            user_id=x_user_id,
            chatroom_id=x_chatroom_id,
            contract_id=contract_id,
        )
    )

    (
        (property_info, key_clauses),
        special_terms,
        (point_ids, chunk_count),
    ) = await asyncio.gather(extraction_task, special_terms_task, index_task)

    property_info = property_info.model_copy(update={"contract_id": contract_id})

    logger.info(
        "pdf_analyze.completed",
        user_id=x_user_id,
        chatroom_id=x_chatroom_id,
        contract_id=str(contract_id),
        chunk_count=chunk_count,
        special_terms_count=len(special_terms),
        key_clauses_count=len(key_clauses),
    )

    return PdfAnalyzeResponse(
        ocr_confidence=max(0.0, min(1.0, ocr_confidence)),
        pii_masked_text=full_text,
        property_info=property_info,
        special_terms=special_terms,
        key_clauses=key_clauses,
        qdrant=QdrantInfo(
            collection=settings.COLLECTION_CONTRACTS,
            chunk_count=chunk_count,
            ids=point_ids,
        ),
        latency_ms=int((time.monotonic() - start) * 1000),
    )
