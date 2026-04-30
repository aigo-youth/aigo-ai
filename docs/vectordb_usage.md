# vectordb 사용 가이드

## 사전 준비

### 1. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 추가(`.env.example` 참고):

```bash
EMBEDDING_MODEL=
QDRANT_PATH=./db
```

### 2. 의존성 설치

```bash
uv sync
```

---

## 기본 사용법 (전체 흐름)

```python
from app.vectordb import Embedder, QdrantStore

embedder = Embedder()

# 2단계: QdrantStore 만들기 (저장소)
#   - "laws" 는 컬렉션(폴더) 이름입니다. 원하는 이름으로 바꿔주세요
store = QdrantStore("laws", embedder)

# 3단계: 텍스트 저장
store.add_docs(
    texts=[
        "임대인은 임차인에게 보증금을 반환해야 한다.",
        "임차인은 계약 만료 후 목적물을 반환해야 한다.",
    ],
    metadatas=[
        {"source": "주택임대차보호법", "조문": "제3조"},
        {"source": "주택임대차보호법", "조문": "제4조"},
    ],
)

# 4단계: 질문으로 검색
results = store.search("보증금을 돌려받으려면?", top_k=3)

# 5단계: 결과 출력
for r in results:
    print(r["score"], r["text"], r["조문"])
```

---

## 데이터 동기화 파이프라인

국가법령정보 API에서 새 데이터를 자동 수집하고, 청킹 후 벡터DB에 적재하는 통합 파이프라인입니다.

### 전체 흐름

```
국가법령정보 API
  → 목록 조회 (fetch_list)
  → 중복 필터링 (data/meta/collected_ids.json 기반)
  → 상세 조회 (fetch_details)
  → raw 저장 (data/raw/*.jsonl)
  → 청킹 (app/ingest/chunker.py)
  │   ├─ prec(판례): RecursiveCharacterTextSplitter(500, 50)
  │   └─ expc(법령해석례): 질의요지 + 이유 결합 (분할 없음)
  → 벡터DB 적재 (QdrantStore.add_docs)
```

### 실행 방법

```bash
# 1회 실행: 새 데이터만 수집 → 청킹 → 적재
uv run python scripts/sync_data.py --once

# 12시간 간격으로 자동 반복
uv run python scripts/sync_data.py --interval 12

# 기본 24시간 간격 (데몬 모드)
uv run python scripts/sync_data.py
```

- `Ctrl+C`로 안전하게 종료됩니다 (현재 작업 완료 후 종료)
- 컬렉션 이름은 `legal` 고정 (`scripts/sync_data.py`의 `COLLECTION_NAME`)

### 중복 관리

수집된 문서 ID는 `data/meta/collected_ids.json`에 기록됩니다.

```json
{
  "prec": ["615767", "616251", "616581"],
  "expc": ["332741", "333012"]
}
```

- 최초 실행 시 기존 `data/raw/*.jsonl`에서 ID를 자동 추출하여 초기화
- 이후 실행마다 이미 수집된 ID는 스킵
- 벡터DB 적재 성공 후에만 ID를 기록하여 데이터 일관성 보장

### 수동 전체 재빌드

동기화 파이프라인과 별개로, 기존 processed 데이터로 벡터DB를 처음부터 다시 구축할 수도 있습니다.

```bash
# 컬렉션 초기화 후 재구축
uv run python scripts/build_vectorstore.py --reset

# 테스트용 (소스별 10건만)
uv run python scripts/build_vectorstore.py --limit 10 --dry-run
```

---

## 각 단계 자세히 보기

### Embedder — 텍스트 벡터 변환

```python
from app.vectordb import Embedder

# Embedder() 는 팩토리 함수입니다. EMBEDDING_MODEL 환경변수를 읽어 OpenAI 혹은 HuggingFace모델 중 적절한 것을 실행합니다.
embedder = Embedder()
```

> 처음 실행할 때 HFEmbedder는 모델을 다운로드합니다 (수백 MB). 시간이 걸릴 수 있습니다.  
> 두 번째 실행부터는 HuggingFace 캐시를 써서 빠릅니다.  
> OpenAIEmbedder는 API 호출만 하므로 즉시 실행됩니다 (단, `OPENAI_API_KEY` 필요).

**여러 텍스트를 한꺼번에 변환** — 대량 저장할 때 씁니다

```python
texts = ["첫 번째 문장", "두 번째 문장", "세 번째 문장"]
vectors = embedder.embed(texts)

# vectors 는 리스트 안에 리스트입니다
# [[0.1, 0.2, ...], [0.3, 0.4, ...], [0.5, 0.6, ...]]
print(len(vectors))     # 3 (텍스트 개수)
print(len(vectors[0]))  # 384 (벡터 차원 수, 모델마다 다름)
print(embedder.vector_size)  # 384 (현재 모델의 벡터 차원)
```

**텍스트 하나만 변환** — 사용자 질문을 검색할 때 씁니다

```python
vector = embedder.embed_question("보증금을 돌려주지 않으면?")
# [0.12, -0.34, 0.78, ...]  (숫자 384개짜리 리스트, 모델마다 다름)
```

**현재 임베더 타입 확인:**

```python
print(type(embedder).__name__)  # "HFEmbedder" 또는 "OpenAIEmbedder"
print(embedder.vector_size)     # 384 (HFEmbedder) 또는 1536 (OpenAIEmbedder)
```

---

### QdrantStore — 저장하고 검색하기

#### 초기화

```python
from app.vectordb import Embedder, QdrantStore

embedder = Embedder()
store = QdrantStore("laws", embedder)
#                    ↑
#                    컬렉션 이름
```

같은 이름의 컬렉션이 이미 있으면 기존 것을 그대로 씁니다.  
없으면 새로 만듭니다.

**연결 모드 선택:**

- **로컬 모드 (기본)**: `QDRANT_URL` 환경변수 미설정 시, `QDRANT_PATH`에서 로컬 파일 기반 저장소 생성
- **클라우드 모드**: `QDRANT_URL` + `QDRANT_API_KEY` 환경변수 설정 시, Qdrant Cloud에 연결

```python
# .env
# 로컬 모드
QDRANT_PATH=./db

# 클라우드 모드 (이 두 변수 설정 시 자동으로 Cloud 모드 활성화)
QDRANT_URL=https://xxxxx.cloud.qdrant.io
QDRANT_API_KEY=your-api-key
```

이제 `QdrantStore`는 추가 인자 없이 환경변수만으로 모드가 자동 선택됩니다.

---

#### add_docs — 텍스트 저장

```python
store.add_docs(
    texts=["저장할 텍스트1", "저장할 텍스트2"],
    metadatas=[
        {"source": "법령이름", "조문": "제1조"},
        {"source": "법령이름", "조문": "제2조"},
    ]
)
```

- `texts`: 저장할 텍스트 목록입니다. 순서대로 `metadatas`와 짝을 맞춥니다
- `metadatas`: 각 텍스트에 붙일 추가 정보입니다. 나중에 검색 결과와 함께 돌아옵니다
- `metadatas`는 생략할 수 있습니다. 생략하면 빈 딕셔너리로 채워집니다

```python
# metadatas 없이 저장하는 것도 가능
store.add_docs(texts=["짧은 테스트 문장"])
```

> **주의**: 같은 텍스트를 여러 번 저장하면 중복으로 쌓입니다.  
> `sync_data.py`를 사용하면 `collected_ids.json` 기반으로 중복이 자동 방지됩니다.  
> 수동으로 `add_docs`를 호출할 때는 저장소를 초기화하거나 중복을 직접 체크하세요.

---

#### search — 유사한 텍스트 검색

```python
results = store.search("보증금을 못 받았어요", top_k=3)
```

- `query`: 자연어로 검색어를 넣으면 됩니다
- `top_k`: 결과를 몇 개 가져올지 정합니다 (기본값: 5)

**결과 형태**

```python
[
    {
        "score": 0.89,           # 유사도 (1에 가까울수록 관련성 높음)
        "text": "임대인은 보증금을...",  # 저장했던 텍스트
        "source": "주택임대차보호법",   # 저장할 때 넣은 메타데이터
        "조문": "제3조",
    },
    {
        "score": 0.76,
        "text": "임차인은 계약 만료 후...",
        "source": "주택임대차보호법",
        "조문": "제4조",
    },
    ...
]
```

**결과 출력 예시**

```python
results = store.search("보증금 반환", top_k=2)

for r in results:
    print(f"유사도: {r['score']:.2f}")
    print(f"조문: {r.get('조문', '없음')}")
    print(f"내용: {r['text']}")
    print("---")
```

---

## 자주 쓰는 패턴

### 법령 데이터를 한꺼번에 불러와서 저장 (수동 적재)

> 일반적으로는 `sync_data.py`가 수집~적재를 자동 처리합니다.  
> 아래는 커스텀 데이터를 직접 적재해야 할 때 사용하세요.

```python
from app.vectordb import Embedder, QdrantStore

embedder = Embedder()
store = QdrantStore("laws", embedder)

# 미리 준비한 법령 데이터
laws = [
    {"text": "임대인은 보증금을 반환해야 한다.", "source": "주택임대차보호법", "조문": "제3조"},
    {"text": "계약 갱신 요구는 1회에 한해 가능하다.", "source": "주택임대차보호법", "조문": "제6조의3"},
]

texts = [law["text"] for law in laws]
metadatas = [{"source": law["source"], "조문": law["조문"]} for law in laws]

store.add_docs(texts=texts, metadatas=metadatas)
print(f"{len(texts)}개 저장 완료")
```

### 검색 결과에서 텍스트만 뽑기

```python
results = store.search("전월세 전환율")
texts_only = [r["text"] for r in results]
```

### 유사도 기준으로 필터링

```python
results = store.search("보증금 반환", top_k=10)

# 유사도 0.7 이상인 것만 사용
filtered = [r for r in results if r["score"] >= 0.7]
```
