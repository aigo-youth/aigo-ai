from typing import Callable, Iterator
from src.vectordb import QdrantStore
from .loaders import LoadedChunk

LoaderFn = Callable[[str], Iterator[LoadedChunk]]

def _batched(stream: Iterator[LoadedChunk], size: int) -> Iterator[list[LoadedChunk]]:
  # * lazy sliding window
  batch = []
  for item in stream:
    batch.append(item)
    if len(batch) >= size:
      yield batch
      batch = []
    if batch:
      yield batch
      

def build_index(
  sources: list[tuple[LoaderFn, str]],
  store: QdrantStore,
  batch_size: int = 64,
  limit_per_source: int | None = None,
  on_batch: Callable[[str, int, int], None] | None = None
):
  """
  Qdrant 컬렉션에 적재

  Args:
    sources (list): 소스 로더와 경로의 튜플 리스트
    store (QdrantStore): Qdrant 스토어 인스턴스
    batch_size (int): 배치 크기 (default: 64)
    limit_per_source (int, optional): 각 소스에서 가져올 최대 항목 수 (default: None)
    on_batch (callable, optional): 배치 처리 후 호출할 콜백 함수 (default: None)
  """
  counts = {}
  
  for loader, path in sources:
    stream = loader(path)
    if limit_per_source is not None:
      stream = _take(stream, limit_per_source)
    
    src_count = 0
    for batch in _batched(stream, batch_size):
      texts = [t for t, _ in batch]
      metas = [m for _, m in batch]
      store.add_docs(texts, metas)
      
      doc_type = metas[0].get("doc_type", "unknown")
      counts[doc_type] = counts.get(doc_type, 0) + len(batch)
      src_count += len(batch)
      # 한 묶음 처리 후 콜백 호출
      if on_batch is not None:
        on_batch(doc_type, len(batch), src_count)
  
  return counts


def _take(stream: Iterator[LoadedChunk], n: int) -> Iterator[LoadedChunk]:
  for i, item in enumerate(stream):
    if i >= n:
      return
    yield item