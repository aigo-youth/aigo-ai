from typing import Any, Literal

import os
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"
oc = os.environ["OC"]

def api(
  oc: str = oc,
  target: str = "eflaw",
  response_type: Literal["JSON", "HTML"] = "JSON",
  params: dict[str, Any] | None = None,
  timeout: int = 30,
) -> dict[str, Any]:
  """
  국가 법령 정보 공동활용 사이트 api 호출 함수
  자세한 가이드라인은 [https://open.law.go.kr/LSO/openApi/guideList.do#] 참고
  
  Args:
    oc: 발급받은 API 인증키
    target: API 서비스 대상
    response_type: 응답 형식("HTML" 또는 "JSON" -> default: JSON
    params: 추가 쿼리 파라미터(선택)
    timeout: 요청 타임아웃
    
  Returns:
    파싱된 JSON 응답 dict
  """
  require_params = {
    "OC": oc,
    "type": response_type,
    "target": target,
    **(params or {})
  }
  
  response = requests.get(_BASE_URL, params=require_params, timeout=timeout)
  response.raise_for_status()
  
  if response_type == "JSON":
    return response.json()
  return response.text