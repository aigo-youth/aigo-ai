import json
import signal
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.clients.collector import fetch_details, fetch_list, save_raw
from app.ingest.chunker import chunk_expc, chunk_prec
from app.vectordb import Embedder, QdrantStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

RAW_DIR = ROOT / "data" / "raw"
META_DIR = ROOT / "data" / "meta"
COLLECTED_IDS_PATH = META_DIR / "collected_ids.json"

COLLECTION_NAME = "legal"
BATCH_SIZE = 64

# ── 수집 대상 정의 ──────────────────────────────────────
TARGETS = {
    "prec": {
        "id_field": "판례일련번호",
        "queries": ["임대차", "보증금", "전세", "임차인", "계약갱신청구권"],
        "chunker": chunk_prec,
    },
    "expc": {
        "id_field": "법령해석례일련번호",
        "queries": ["임대차", "보증금", "주택임대차", "전세", "임차인"],
        "chunker": chunk_expc,
    },
}

_running = True


def _signal_handler(sig, frame):
    global _running
    log.info("종료 신호 수신. 현재 작업 완료 후 종료합니다.")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# 수집 이력 관리
def load_collected_ids() -> dict[str, set[str]]:
    """이미 수집된 문서 ID 목록 로드."""
    if COLLECTED_IDS_PATH.exists():
        data = json.loads(COLLECTED_IDS_PATH.read_text(encoding="utf-8"))
        return {k: set(v) for k, v in data.items()}
    return {}


def save_collected_ids(collected: dict[str, set[str]]) -> None:
    """수집된 문서 ID 목록 저장."""
    META_DIR.mkdir(parents=True, exist_ok=True)
    data = {k: sorted(v) for k, v in collected.items()}
    COLLECTED_IDS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def init_collected_ids() -> dict[str, set[str]]:
    """기존 raw JSONL에서 수집 이력 초기화."""
    collected = load_collected_ids()
    if collected:
        return collected

    log.info("수집 이력 초기화: 기존 raw 데이터에서 ID 추출 중...")
    for target, cfg in TARGETS.items():
        raw_path = RAW_DIR / f"{target}.jsonl"
        if not raw_path.exists():
            continue
        ids = set()
        with open(raw_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                doc_id = str(row.get(cfg["id_field"], ""))
                if doc_id:
                    ids.add(doc_id)
        collected[target] = ids
        log.info(f"  {target}: 기존 {len(ids)}건 발견")

    save_collected_ids(collected)
    return collected


# DB 적재
def index_chunks(store: QdrantStore, chunks: list[tuple[str, dict]]) -> int:
    """청크 리스트를 배치 단위로 벡터DB에 적재. 적재 건수 반환."""
    if not chunks:
        return 0

    total = 0
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [text for text, _ in batch]
        metas = [meta for _, meta in batch]
        store.add_docs(texts, metas)
        total += len(batch)

    return total


# 동기화
def sync_target(
    target: str,
    cfg: dict,
    collected: dict[str, set[str]],
    store: QdrantStore,
) -> dict[str, int]:
    """단일 target: 수집 → 청킹 → 적재. 결과 통계 반환."""
    id_field = cfg["id_field"]
    chunker = cfg["chunker"]
    existing_ids = collected.get(target, set())

    stats = {"collected": 0, "chunks": 0}

    for query in cfg["queries"]:
        log.info(f"[{target}] '{query}' 검색 중...")
        try:
            items = fetch_list(target=target, query=query)
        except Exception as e:
            log.error(f"[{target}] '{query}' 목록 조회 실패: {e}")
            continue

        # 중복 필터링
        new_items = [
            item for item in items if str(item.get(id_field, "")) not in existing_ids
        ]

        if not new_items:
            log.info(f"[{target}] '{query}': 새 문서 없음 (전체 {len(items)}건 중)")
            continue

        log.info(
            f"[{target}] '{query}': {len(new_items)}건 새 문서 발견 "
            f"(전체 {len(items)}건)"
        )

        # 상세 조회
        try:
            details = fetch_details(
                target=target, items=new_items, id_field=id_field,
            )
        except Exception as e:
            log.error(f"[{target}] '{query}' 상세 조회 실패: {e}")
            continue

        # raw 저장 (백업용)
        save_raw(records=details, target=target, mode="a")

        # 청킹
        all_chunks = []
        for record in details:
            all_chunks.extend(chunker(record))

        # 벡터DB 적재
        indexed = index_chunks(store, all_chunks)

        # ID 기록 (적재 성공 후에만)
        for item in details:
            doc_id = str(item.get(id_field, ""))
            if doc_id:
                existing_ids.add(doc_id)

        stats["collected"] += len(details)
        stats["chunks"] += indexed
        log.info(
            f"[{target}] '{query}': {len(details)}건 수집, "
            f"{indexed}건 청크 적재 완료"
        )

    collected[target] = existing_ids
    return stats


def sync_all() -> dict[str, dict[str, int]]:
    """모든 target 증분 동기화: 수집 → 청킹 → 벡터DB 적재."""
    collected = init_collected_ids()

    # 벡터DB 초기화 (한 번만)
    log.info("벡터DB 연결 중...")
    embedder = Embedder()
    store = QdrantStore(collection_name=COLLECTION_NAME, embedder=embedder)
    log.info(f"벡터DB 연결 완료 (mode={store.mode})")

    results = {}
    for target, cfg in TARGETS.items():
        try:
            stats = sync_target(target, cfg, collected, store)
            results[target] = stats
        except Exception as e:
            log.error(f"[{target}] 동기화 실패: {e}")
            results[target] = {"collected": 0, "chunks": 0}

    save_collected_ids(collected)

    # 결과 출력
    log.info("── 동기화 결과 ──")
    total_collected = 0
    total_chunks = 0
    for target, stats in results.items():
        log.info(f"  {target}: {stats['collected']}건 수집, {stats['chunks']}건 적재")
        total_collected += stats["collected"]
        total_chunks += stats["chunks"]
    log.info(f"  합계: {total_collected}건 수집, {total_chunks}건 적재")

    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="실시간 데이터 동기화 파이프라인")
    parser.add_argument("--once", action="store_true", help="1회 실행 후 종료")
    parser.add_argument(
        "--interval", type=float, default=24, help="실행 간격 (시간, 기본: 24)"
    )
    args = parser.parse_args()

    if args.once:
        log.info("1회 동기화 시작")
        sync_all()
        return

    interval_sec = args.interval * 3600
    log.info(f"스케줄러 시작 (간격: {args.interval}시간)")

    while _running:
        sync_all()
        log.info(f"다음 실행까지 {args.interval}시간 대기...")

        waited = 0
        while waited < interval_sec and _running:
            time.sleep(min(10, interval_sec - waited))
            waited += 10

    log.info("스케줄러 종료")


if __name__ == "__main__":
    main()
