from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=True, # .dev, .prod 구분용
    extra="ignore" # 환경변수 외의 설정값 무시
  )
  
  APP_ENV: Literal["dev", "prod"] = "dev"
  LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
  HOST: str = "0.0.0.0"
  PORT: int = 8000
  
  SERVICE_KEY: str = Field(
    default="",
    description="서비스 인증키. API 요청 시 헤더에 포함되어야 함"
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

  OC: str = ""

  @property
  def is_production(self) -> bool:
    return self.APP_ENV == "prod"
  

@lru_cache(maxsize=1)
def get_settings() -> Settings:
  return Settings()


settings = get_settings()

  