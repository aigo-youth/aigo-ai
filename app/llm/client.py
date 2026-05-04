from langchain_openai import ChatOpenAI

from app.settings import settings

_kwargs: dict = {
    "model": settings.LLM_MODEL,
    "api_key": settings.LLM_API_KEY,
    "temperature": 0.3,
    "timeout": 90,
    "max_retries": 0,
}

if settings.LLM_BASE_URL:
    _kwargs["base_url"] = settings.LLM_BASE_URL

llm = ChatOpenAI(**_kwargs)
streaming_llm = ChatOpenAI(**_kwargs, streaming=True)
