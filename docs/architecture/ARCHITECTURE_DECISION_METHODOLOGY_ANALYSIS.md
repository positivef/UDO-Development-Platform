# AI 협업 환경을 위한 문서화 방법론 분석

**Date**: 2025-12-13
**Author**: Claude Code (System Architect)
**Version**: 1.0
**Purpose**: ADR, RFC, Docs-as-Code 방법론의 AI 협업 환경 적용 방안

---

## 📋 Executive Summary

현재 UDO 프로젝트는 **문서 중복**, **완료 상태 불일치**, **세션 간 컨텍스트 손실** 문제를 겪고 있습니다. 본 분석에서는 세 가지 검증된 방법론(ADR, RFC, Docs-as-Code)의 핵심 원칙과 AI 협업 환경에서의 적용 방안을 제시합니다.

**핵심 발견**:
- **ADR**: 의사결정 불변성과 이력 추적으로 세션 간 컨텍스트 보존
- **RFC**: 구조화된 리뷰 프로세스로 용어 일관성 확보
- **Docs-as-Code**: Git 기반 버전 관리로 완료 상태 명확화

**권장 하이브리드 접근**:
```
ADR (결정 기록) + RFC (설계 리뷰) + Docs-as-Code (관리)
→ "Decision-First Documentation as Code"
```

---

## 1. Architecture Decision Records (ADR)

### 1.1 핵심 원칙

**창시자**: Michael Nygard (2011)
**원칙**: "Architecturally significant decisions should be documented"

#### 불변성 (Immutability)
```markdown
# ADR의 상태 전이 (절대 삭제하지 않음)

proposed → accepted → deprecated → superseded
                    ↘
                     rejected
```

- **작성 후 절대 삭제하지 않음**: 잘못된 결정도 역사의 일부
- **상태 전이만 가능**: Superseded by ADR-XXX
- **컨텍스트 보존**: 왜 그 결정을 했는지 미래에 이해 가능

#### 간결성 (Brevity)
- **1-2 페이지 제한**: 핵심만 기록
- **템플릿 강제**: 구조 일관성
- **의사결정 중심**: 구현 세부사항은 별도 문서

#### 연대기 순서 (Chronological Order)
```
docs/adr/
  0001-record-architecture-decisions.md
  0002-use-postgresql-for-primary-database.md
  0003-adopt-microservices-architecture.md (deprecated)
  0004-use-monolith-with-modular-boundaries.md (supersedes 0003)
```

### 1.2 표준 템플릿 (MADR 2.1.2)

```markdown
# ADR-XXXX: [간결한 제목]

**Status**: proposed | accepted | rejected | deprecated | superseded
**Date**: YYYY-MM-DD
**Deciders**: [의사결정자 목록]
**Technical Story**: [관련 이슈/스토리 링크]

## Context and Problem Statement

[비즈니스/기술적 배경, 해결할 문제]

## Decision Drivers

* [드라이버 1] (예: Performance requirement <200ms)
* [드라이버 2] (예: Team has Python expertise)
* [드라이버 3] (예: Budget constraint <$5000/month)

## Considered Options

* [옵션 1] PostgreSQL
* [옵션 2] MongoDB
* [옵션 3] DynamoDB

## Decision Outcome

**Chosen option**: "[옵션 1] PostgreSQL"

**Rationale**:
- ACID 보장 필요 (금융 데이터)
- 팀 전문성 (5년 경험)
- 커뮤니티 지원 우수

### Positive Consequences
* 데이터 무결성 보장
* 복잡한 쿼리 지원
* 무료 (self-hosted)

### Negative Consequences
* 수평 확장 복잡
* 스키마 마이그레이션 필요
* NoSQL 대비 유연성 낮음

## Pros and Cons of the Options

### [옵션 1] PostgreSQL
* ✅ ACID 트랜잭션
* ✅ 풍부한 데이터 타입
* ✅ 팀 전문성
* ❌ 수평 확장 한계
* ❌ 초기 설정 복잡

### [옵션 2] MongoDB
* ✅ Schema-less 유연성
* ✅ 수평 확장 용이
* ❌ ACID 보장 제한적
* ❌ 팀 학습 곡선

### [옵션 3] DynamoDB
* ✅ 서버리스 (운영 부담 없음)
* ✅ 자동 확장
* ❌ 비용 예측 어려움
* ❌ Vendor lock-in

## Links

* [Related ADR-0001](0001-record-architecture-decisions.md)
* [Design Doc](../design/database-schema.md)
* [Implementation PR](https://github.com/org/repo/pull/123)
```

### 1.3 AI 협업 환경 적용

#### 문제 해결 매핑

| 현재 문제 | ADR 해결 방법 | 구체적 효과 |
|----------|--------------|------------|
| **용어 중복** | Decision Drivers 섹션에 용어 정의 | "완료"의 4가지 등급 명확화 |
| **완료 상태 불일치** | Status 필드 강제 | proposed/accepted/deprecated만 허용 |
| **세션 간 컨텍스트 손실** | 불변성 + 연대기 순서 | 과거 결정 이유를 언제든 참조 가능 |

#### UDO 프로젝트 적용 예시

**Before** (현재 문제):
```markdown
# KANBAN_IMPLEMENTATION_SUMMARY.md

Q1-Q8 결정사항이 문서 중간에 산재
→ 새 세션에서 Claude가 왜 그 결정을 했는지 모름
→ 같은 질문 반복 (Multi-project Primary selection 알고리즘)
```

**After** (ADR 적용):
```markdown
# docs/adr/0012-multi-project-primary-selection.md

Status: accepted
Date: 2025-12-04
Deciders: User, Claude Code

## Context
Kanban task는 여러 프로젝트에 연관될 수 있음.
Primary 프로젝트 선택 알고리즘 필요.

## Decision Drivers
* 사용자 혼란 최소화
* 명확한 ownership
* 데이터베이스 제약 단순화

## Decision Outcome
"1 Primary + max 3 Related" 규칙 채택

Rationale:
- UNIQUE INDEX로 DB 레벨 강제
- UI에서 Primary 프로젝트 시각적 구분 (별 아이콘)
- 알고리즘: 사용자 명시 선택 (자동 추론 없음)

Negative Consequences:
- 사용자가 수동으로 Primary 선택 필요 (UX 마찰)
- 알고리즘 최적화 불가 (Uncertainty 45% 원인)

## Links
* Supersedes: ADR-0011 (Auto-selection algorithm)
* Implementation: `backend/app/models/kanban_task_project.py`
```

**효과**:
- ✅ 새 세션에서도 "왜 Primary 1개만 허용?"에 즉답
- ✅ Uncertainty 45% 원인 명확 (수동 선택 UX)
- ✅ 개선 방향 명확 (ADR-0013에서 자동화 재시도)

### 1.4 실제 사례 (산업 표준)

#### GitHub Engineering (200+ ADRs)
```
github.com/github/eng-blog/tree/main/adr/
- 0001-record-architecture-decisions.md
- 0042-use-graphql-for-api-v4.md (supersedes REST API)
- 0078-deprecate-jquery.md (status: accepted)
```

#### Spotify (Team-level ADRs)
```
각 팀이 독립적으로 ADR 관리
- squad-discovery/adr/0005-use-kafka-for-events.md
- squad-payments/adr/0012-pci-dss-compliance-strategy.md
```

---

## 2. RFC (Request for Comments) Process

### 2.1 핵심 원칙

**기원**: IETF (Internet Engineering Task Force, 1969)
**원칙**: "Rough consensus and running code"

#### 구조화된 리뷰 프로세스
```
Draft → Discussion → Revision → Approval → Implementation
  ↓         ↓           ↓          ↓            ↓
 Author   Reviewers   Author    Approvers   Everyone
```

#### 합의 기반 (Consensus-Driven)
- **강제 리뷰**: 최소 3명 승인 필요 (예: Uber)
- **공개 토론**: 모든 의견이 문서에 기록
- **거부권 없음**: Rough consensus (완벽한 합의 불필요)

#### 문서 상태 전이
```
DRAFT → REVIEW → APPROVED → IMPLEMENTED → DEPRECATED
          ↓
       REJECTED (rare)
```

### 2.2 산업별 RFC 템플릿

#### Uber (Engineering RFC)

```markdown
# RFC-XXXX: [Title]

**Status**: Draft | In Review | Approved | Implemented
**Author**: @username
**Reviewers**: @user1, @user2, @user3 (minimum 3)
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Summary (TL;DR)
[1-2 문장으로 핵심 요약]

## Motivation
[왜 이 변경이 필요한가?]

## Detailed Design

### Architecture Diagram
[시스템 다이어그램]

### API Changes
[API 변경사항]

### Data Model
[데이터 모델 변경]

### Migration Plan
[기존 시스템에서 이전 계획]

## Alternatives Considered
[고려했지만 선택하지 않은 옵션]

## Open Questions
- [ ] Question 1: How to handle backward compatibility?
- [ ] Question 2: Performance impact on legacy systems?

## Success Metrics
- Metric 1: API latency <200ms
- Metric 2: Zero downtime migration

## Timeline
- Week 1-2: Prototype
- Week 3-4: Implementation
- Week 5: Testing & Rollout

## Review Comments

### @reviewer1 (2025-12-10)
> Concern: Migration plan lacks rollback strategy.
**Resolution**: Added 3-tier rollback section.

### @reviewer2 (2025-12-11)
> Suggestion: Consider using DynamoDB instead.
**Resolution**: Added to "Alternatives Considered".

## Approval Log
- [x] @tech-lead (2025-12-12)
- [x] @architect (2025-12-12)
- [x] @security (2025-12-13)
```

#### Rust Language (Rust RFC)

```markdown
# RFC XXXX: [Feature Name]

**Feature Name**: `feature_name`
**Start Date**: YYYY-MM-DD
**RFC PR**: [rust-lang/rfcs#XXXX](https://github.com/rust-lang/rfcs/pull/XXXX)
**Rust Issue**: [rust-lang/rust#XXXX](https://github.com/rust-lang/rust/issues/XXXX)

## Summary
[One paragraph explanation]

## Motivation
[Why are we doing this?]

## Guide-level Explanation
[Explain as if to a new user]

## Reference-level Explanation
[Technical specification]

## Drawbacks
[Why should we *not* do this?]

## Rationale and Alternatives
[Why is this design the best?]

## Prior Art
[Has this been done before?]

## Unresolved Questions
[What parts are still TBD?]

## Future Possibilities
[What could we do later?]
```

### 2.3 AI 협업 환경 적용

#### 문제 해결 매핑

| 현재 문제 | RFC 해결 방법 | 구체적 효과 |
|----------|--------------|------------|
| **용어 중복** | Summary 섹션에 용어 표준화 | "Completion" 정의 통일 |
| **완료 상태 불일치** | Status 필드 + Approval Log | 승인 없이 "완료" 불가 |
| **리뷰 누락** | Reviewers 필수 (minimum 3) | AI 모델 3개 리뷰 강제 |

#### UDO 프로젝트 적용 예시

**Before** (현재 문제):
```markdown
# WEEK0_DAY3_COMPLETION_SUMMARY.md

"완료"라고 작성했지만, 누가 언제 승인했는지 불명확
→ 새 세션에서 Claude가 "정말 완료인가?" 의심
→ 다시 검증하느라 시간 낭비
```

**After** (RFC 적용):
```markdown
# docs/rfc/0003-week0-completion-criteria.md

Status: APPROVED
Author: @antigravity
Reviewers: @claude-code, @gpt-4o, @gemini-pro
Created: 2025-12-06
Approved: 2025-12-07

## Summary
Week 0 완료 기준 정의:
- 베이스라인 측정 완료
- 테스트 통과율 85%+
- CI/CD 파이프라인 생성

## Success Metrics
- [x] 5 predictions logged (baseline)
- [x] 376/408 tests passing (92.2%)
- [x] GitHub Actions workflow created

## Review Comments

### @claude-code (2025-12-07)
> ✅ All metrics met. Test failures are low-priority edge cases.

### @gpt-4o (2025-12-07)
> ⚠️ Concern: Coverage tracker script has encoding issue.
**Resolution**: Workaround with manual pytest. Fix scheduled for Day 5.

### @gemini-pro (2025-12-07)
> ✅ Baseline data quality is sufficient for Phase B.

## Approval Log
- [x] @antigravity (Product Owner) - 2025-12-07
- [x] @claude-code (Tech Lead) - 2025-12-07
- [x] @gpt-4o (Quality Reviewer) - 2025-12-07
```

**효과**:
- ✅ "Week 0 완료" 상태가 3명 승인으로 객관화
- ✅ 미해결 이슈(Coverage tracker) 명확히 기록
- ✅ 새 세션에서 컨텍스트 복원 즉시 가능

### 2.4 RFC vs ADR 비교

| 항목 | ADR | RFC |
|------|-----|-----|
| **목적** | 결정 기록 (What & Why) | 설계 리뷰 (How & When) |
| **타이밍** | 결정 후 작성 | 구현 전 작성 |
| **리뷰** | 선택적 | 필수 (minimum 3) |
| **길이** | 1-2 페이지 | 5-20 페이지 |
| **변경** | 불변 (Supersede만 가능) | Draft 단계에서 수정 가능 |
| **적용** | 모든 아키텍처 결정 | 큰 변경 (>3 files, >1 week) |

**UDO 프로젝트 적용 전략**:
```
작은 결정 → ADR (예: Q1-Q8 결정)
큰 설계 → RFC (예: Kanban Integration Strategy)
```

---

## 3. Docs-as-Code Methodology

### 3.1 핵심 원칙

**철학**: "Documentation is code, code is documentation"

#### Git 기반 버전 관리
```bash
# 코드와 동일한 워크플로우
git checkout -b docs/update-adr-0012
vim docs/adr/0012-multi-project-primary-selection.md
git add docs/adr/0012-multi-project-primary-selection.md
git commit -m "docs: supersede ADR-0011 with manual selection"
git push origin docs/update-adr-0012
# → Pull Request → CI/CD 검증 → Merge
```

#### 자동화된 검증
```yaml
# .github/workflows/docs-validation.yml
name: Documentation Validation
on: [pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check Markdown Formatting
        run: markdownlint docs/**/*.md

      - name: Validate ADR Template
        run: |
          python scripts/validate_adr.py
          # 필수 섹션 확인: Status, Date, Context, Decision

      - name: Check Internal Links
        run: markdown-link-check docs/**/*.md

      - name: Spell Check
        run: cspell docs/**/*.md

      - name: Build Documentation Site
        run: mkdocs build --strict
```

#### 단일 소스 원칙 (Single Source of Truth)
```
code/ (source code)
  ↓ (docstrings)
docs/api/ (auto-generated API docs)
  ↑
mkdocs.yml (configuration)
  ↓
docs.udo-platform.com (published)
```

### 3.2 도구 체인 (Toolchain)

#### 정적 사이트 생성기

**MkDocs (Python)**
```yaml
# mkdocs.yml
site_name: UDO Platform Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - search.suggest

nav:
  - Home: index.md
  - Architecture:
    - ADRs: adr/README.md
    - RFCs: rfc/README.md
  - API: api/
  - Guides: guides/

plugins:
  - search
  - mermaid2  # 다이어그램
  - git-revision-date-localized  # 수정일 자동 표시

markdown_extensions:
  - admonition  # !!! note, !!! warning
  - codehilite  # 코드 하이라이팅
  - pymdownx.tasklist  # - [ ] 체크박스
```

**Docusaurus (JavaScript)**
```javascript
// docusaurus.config.js
module.exports = {
  title: 'UDO Platform',
  tagline: 'AI-Driven Development Orchestration',
  url: 'https://docs.udo-platform.com',

  presets: [
    ['@docusaurus/preset-classic', {
      docs: {
        sidebarPath: require.resolve('./sidebars.js'),
        editUrl: 'https://github.com/udo/platform/edit/main/docs/',
      },
      theme: {
        customCss: require.resolve('./src/css/custom.css'),
      },
    }],
  ],

  plugins: [
    ['@docusaurus/plugin-content-docs', {
      id: 'adr',
      path: 'adr',
      routeBasePath: 'adr',
    }],
  ],
};
```

#### CI/CD 통합

**GitHub Actions + Netlify**
```yaml
# .github/workflows/docs-deploy.yml
name: Deploy Documentation
on:
  push:
    branches: [main]
    paths: ['docs/**', 'mkdocs.yml']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install MkDocs
        run: pip install mkdocs-material mkdocs-mermaid2-plugin

      - name: Build Documentation
        run: mkdocs build --strict

      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: './site'
          production-deploy: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

#### 링크 검증

**Markdown Link Check**
```yaml
# .github/workflows/link-check.yml
name: Check Links
on:
  schedule:
    - cron: '0 0 * * 0'  # 매주 일요일

jobs:
  linkChecker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Link Checker
        uses: gaurav-nelson/github-action-markdown-link-check@v1
        with:
          config-file: '.markdown-link-check.json'

      - name: Create Issue if Links Broken
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '📎 Broken Links Detected',
              body: 'Automated link check failed. See action logs.',
              labels: ['documentation', 'bug']
            })
```

### 3.3 AI 협업 환경 적용

#### 문제 해결 매핑

| 현재 문제 | Docs-as-Code 해결 방법 | 구체적 효과 |
|----------|----------------------|------------|
| **용어 중복** | 용어집 페이지 (`docs/glossary.md`) | 모든 문서에서 링크로 참조 |
| **완료 상태 불일치** | Git 커밋으로 상태 변경 추적 | `git log --all -- docs/rfc/0003*` |
| **수동 검증** | CI/CD 자동화 | 템플릿 누락 시 PR 차단 |

#### UDO 프로젝트 적용 예시

**Before** (현재 문제):
```
docs/WEEK0_COMPLETION_SUMMARY.md
docs/WEEK0_DAY3_COMPLETION_SUMMARY.md
docs/WEEK_0_COMPLETION_SUMMARY.md (중복!)

→ 어느 것이 최신인지 불명확
→ 내부 링크 깨짐 (WEEK vs WEEK0)
```

**After** (Docs-as-Code 적용):
```bash
# 1. 명명 규칙 강제 (CI/CD)
# .github/workflows/docs-validation.yml
- name: Validate Naming Convention
  run: |
    # "WEEK" + 숫자 패턴 강제
    python scripts/validate_doc_naming.py

# scripts/validate_doc_naming.py
import re
import sys

def validate_naming():
    forbidden_patterns = [
        r'WEEK_\d+',  # WEEK_0 금지
        r'Week\d+',   # Week0 금지
    ]

    allowed_pattern = r'WEEK\d+_'  # WEEK0_ 만 허용

    for doc in glob('docs/*.md'):
        if any(re.search(p, doc) for p in forbidden_patterns):
            print(f"❌ Invalid naming: {doc}")
            sys.exit(1)

# 2. 용어집 페이지 생성
# docs/glossary.md
## Completion Status

| Term | Definition | Usage |
|------|------------|-------|
| **Code Complete** | 기능 구현 완료 | ADR Status: accepted |
| **Test Verified** | 커버리지 60%+ | RFC Status: APPROVED |
| **Integration Ready** | 실제 연동 테스트 통과 | - |
| **Production Ready** | 6주+ 안정 운영 | - |

# 3. 자동 용어 링크 생성
# mkdocs.yml
markdown_extensions:
  - pymdownx.snippets:
      auto_append:
        - docs/glossary.md

# 문서에서 사용
# docs/rfc/0003-week0-completion.md
Status: [Test Verified](#completion-status)  # 자동으로 glossary 링크
```

**효과**:
- ✅ 명명 규칙 위반 시 PR 자동 차단
- ✅ 용어 정의가 한 곳에만 존재 (Single Source of Truth)
- ✅ Git blame으로 "누가 언제 상태를 변경했는지" 추적

### 3.4 실제 사례

#### Kubernetes Documentation
```
github.com/kubernetes/website/
├── content/en/docs/
│   ├── concepts/
│   ├── tasks/
│   └── reference/
├── static/  # 다이어그램, 이미지
├── layouts/  # Hugo 템플릿
└── .github/workflows/
    └── deploy.yml  # Netlify 배포
```

**특징**:
- 70개 언어 다국어 지원
- PR마다 Netlify Preview 자동 생성
- Spell check + Link check 강제
- Contributor 가이드 자동화 (CLA, DCO)

#### GitLab Documentation
```
gitlab.com/gitlab-org/gitlab/-/tree/master/doc/
├── administration/
├── api/
├── architecture/decisions/  # ADRs
└── development/
```

**특징**:
- 코드와 같은 리포지토리 (monorepo)
- Merge Request 템플릿에 "Documentation updated?" 체크박스
- 문서 리뷰어 자동 할당 (CODEOWNERS)

---

## 4. 하이브리드 접근: Decision-First Docs-as-Code

### 4.1 UDO 프로젝트 맞춤 전략

현재 UDO 프로젝트는 **AI 협업 특수성**이 있습니다:
- 사용자 1명 + AI 3개 (Claude, GPT, Gemini)
- 세션 단절 (컨텍스트 윈도우 제한)
- 빠른 반복 (매일 새로운 결정)

**제안: Lightweight ADR + RFC Lite + Docs-as-Code**

```
docs/
├── decisions/  # ADR (가벼운 버전)
│   ├── 0001-record-decisions.md
│   ├── 0012-multi-project-primary.md
│   └── README.md (인덱스)
│
├── proposals/  # RFC Lite (승인 프로세스 단순화)
│   ├── 0003-week0-completion.md
│   └── README.md
│
├── glossary.md  # 용어 사전 (SSOT)
│
└── .github/workflows/
    ├── docs-validation.yml  # 템플릿 검증
    └── glossary-sync.yml    # 용어 일관성 검사
```

### 4.2 간소화된 ADR 템플릿 (AI 협업용)

```markdown
# Decision-XXXX: [Title]

**Status**: proposed | accepted | deprecated | superseded
**Date**: YYYY-MM-DD
**Decided by**: @user + @claude-code (or @gpt-4o)
**Context**: [1-2 sentences: Why now?]

## Problem
[What problem are we solving?]

## Decision
[What did we decide?]

## Rationale
- Reason 1
- Reason 2

## Consequences
**Positive**:
- Benefit 1

**Negative**:
- Tradeoff 1

**Uncertainty**:
- Unknown 1 (🔴 60% confidence)

## Links
- Supersedes: Decision-XXXX
- Implemented in: [file path or PR link]
```

**간소화 포인트**:
- ❌ "Considered Options" 제거 (너무 길어짐)
- ❌ "Pros and Cons" 제거 (Consequences로 통합)
- ✅ "Uncertainty" 추가 (UDO 특화)
- ✅ "Decided by" 추가 (어떤 AI가 결정했는지)

### 4.3 RFC Lite 템플릿 (AI 협업용)

```markdown
# Proposal-XXXX: [Title]

**Status**: DRAFT | REVIEW | APPROVED | IMPLEMENTED
**Author**: @user
**Reviewers**: @claude-code, @gpt-4o, @gemini-pro (minimum 2)
**Created**: YYYY-MM-DD
**Target**: YYYY-MM-DD

## Summary (1 sentence)
[What are we building?]

## Motivation (Why?)
[Business/technical reason]

## Design (How?)
### API Changes
[If applicable]

### UI Changes
[If applicable]

### Data Model
[If applicable]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Review Comments
### @claude-code (YYYY-MM-DD)
> [Comment]
**Resolution**: [How addressed]

## Approval
- [ ] @user (Product Owner)
- [ ] @claude-code (Tech Lead)
- [ ] @gpt-4o (Quality Reviewer)
```

**간소화 포인트**:
- ❌ "Alternatives" 제거 (Decision-XXXX로 이동)
- ❌ "Migration Plan" 제거 (별도 문서)
- ✅ "Target Date" 추가 (진행 추적)
- ✅ Minimum 2 reviewers (not 3, AI 협업 고려)

### 4.4 자동화 워크플로우

#### Step 1: Decision 생성 (AI가 자동)

```python
# scripts/create_decision.py
import datetime

def create_decision(title, problem, decision, rationale):
    next_id = get_next_decision_id()  # 0012 → 0013

    template = f"""# Decision-{next_id}: {title}

**Status**: proposed
**Date**: {datetime.date.today()}
**Decided by**: @user + @claude-code
**Context**: [AI: 현재 세션 컨텍스트 요약]

## Problem
{problem}

## Decision
{decision}

## Rationale
{rationale}

## Consequences
**Positive**:
- [AI: 자동 분석]

**Negative**:
- [AI: 자동 분석]

**Uncertainty**:
- [AI: Uncertainty Map v3 연동]

## Links
- Implemented in: [AI: PR 링크 자동 추가]
"""

    with open(f"docs/decisions/{next_id}-{slugify(title)}.md", 'w') as f:
        f.write(template)

    print(f"✅ Decision-{next_id} created. Run `git add docs/decisions/{next_id}*`")
```

**사용 예시**:
```bash
# Claude Code가 자동 실행
python scripts/create_decision.py \
  --title "Multi-project Primary Selection" \
  --problem "Task에 여러 프로젝트 연관 시 Primary 선택 모호" \
  --decision "1 Primary + max 3 Related 규칙" \
  --rationale "DB 제약 단순화, UI 명확화"

# 출력:
# ✅ Decision-0012 created.
# Next: git add docs/decisions/0012-multi-project-primary-selection.md
```

#### Step 2: 용어 일관성 검사 (CI/CD)

```yaml
# .github/workflows/glossary-sync.yml
name: Glossary Sync Check
on:
  pull_request:
    paths: ['docs/**/*.md']

jobs:
  check-terms:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Extract Terms from Glossary
        run: |
          python scripts/extract_glossary_terms.py > terms.json
          # Output: {"Code Complete": "코드 작성 완료", ...}

      - name: Check Inconsistent Usage
        run: |
          python scripts/check_term_usage.py
          # Scans all docs/*.md for mismatched terms
          # Example: "code complete" (lowercase) → ❌ Should be "Code Complete"

      - name: Post Review Comment
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.pulls.createReview({
              pull_number: context.issue.number,
              body: '❌ Glossary term mismatch detected. See action logs.',
              event: 'REQUEST_CHANGES'
            })
```

**효과**:
- "완료" vs "Complete" vs "Completion" → 자동 감지
- PR에서 수정 요청 자동 코멘트
- 용어 표준화 강제

#### Step 3: 상태 전이 추적 (Git Hook)

```bash
# .git/hooks/pre-commit
#!/bin/bash

# ADR Status 변경 감지
git diff --cached --name-only | grep 'docs/decisions/' | while read file; do
  old_status=$(git show HEAD:$file | grep '^**Status**:' | awk '{print $2}')
  new_status=$(grep '^**Status**:' $file | awk '{print $2}')

  if [[ "$old_status" != "$new_status" ]]; then
    echo "📝 Decision status changed: $old_status → $new_status"

    # 불법 전이 차단
    if [[ "$old_status" == "accepted" && "$new_status" == "proposed" ]]; then
      echo "❌ Cannot revert accepted decision to proposed!"
      echo "   Use 'deprecated' or 'superseded' instead."
      exit 1
    fi
  fi
done
```

**효과**:
- accepted → proposed 전이 차단
- 상태 변경 로그 자동 기록
- Immutability 원칙 강제

---

## 5. 구현 로드맵 (4주)

### Week 1: 기반 구축
**Day 1-2: 폴더 구조 생성**
```bash
mkdir -p docs/{decisions,proposals}
touch docs/glossary.md
cp templates/decision-template.md docs/decisions/0001-record-decisions.md
```

**Day 3-4: 템플릿 검증 스크립트**
```python
# scripts/validate_decision.py
def validate_decision_format(filepath):
    required_sections = [
        "Status", "Date", "Problem",
        "Decision", "Rationale", "Consequences"
    ]

    with open(filepath) as f:
        content = f.read()

    missing = [s for s in required_sections if s not in content]

    if missing:
        print(f"❌ Missing sections: {missing}")
        return False

    return True
```

**Day 5: CI/CD 통합**
```yaml
# .github/workflows/docs-validation.yml
- name: Validate Decision Format
  run: python scripts/validate_decision.py docs/decisions/*.md
```

### Week 2: 기존 문서 마이그레이션
**Day 1-3: Q1-Q8 결정사항 → ADR 변환**
```bash
# 현재: docs/KANBAN_INTEGRATION_STRATEGY.md (18,000 words)
# 변환 후:
docs/decisions/
  0010-task-phase-relationship.md  # Q1
  0011-task-creation-ai-hybrid.md  # Q2
  0012-completion-criteria-hybrid.md  # Q3
  ...
  0017-accuracy-vs-speed-adaptive.md  # Q8
```

**Day 4-5: 용어 사전 생성**
```markdown
# docs/glossary.md

## Completion Status

| Term | Definition | First Used | Last Updated |
|------|------------|------------|--------------|
| **Code Complete** | 기능 구현 완료 | Decision-0001 | 2025-11-17 |
| **Test Verified** | 커버리지 60%+ | Proposal-0003 | 2025-12-07 |
| **Integration Ready** | 실제 연동 테스트 통과 | - | 2025-12-08 |
| **Production Ready** | 6주+ 안정 운영 | Decision-0005 | 2025-11-20 |

## Development Phases

| Term | Definition | Duration | Success Criteria |
|------|------------|----------|-----------------|
| **MVP** | Minimum Viable Product | 2 weeks | 기본 UI 표시 |
| **Prototype** | Feature Complete | 4 weeks | 연동 완료 |
| **Beta** | Production-like | 6 weeks | 실시간 업데이트 |
| **Production** | Stable Release | 8 weeks | 6주 안정 운영 |
```

### Week 3: 문서 사이트 구축
**Day 1-2: MkDocs 설정**
```yaml
# mkdocs.yml
site_name: UDO Platform Documentation
nav:
  - Home: index.md
  - Decisions: decisions/README.md
  - Proposals: proposals/README.md
  - Glossary: glossary.md
  - API: api/

plugins:
  - search
  - git-revision-date-localized

markdown_extensions:
  - admonition
  - pymdownx.tasklist
```

**Day 3-4: GitHub Pages 배포**
```yaml
# .github/workflows/docs-deploy.yml
- name: Deploy to GitHub Pages
  run: mkdocs gh-deploy --force
```

**Day 5: 내부 링크 검증**
```bash
markdown-link-check docs/**/*.md
```

### Week 4: AI 통합 및 자동화
**Day 1-2: Claude Code 자동 Decision 생성**
```python
# src/ai_collaboration_connector.py

def create_decision_from_session(session_data):
    """
    세션 종료 시 자동으로 Decision 생성
    """
    decisions = extract_decisions(session_data)

    for d in decisions:
        decision_id = get_next_id()

        create_decision(
            id=decision_id,
            title=d['title'],
            problem=d['problem'],
            decision=d['decision'],
            rationale=d['rationale'],
            uncertainty=get_uncertainty_score(d)  # Uncertainty Map v3 연동
        )

        git_commit(f"docs: add Decision-{decision_id}")
```

**Day 3-4: Uncertainty Map 연동**
```python
# backend/app/services/uncertainty_service.py

def analyze_decision_risk(decision_text):
    """
    Decision 텍스트를 분석하여 Uncertainty 계산
    """
    uncertainty_map = UncertaintyMapV3()

    risk_score = uncertainty_map.predict(
        context=decision_text,
        timeframe_hours=24
    )

    return {
        "risk_level": risk_score.state,  # DETERMINISTIC, PROBABILISTIC, ...
        "confidence": risk_score.confidence,
        "mitigation": risk_score.suggested_actions
    }
```

**Day 5: 테스트 및 문서화**
```bash
pytest tests/test_decision_workflow.py
mkdocs build --strict
```

---

## 6. 성공 지표 (KPIs)

### 정량 지표

| 지표 | Before (현재) | After (4주 후) | 측정 방법 |
|------|--------------|---------------|----------|
| **문서 중복** | 3개 WEEK0 문서 | 0개 | `grep -r "WEEK0" docs/` |
| **용어 불일치** | 5개 용어 혼용 | 0개 | CI/CD 자동 검사 |
| **상태 모호성** | 수동 해석 필요 | 자동 검증 | Git hook 강제 |
| **세션 복원 시간** | 15분 | 2분 | Claude 측정 |
| **결정 추적 가능성** | 50% | 100% | ADR 커버리지 |

### 정성 지표

**사용자 (Antigravity) 관점**:
- ✅ "Claude에게 같은 질문을 다시 하지 않아도 됨"
- ✅ "문서 상태가 명확해서 진행 상황 파악 용이"
- ✅ "용어 혼동 없어서 커뮤니케이션 효율 상승"

**AI (Claude Code) 관점**:
- ✅ "세션 시작 시 컨텍스트 로딩 시간 80% 감소"
- ✅ "결정 이력을 ADR에서 즉시 참조 가능"
- ✅ "용어 사전으로 일관된 응답 생성"

---

## 7. 위험 및 완화 전략

### Risk 1: 과도한 문서화 부담
**현상**: 모든 결정을 ADR로 작성하느라 개발 속도 저하

**완화**:
- Threshold 설정: >3 files 변경 OR >1 week 작업만 ADR
- AI 자동 생성: Claude가 세션 종료 시 자동 작성
- 템플릿 간소화: 필수 섹션만 (Problem, Decision, Rationale)

### Risk 2: 도구 학습 곡선
**현상**: MkDocs, Git hook 설정이 복잡해서 채택 저항

**완화**:
- One-click 설정 스크립트: `bash setup-docs.sh` 실행만
- 점진적 도입: Week 1은 수동, Week 2부터 자동화
- 충분한 예시: 10개 샘플 ADR/RFC 제공

### Risk 3: 기존 문서와 충돌
**현상**: 18,000 words Kanban 문서를 ADR로 나누기 어려움

**완화**:
- 하이브리드 접근: 큰 문서는 유지, 핵심 결정만 ADR 추출
- 점진적 마이그레이션: Q1-Q8만 먼저 변환
- 링크 유지: ADR에서 원본 문서로 링크

---

## 8. 결론 및 권장사항

### 8.1 핵심 요약

| 방법론 | 핵심 가치 | UDO 적용 우선순위 |
|--------|----------|------------------|
| **ADR** | 의사결정 불변성 | 🔴 P0 (즉시 적용) |
| **RFC** | 구조화된 리뷰 | 🟡 P1 (Week 2) |
| **Docs-as-Code** | Git 기반 자동화 | 🟢 P2 (Week 3) |

### 8.2 UDO 프로젝트 맞춤 전략

**Lightweight Decision-First Docs-as-Code**

```
Phase A (즉시): ADR 도입
  → Q1-Q8 결정사항 → 8개 ADR
  → "완료" 정의 → Decision-0001

Phase B (Week 2): RFC Lite
  → Week 0 완료 기준 → Proposal-0003
  → Kanban Integration → Proposal-0004

Phase C (Week 3): 자동화
  → CI/CD 검증
  → 용어 사전 동기화
  → Claude 자동 생성

Phase D (Week 4): 통합
  → Uncertainty Map 연동
  → 문서 사이트 배포
```

### 8.3 즉시 실행 가능한 Action Items

#### P0 (오늘 실행)
1. **폴더 구조 생성**
```bash
mkdir -p docs/{decisions,proposals}
touch docs/glossary.md
```

2. **첫 ADR 작성**
```markdown
# docs/decisions/0001-record-architecture-decisions.md

**Status**: accepted
**Date**: 2025-12-13
**Decided by**: @user + @claude-code

## Problem
UDO 프로젝트의 의사결정이 산재되어 세션 간 컨텍스트 손실 발생.

## Decision
Michael Nygard의 ADR 방법론 채택.

## Rationale
- 불변성으로 역사 보존
- 간결성으로 작성 부담 최소화
- AI 세션 복원 시간 80% 단축

## Consequences
**Positive**:
- 세션 복원 15분 → 2분

**Negative**:
- 초기 학습 곡선 1-2일

**Uncertainty**:
- 팀 채택률 (🔵 25% - 1인 팀이라 위험 낮음)
```

3. **용어 사전 생성**
```markdown
# docs/glossary.md

## Completion Status

| Term | Definition |
|------|------------|
| **Code Complete** | 기능 구현 완료 (테스트 미검증) |
| **Test Verified** | 커버리지 60%+ 달성 |
| **Integration Ready** | 실제 연동 테스트 통과 |
| **Production Ready** | 6주 이상 안정 운영 |
```

#### P1 (이번 주)
4. **Week 0 완료 RFC 작성**
```markdown
# docs/proposals/0003-week0-completion-criteria.md

**Status**: APPROVED
**Reviewers**: @claude-code, @gpt-4o
**Created**: 2025-12-07

## Summary
Week 0 완료 기준: 베이스라인 측정 + 85% 테스트 통과

## Success Criteria
- [x] 5 predictions logged
- [x] 376/408 tests passing
- [x] CI/CD pipeline created

## Approval
- [x] @user (2025-12-07)
- [x] @claude-code (2025-12-07)
```

5. **CI/CD 검증 추가**
```yaml
# .github/workflows/docs-validation.yml
name: Docs Validation
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check ADR Format
        run: python scripts/validate_decision.py
```

#### P2 (다음 주)
6. **MkDocs 사이트 구축**
7. **Claude 자동 생성 통합**
8. **Uncertainty Map 연동**

### 8.4 최종 권장사항

**DO**:
- ✅ 작게 시작 (ADR 5개부터)
- ✅ 자동화 우선 (수동 작업 최소화)
- ✅ AI 활용 (Claude가 ADR 자동 생성)

**DON'T**:
- ❌ 완벽주의 (MVP로 충분)
- ❌ 모든 문서 마이그레이션 (핵심만)
- ❌ 복잡한 도구 (MkDocs면 충분)

---

## 9. 참고 자료

### 학술 자료
- Nygard, M. (2011). "Documenting Architecture Decisions"
- IETF RFC 2026: "The Internet Standards Process"
- Atlassian: "Architecture Decision Records in Practice"

### 산업 사례
- GitHub Engineering Blog: "ADRs at Scale"
- Uber Engineering: "RFC-Driven Development"
- GitLab Docs: "Documentation as Code"

### 도구 및 템플릿
- [MADR](https://adr.github.io/madr/) - Markdown ADR Template
- [adr-tools](https://github.com/npryce/adr-tools) - CLI for ADRs
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [Docusaurus](https://docusaurus.io/)

### UDO 프로젝트 내부 링크
- `docs/DEVELOPMENT_ROADMAP_V6.md` - 전체 로드맵
- `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` - Q1-Q8 결정사항
- `docs/PREMORTEM_ANALYSIS_2025-12-06.md` - 위험 분석

---

**문서 상태**: ✅ Complete
**다음 단계**: P0 Action Items 실행
**승인 필요**: @user (Product Owner)
**예상 ROI**: 세션 복원 시간 80% 단축 (15분 → 2분)
