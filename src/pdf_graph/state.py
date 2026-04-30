"""PDF 텍스트 추출 과정의 LangGraph 파이프라인 상태 스키마"""

from typing import Literal, TypedDict

class FileInfo(TypedDict):
    title: str
    volume: float   # MB 단위
    page_count: int

class PDF_State(TypedDict):
    file_path: str                              # pdf 파일의 경로 (이는 실제 적용 단계에서 작동 메커니즘이 어떠냐에 따라 변경될 수 있음)
    file_info: FileInfo                         # pdf 파일의 용량(MB)과 페이지 수 정보를 담음
    file_type: Literal["Scan", "Digital"]       # PDF의 형식 저장
    extracted_text: str                         # pymupdf 혹은 OCR을 통해 추출된 text을 담음
    ocr_accuracy_score: float                   # OCR에서 Accuracy Score을 담음
    masked_text: str                            # 마스킹 노드가 마스킹한 string을 담음
    special_term: str                           # 특약 항목만 추출한 string을 담음