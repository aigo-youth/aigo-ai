# Git 협업 전략 문서

## 브랜치 전략

### 브랜치 구조

- `main`: 프로덕션 배포 브랜치 (직접 수정 금지)
- `{type}/{feature}`: 개인 작업 브랜치

### 브랜치 명명 규칙

```
{type}/{feature}
```

- 소문자로 작성
- feature에는 현재 자신이 하고 있는 작업을 간단하게 작성

---

## 작업 흐름 (처음부터 끝까지)

> 처음 Git을 사용하는 분들을 위해 전체 흐름을 순서대로 정리했습니다.

### 1단계: 작업 시작 전 — main 최신화

새 작업을 시작하기 전에 항상 main 브랜치를 최신 상태로 가져옵니다.

```bash
git checkout main
git pull origin main
```

### 2단계: 작업 브랜치 생성

main에서 새 브랜치를 만들고 이동합니다.

```bash
git checkout -b feat/login
```

### 3단계: 작업 및 커밋

파일을 수정한 후 커밋합니다.

```bash
git add 파일명
git commit -m "feat: 로그인 기능 구현"
```

### 4단계: push 전 충돌 예방 — main 변경사항 반영

push하기 전에 다른 팀원이 main에 올린 변경사항을 내 브랜치에 반영합니다.

```bash
git checkout main
git pull origin main
git checkout feat/login
git merge main
```

### 5단계: push 전 보안 체크 (필수)

push 전에 아래 항목을 반드시 확인하세요.

#### `.env` 파일 확인

#### `.env.example` 업데이트

`.env`에 새로운 키를 추가했다면 `.env.example`도 함께 업데이트합니다.

### 6단계: 원격 브랜치에 push

```bash
git push origin feat/login
```

### 7단계: Pull Request 생성

GitHub에서 PR을 생성합니다.

- base: `main` ← compare: `feat/login`
- PR 템플릿에 맞게 내용 작성
- Reviewers에 팀원 최소 1명 지정

### 8단계: 리뷰 반영 및 Merge

- 리뷰 요청사항을 반영해 커밋 후 push
- 승인 후 Merge

### 9단계: 브랜치 삭제 (Merge 직후 바로)

Merge 완료 후 작업 브랜치는 바로 삭제합니다. 브랜치를 오래 두면 충돌 가능성이 높아집니다.

GitHub에서 PR 완료 후 "Delete branch" 버튼 클릭, 또는:

```bash
# 원격 브랜치 삭제
git push origin --delete feat/login

# 로컬 브랜치 삭제
git checkout main
git branch -d feat/login
```

### 10단계: 다음 작업 전 main 재최신화

```bash
git checkout main
git pull origin main
```

---

## 커밋 컨벤션

### type 목록

| 타입     | 상황                          |
| -------- | ----------------------------- |
| feat     | 새로운 기능 추가              |
| fix      | 버그 수정                     |
| docs     | README, 주석 등 문서 수정     |
| refactor | 기능 변경 없이 코드 구조 개선 |
| chore    | 패키지 설치, 설정 파일 수정   |
| style    | 코드 포맷, 린트 수정          |

### 커밋 메시지 작성 예시

```
feat: 사용자 로그인 API 구현
fix: 회원가입 유효성 검증 오류 수정
chore: Prettier 설정 추가
docs: README에 설치 가이드 추가
```

- 커밋 메시지는 말머리(type) 제외 한글로 작성
- 제목은 50자 이내로 간결하게

---

## Pull Request 프로세스

### PR 생성 규칙

1. **제목 형식**: 커밋 컨벤션과 동일 (`feat:`, `fix:` 등)
2. **Reviewers**: 팀원 최소 1명 이상의 리뷰 필수
3. **Merge 조건**: 최소 1명 이상의 Approve 필요

### Merge 후 할 일

- [ ] GitHub에서 "Delete branch" 클릭
- [ ] 로컬에서 브랜치 삭제 (`git branch -d 브랜치명`)
- [ ] `git checkout main && git pull origin main`으로 최신화

---

## 금지 사항

```
❌ main 브랜치에 직접 push
❌ 타인의 브랜치 직접 수정
❌ force push (git push -f) 사용
❌ 대용량 파일 커밋 (100MB 이상)
❌ .env 파일 커밋
❌ API 키, 비밀번호 하드코딩
❌ Merge 후 브랜치 방치
```

이 문서는 팀 상황에 맞춰 지속적으로 업데이트됩니다.
