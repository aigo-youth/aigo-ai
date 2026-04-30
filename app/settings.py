import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_ENV = os.getenv("APP_ENV", "dev")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", f".env.{_APP_ENV}"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # 환경변수 외의 설정값 무시
    )

    APP_ENV: Literal["dev", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    INTERNAL_API_KEY: str = Field(
        default="",
        description=(
            "Django ↔ FastAPI 내부 인증키. 요청 헤더 X-Internal-Api-Key 와 비교한다. "
            "Secrets Manager 보관, 90일 회전 (API 명세 0.1)."
        ),
    )

    EMBEDDING_MODEL: str = "nlpai-lab/KURE-v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
    LLM_BASE_URL: str = "https://api.lgai.co.kr/v1/llm"

    QDRANT_PATH: str = "./vector_db"
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    COLLECTION_LEGAL: str = "legal"
    COLLECTION_CONTRACTS: str = "contracts"

    RETRIEVAL_TOP_K: int = 5
    CONTEXT_TOP_K: int = 3
    RELEVANCE_THRESHOLD: float = 0.35

    # PDF / OCR 한도
    MAX_PDF_BYTES: int = 5 * 1024 * 1024  # 5MB
    MAX_PDF_PAGES: int = 50
    OCR_TIMEOUT_SECONDS: int = 60

    OC: str = ""

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
