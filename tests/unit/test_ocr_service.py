import asyncio
import os

import pytest

from app.services import ocr_service
from app.services.ocr_service import OCRServiceError


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_pdf_bytes() -> bytes:
    return b"%PDF-1.4\n" + b"x" * 256


def test_returns_dict_for_digital_pdf(monkeypatch):
    """디지털 PDF: digital_to_text 사용, ocr_accuracy_score 는 None"""

    def fake_process(path: str) -> dict:
        assert os.path.exists(path)
        return {
            "page_count": 3,
            "full_text": "마스킹된 텍스트",
            "file_type": "Digital",
            "ocr_accuracy_score": None,
        }

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    result = _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))

    assert result["file_type"] == "Digital"
    assert result["full_text"] == "마스킹된 텍스트"
    assert result["page_count"] == 3
    assert result["ocr_accuracy_score"] is None
    assert result["processing_ms"] >= 0


def test_returns_dict_for_scan_pdf(monkeypatch):
    """스캔 PDF: ocr_accuracy_score float 통과"""

    def fake_process(path: str) -> dict:
        return {
            "page_count": 2,
            "full_text": "OCR 결과",
            "file_type": "Scan",
            "ocr_accuracy_score": 0.87,
        }

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    result = _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))

    assert result["file_type"] == "Scan"
    assert result["ocr_accuracy_score"] == pytest.approx(0.87)


def test_temp_file_is_cleaned_up_on_success(monkeypatch):
    """성공 경로에서도 임시 파일은 unlink"""
    recorded: dict[str, str] = {}

    def fake_process(path: str) -> dict:
        recorded["path"] = path
        assert os.path.exists(path)
        return {
            "page_count": 1,
            "full_text": "ok",
            "file_type": "Digital",
            "ocr_accuracy_score": None,
        }

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))

    assert "path" in recorded
    assert not os.path.exists(recorded["path"])


def test_temp_file_is_cleaned_up_on_error(monkeypatch):
    """예외 경로에서도 임시 파일은 unlink"""
    recorded: dict[str, str] = {}

    def fake_process(path: str) -> dict:
        recorded["path"] = path
        raise OCRServiceError("암호화된 PDF는 지원하지 않습니다.")

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    with pytest.raises(OCRServiceError, match="암호화"):
        _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))

    assert "path" in recorded
    assert not os.path.exists(recorded["path"])


def test_propagates_ocr_service_error_unchanged(monkeypatch):
    """페이지 한도/마스킹 실패 등 OCRServiceError 는 그대로 전파"""

    def fake_process(path: str) -> dict:
        raise OCRServiceError("PDF 페이지 수가 한도(50)를 초과합니다.")

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    with pytest.raises(OCRServiceError, match="페이지 수가 한도"):
        _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))


def test_wraps_unknown_exception_as_ocr_service_error(monkeypatch):
    """모르는 예외는 OCRServiceError 로 감싸서 외부에 OCR_FAILED 로 노출"""

    def fake_process(path: str) -> dict:
        raise RuntimeError("fitz boom")

    monkeypatch.setattr(ocr_service, "_process_sync", fake_process)
    with pytest.raises(OCRServiceError, match="PDF 처리 실패"):
        _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))


def test_timeout_raises_ocr_service_error(monkeypatch):
    """OCR_TIMEOUT_SECONDS 초과 시 OCRServiceError(timeout 메시지)로 변환"""
    import time as real_time

    def slow_process(path: str) -> dict:
        real_time.sleep(0.5)
        return {
            "page_count": 1,
            "full_text": "x",
            "file_type": "Digital",
            "ocr_accuracy_score": None,
        }

    monkeypatch.setattr(ocr_service, "_process_sync", slow_process)
    monkeypatch.setattr(ocr_service.settings, "OCR_TIMEOUT_SECONDS", 0.05)

    with pytest.raises(OCRServiceError, match="시간이 초과"):
        _run(ocr_service.run_pdf_ocr(_make_pdf_bytes()))
