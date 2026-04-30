"""레거시 호환 shim. 실제 설정은 app.settings.settings 를 사용할 것."""

from app.settings import settings as _s

LLM_API_KEY: str = _s.LLM_API_KEY
LLM_MODEL: str = _s.LLM_MODEL
LLM_BASE_URL: str = _s.LLM_BASE_URL

QDRANT_PATH: str = _s.QDRANT_PATH
QDRANT_URL: str = _s.QDRANT_URL
QDRANT_API_KEY: str = _s.QDRANT_API_KEY

EMBEDDING_MODEL: str = _s.EMBEDDING_MODEL

COLLECTION_NAME: str = _s.COLLECTION_LEGAL

RETRIEVAL_TOP_K: int = _s.RETRIEVAL_TOP_K
CONTEXT_TOP_K: int = _s.CONTEXT_TOP_K
RELEVANCE_THRESHOLD: float = _s.RELEVANCE_THRESHOLD
