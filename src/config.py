"""환경변수 + 상수 중앙 관리."""

import os

from dotenv import load_dotenv

load_dotenv()

# ── API 키 ──────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ── Qdrant ──────────────────────────────────────────────
QDRANT_PATH: str = os.getenv("QDRANT_PATH", "./db")
QDRANT_URL: str = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

# ── 임베딩 ──────────────────────────────────────────────
EMBEDDING_MODEL: str = os.getenv(
  "EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
)

# ── 컬렉션 ──────────────────────────────────────────────
COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "legal")

# ── 검색 파라미터 ───────────────────────────────────────
RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CONTEXT_TOP_K: int = int(os.getenv("CONTEXT_TOP_K", "3"))

# ── 유사도 임계값 ───────────────────────────────────────
# 0.25 -- 너무 관대, 무관한 문서 포함 위험
# 0.30 -- 보수적 기준, recall 우선
# 0.35 -- 균형점 (현재 기본값)
# 0.40 -- 엄격, precision 우선
# 0.45 -- 매우 엄격, 검색 실패 빈번
RELEVANCE_THRESHOLD: float = float(
  os.getenv("RELEVANCE_THRESHOLD", "0.35")
)
