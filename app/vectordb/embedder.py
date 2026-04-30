import os 
from typing import Protocol

from openai import OpenAI
from sentence_transformers import SentenceTransformer

_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


# duck typing을 이용한 Embedder 인터페이스
class EmbedderProtocol(Protocol):
  vector_size: int
  def embed(self, texts: list[str]) -> list[list[float]]: ...
  def embed_question(self, text: str) -> list[float]: ...


class HFEmbedder:
  """sentence-transformers 기반 로컬 임베더"""
  def __init__(self, model_name: str) -> None:
    self._model = SentenceTransformer(model_name)
    self.vector_size = self._model.get_sentence_embedding_dimension()
    
  def embed(self, texts: list[str]) -> list[list[float]]:
    """
    여러 텍스트를 한꺼번에 벡터로 변환합니다.

    문서를 대량으로 벡터DB에 저장할 때 사용합니다.
    한 번에 여러 텍스트를 처리하므로 반복 호출보다 효율적입니다.

    Args:
      texts: 변환할 텍스트 목록.
             예: ["임대차 계약이란...", "보증금 반환 기한은..."]

    Returns:
      각 텍스트에 대응하는 벡터 목록.
      반환 형태: [[0.12, -0.34, ...], [0.56, 0.78, ...], ...]
      리스트의 순서는 입력 texts의 순서와 동일합니다.
    """
    vectors = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return vectors.tolist()

  def embed_question(self, text: str) -> list[float]:
    """
    단일 텍스트를 벡터로 변환합니다.

    사용자가 입력한 질문을 검색에 사용할 벡터로 바꿀 때 주로 사용합니다.
    내부적으로 embed()를 호출하며, 텍스트 한 개만 처리합니다.

    Args:
      text: 변환할 텍스트 한 개.
            예: "집주인이 보증금을 돌려주지 않으면 어떻게 하나요?"

    Returns:
      텍스트를 표현하는 float 벡터 (1차원 리스트).
      예: [0.12, -0.34, 0.78, ...]
    """ 
    return self.embed([text])[0]


class OpenAIEmbedder:
  """OpenAI Embeddings API 기반 임베더(text-embedding-3-small 전용)"""
  def __init__(self) -> None:
    self._client = OpenAI()
    self.vector_size = 1536

  def embed(self, texts: list[str]) -> list[list[float]]:
    resp = self._client.embeddings.create(model="text-embedding-3-small", input=texts)
    return [item.embedding for item in resp.data]
  
  def embed_question(self, text: str) -> list[float]:
    return self.embed([text])[0]
  

def Embedder(model_name: str = _EMBEDDING_MODEL) -> EmbedderProtocol:
  if model_name and model_name.startswith("text-embedding-"):
    return OpenAIEmbedder()
  return HFEmbedder(model_name)