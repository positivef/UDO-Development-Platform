# UDO Documentation Rules System v2.0 (Complete)

**Created**: 2025-12-15
**Status**: Complete - Ready for Implementation
**Scope**: docs/ + claudedocs/ + Obsidian Integration

---

## 1. Executive Summary

### 1.1 Problem Statement
- 기존 docs/ 폴더에 171개 파일이 11개 서브폴더에 분산
- claudedocs/와 docs/ 간 역할 구분 불명확
- AI 생성 문서와 Human 작성 문서 혼재
- Obsidian 동기화 규칙과 문서화 규칙 미연계

### 1.2 Solution: 3-Layer Documentation System

```
┌─────────────────────────────────────────────────────────────────┐
│                    UDO Documentation System                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: docs/              → Human-facing (영구 보존)          │
│  Layer 2: claudedocs/        → AI-generated (세션 기반)          │
│  Layer 3: Obsidian Vault     → Knowledge Asset (지식 자산)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: docs/ - Human-Facing Documentation

### 2.1 현재 구조 (유지)

```
docs/
├── analysis/           # 설계 검토, 성능 분석, 전략 분석
├── architecture/       # 시스템 아키텍처 문서
├── features/           # 기능별 상세 문서
│   ├── ai-collaboration/
│   ├── gi-ck/
│   ├── kanban/
│   ├── obsidian/
│   ├── time-tracking/
│   ├── udo/
│   └── uncertainty/
├── guides/             # 사용자/개발자 가이드
│   └── development/
├── PRDs/               # Product Requirements
│   ├── 01_RAW/
│   ├── 03_FINAL/
│   └── 04_DRAFT/
├── sessions/           # 세션 관련 (→ claudedocs로 이동 대상)
│   ├── progress/
│   └── worklogs/
├── templates/          # 문서 템플릿
├── Obsidian/           # Obsidian 관련 가이드
└── _ARCHIVE/           # 폐기된 문서
```

### 2.2 폴더별 규칙

| 폴더 | 용도 | 작성자 | 수명 | Obsidian 동기화 |
|------|------|--------|------|-----------------|
| `analysis/` | 설계 검토, 전략 분석 | Human/Hybrid | 영구 | ✅ 분석 완료 시 |
| `architecture/` | 시스템 아키텍처 | Human | 영구 | ✅ 변경 시 |
| `features/{name}/` | 기능별 상세 문서 | Human/Hybrid | 영구 | ✅ 릴리즈 시 |
| `guides/` | 사용자/개발 가이드 | Human | 영구 | ✅ 업데이트 시 |
| `guides/development/` | 개발 프로세스 가이드 | Human | 영구 | ✅ 워크플로우 변경 시 |
| `PRDs/` | 제품 요구사항 | Human | 영구 | ✅ 승인 시 |
| `PRDs/01_RAW/` | 초기 PRD 초안 | Human/AI | 임시 | ❌ |
| `PRDs/03_FINAL/` | 최종 승인 PRD | Human | 영구 | ✅ |
| `PRDs/04_DRAFT/` | 검토 중 PRD | Human/AI | 임시 | ❌ |
| `templates/` | 문서 템플릿 | Human | 영구 | ❌ |
| `Obsidian/` | Obsidian 가이드 | Human | 영구 | ✅ |
| `_ARCHIVE/` | 폐기 문서 | - | 아카이브 | ❌ |

### 2.3 sessions/ 폴더 마이그레이션 계획

**현재 문제**: `docs/sessions/` 폴더가 AI 생성 콘텐츠와 세션 기반 문서를 포함

**해결 방안**:
```
docs/sessions/progress/WEEK*.md  → claudedocs/completion/
docs/sessions/worklogs/*.md      → claudedocs/worklog/
docs/sessions/CURRENT_*.md       → claudedocs/worklog/
```

**마이그레이션 후 폴더 제거**: `docs/sessions/` 삭제

---

## 3. Layer 2: claudedocs/ - AI-Generated Documentation

### 3.1 구조

```
claudedocs/
├── analysis/      # 코드/아키텍처 분석 리포트
├── completion/    # 마일스톤 완료 요약
├── decisions/     # 결정 기록 (ADR)
├── worklog/       # 일일/주간 작업 로그
└── whiteboard/    # 초안, 탐색, 브레인스토밍
```

### 3.2 폴더별 규칙

| 폴더 | 용도 | 보존 기간 | Obsidian 동기화 | 파일명 규칙 |
|------|------|-----------|-----------------|-------------|
| `analysis/` | 분석 리포트 | 90일 | ✅ 완료 시 | `YYYY-MM-DD-{TOPIC}-ANALYSIS.md` |
| `completion/` | 완료 요약 | 영구 | ✅ 즉시 | `YYYY-MM-DD-{MILESTONE}-COMPLETE.md` |
| `decisions/` | 결정 기록 | 영구 | ✅ 즉시 | `YYYY-MM-DD-ADR-{NNN}-{TITLE}.md` |
| `worklog/` | 작업 로그 | 30일 | ✅ 일일 | `YYYY-MM-DD-worklog.md` |
| `whiteboard/` | 초안/탐색 | 7일 | ❌ | `draft-{topic}.md` |

### 3.3 AI 자동 분류 로직

```python
def classify_ai_document(doc_type: str, content_summary: str) -> str:
    """
    AI가 문서를 생성할 때 자동으로 폴더를 결정하는 로직
    """
    # Pattern matching
    patterns = {
        "analysis": ["분석", "analysis", "review", "검토", "assessment"],
        "completion": ["완료", "complete", "done", "finished", "milestone"],
        "decisions": ["결정", "decision", "ADR", "선택", "채택"],
        "worklog": ["작업", "work", "today", "오늘", "진행"],
        "whiteboard": ["초안", "draft", "탐색", "explore", "idea"]
    }

    for folder, keywords in patterns.items():
        if any(kw in content_summary.lower() for kw in keywords):
            return f"claudedocs/{folder}/"

    return "claudedocs/whiteboard/"  # Default
```

---

## 4. Layer 3: Obsidian Integration

### 4.1 동기화 대상 매핑

```
┌─────────────────────────────────────────────────────────────────────┐
│                  GitHub → Obsidian 동기화 매핑                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  docs/architecture/*        → Obsidian/3-Areas/UDO/Architecture/    │
│  docs/features/{name}/*     → Obsidian/3-Areas/UDO/Features/{name}/ │
│  docs/analysis/*            → Obsidian/3-Areas/UDO/Analysis/        │
│  docs/guides/*              → Obsidian/3-Areas/UDO/Guides/          │
│  docs/PRDs/03_FINAL/*       → Obsidian/3-Areas/UDO/PRDs/            │
│                                                                      │
│  claudedocs/completion/*    → Obsidian/개발일지/YYYY-MM-DD/          │
│  claudedocs/worklog/*       → Obsidian/개발일지/YYYY-MM-DD/          │
│  claudedocs/decisions/*     → Obsidian/4-Resources/Decisions/       │
│  claudedocs/analysis/*      → Obsidian/3-Areas/UDO/Analysis/        │
│                                                                      │
│  ❌ NOT synced:                                                      │
│  - claudedocs/whiteboard/*  (임시 문서)                              │
│  - docs/PRDs/01_RAW/*       (초안)                                   │
│  - docs/PRDs/04_DRAFT/*     (검토 중)                                │
│  - docs/templates/*         (템플릿)                                 │
│  - docs/_ARCHIVE/*          (폐기)                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 동기화 트리거 조건

기존 OBSIDIAN_SYNC_RULES.md 확장:

```yaml
# 자동 동기화 트리거
sync_triggers:
  # 문서 유형별 트리거
  completion_summary:
    trigger: "마일스톤 완료 시"
    source: "claudedocs/completion/"
    target: "개발일지/YYYY-MM-DD/"
    immediate: true

  worklog:
    trigger: "작업 세션 종료 시"
    source: "claudedocs/worklog/"
    target: "개발일지/YYYY-MM-DD/"
    immediate: true

  architecture_change:
    trigger: "아키텍처 문서 변경 시"
    source: "docs/architecture/"
    target: "3-Areas/UDO/Architecture/"
    requires_review: true

  feature_release:
    trigger: "기능 릴리즈 시"
    source: "docs/features/{name}/"
    target: "3-Areas/UDO/Features/{name}/"
    requires_review: true

  decision_record:
    trigger: "ADR 작성 시"
    source: "claudedocs/decisions/"
    target: "4-Resources/Decisions/"
    immediate: true
```

### 4.3 Obsidian 지식 자산 구조

```
Obsidian Vault/
├── 개발일지/
│   └── YYYY-MM-DD/
│       ├── {작업명}.md          # claudedocs/worklog + completion
│       └── ...
├── 3-Areas/
│   └── UDO/
│       ├── Architecture/        # docs/architecture/
│       ├── Features/            # docs/features/
│       │   ├── kanban/
│       │   ├── uncertainty/
│       │   └── ...
│       ├── Analysis/            # docs/analysis/ + claudedocs/analysis/
│       ├── Guides/              # docs/guides/
│       └── PRDs/                # docs/PRDs/03_FINAL/
├── 4-Resources/
│   ├── Decisions/               # claudedocs/decisions/
│   └── Knowledge-Base/
│       └── Knowledge-Dashboard.md
└── 5-MOCs/
    └── UDO-MOC.md               # Master index
```

---

## 5. Complete Decision Tree

### 5.1 문서 생성 시 폴더 결정

```
┌─────────────────────────────────────────────────────────────────┐
│                    새 문서 생성 결정 트리                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │     작성자가 누구인가?         │
              └───────────────────────────────┘
                     /              \
                    /                \
                   ▼                  ▼
          ┌─────────────┐      ┌─────────────┐
          │    Human    │      │  AI (Claude)│
          └─────────────┘      └─────────────┘
                 │                     │
                 ▼                     ▼
    ┌────────────────────┐   ┌────────────────────┐
    │    문서 유형?       │   │    문서 유형?       │
    └────────────────────┘   └────────────────────┘
           │                        │
    ┌──────┼──────┐          ┌──────┼──────┐
    ▼      ▼      ▼          ▼      ▼      ▼
 Guide  Feature  PRD      Analysis Work  Decision
   │      │       │          │      │      │
   ▼      ▼       ▼          ▼      ▼      ▼
docs/   docs/   docs/    claude  claude claude
guides/ features PRDs/   docs/   docs/  docs/
                         analysis worklog decisions
```

### 5.2 Quick Reference Table (완전판)

| 문서 유형 | 작성자 | 위치 | 파일명 | Obsidian | 보존 |
|-----------|--------|------|--------|----------|------|
| 사용자 가이드 | Human | `docs/guides/` | `{topic}.md` | ✅ | 영구 |
| 개발 가이드 | Human | `docs/guides/development/` | `{topic}.md` | ✅ | 영구 |
| 기능 문서 | Human | `docs/features/{name}/` | `{FEATURE}_*.md` | ✅ | 영구 |
| 아키텍처 | Human | `docs/architecture/` | `*_ARCHITECTURE*.md` | ✅ | 영구 |
| PRD 초안 | Human/AI | `docs/PRDs/01_RAW/` | `PRD_*_RAW.md` | ❌ | 임시 |
| PRD 최종 | Human | `docs/PRDs/03_FINAL/` | `PRD_*_FINAL.md` | ✅ | 영구 |
| 설계 분석 | Human | `docs/analysis/` | `*_REVIEW.md` | ✅ | 영구 |
| 코드 분석 | AI | `claudedocs/analysis/` | `YYYY-MM-DD-*-ANALYSIS.md` | ✅ | 90일 |
| 완료 요약 | AI | `claudedocs/completion/` | `YYYY-MM-DD-*-COMPLETE.md` | ✅ | 영구 |
| 결정 기록 | AI | `claudedocs/decisions/` | `YYYY-MM-DD-ADR-*.md` | ✅ | 영구 |
| 작업 로그 | AI | `claudedocs/worklog/` | `YYYY-MM-DD-worklog.md` | ✅ | 30일 |
| 초안/탐색 | AI | `claudedocs/whiteboard/` | `draft-*.md` | ❌ | 7일 |

---

## 6. docs/ vs claudedocs/ 구분 기준 (최종)

### 6.1 핵심 원칙

```
┌─────────────────────────────────────────────────────────────────┐
│                    docs/ vs claudedocs/ 구분                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  docs/                          claudedocs/                      │
│  ─────                          ───────────                      │
│  • Human 작성 또는 승인          • AI 자동 생성                   │
│  • 영구 보존                     • 세션/기간 기반 보존             │
│  • 사용자/개발자 대상            • 내부 추적/분석 용도             │
│  • 버전 관리 중요               • 스냅샷 성격                     │
│  • 구조화된 폴더                • 시간 기반 정리                   │
│                                                                  │
│  중복 해소:                                                       │
│  ─────────                                                       │
│  docs/analysis/     = Human 주도 설계 검토 (Design Review)       │
│  claudedocs/analysis/ = AI 자동 분석 리포트 (Code Analysis)      │
│                                                                  │
│  docs/sessions/progress/ → claudedocs/completion/ (마이그레이션) │
│  docs/sessions/worklogs/ → claudedocs/worklog/ (마이그레이션)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 경계 케이스 처리

| 케이스 | 결정 | 근거 |
|--------|------|------|
| AI가 작성한 기능 문서 | `docs/features/` + `author: hybrid` | 영구 보존 필요 |
| Human이 요청한 분석 | `claudedocs/analysis/` | AI 생성물, 임시성 |
| 마일스톤 완료 요약 | `claudedocs/completion/` | AI 생성, 세션 기반 |
| 아키텍처 변경 기록 | `docs/architecture/` | 영구 보존, Human 검토 필요 |
| 일일 작업 로그 | `claudedocs/worklog/` | AI 생성, 30일 보존 |
| PRD 초안 (AI 생성) | `docs/PRDs/01_RAW/` | PRD 워크플로우 유지 |

---

## 7. Frontmatter 표준 (확장)

### 7.1 필수 필드

```yaml
---
title: "문서 제목"
created: "2025-12-15"
author: "human" | "claude" | "hybrid"
status: "draft" | "review" | "stable" | "deprecated"
---
```

### 7.2 Layer별 추가 필드

**docs/ 문서**:
```yaml
---
title: "Kanban Integration Guide"
created: "2025-12-15"
updated: "2025-12-15"
author: "human"
status: "stable"
category: "guide"           # guide | feature | architecture | analysis | prd
feature: "kanban"           # 관련 기능 (features/ 하위일 경우)
version: "1.0"
tags:
  - kanban
  - integration
obsidian_sync: true         # Obsidian 동기화 대상 여부
obsidian_path: "3-Areas/UDO/Features/kanban/"  # Obsidian 대상 경로
---
```

**claudedocs/ 문서**:
```yaml
---
title: "Week 1 Day 2 Completion Summary"
created: "2025-12-15"
author: "claude"
status: "stable"
category: "completion"      # analysis | completion | decision | worklog | whiteboard
ai_model: "claude-opus-4.5"
session_id: "abc123"
confidence: 95              # AI 신뢰도 (0-100)
retention_days: null        # null = 영구, 숫자 = 해당 일수 후 삭제
obsidian_sync: true
obsidian_path: "개발일지/2025-12-15/"
milestone: "Week 1 Day 2"
completion_percentage: 100
---
```

---

## 8. 실행 가능한 AI 규칙

### 8.1 문서 생성 전 체크리스트

```python
def pre_document_creation_check():
    """
    문서 생성 전 AI가 수행해야 할 체크리스트
    """
    checklist = [
        "1. 문서 유형 결정 (분석/완료/결정/작업로그/초안)",
        "2. 작성자 결정 (human/claude/hybrid)",
        "3. 폴더 결정 (docs/ vs claudedocs/)",
        "4. 파일명 규칙 확인",
        "5. Frontmatter 템플릿 준비",
        "6. Obsidian 동기화 대상 여부 확인"
    ]
    return checklist
```

### 8.2 문서 생성 후 체크리스트

```python
def post_document_creation_check():
    """
    문서 생성 후 AI가 수행해야 할 체크리스트
    """
    checklist = [
        "1. Frontmatter 검증 (필수 필드 존재)",
        "2. 파일 위치 검증 (규칙 준수)",
        "3. Obsidian 동기화 트리거 확인",
        "4. 관련 MOC/인덱스 업데이트 필요 여부"
    ]
    return checklist
```

### 8.3 Quick Decision Script

```python
def decide_document_location(
    author: str,           # "human" | "claude" | "hybrid"
    doc_type: str,         # "guide" | "feature" | "analysis" | "completion" | etc.
    is_permanent: bool,    # 영구 보존 필요 여부
    needs_review: bool     # Human 검토 필요 여부
) -> tuple[str, str]:      # (folder_path, obsidian_path)
    """
    문서 위치 결정 로직
    """

    # Human 작성 또는 영구 보존 필요 → docs/
    if author == "human" or (is_permanent and needs_review):
        if doc_type == "guide":
            return ("docs/guides/", "3-Areas/UDO/Guides/")
        elif doc_type == "feature":
            return ("docs/features/{name}/", "3-Areas/UDO/Features/{name}/")
        elif doc_type == "architecture":
            return ("docs/architecture/", "3-Areas/UDO/Architecture/")
        elif doc_type == "analysis":
            return ("docs/analysis/", "3-Areas/UDO/Analysis/")
        elif doc_type == "prd":
            return ("docs/PRDs/", "3-Areas/UDO/PRDs/")

    # AI 생성 → claudedocs/
    if author == "claude":
        if doc_type == "analysis":
            return ("claudedocs/analysis/", "3-Areas/UDO/Analysis/")
        elif doc_type == "completion":
            return ("claudedocs/completion/", "개발일지/{date}/")
        elif doc_type == "decision":
            return ("claudedocs/decisions/", "4-Resources/Decisions/")
        elif doc_type == "worklog":
            return ("claudedocs/worklog/", "개발일지/{date}/")
        elif doc_type == "whiteboard":
            return ("claudedocs/whiteboard/", None)  # No sync

    # Default
    return ("claudedocs/whiteboard/", None)
```

---

## 9. Obsidian 동기화 실행 규칙

### 9.1 자동 동기화 트리거

```python
def should_sync_to_obsidian(doc_path: str, frontmatter: dict) -> bool:
    """
    Obsidian 동기화 여부 결정
    """
    # Frontmatter에 명시된 경우 우선
    if "obsidian_sync" in frontmatter:
        return frontmatter["obsidian_sync"]

    # 폴더별 기본 규칙
    no_sync_folders = [
        "claudedocs/whiteboard/",
        "docs/PRDs/01_RAW/",
        "docs/PRDs/04_DRAFT/",
        "docs/templates/",
        "docs/_ARCHIVE/"
    ]

    for folder in no_sync_folders:
        if folder in doc_path:
            return False

    return True  # 나머지는 동기화
```

### 9.2 동기화 실행 스크립트

```python
async def sync_document_to_obsidian(
    source_path: str,
    obsidian_target_path: str,
    frontmatter: dict
):
    """
    GitHub → Obsidian 동기화 실행
    """
    # 1. 소스 파일 읽기
    content = read_file(source_path)

    # 2. Obsidian 경로 생성
    if "{date}" in obsidian_target_path:
        obsidian_target_path = obsidian_target_path.replace(
            "{date}",
            frontmatter.get("created", datetime.now().strftime("%Y-%m-%d"))
        )

    # 3. MCP를 통한 Obsidian 업데이트
    await mcp__obsidian__obsidian_append_content(
        filepath=obsidian_target_path + "/" + Path(source_path).name,
        content=content
    )

    # 4. 동기화 로그 기록
    log_sync_event(source_path, obsidian_target_path)
```

---

## 10. 마이그레이션 계획

### 10.1 Phase 1: 즉시 실행 (완료)

- [x] claudedocs/ 서브폴더 생성 (analysis, completion, decisions, worklog, whiteboard)
- [x] 기존 claudedocs/ 파일 재배치
- [x] 규칙 문서 작성

### 10.2 Phase 2: docs/sessions/ 마이그레이션

```bash
# 실행 예정
mv docs/sessions/progress/WEEK*.md claudedocs/completion/
mv docs/sessions/worklogs/*.md claudedocs/worklog/
mv docs/sessions/CURRENT_*.md claudedocs/worklog/
# sessions/ 폴더 삭제 후 .gitkeep 대체
```

### 10.3 Phase 3: Frontmatter 추가

모든 기존 docs/ 문서에 표준 Frontmatter 추가 (자동화 스크립트 필요)

### 10.4 Phase 4: Obsidian MOC 업데이트

- UDO-MOC.md 생성/업데이트
- 각 영역별 인덱스 페이지 생성

---

## 11. 검증 체크리스트

### 11.1 규칙 준수 검증

- [ ] 모든 AI 생성 문서가 claudedocs/에 위치
- [ ] 모든 Human 문서가 docs/에 위치
- [ ] 모든 문서에 유효한 Frontmatter 존재
- [ ] Obsidian 동기화 대상 문서 정상 동기화
- [ ] 보존 기간 초과 문서 자동 정리

### 11.2 예외 처리

| 예외 상황 | 처리 방법 |
|-----------|-----------|
| Frontmatter 누락 | Pre-commit hook에서 거부 |
| 잘못된 폴더 배치 | AI 자동 수정 제안 |
| Obsidian 동기화 실패 | 재시도 3회 후 알림 |
| 파일명 규칙 위반 | Pre-commit hook에서 경고 |

---

## 12. Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AI DOCUMENTATION QUICK GUIDE v2.0                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📁 문서 유형별 위치                                                  │
│  ─────────────────                                                   │
│  코드 분석 리포트      → claudedocs/analysis/                        │
│  마일스톤 완료 요약    → claudedocs/completion/                       │
│  결정 기록 (ADR)       → claudedocs/decisions/                       │
│  일일 작업 로그        → claudedocs/worklog/                         │
│  초안/탐색             → claudedocs/whiteboard/                      │
│                                                                      │
│  ⚠️  docs/에 생성 금지 (Human 요청 시만 예외)                         │
│                                                                      │
│  📝 파일명 규칙                                                       │
│  ─────────────                                                       │
│  분석: YYYY-MM-DD-{TOPIC}-ANALYSIS.md                                │
│  완료: YYYY-MM-DD-{MILESTONE}-COMPLETE.md                            │
│  결정: YYYY-MM-DD-ADR-{NNN}-{TITLE}.md                               │
│  로그: YYYY-MM-DD-worklog.md                                         │
│  초안: draft-{topic}.md                                              │
│                                                                      │
│  🔄 Obsidian 동기화                                                   │
│  ────────────────                                                    │
│  completion/ → 개발일지/YYYY-MM-DD/                                  │
│  worklog/    → 개발일지/YYYY-MM-DD/                                  │
│  decisions/  → 4-Resources/Decisions/                                │
│  analysis/   → 3-Areas/UDO/Analysis/                                 │
│  whiteboard/ → ❌ 동기화 안함                                         │
│                                                                      │
│  ✅ 필수 Frontmatter                                                  │
│  ─────────────────                                                   │
│  ---                                                                 │
│  title: "..."                                                        │
│  created: "YYYY-MM-DD"                                               │
│  author: "claude"                                                    │
│  status: "stable"                                                    │
│  category: "completion"                                              │
│  obsidian_sync: true                                                 │
│  obsidian_path: "개발일지/2025-12-15/"                               │
│  ---                                                                 │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-15 | Claude | 초기 버전 (claudedocs 중심) |
| 2.0 | 2025-12-15 | Claude | 완전판 (docs/ + claudedocs/ + Obsidian 통합) |

---

**Status**: ✅ **COMPLETE** - Ready for Implementation
