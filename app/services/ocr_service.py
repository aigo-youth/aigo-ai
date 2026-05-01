import asyncio
import contextlib
import os
import tempfile
import time

from app.settings import settings


class OCRServiceError(Exception):
    """OCR 처리 중 발생한 오류."""


def _process_sync(path: str) -> dict:
    """디스크 경로의 PDF를 동기적으로 처리한다.

    텍스트 추출 후 PII 마스킹 노드를 반드시 통과시킨다.
    마스킹 단계가 실패하면 OCRServiceError 를 발생시켜
    원문(PII 포함) 텍스트가 호출자에게 반환되지 않도록 한다.

    Returns:
      {page_count, full_text, file_type, ocr_accuracy_score}
      여기서 full_text 는 PII 마스킹이 적용된 텍스트이다.
    """
    import fitz

    from app.pdf_graph.nodes.check_pdf import check_pdf
    from app.pdf_graph.nodes.masking_text import masking_text

    doc = fitz.open(path)
    try:
        if doc.is_encrypted:
            raise OCRServiceError("암호화된 PDF는 지원하지 않습니다.")
    finally:
        doc.close()

    state: dict = {"file_path": path}
    check_result = check_pdf(state)
    state.update(check_result)

    page_count = check_result["file_info"]["page_count"]
    if page_count > settings.MAX_PDF_PAGES:
        raise OCRServiceError(
            f"PDF 페이지 수가 한도({settings.MAX_PDF_PAGES})를 초과합니다."
        )

    file_type = check_result["file_type"]

    if file_type == "Digital":
        from app.pdf_graph.nodes.digital_to_text import digital_to_text

        extract_result = digital_to_text(state)
        ocr_accuracy_score = None
    else:
        from app.pdf_graph.nodes.scan_to_text import scan_to_text

        extract_result = scan_to_text(state)
        ocr_accuracy_score = extract_result.get("ocr_accuracy_score")

    state.update(extract_result)

    try:
        masking_result = masking_text(state)
    except Exception as exc:
        raise OCRServiceError("PII 마스킹에 실패했습니다.") from exc

    masked_text = masking_result.get("masked_text")
    if not isinstance(masked_text, str):
        raise OCRServiceError("PII 마스킹 결과가 유효하지 않습니다.")

    return {
        "page_count": page_count,
        "full_text": masked_text,
        "file_type": file_type,
        "ocr_accuracy_score": ocr_accuracy_score,
    }


async def run_pdf_ocr(file_bytes: bytes) -> dict:
    """업로드된 PDF 바이트를 OCR 처리하여 결과 dict를 반환한다.

    Raises:
      OCRServiceError: 페이지 한도 초과, 처리 시간 초과, 파싱 실패 등.
    """
    start = time.monotonic()

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_bytes)

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(_process_sync, tmp_path),
                timeout=settings.OCR_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            raise OCRServiceError("OCR 처리 시간이 초과되었습니다.") from exc
        except OCRServiceError:
            raise
        except Exception as exc:
            raise OCRServiceError(f"PDF 처리 실패: {exc}") from exc
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)

    result["processing_ms"] = int((time.monotonic() - start) * 1000)
    return result
