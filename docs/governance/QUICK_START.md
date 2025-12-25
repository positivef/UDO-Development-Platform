# 🚀 거버넌스 시스템 Quick Start

> **소요 시간**: 5분  
> **전제 조건**: Python 3.13+, Git

---

## 1. 설치 확인

Pre-commit이 이미 설치되어 있습니다:

```bash
# 상태 확인
.venv\Scripts\pre-commit.exe --version
```

---

## 2. 자동 검증 작동 방식

### 커밋 시 (1-3초)
```bash
git add .
git commit -m "feat: 새 기능"

# 자동 실행되는 검사:
# ✅ Black (Python 포맷팅)
# ✅ Flake8 (구문 오류만)
# ✅ Trailing whitespace
# ✅ YAML/JSON 검증
```

### 푸시 시 (10-30초)
```bash
git push

# 추가 실행되는 검사:
# ✅ 시스템 규칙 검증 (validate_system_rules.py)
# ✅ Full Flake8 (복잡도 포함)
```

---

## 3. 긴급 상황 대처

### 훅 스킵하기
```bash
# 모든 훅 스킵
git commit --no-verify -m "hotfix: 긴급 수정"

# 또는
git push --no-verify
```

### 일시적으로 비활성화
```bash
# 비활성화
.venv\Scripts\pre-commit.exe uninstall

# 다시 활성화
.venv\Scripts\pre-commit.exe install
.venv\Scripts\pre-commit.exe install --hook-type pre-push
```

---

## 4. 수동 실행

```bash
# 모든 파일 검사
.venv\Scripts\pre-commit.exe run --all-files

# 특정 파일만
.venv\Scripts\pre-commit.exe run --files backend/app/main.py
```

---

## 5. 관련 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| 코딩 스타일 | `AGENTS.md` | Python/TS 규칙 |
| 시스템 규칙 | `.claude/RULES.md` | 전체 시스템 규칙 |
| 불확실성 지도 | `src/uncertainty_map_v3.py` | 리스크 분석 |

---

## 6. 문제 해결

### 훅 설치가 안 됐다면
```bash
.venv\Scripts\pre-commit.exe install
.venv\Scripts\pre-commit.exe install --hook-type pre-push
```

### Black 포맷팅 오류
```bash
# 자동 수정
.venv\Scripts\black.exe backend src scripts tests
```

### Flake8 오류
```bash
# 오류 확인
.venv\Scripts\flake8.exe backend src --show-source
```

---

**설정 완료!** 이제 모든 커밋이 자동으로 검증됩니다. 🎉
