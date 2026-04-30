import json
import math
import time
from typing import Any, Literal
from pathlib import Path

from .api import api

_RAW_DIR = Path(__file__).parents[2] / "data" / "raw"


def fetch_list(
  target: str,
  query: str,
  max_items: int | None = None,
  extra_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
  """
  목록 조회 API 호출 + pagination 자동 처리

  Args:
    target: 데이터 소스 (eflaw, prec, expc, acr)
    query: 검색 질의어
    max_items: 최대 수집 건수 (None=전체)
    extra_params: 추가 쿼리 파라미터 (예: {"search": 2} for 본문검색)

  Returns:
    수집된 항목 리스트
  """
  display = 100
  base = {"display": display, "query": query, **(extra_params or {})}

  first = api(target=target, service="search", params={**base, "page": 1})
  total_cnt = int(_get_root(first, target).get("totalCnt", 0))
  total_pages = math.ceil(total_cnt / display)

  items: list[dict[str, Any]] = _extract_list_items(first, target)
  for page in range(2, total_pages + 1):
    resp = api(target=target, service="search", params={**base, "page": page})
    items.extend(_extract_list_items(resp, target))

  return items[:max_items] if max_items else items
  

def fetch_details(
  target: str,
  items: list[dict[str, Any]],
  id_field: str,
  response_type: Literal["JSON", "HTML"] = "JSON",
  delay: float = 0.5,
) -> list[dict[str, Any]]:
  """
  목록 항목별로 본문 조회 후 목록 메타데이터와 병합하여 반환

  Args:
    target: 데이터 소스 (acr, prec, expc, eflaw)
    items: fetch_list() 결과
    id_field: 본문 조회에 사용할 ID 필드명 (예: "결정문일련번호")
    response_type: 본문 응답 형식 ("HTML" or "JSON")
    delay: 요청 간 대기 시간(초) - 서버 과부하 방지

  Returns:
    목록 메타데이터 + 본문 내용이 합쳐진 레코드 리스트
  """
  results = []
  for item in items:
    doc_id = str(item.get(id_field, ""))
    if not doc_id:
      continue
    body = api(target=target, service="detail", response_type=response_type, params={"ID": doc_id})
    results.append({**item, "본문": body})
    time.sleep(delay)
  return results


def save_raw(
  records: list[dict[str, Any]],
  target: str,
  mode: str = "a",
) -> Path:
  """
  수집한 raw data를 data/raw/{target}.jsonl에 저장

  Args:
    records: fetch_details() 결과
    target: 파일명 구분용 (eflaw, prec, expc, acr)
    mode: 'a'=추가, 'w'=덮어쓰기

  Returns:
      저장된 파일 경로
  """
  _RAW_DIR.mkdir(parents=True, exist_ok=True)
  path = _RAW_DIR / f"{target}.jsonl"
  
  with open(path, mode, encoding="utf-8") as f:
    for record in records:
      f.write(json.dumps(record, ensure_ascii=False) + "\n")
      
  return path


def _get_root(response: dict, target: str) -> dict:
  key_map = {
    "eflaw": "LawSearch",
    "prec":  "PrecSearch",
    "expc":  "Expc",
    "acr":   "Acr",
  }
  return response.get(key_map.get(target, ""), response)


def _extract_list_items(response: dict, target: str) -> list[dict]:
  root = _get_root(response, target)
  # 각 target의 실제 응답 items 키: eflaw=law, prec=prec, expc=expc, acr=acr
  items = root.get("law", root.get("prec", root.get("expc", root.get("acr", []))))
  if isinstance(items, dict):
    items = [items]
  return items if isinstance(items, list) else []
