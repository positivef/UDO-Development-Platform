# Obsidian Sync MVP Roadmap

**Date**: 2025-12-16
**Status**: Active
**Approach**: MVP-First, Data-Driven Expansion

---

## Current State (Week 2)

### Working Components (Keep As-Is)
```
scripts/
├── obsidian_auto_sync.py      # v2.0 - Git commit → 개발일지
├── obsidian_append.py         # MCP append helper
├── obsidian_3stage_search.py  # 3-tier search
├── obsidian_tag_enforcer.py   # Tag validation
└── install_obsidian_git_hook.py # Git hook installer
```

### Features Already Working
- Git commit → 개발일지 자동 생성
- 시간 추적 (HH:MM 형식)
- YAML frontmatter 자동 생성
- AI 인사이트 추론 (배운 점, 시행착오, 다음 단계)
- 트리거 조건 자동 감지 (3+ 파일, feat:/fix: 메시지)

### External Dependencies: 0
- Python 표준 라이브러리만 사용
- networkx, pandoc, xelatex 불필요

---

## Phase 0: Maintain Current (Now)

**Action**: 변경 없음

**Existing Script**: `scripts/obsidian_auto_sync.py`

```bash
# 현재 동작 확인
python scripts/obsidian_auto_sync.py --commit-hash HEAD
```

**Output**:
```
개발일지/YYYY-MM-DD/Topic.md
├── YAML frontmatter
├── 커밋 정보
├── 변경 파일 목록
├── AI 인사이트 (배운 점, 시행착오, 다음 단계)
└── 시간 추적
```

---

## Phase 1: MVP Single Category (Week 5-6)

**Trigger**: UDO 핵심 기능 완료 후 (Uncertainty UI, Confidence Dashboard)

**Duration**: 5 days

**Goal**: 🌱 Beginner Concepts 단일 카테고리 자동 추출

### Day 1-2: Keyword Extractor
```python
# scripts/knowledge_extractor_mvp.py

BEGINNER_PATTERNS = {
    "함수 분리": ["def ", "function ", "extract", "refactor"],
    "에러 처리": ["try:", "catch", "except", "error"],
    "테스트": ["test_", "describe(", "it(", "pytest"],
    "타입 힌팅": ["->", ": str", ": int", "TypeScript"],
    "API 설계": ["endpoint", "route", "GET", "POST"],
}

def extract_concepts(commit_diff: str) -> List[str]:
    """키워드 매칭으로 🌱 개념 추출"""
    concepts = []
    for concept, patterns in BEGINNER_PATTERNS.items():
        if any(p in commit_diff for p in patterns):
            concepts.append(concept)
    return concepts
```

### Day 3: Note Generator
```python
def create_concept_note(concept: str, source_commit: str, example_code: str):
    """🌱 노트 생성"""
    note_path = f"2-Areas/Learning/Beginner-Concepts/{concept}.md"

    content = f"""---
type: beginner-concept
source: {source_commit}
date: {datetime.now().isoformat()}
---

# {concept}

## Pattern
{example_code}

## Source
[[{source_commit}]]
"""
    save_to_obsidian(note_path, content)
```

### Day 4: Dashboard Update
```python
def update_knowledge_dashboard():
    """Knowledge Dashboard 업데이트"""
    concepts = scan_beginner_concepts()

    dashboard = f"""# Knowledge Dashboard

## 🌱 Beginner Concepts ({len(concepts)})
{format_concept_list(concepts)}

## Recent Updates
{format_recent_updates(concepts)}

*Auto-generated: {datetime.now()}*
"""
    save_to_obsidian("5-MOCs/Knowledge-Dashboard.md", dashboard)
```

### Day 5: Integration & Testing
```bash
# Git hook 통합 테스트
git commit -m "feat: Add test function"
# Expected:
# - 개발일지 생성 ✅
# - 🌱 "함수 분리" 또는 "테스트" 추출 ✅
# - Dashboard 업데이트 ✅
```

### Success Criteria
| Metric | Target |
|--------|--------|
| 개발일지 생성 성공률 | ≥95% |
| 🌱 추출 정확도 | ≥70% |
| 오탐 (false positive) | ≤20% |
| 동기화 시간 | <5초 |

---

## Phase 2: Measurement System (Week 7-8)

**Trigger**: Phase 1 완료 후

**Goal**: 데이터 수집 및 ROI 측정

### Metrics to Track
```python
METRICS = {
    "concepts_extracted": 0,      # 추출된 개념 수
    "concepts_reused": 0,         # 재사용된 횟수
    "manual_corrections": 0,      # 수동 수정 횟수
    "search_queries": 0,          # 검색 쿼리 수
    "search_hits": 0,             # 검색 성공 수
    "sync_time_ms": [],           # 동기화 시간
}
```

### Decision Points
```
IF concepts_extracted >= 50 AND reuse_rate >= 30%:
    → Phase 3: 카테고리 확장

IF manual_corrections > 30%:
    → 패턴 개선 필요

IF sync_time_ms > 5000:
    → 성능 최적화 필요
```

---

## Phase 3: Category Expansion (Month 3+)

**Trigger**: Phase 2 메트릭 달성

**Categories to Add** (순차적):
1. 👔 Management Insights (테스트 커버리지, 성능)
2. ⚖️ Technical Debt (TODO, FIXME)
3. 🎯 Patterns (디자인 패턴)
4. 🤖 AI Synergy (AI 활용 사례)

### Expansion Criteria (per category)
| Metric | Required |
|--------|----------|
| 기존 카테고리 안정화 | 2주 |
| 추출 정확도 유지 | ≥70% |
| 사용자 피드백 | Positive |

---

## Phase 4: Advanced Features (Month 6+)

**Trigger**: 실제 수요 발생

### CurriculumBuilder
**조건**: 🌱 노트 50개 이상 축적 + 교육 요청 10건+

### ManualGenerator
**조건**: PDF 요청 10건+

### 5-System Integration
**조건**: 다른 VibeCoding 시스템 활성 사용

---

## Archived Documents

**Location**: `docs/_ARCHIVE/`

| Document | Status | Reason |
|----------|--------|--------|
| UNIFIED_OBSIDIAN_SYNC_STRATEGY.md | Archived | 현재 단계에서 과도 |
| LEARNING_CURRICULUM_AUTOMATION.md | Archived | 수요 발생 시 재검토 |

**Note**: 설계는 보관, 구현은 필요할 때

---

## Quick Reference

### Current Command
```bash
# 개발일지 생성 (이미 동작 중)
python scripts/obsidian_auto_sync.py --commit-hash HEAD
```

### Phase 1 Command (Week 5-6)
```bash
# 🌱 추출 추가 예정
python scripts/knowledge_extractor_mvp.py --commit-hash HEAD
```

### File Locations
```
scripts/
├── obsidian_auto_sync.py       # 현재 (유지)
└── knowledge_extractor_mvp.py  # Phase 1 (예정)

docs/
├── OBSIDIAN_SYNC_MVP_ROADMAP.md  # 이 문서
├── OPUS_CRITICAL_REVIEW_*.md     # 분석 문서
├── MULTI_ANGLE_ANALYSIS_*.md     # 분석 문서
└── _ARCHIVE/                     # 아카이브된 설계 문서
```

---

## Summary

| Phase | Timeline | Focus | External Deps |
|-------|----------|-------|---------------|
| 0: Maintain | Now | 현재 기능 유지 | 0 |
| 1: MVP | Week 5-6 | 🌱 단일 카테고리 | 0 |
| 2: Measure | Week 7-8 | 데이터 수집 | 0 |
| 3: Expand | Month 3+ | 카테고리 확장 | 0 |
| 4: Advanced | Month 6+ | 고급 기능 | TBD |

**Core Principle**:
> 작동하는 것부터, 측정 기반 확장, 외부 의존성 최소화
