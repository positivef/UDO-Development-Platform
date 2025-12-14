# Documentation Automation System

**Last Updated**: 2025-12-13
**Status**: ✅ Active

---

## Overview

이 시스템은 문서 관리를 완전 자동화하여 세션 간 컨텍스트 연속성을 보장합니다.

### 자동화 수준

| 기능 | 자동화 | 트리거 |
|------|--------|--------|
| 문서 구조 검증 | ✅ | Git pre-commit |
| CURRENT.md 업데이트 | ✅ | 세션 시작/종료 |
| 세션 핸드오프 생성 | ✅ | 세션 종료 |
| Obsidian 동기화 | ✅ | 세션 종료 |
| 링크 유효성 검사 | ✅ | CI/CD |
| 문서 건강 체크 | ✅ | CI/CD |

---

## Quick Start

### 1. Hook 설치 (최초 1회)

```bash
.venv\Scripts\python.exe scripts/install_doc_hooks.py
```

### 2. 세션 시작

```bash
.venv\Scripts\python.exe scripts/session_automation.py start
```

### 3. 작업 중 체크포인트

```bash
.venv\Scripts\python.exe scripts/session_automation.py checkpoint --notes "Feature X 완료"
```

### 4. 세션 종료

```bash
.venv\Scripts\python.exe scripts/session_automation.py end --summary "Kanban UI 구현 완료"
```

---

## 자동 실행되는 것들

### Git Pre-commit Hook

커밋할 때 자동으로:
1. `docs/` 폴더 구조 검증
2. 루트에 허용되지 않은 파일 확인
3. 필수 폴더 존재 확인
4. 내부 링크 유효성 경고

**우회 방법** (권장하지 않음):
```bash
git commit --no-verify
```

### Git Post-commit Hook

커밋 후 자동으로:
- 세션 체크포인트 생성
- 커밋 메시지 기록

### CI/CD (GitHub Actions)

PR/Push 시 자동으로:
- 문서 구조 전체 검증
- CURRENT.md 최신성 체크 (7일 이상 경고)
- 깨진 링크 리포트 생성
- 실패 시 GitHub Issue 자동 생성

---

## 스크립트 설명

### `scripts/check_doc_structure.py`

문서 구조 검증기.

```bash
# 검증만
.venv\Scripts\python.exe scripts/check_doc_structure.py

# 자동 수정 (미구현)
.venv\Scripts\python.exe scripts/check_doc_structure.py --fix
```

**검증 항목**:
- [1/5] 루트 파일 체크 (허용된 파일만)
- [2/5] 필수 폴더 확인
- [3/5] Feature 하위 폴더 확인
- [4/5] 내부 링크 검증
- [5/5] 네이밍 컨벤션

### `scripts/session_automation.py`

세션 생명주기 관리 (v2.0 - 복구 시스템 포함).

```bash
# 세션 시작
.venv\Scripts\python.exe scripts/session_automation.py start

# 체크포인트
.venv\Scripts\python.exe scripts/session_automation.py checkpoint --notes "작업 내용"

# 세션 종료
.venv\Scripts\python.exe scripts/session_automation.py end --summary "완료 요약"

# 상태 확인 (고아 세션 감지)
.venv\Scripts\python.exe scripts/session_automation.py status

# 비정상 종료 복구 (v2.0 NEW)
.venv\Scripts\python.exe scripts/session_automation.py status
```

**자동 수행**:
- CURRENT.md Change Log 업데이트
- 핸드오프 문서 생성 (`docs/sessions/worklogs/`)
- Obsidian 동기화 (`개발일지/` 폴더)

### `scripts/install_doc_hooks.py`

Git hook 설치/제거.

```bash
# 설치
.venv\Scripts\python.exe scripts/install_doc_hooks.py

# 제거
.venv\Scripts\python.exe scripts/install_doc_hooks.py --uninstall
```

---

## 파일 구조

```
scripts/
├── check_doc_structure.py      # 문서 구조 검증
├── session_automation.py       # 세션 자동화
├── install_doc_hooks.py        # Hook 설치
└── install_obsidian_git_hook.py  # 기존 Obsidian hook

.github/workflows/
└── docs-validation.yml         # CI/CD 워크플로우

.git/hooks/
├── pre-commit                  # 문서 검증 hook
└── post-commit                 # 체크포인트 hook

.udo/
└── session_state.json          # 세션 상태 파일
```

---

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `OBSIDIAN_VAULT_PATH` | Obsidian vault 경로 | `C:/Users/user/Documents/Obsidian Vault` |

---

## 트러블슈팅

### Hook이 실행 안 됨

```bash
# 권한 확인
ls -la .git/hooks/pre-commit

# 재설치
.venv\Scripts\python.exe scripts/install_doc_hooks.py
```

### CURRENT.md 업데이트 안 됨

```bash
# 세션 상태 확인
.venv\Scripts\python.exe scripts/session_automation.py status

# 수동 업데이트
# docs/CURRENT.md의 Change Log 섹션 직접 편집
```

### CI/CD 실패

1. GitHub Actions 로그 확인
2. `python scripts/check_doc_structure.py` 로컬 실행
3. 에러 메시지에 따라 수정

---

## 관련 문서

- [SSOT_REGISTRY.md](../SSOT_REGISTRY.md) - 문서 계층 정의
- [CURRENT.md](../CURRENT.md) - 현재 상태
- [README.md](../README.md) - AI 진입점

---

*이 문서는 Level 3 완전 자동화 구현의 일부입니다.*
