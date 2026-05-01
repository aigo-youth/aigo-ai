from typing import Literal

from pydantic import BaseModel, Field


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
