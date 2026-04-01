# 국가법령정보 공동활용 API

국가법령정보센터(law.go.kr) Open API를 호출하는 유틸리티 함수입니다.

**공식 가이드**: https://open.law.go.kr/LSO/openApi/guideList.do

---

## 사전 준비

### 1. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 추가:

```
OC=발급받은_인증키
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

---

## `api()` 함수

**위치**: `src/api/api.py`

### 파라미터

| 파라미터        | 타입                 | 기본값           | 설명                |
| --------------- | -------------------- | ---------------- | ------------------- |
| `oc`            | `str`                | `.env`의 `OC` 값 | 발급받은 API 인증키 |
| `target`        | `str`                | `"eflaw"`        | 조회 대상 서비스    |
| `response_type` | `"JSON"` \| `"HTML"` | `"JSON"`         | 응답 형식           |
| `params`        | `dict \| None`       | `None`           | 추가 쿼리 파라미터  |
| `timeout`       | `int`                | `30`             | 요청 타임아웃 (초)  |

### 반환값

- `response_type="JSON"` (기본): `dict` — 파싱된 JSON 응답
- `response_type="HTML"`: `str` — HTML 문자열

---

## 사용 예시

### 기본 호출 — 현행 법령 목록 조회

```python
result = api()
law_search = result["LawSearch"]

print(f"총 결과 수: {law_search['totalCnt']}")
for law in law_search["law"]:
    print(f"[{law['법령구분명']}] {law['법령명한글']}")
```

### 법령명으로 검색

```python
result = api(params={"query": "개인정보", "display": 5})
laws = result["LawSearch"]["law"]

for law in laws:
    print(f"[{law['법령구분명']}] {law['법령명한글']} (시행일: {law['시행일자']})")
```

### 판례 검색

```python
result = api(target="prec", params={"query": "손해배상", "display": 5})
cases = result["PrecSearch"]["prec"]

for case in cases:
    print(f"[{case['사건종류명']}] {case['사건명']} — {case['선고일자']}")
```

### 페이지네이션

```python
# 2페이지, 페이지당 10건
result = api(params={"query": "개인정보", "display": 10, "page": 2})
law_search = result["LawSearch"]

print(f"페이지: {law_search['page']} / 총 {law_search['totalCnt']}건")
```

---

## 응답 구조

```json
{
  "LawSearch": {
    "resultCode": "00",
    "resultMsg": "success",
    "totalCnt": "166440",
    "page": "1",
    "numOfRows": "20",
    "target": "eflaw",
    "law": [
      {
        "법령명한글": "개인정보 보호법",
        "법령구분명": "법률",
        "소관부처명": "개인정보보호위원회",
        "시행일자": "20230915",
        "공포일자": "20230315",
        "현행연혁코드": "현행",
        "법령상세링크": "/DRF/lawService.do?..."
      }
    ]
  }
}
```

---

## 에러 처리

### 에러 유형 정리

| 상황               | 에러                 | 해결 방법                         |
| ------------------ | -------------------- | --------------------------------- |
| `.env`에 `OC` 없음 | `KeyError: 'OC'`     | `.env` 파일에 `OC=인증키` 추가    |
| 잘못된 인증키      | `HTTPError: 400`     | 발급받은 OC 값 재확인             |
| 네트워크 오류      | `ConnectionError`    | 인터넷 연결 확인                  |
| 응답 타임아웃      | `Timeout`            | `timeout` 파라미터 값 증가        |
| API 서버 오류      | `HTTPError: 5xx`     | 잠시 후 재시도                    |
| API 응답 실패      | `resultCode != "00"` | `resultMsg` 확인 후 파라미터 점검 |

### try/except 패턴

```python
import requests

try:
    result = api(params={"query": "개인정보"})
except KeyError:
    # .env에 OC가 없을 때
    print("OC 인증키가 설정되지 않았습니다. .env 파일을 확인하세요.")
except requests.exceptions.Timeout:
    # 타임아웃
    print("요청 시간이 초과됐습니다. timeout 값을 늘리거나 재시도하세요.")
except requests.exceptions.ConnectionError:
    # 네트워크 오류
    print("네트워크 연결에 실패했습니다.")
except requests.exceptions.HTTPError as e:
    # 4xx / 5xx 응답
    print(f"HTTP 오류: {e.response.status_code}")
```

### API 응답 코드 확인

`api()`가 정상 반환되더라도 응답 내 `resultCode`가 실패일 수 있습니다.

```python
result = api(params={"query": "개인정보"})
law_search = result["LawSearch"]

if law_search["resultCode"] != "00":
    print(f"API 오류: {law_search['resultMsg']}")
else:
    laws = law_search["law"]
```

### 주의사항

반환값은 `dict`입니다. `.response()` 같은 메서드는 없습니다.

```python
# 잘못된 예
result = api().response()  # AttributeError

# 올바른 예
result = api()
laws = result["LawSearch"]["law"]
```
