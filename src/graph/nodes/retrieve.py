from functools import lru_cache
from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.config import COLLECTION_NAME, EMBEDDING_MODEL, RETRIEVAL_TOP_K
from src.graph.state import PipelineState
from src.vectordb import Embedder, QdrantStore


@lru_cache(maxsize=1)
def _get_store() -> QdrantStore:
  """QdrantStore 싱글턴 반환.

  임베더와 컬렉션을 한 번만 초기화
  """
  embedder = Embedder(EMBEDDING_MODEL)
  return QdrantStore(
    collection_name=COLLECTION_NAME,
    embedder=embedder,
  )


def _build_filter(
  intent_metadata: dict[str, str] | None,
) -> Filter | None:
  """
  intent_metadata에서 Qdrant payload 필터를 생성한다.

  Args:
    intent_metadata: 의도 분류에서 태깅된 메타데이터.
      doc_type 키가 있으면 해당 값으로 필터링한다.

  Returns:
    Filter 객체 또는 None (필터 조건 없음).
  """
  if not intent_metadata:
    return None

  conditions: list[FieldCondition] = []

  doc_type = intent_metadata.get("doc_type")
  if doc_type:
    conditions.append(
      FieldCondition(key="doc_type", match=MatchValue(value=doc_type))
    )

  if not conditions:
    return None

  return Filter(must=conditions)


def retrieve(state: PipelineState) -> PipelineState:
  """Qdrant에서 사용자 질의와 관련된 문서를 검색한다.

  Args:
    state: 파이프라인 상태. user_query와 intent_metadata 필요.

  Returns:
    retrieved_docs와 top_score 키가 갱신된 상태.
  """
  store = _get_store()
  query = state["user_query"]
  metadata = state.get("intent_metadata", {})

  filters = _build_filter(metadata)
  results: list[dict[str, Any]] = store.search(
    query=query,
    top_k=RETRIEVAL_TOP_K,
    filters=filters,
  )

  top_score = results[0]["score"] if results else 0.0

  return {
    "retrieved_docs": results,
    "top_score": top_score,
  }
