"""LLM 클라이언트 초기화.

RunPod vLLM 등 OpenAI 호환 엔드포인트를 ChatOpenAI로 연결한다.
LLM_BASE_URL이 비어 있으면 OpenAI 기본 엔드포인트를 사용한다.
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from src.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

_kwargs: dict = {
  "model": LLM_MODEL,
  "api_key": LLM_API_KEY,
  "temperature": 0.3,
}

if LLM_BASE_URL:
  _kwargs["base_url"] = LLM_BASE_URL

llm = ChatOpenAI(**_kwargs)
