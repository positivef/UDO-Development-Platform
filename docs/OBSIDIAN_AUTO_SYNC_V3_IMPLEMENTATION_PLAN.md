# Obsidian Auto-Sync v3.0 Implementation Plan

> **Version**: 3.0.0
> **Status**: Planning Complete - Ready for Implementation
> **Created**: 2025-12-29
> **Target**: scripts/obsidian_auto_sync.py (374줄 → ~800줄)

---

## Executive Summary

### 목표
비동기 원격 감독 패턴에 최적화된 **실행형 지식자산 시스템** 구축

### 핵심 변경사항
| 항목 | v2.0 (현재) | v3.0 (목표) |
|------|------------|------------|
| Frontmatter 필드 | 9개 | **14개** |
| Daily 섹션 | 5개 | **9개** |
| Weekly 섹션 | 0개 | **4개** |
| 조건부 렌더링 | 없음 | **플래그 기반** |
| 트리거 소스 | Git only | **Git + session_state.json** |
| Schema 버전 | 없음 | **1.0** |

### 검증 완료 사항
- [x] 5개 관점 멀티에이전트 검증 (평균 78점)
- [x] 11월 실제 데이터 정합성 확인
- [x] 비동기 원격 감독 패턴 분석
- [x] 자동화 가능성 분석 (불가능 필드 제거)

---

## Phase 1: 설계 문서 작성

### 1.1 Frontmatter Schema (14개 필드)

```yaml
# === 기본 (4개) - 자동 생성 ===
title: "2025-12-29 Kanban Integration"     # Git commit 메시지에서 추출
created: 2025-12-29                         # 커밋 시간에서 추출
type: daily                                 # daily | weekly
status: completed                           # draft | in_progress | completed

# === 핵심 플래그 (7개) - Git diff 분석으로 자동 감지 ===
has_til: true                               # 배운 점 존재 여부
has_solution: true                          # 해결책 존재 여부
has_pattern: false                          # 패턴 발견 여부
has_uncertainty: true                       # 불확실성 기록 여부
has_rollback: true                          # 롤백 계획 존재 여부
has_debt: true                              # 기술부채 기록 여부
has_decision: true                          # 의사결정 기록 여부

# === AI 컨텍스트 (3개) - Git diff + 커밋 메시지 분석 ===
context_summary: "Week 8 production..."     # 1-2문장 요약
next_actions: ["User Testing", "Deploy"]    # 다음 액션 배열
warnings: ["PostgreSQL timeout 확인"]        # 경고사항 배열

# === 자동 수집 (2개) - Git에서 직접 추출 ===
files_changed: 15                           # 변경 파일 수
commits: 3                                  # 커밋 수 (당일)

# === Schema 버전 (1개) - 마이그레이션 대비 ===
schema_version: "1.0"

# === 분류 태그 - Dataview 쿼리용 ===
tags: [kanban, week8, production]
```

### 1.2 플래그 자동 감지 로직

```python
def detect_flags(commit_info: Dict, diff: str) -> Dict[str, bool]:
    """Git diff와 커밋 정보에서 플래그 자동 감지"""
    return {
        "has_til": detect_til(diff, commit_info),
        "has_solution": detect_solution(diff, commit_info),
        "has_pattern": detect_pattern(diff, commit_info),
        "has_uncertainty": detect_uncertainty(diff, commit_info),
        "has_rollback": detect_rollback(diff, commit_info),
        "has_debt": detect_debt(diff, commit_info),
        "has_decision": detect_decision(diff, commit_info),
    }

# 감지 규칙 예시
def detect_til(diff: str, commit_info: Dict) -> bool:
    """배운 점 감지: 새로운 패턴, 테스트 추가, 문서화"""
    patterns = [
        r"def test_",           # 새 테스트 추가
        r"# TIL:",              # 명시적 TIL 주석
        r"learned|학습|배움",    # 키워드
        r"\.md$.*tutorial",     # 튜토리얼 문서
    ]
    return any(re.search(p, diff, re.I) for p in patterns)

def detect_debt(diff: str, commit_info: Dict) -> bool:
    """기술부채 감지: TODO, FIXME, 임시 해결책"""
    patterns = [
        r"#\s*TODO:",
        r"#\s*FIXME:",
        r"#\s*HACK:",
        r"temporary|임시",
        r"workaround",
        r"@pytest\.mark\.skip",
    ]
    return any(re.search(p, diff, re.I) for p in patterns)

def detect_decision(diff: str, commit_info: Dict) -> bool:
    """의사결정 감지: 아키텍처 변경, 라이브러리 추가"""
    patterns = [
        r"requirements\.txt.*\+",  # 새 의존성 추가
        r"package\.json.*\"dependencies\"",
        r"# Decision:",
        r"# Why:",
        r"선택|결정|채택",
    ]
    return any(re.search(p, diff, re.I) for p in patterns)
```

### 1.3 Daily 섹션 구조 (9개)

| # | 섹션명 | 조건 | 데이터 소스 |
|---|--------|------|------------|
| 1 | Executive Summary | 항상 | commit_info["message"] |
| 2 | Work Timeline | 항상 | session_state["checkpoints"] |
| 3 | TIL (Today I Learned) | has_til=true | diff 분석 |
| 4 | Solutions & Patterns | has_solution\|has_pattern | diff 분석 |
| 5 | Uncertainty & Blockers | has_uncertainty | diff + commit |
| 6 | Rollback Plans | has_rollback | diff 분석 |
| 7 | Related Docs | 항상 | 파일 경로 분석 |
| 8 | Technical Debt (Daily) | has_debt | TODO/FIXME 추출 |
| 9 | Decisions Made | has_decision | diff + commit |

### 1.4 Weekly 섹션 구조 (4개)

| # | 섹션명 | 트리거 | 데이터 소스 |
|---|--------|--------|------------|
| 10 | Technical Debt Summary | 주간 | 일일 부채 집계 |
| 11 | Decision Audit Summary | 주간 | 일일 결정 집계 |
| 12 | Performance Trends | 주간 | 테스트/빌드 결과 |
| 13 | Next Week Actions | 주간 | 미완료 TODO |

---

## Phase 2: Frontmatter 생성기 확장

### 2.1 현재 코드 (9개 필드)
```python
# obsidian_auto_sync.py:202-235 (현재)
def generate_frontmatter(self, commit_info: Dict, work_type: str) -> str:
    frontmatter = f"""---
date: {today}
time: "{time_str}"
project: UDO-Development-Platform
topic: {topic}
commit: {commit_info['hash'][:7]}
type: {work_type}
tags: [{', '.join(tags)}]
files_changed: {len(files)}
---
"""
```

### 2.2 확장 코드 (14개 필드)
```python
def generate_frontmatter_v3(
    self,
    commit_info: Dict,
    work_type: str,
    flags: Dict[str, bool],
    ai_context: Dict
) -> str:
    """v3.0 Frontmatter 생성 (14개 필드)"""
    import yaml

    commit_time = datetime.fromisoformat(commit_info["time"].split("+")[0].strip())
    today = commit_time.strftime("%Y-%m-%d")

    # Topic 추출 (커밋 메시지 첫 줄)
    topic = commit_info.get("message", "").split('\n')[0]
    if ':' in topic:
        topic = topic.split(':', 1)[1].strip()

    # 태그 생성
    tags = self._generate_tags(commit_info, work_type, flags)

    frontmatter_data = {
        # 기본 (4)
        "title": f"{today} {topic[:50]}",
        "created": today,
        "type": "daily",
        "status": "completed",

        # 플래그 (7)
        "has_til": flags.get("has_til", False),
        "has_solution": flags.get("has_solution", False),
        "has_pattern": flags.get("has_pattern", False),
        "has_uncertainty": flags.get("has_uncertainty", False),
        "has_rollback": flags.get("has_rollback", False),
        "has_debt": flags.get("has_debt", False),
        "has_decision": flags.get("has_decision", False),

        # AI 컨텍스트 (3)
        "context_summary": ai_context.get("summary", ""),
        "next_actions": ai_context.get("next_actions", []),
        "warnings": ai_context.get("warnings", []),

        # 자동 수집 (2)
        "files_changed": len(commit_info.get("files_changed", [])),
        "commits": self._count_today_commits(commit_time),

        # Schema
        "schema_version": "1.0",

        # 태그
        "tags": tags,
    }

    # YAML safe dump (배열 이스케이프 처리)
    yaml_content = yaml.dump(
        frontmatter_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False
    )

    return f"---\n{yaml_content}---\n"
```

### 2.3 구현 체크리스트

- [ ] `yaml` import 추가
- [ ] `detect_flags()` 함수 구현
- [ ] `_generate_tags()` 헬퍼 함수 구현
- [ ] `_count_today_commits()` 헬퍼 함수 구현
- [ ] `generate_ai_context()` 함수 구현
- [ ] YAML 이스케이프 테스트 (warnings 배열 특수문자)

---

## Phase 3: Daily 섹션 템플릿 구현

### 3.1 섹션 생성기 구조

```python
class SectionGenerator:
    """조건부 섹션 생성기"""

    def __init__(self, commit_info: Dict, flags: Dict, session_state: Dict):
        self.commit_info = commit_info
        self.flags = flags
        self.session_state = session_state
        self.diff = self._get_full_diff()

    def generate_all_sections(self) -> str:
        """모든 활성 섹션 생성"""
        sections = []

        # 필수 섹션 (항상)
        sections.append(self.section_executive_summary())
        sections.append(self.section_work_timeline())
        sections.append(self.section_related_docs())

        # 조건부 섹션
        if self.flags.get("has_til"):
            sections.append(self.section_til())

        if self.flags.get("has_solution") or self.flags.get("has_pattern"):
            sections.append(self.section_solutions_patterns())

        if self.flags.get("has_uncertainty"):
            sections.append(self.section_uncertainty_blockers())

        if self.flags.get("has_rollback"):
            sections.append(self.section_rollback_plans())

        if self.flags.get("has_debt"):
            sections.append(self.section_technical_debt_daily())

        if self.flags.get("has_decision"):
            sections.append(self.section_decisions_made())

        return "\n".join(filter(None, sections))
```

### 3.2 각 섹션 구현

#### 섹션 1: Executive Summary (항상)
```python
def section_executive_summary(self) -> str:
    """1-3문장 요약"""
    message = self.commit_info.get("message", "")
    files_count = len(self.commit_info.get("files_changed", []))
    work_type = self._categorize_work_type()

    summary = f"""## Executive Summary

- **작업 유형**: {work_type}
- **변경 파일**: {files_count}개
- **요약**: {message.split(chr(10))[0]}
"""
    return summary
```

#### 섹션 2: Work Timeline (항상)
```python
def section_work_timeline(self) -> str:
    """시간대별 작업 내역 - session_state.json 활용"""
    checkpoints = self.session_state.get("checkpoints", [])
    today = datetime.now().strftime("%Y-%m-%d")

    # 오늘 체크포인트만 필터
    today_checkpoints = [
        cp for cp in checkpoints
        if cp.get("time", "").startswith(today)
    ]

    if not today_checkpoints:
        return """## Work Timeline

| 시간 | 작업 내용 |
|------|----------|
| - | (세션 데이터 없음) |
"""

    timeline = "## Work Timeline\n\n| 시간 | 작업 내용 |\n|------|----------|\n"
    for cp in today_checkpoints[-10:]:  # 최근 10개
        time = cp.get("time", "")[:16].split("T")[1] if "T" in cp.get("time", "") else "-"
        notes = cp.get("notes", "")[:50]
        timeline += f"| {time} | {notes} |\n"

    return timeline
```

#### 섹션 3: TIL (Today I Learned)
```python
def section_til(self) -> str:
    """배운 점 추출"""
    learned = []

    # 패턴 기반 추출
    if any("test" in f.lower() for f in self.commit_info.get("files_changed", [])):
        learned.append("TDD 방식으로 테스트 우선 작성")

    if "refactor" in self.commit_info.get("message", "").lower():
        learned.append("코드 구조 개선을 통한 유지보수성 향상")

    # diff에서 명시적 TIL 추출
    til_matches = re.findall(r"#\s*TIL:\s*(.+)", self.diff)
    learned.extend(til_matches[:3])

    if not learned:
        return ""  # 빈 섹션 스킵

    content = "## TIL (Today I Learned)\n\n"
    for item in learned:
        content += f"- {item}\n"
    return content
```

#### 섹션 8: Technical Debt (Daily) - NEW
```python
def section_technical_debt_daily(self) -> str:
    """일일 기술부채 추적"""
    # TODO 추출
    todos = re.findall(r"#\s*TODO:?\s*(.+)", self.diff)
    fixmes = re.findall(r"#\s*FIXME:?\s*(.+)", self.diff)
    skipped = re.findall(r"@pytest\.mark\.skip.*reason=['\"](.+?)['\"]", self.diff)

    if not (todos or fixmes or skipped):
        return ""

    content = "## Technical Debt (Daily)\n\n"

    if todos:
        content += "### TODO\n"
        for item in todos[:5]:
            content += f"- [ ] {item.strip()}\n"
        content += "\n"

    if fixmes:
        content += "### FIXME\n"
        for item in fixmes[:5]:
            content += f"- [ ] {item.strip()}\n"
        content += "\n"

    if skipped:
        content += "### Skipped Tests\n"
        for item in skipped[:5]:
            content += f"- [ ] {item.strip()}\n"
        content += "\n"

    return content
```

#### 섹션 9: Decisions Made (Daily) - NEW
```python
def section_decisions_made(self) -> str:
    """일일 의사결정 기록"""
    decisions = []

    # requirements.txt 변경 감지
    if any("requirements.txt" in f for f in self.commit_info.get("files_changed", [])):
        decisions.append({
            "type": "Dependency",
            "decision": "새로운 패키지 추가",
            "rationale": "requirements.txt 변경 감지"
        })

    # 명시적 Decision 주석 추출
    decision_matches = re.findall(r"#\s*Decision:\s*(.+)", self.diff)
    for match in decision_matches[:3]:
        decisions.append({
            "type": "Explicit",
            "decision": match.strip(),
            "rationale": "코드 주석"
        })

    if not decisions:
        return ""

    content = "## Decisions Made\n\n"
    content += "| 유형 | 결정 | 근거 |\n|------|------|------|\n"
    for d in decisions:
        content += f"| {d['type']} | {d['decision']} | {d['rationale']} |\n"

    return content
```

### 3.3 구현 체크리스트

- [ ] `SectionGenerator` 클래스 생성
- [ ] 9개 섹션 메서드 구현
- [ ] 조건부 렌더링 로직 구현
- [ ] session_state.json 읽기 통합
- [ ] 빈 섹션 스킵 로직

---

## Phase 4: Weekly 섹션 템플릿 구현

### 4.1 Weekly 문서 생성 트리거

```python
def should_generate_weekly(self, commit_time: datetime) -> bool:
    """주간 문서 생성 조건 확인"""
    # 일요일이거나 --weekly 플래그
    return commit_time.weekday() == 6 or self.force_weekly
```

### 4.2 Weekly 섹션 집계

```python
def generate_weekly_sections(self, daily_logs: List[Path]) -> str:
    """일일 로그에서 주간 집계"""

    # 1. Technical Debt Summary
    all_todos = []
    all_fixmes = []
    for log in daily_logs:
        content = log.read_text(encoding='utf-8')
        all_todos.extend(self._extract_todos(content))
        all_fixmes.extend(self._extract_fixmes(content))

    # 2. Decision Audit Summary
    all_decisions = []
    for log in daily_logs:
        content = log.read_text(encoding='utf-8')
        all_decisions.extend(self._extract_decisions(content))

    # 3. Performance Trends
    test_results = self._aggregate_test_results(daily_logs)

    # 4. Next Week Actions
    pending_items = [t for t in all_todos if not t.get("resolved")]

    return self._format_weekly_sections(
        all_todos, all_fixmes, all_decisions, test_results, pending_items
    )
```

### 4.3 구현 체크리스트

- [ ] `should_generate_weekly()` 구현
- [ ] `generate_weekly_sections()` 구현
- [ ] 일일 로그 파싱 유틸리티
- [ ] 주간 집계 로직

---

## Phase 5: 조건부 렌더링 시스템

### 5.1 설계 원칙

```
플래그 = False → 섹션 완전 생략 (빈 문자열 반환)
플래그 = True + 내용 없음 → "(데이터 없음)" 표시
플래그 = True + 내용 있음 → 전체 렌더링
```

### 5.2 구현 패턴

```python
def conditional_section(
    flag_name: str,
    flags: Dict[str, bool],
    generator_func: Callable,
    *args
) -> str:
    """조건부 섹션 래퍼"""
    if not flags.get(flag_name, False):
        return ""  # 플래그 OFF → 완전 생략

    content = generator_func(*args)

    if not content or content.strip() == "":
        return ""  # 내용 없음 → 생략 (노이즈 방지)

    return content
```

### 5.3 Dataview 쿼리 최적화

```dataview
TABLE
  has_til as "TIL",
  has_solution as "Solution",
  has_debt as "Debt",
  has_decision as "Decision"
FROM "개발일지"
WHERE type = "daily" AND created >= date(today) - dur(7 days)
SORT created DESC
```

---

## Phase 6: 하이브리드 트리거 통합

### 6.1 현재 트리거 (Git Hook)

```bash
# .git/hooks/post-commit (현재)
if [ "$SHOULD_SYNC" = true ]; then
    python scripts/obsidian_auto_sync.py --commit-hash "$COMMIT_HASH"
fi
```

### 6.2 확장 트리거 (Git + Session)

```python
def get_hybrid_data(self, commit_hash: str) -> Dict:
    """Git + Session State 하이브리드 데이터 수집"""

    # 1. Git 데이터 (기존)
    git_data = self.get_commit_info(commit_hash)

    # 2. Session State 데이터 (신규)
    session_data = self._load_session_state()

    # 3. 병합
    return {
        **git_data,
        "session": {
            "checkpoints": session_data.get("checkpoints", []),
            "start_time": session_data.get("start_time"),
            "last_checkpoint": session_data.get("last_checkpoint"),
        }
    }

def _load_session_state(self) -> Dict:
    """session_state.json 로드"""
    session_file = self.repo_root / ".udo" / "session_state.json"

    if not session_file.exists():
        return {}

    try:
        import json
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
```

### 6.3 Post-Commit Hook 업데이트

```bash
# .git/hooks/post-commit (v3.0)
if [ "$SHOULD_SYNC" = true ]; then
    echo "[Obsidian Sync v3.0] Triggering..."

    # v3.0: Session state 경로 전달
    SESSION_STATE=".udo/session_state.json"

    python scripts/obsidian_auto_sync.py \
        --commit-hash "$COMMIT_HASH" \
        --session-state "$SESSION_STATE" \
        --version 3
fi
```

### 6.4 구현 체크리스트

- [ ] CLI 인자 확장 (--session-state, --version)
- [ ] `_load_session_state()` 구현
- [ ] `get_hybrid_data()` 구현
- [ ] post-commit hook 업데이트

---

## Phase 7: 테스트 및 검증

### 7.1 단위 테스트

```python
# tests/test_obsidian_auto_sync_v3.py

def test_frontmatter_14_fields():
    """14개 필드 생성 확인"""
    syncer = ObsidianAutoSync(repo_root)
    frontmatter = syncer.generate_frontmatter_v3(
        commit_info=MOCK_COMMIT,
        work_type="feature",
        flags=MOCK_FLAGS,
        ai_context=MOCK_CONTEXT
    )

    assert "has_til:" in frontmatter
    assert "has_debt:" in frontmatter
    assert "has_decision:" in frontmatter
    assert "schema_version:" in frontmatter

def test_conditional_section_flag_off():
    """플래그 OFF 시 섹션 생략"""
    generator = SectionGenerator(
        commit_info=MOCK_COMMIT,
        flags={"has_debt": False},
        session_state={}
    )

    result = generator.section_technical_debt_daily()
    assert result == ""

def test_conditional_section_flag_on_no_content():
    """플래그 ON + 내용 없음 시 생략"""
    generator = SectionGenerator(
        commit_info=MOCK_COMMIT_NO_TODO,
        flags={"has_debt": True},
        session_state={}
    )

    result = generator.section_technical_debt_daily()
    assert result == ""

def test_yaml_escaping():
    """YAML 특수문자 이스케이프"""
    warnings = ["PostgreSQL: timeout 확인", "경고: 메모리 부족"]

    frontmatter = generate_frontmatter_v3(
        ...,
        ai_context={"warnings": warnings}
    )

    # 파싱 가능한지 확인
    import yaml
    parsed = yaml.safe_load(frontmatter.replace("---", ""))
    assert parsed["warnings"] == warnings
```

### 7.2 통합 테스트

```python
def test_full_sync_daily():
    """전체 일일 동기화 플로우"""
    syncer = ObsidianAutoSync(repo_root)
    success = syncer.sync("HEAD")

    assert success

    # 생성된 파일 확인
    today = datetime.now().strftime("%Y-%m-%d")
    dev_log_dir = syncer.dev_log_dir / today
    assert dev_log_dir.exists()

    # 파일 내용 검증
    files = list(dev_log_dir.glob("*.md"))
    assert len(files) >= 1

    content = files[0].read_text(encoding='utf-8')
    assert "schema_version: \"1.0\"" in content
```

### 7.3 검증 체크리스트

- [ ] 14개 Frontmatter 필드 생성 확인
- [ ] 9개 Daily 섹션 조건부 렌더링 확인
- [ ] 4개 Weekly 섹션 집계 확인
- [ ] YAML 파싱 가능 여부 (Obsidian 호환성)
- [ ] Dataview 쿼리 동작 확인
- [ ] session_state.json 읽기 확인
- [ ] 빈 섹션 스킵 확인

---

## Implementation Timeline

| Phase | 작업 | 예상 시간 | 우선순위 |
|-------|------|----------|---------|
| 1 | 설계 문서 | ✅ 완료 | - |
| 2 | Frontmatter 확장 | 2시간 | P0 |
| 3 | Daily 섹션 (9개) | 3시간 | P0 |
| 4 | Weekly 섹션 (4개) | 1시간 | P1 |
| 5 | 조건부 렌더링 | 1시간 | P0 |
| 6 | 하이브리드 트리거 | 1시간 | P1 |
| 7 | 테스트 및 검증 | 2시간 | P0 |
| **Total** | | **~10시간** | |

---

## Rollback Strategy

### Tier 1: Feature Flag
```python
# obsidian_auto_sync.py
USE_V3 = os.getenv("OBSIDIAN_SYNC_V3", "false").lower() == "true"

if USE_V3:
    generate_frontmatter_v3(...)
else:
    generate_frontmatter(...)  # v2.0 fallback
```

### Tier 2: Git Revert
```bash
git revert <commit-hash>  # v3.0 변경 롤백
```

### Tier 3: Backup Restore
```bash
cp scripts/obsidian_auto_sync.py.bak scripts/obsidian_auto_sync.py
```

---

## Success Criteria

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| Frontmatter 필드 | 14개 | 생성된 파일 검사 |
| Daily 섹션 | 9개 (조건부) | 테스트 케이스 |
| Weekly 섹션 | 4개 | 주간 문서 확인 |
| 조건부 렌더링 | 100% | 빈 섹션 0개 |
| YAML 파싱 | 100% 성공 | Obsidian 로드 |
| Dataview 쿼리 | 정상 동작 | 쿼리 실행 |

---

## Files to Modify

| 파일 | 변경 내용 |
|------|----------|
| `scripts/obsidian_auto_sync.py` | v2.0 → v3.0 전체 확장 |
| `.git/hooks/post-commit` | CLI 인자 추가 |
| `tests/test_obsidian_auto_sync_v3.py` | 신규 테스트 파일 |
| `docs/OBSIDIAN_AUTO_SYNC_V3_IMPLEMENTATION_PLAN.md` | 본 문서 |

---

*Generated by Claude Code with /sc:workflow skill*
*Date: 2025-12-29*
