from typing import Any, Literal

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

_SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"
_SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do"
oc = os.environ["OC"]

_retry_strategy = Retry(
  total=3,
  backoff_factor=2,        # 재시도 간격: 2s, 4s, 8s
  status_forcelist=[429, 500, 502, 503, 504],
)
_adapter = HTTPAdapter(max_retries=_retry_strategy)
_session = requests.Session()
_session.mount("http://", _adapter)


def api(
  oc: str = oc,
  target: str = "eflaw",
  service: Literal["search", "detail"] = "search",
  response_type: Literal["JSON", "HTML"] = "JSON",
  params: dict[str, Any] | None = None,
  timeout: int = 60,
) -> dict[str, Any]:
  """
  국가 법령 정보 공동활용 사이트 api 호출 함수
  자세한 가이드라인은 [https:// open.law.go.kr/LSO/openApi/guideList.do#] 참고

  Args:
    oc: 발급받은 API 인증키
    target: API 서비스 대상 (eflaw, prec, expc, acr)
    service: "search"=목록 조회(lawSearch.do), "detail"=본문 조회(lawService.do)
    response_type: 응답 형식("HTML" 또는 "JSON") -> default: JSON
    params: 추가 쿼리 파라미터(선택)
    timeout: 요청 타임아웃 (초)

  Returns:
    파싱된 JSON 응답 dict
  """
  url = _SERVICE_URL if service == "detail" else _SEARCH_URL
  require_params = {
    "OC": oc,
    "type": response_type,
    "target": target,
    **(params or {})
  }

  response = _session.get(url, params=require_params, timeout=timeout)
  response.raise_for_status()

  if response_type == "JSON":
    return response.json()
  return response.text