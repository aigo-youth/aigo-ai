import os
from uuid import uuid4
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .embedder import Embedder

_DEFAULT_PATH = os.getenv("QDRANT_PATH")


# TODO: 클라우드 저장으로 전환
class QdrantStore:
  """
  Qdrant 로컬 컬렉션 관리 및 RAG용 검색을 위한 클래스
  """
  
  def __init__(self, collection_name: str, embedder: Embedder, path: str = _DEFAULT_PATH) -> None:
    """
    Qdrant Store 초기화

    Args:
      collection_name (str): 사용할 컬렉션 이름
      embedder (Embedder): 텍스트를 임베딩으로 변환할 클래스
      path (str, optional): Qdrant 데이터를 저장할 로컬 디렉토리 경로
    """
    # 로컬 기반
    self._client = QdrantClient(path=path)
    self._collection = collection_name
    self._embedder = embedder
    
    # 중복 생성 방지
    existing = {c.name for c in self._client.get_collections().collections}
    if collection_name not in existing:
      self._client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
          size=embedder.vector_size,
          # TODO: 임베딩 모델에 맞춰서 변환
          distance=Distance.COSINE,   # 코사인 기반
        ),
      ) 
  
  # 문서 저장
  def add_docs(
    self,
    texts: list[str],
    metadatas: list[dict[str, Any]] | None = None,
  ) -> None:
    """
    Chunk 임베딩 후 Vector DB에 저장

    Args:
      texts (list[str]): 임베딩할 텍스트 청크 목록
      metadatas (list[dict[str, Any]] | None, optional): 각 텍스트에 대응하는 메타데이터 (ex. 법령, 조문번호...)
    """
    if not texts:
      return
    
    # 만약 메타데이터 없음 빈 dict로 채움
    # => zip 사용 시 오류 방지
    metadatas = metadatas or [{} for _ in texts]
    vectors = self._embedder.embed(texts)
    
    points = [
      PointStruct(
        id=uuid4(),
        vector=vec,
        payload={"text": text, **meta},
      )
      for text, vec, meta in zip(texts, vectors, metadatas)
    ]
    self._client.upsert(collection_name=self._collection, points=points)
    
  # RAG 검색
  def search(
    self,
    query: str,
    top_k: int = 5,
  ) -> list[dict[str, Any]]:
    """
    쿼리와 가장 유사한 청크 반환

    Args:
        query (str): 자연어 검색 질의
        top_k (int, optional): 반환할 topk 수(default 5)
    """
    # 질의 -> 벡터 변환
    query_to_vector = self._embedder.embed_question(query)
    hits = self._client.query_points(
      collection_name=self._collection,
      query=query_to_vector,
      limit=top_k,
    ).points
    
    return [
      {"score": hit.score, **hit.payload} # 1에 가까울 수록 유사
      for hit in hits
    ]
    