import os 
import sys
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.ingest import build_index, load_eflaw, load_expc, load_prec
from app.vectordb import Embedder, QdrantStore
DEFAULT_COLLECTION = "legal"

DEFAULT_SOURCES = [
  (load_eflaw, str(ROOT / "data/processed/eflaw_chunks.jsonl")),
  (load_prec, str(ROOT / "data/processed/prec_chunk_recursive_character.jsonl")),
  (load_expc, str(ROOT / "data/processed/expc_after_chunking.jsonl")),
]


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="통합 법령 벡터스토어 빌드")
  parser.add_argument(
    "--collection", default=DEFAULT_COLLECTION, help="Qdrant 컬렉션 이름"
  )
  parser.add_argument("--batch-size", type=int, default=64, help="배치 크기")
  parser.add_argument(
    "--limit", type=int, default=None, help="소스별 최대 적재 개수 (테스트용)"
  )
  parser.add_argument(
    "--reset", action="store_true", help="컬렉션을 삭제 후 재구축"
  )
  parser.add_argument(
    "--dry-run", action="store_true", help="데이터 로딩만 수행, Qdrant 적재 스킵"
  )
  return parser.parse_args()


def _maybe_reset(store: QdrantStore, collection: str) -> None:
  """컬렉션 초기화. Cloud 모드는 delete_collection, 로컬은 디렉토리 삭제."""
  if store.mode == "cloud":
    print(f"[reset] Cloud 컬렉션 '{collection}' 삭제 중...")
    store.client.delete_collection(collection_name=collection)
  else:
    qdrant_path = os.getenv("QDRANT_PATH")
    if not qdrant_path:
      print("[경고] QDRANT_PATH 환경변수가 없습니다. .env 확인 필요.")
      return
    p = Path(qdrant_path)
    if p.exists():
      print(f"[reset] {p} 삭제 중...")
      shutil.rmtree(p)


def _dry_run(sources: list, limit: int | None) -> None:
  """데이터 로딩만 수행하여 건수를 확인한다."""
  from app.ingest.indexer import _take

  print("[dry-run] 데이터 로딩 검증 (Qdrant 적재 없음)\n")
  total = 0
  for loader, path in sources:
    stream = loader(path)
    if limit is not None:
      stream = _take(stream, limit)
    count = sum(1 for _ in stream)
    total += count
    print(f"  {Path(path).name}: {count:,}건")
  print(f"\n  TOTAL: {total:,}건")


def main() -> None:
  args = _parse_args()

  if args.dry_run:
    _dry_run(DEFAULT_SOURCES, args.limit)
    return

  if args.reset:
    # reset 시 store 생성 전에 로컬 디렉토리를 삭제해야 하므로 분기
    qdrant_url = os.getenv("QDRANT_URL")
    if qdrant_url:
      embedder = Embedder()
      store = QdrantStore(collection_name=args.collection, embedder=embedder)
      _maybe_reset(store, args.collection)
      # 컬렉션 삭제 후 재생성을 위해 store를 다시 초기화
      store = QdrantStore(collection_name=args.collection, embedder=embedder)
    else:
      qdrant_path = os.getenv("QDRANT_PATH")
      if qdrant_path:
        p = Path(qdrant_path)
        if p.exists():
          print(f"[reset] {p} 삭제 중...")
          shutil.rmtree(p)
      embedder = Embedder()
      store = QdrantStore(collection_name=args.collection, embedder=embedder)
  else:
    embedder = Embedder()
    store = QdrantStore(collection_name=args.collection, embedder=embedder)

  print(f"[시작] mode={store.mode} collection={args.collection} "
        f"batch_size={args.batch_size} limit={args.limit}")

  def _log(doc_type: str, batch_n: int, total: int) -> None:
    print(f"  [{doc_type}] +{batch_n} (누적 {total})")

  counts = build_index(
    sources=DEFAULT_SOURCES,
    store=store,
    batch_size=args.batch_size,
    limit_per_source=args.limit,
    on_batch=_log,
  )

  print("\n[완료] doc_type별 적재 수:")
  for dt, n in counts.items():
    print(f"  {dt}: {n:,}")
  print(f"  TOTAL: {sum(counts.values()):,}")


if __name__ == "__main__":
  main()
