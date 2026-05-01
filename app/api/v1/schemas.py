from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# 표준 에러 응답
class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail


# POST v1/chat/stream
class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=10_000)


class ContractContext(BaseModel):
    has_contract: bool = False
    special_terms_summary: str | None = None
    qdrant_chunk_filter: dict | None = None


class ChatStreamRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1_000)
    history: list[ChatHistoryMessage] = Field(default_factory=list)
    contract_context: ContractContext | None = None


# POST v1/pdf/analyze


class PropertyInfo(BaseModel):
    """매물 정보 (Property_info 테이블 매핑)."""

    contract_id: UUID | None = None  # 계약서ID (PK)
    location: str | None = Field(default=None, max_length=40)  # 소재지
    start_date: date | None = None  # 계약시작일
    end_date: date | None = None  # 계약종료일
    month_rent: int | None = None  # 월세
    deposit: int | None = None  # 보증금
    house_cost: str | None = Field(default=None, max_length=10)  # 관리비


class SpecialTerm(BaseModel):
    id: int
    section: str | None = None
    content: str
    editable: bool = True


class KeyClause(BaseModel):
    id: int
    section: str
    content: str


class QdrantInfo(BaseModel):
    collection: str
    chunk_count: int
    ids: list[str] = Field(default_factory=list)


class PdfAnalyzeResponse(BaseModel):
    ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    pii_masked_text: str
    property_info: PropertyInfo
    special_terms: list[SpecialTerm] = Field(default_factory=list)
    key_clauses: list[KeyClause] = Field(default_factory=list)
    qdrant: QdrantInfo
    latency_ms: int = Field(..., ge=0)


# POST v1/embed


class EmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=64)
    model: str = "kure-v1"


class EmbedResponse(BaseModel):
    model: str
    embeddings: list[list[float]]
    latency_ms: int = Field(..., ge=0)
