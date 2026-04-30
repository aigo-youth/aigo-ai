import json
from pathlib import Path
from typing import Any, Iterator

# 공통 출력 타입: (text, metadata)
LoadedChunk = tuple[str, dict[str, Any]]


def _iter_jsonl(path: str | Path) -> Iterator[dict[str, Any]]:
  with open(path, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      yield json.loads(line)
      

def load_eflaw(path: str | Path) -> Iterator[LoadedChunk]:
  for row in _iter_jsonl(path):
    text = row.get("text", "")
    if not text:
      continue
    meta = {
      "doc_type": "법령",
      "chunk_id": row.get("chunk_id"),
      "title": row.get("법령명"),
      "source_id": row.get("법령ID"),
      "법령구분명": row.get("법령구분명"),
      "시행일자": row.get("시행일자"),
      "공포일자": row.get("공포일자"),
      "재개정구분명": row.get("제개정구분명"),
      "조문번호": row.get("조문번호_표기"),
      "조문제목": row.get("조문제목"),
    }
    yield text, meta
    

def load_prec(path: str | Path) -> Iterator[LoadedChunk]:
  for row in _iter_jsonl(path):
    text = row.get("embed_text", "")
    if not text:
      continue
    inner = row.get("metadata", {})
    meta =  {
      "doc_type": "판례",
      "chunk_id": inner.get("chunk_index"),
      "title": inner.get("사건명"),
      "source_id": inner.get("판례일련번호"),
      "사건번호": inner.get("사건번호"),
      "선고일자": inner.get("선고일자"),
      "법원명": inner.get("법원명"),
      "판결유형": inner.get("판결유형"),
      "사건종류명": inner.get("사건종류명"),
    }
    yield text, meta
    

def load_expc(path: str | Path) -> Iterator[LoadedChunk]:
  for row in _iter_jsonl(path):
    text = row.get("page_content", "")
    if not text:
      continue
    outer = row.get("metadata", {})
    # 청킹 후 JSONL은 metadata가 이중 중첩됨 (metadata.metadata.안건명)
    inner = outer.get("metadata", outer)
    meta = {
      "doc_type": "법령해석례",
      "chunk_id": inner.get("안건번호"),
      "title": inner.get("안건명"),
      "source_id": inner.get("법령해석례일련번호"),
      "회신일자": inner.get("회신일자"),
    }
    yield text, meta