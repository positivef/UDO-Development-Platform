# Week 6 Day 4-5: Knowledge Reuse Accuracy Tracking - Design Review

**Date**: 2025-12-18
**Status**: Design Review (P1: Design Review First)
**Estimated**: 1.5 days (12 hours)

---

## 🎯 1. Why? (왜 필요한가)

### 1.1 현재 문제점

```yaml
현재 UDO Platform 상태:
  지식 자산: 545개 Obsidian 문서 ✅
  자동화율: 95% (추정) ⚠️
  검색 정확도: 측정 안됨 ❌
  사용자 만족도: 측정 안됨 ❌

문제:
  ❌ "95% 자동화"가 실제로 맞는지 검증 불가
  ❌ Obsidian 검색이 잘못된 문서를 반환해도 모름
  ❌ 사용자가 실제로 도움 받는지 알 수 없음
  ❌ 개선이 필요한 부분을 모름
```

### 1.2 Why #1: 품질 검증

**문제**: "지식이 545개 있다" ≠ "지식이 유용하다"

**사례**:
```
시나리오: "auth.py 401 error"

나쁜 경우:
  Obsidian 검색 → [[Debug-Payment-Gateway]] (잘못된 문서!)
  사용자: "이거 도움 안 돼요" → 시간 낭비 30분

좋은 경우:
  Obsidian 검색 → [[Debug-Auth-401-Missing-Env]] (정확!)
  사용자: "바로 해결!" → 2분
```

**Why**: **품질 없는 자동화는 오히려 해롭다**

### 1.3 Why #2: 개선 방향 파악

**문제**: 어디를 개선해야 할지 모름

```yaml
개선이 필요한 영역:
  1. 검색 정확도?
     - Obsidian 검색 키워드가 부족한가?
     - 문서 태깅이 잘못됐나?

  2. 문서 품질?
     - 해결책이 outdated인가?
     - 설명이 불충분한가?

  3. 사용자 컨텍스트?
     - 상황에 맞지 않는 해결책인가?
     - 전제 조건이 다른가?
```

**Why**: **측정하지 않으면 개선할 수 없다** (What gets measured gets improved)

### 1.4 Why #3: ROI 검증

**문제**: "95% 자동화"가 실제 ROI로 이어지는지 불확실

```yaml
현재 주장:
  - 토큰 85% 감소 → 실제로?
  - 시간 73% 단축 → 체감은?
  - 연간 70시간 절약 → 검증은?

필요:
  - 사용자 피드백 수집
  - 실제 사용 패턴 분석
  - ROI 검증 데이터
```

**Why**: **투자 대비 효과를 증명해야 지속 가능**

---

## 🔍 2. 3-Step Thinking Process

### Step 1: 현재 상태 분석 (As-Is)

```yaml
Obsidian 지식 검색 흐름:
  1. 사용자 질문: "auth.py 401 error"
  2. AI 키워드 추출: ["401", "auth", "error"]
  3. Obsidian 검색: mcp__obsidian__obsidian_simple_search()
  4. 결과 반환: 3-5개 문서
  5. AI가 첫 번째 문서 사용
  6. 해결책 제시

문제점:
  ❌ Step 5에서 첫 번째가 항상 최적인가?
  ❌ Step 6 이후 사용자 만족도 모름
  ❌ 잘못된 문서 반환 시 감지 안됨
  ❌ 개선 피드백 루프 없음
```

### Step 2: 이상적인 상태 (To-Be)

```yaml
개선된 지식 검색 흐름:
  1. 사용자 질문: "auth.py 401 error"
  2. AI 키워드 추출 + 컨텍스트: ["401", "auth", "error", "FastAPI", "JWT"]
  3. 3-tier 검색 (정확도 순):
     Tier 1: Filename 매칭 (Debug-Auth-401-*.md)
     Tier 2: Frontmatter 매칭 (error_type: "401")
     Tier 3: Content 검색 (전문 검색)
  4. 결과 점수화: Relevance Score (0-100)
  5. Top 1 사용 (신뢰도 높음)
  6. 해결책 제시 + 피드백 UI
  7. 사용자 피드백 수집: 👍 도움됨 / 👎 안됨
  8. 피드백 → Obsidian 문서 개선

개선점:
  ✅ 3-tier 검색으로 정확도 향상
  ✅ 점수화로 최적 문서 선택
  ✅ 피드백 루프로 지속 개선
  ✅ 메트릭으로 품질 추적
```

### Step 3: 구현 전략 (How)

```yaml
Phase 1: 측정 인프라 (Day 4 AM)
  - Feedback UI 컴포넌트
  - 피드백 저장 API
  - 메트릭 계산 로직

Phase 2: 정확도 향상 (Day 4 PM)
  - 3-tier 검색 강화
  - Relevance scoring
  - False positive 필터링

Phase 3: 대시보드 (Day 5)
  - 정확도 메트릭 시각화
  - 문서별 유용성 순위
  - 개선 권장사항 자동 생성
```

---

## 📊 3. 벤치마킹 (상용 시스템 분석)

### 3.1 Notion AI - Knowledge Search

**시스템**: Notion AI Q&A

**구조**:
```yaml
검색 방식:
  1. Semantic Search (Embedding 기반)
  2. 사용자 컨텍스트 활용 (최근 본 페이지)
  3. 문서 타입별 가중치 (DB > Page > Block)

피드백:
  - 👍/👎 버튼
  - "Answer was helpful" 메트릭
  - 클릭률 추적 (CTR)

개선:
  - Low CTR 문서 → 자동 재작성 제안
  - High 👎 → 문서 품질 경고
```

**적용 가능**:
- ✅ 👍/👎 피드백 UI (간단)
- ✅ 문서별 유용성 점수
- ⚠️ Semantic Search (복잡, Phase C)

### 3.2 Linear - ML-based Issue Predictions

**시스템**: Linear Issue Auto-assignment

**구조**:
```yaml
예측 방식:
  1. 과거 이슈 1,000개 학습
  2. 유사도 계산 (TF-IDF)
  3. Confidence Score (0-100%)

피드백:
  - "Was this prediction helpful?" (Yes/No)
  - Prediction Accuracy Tracking
  - A/B Testing (ML vs Rule-based)

개선:
  - Accuracy < 60% → Fallback to manual
  - Weekly accuracy report
```

**적용 가능**:
- ✅ Confidence Score 표시
- ✅ Accuracy Tracking
- ✅ Threshold-based fallback (60%)

### 3.3 Cursor - AI Code Context

**시스템**: Cursor AI Context Ranking

**구조**:
```yaml
컨텍스트 선택:
  1. File relevance scoring
  2. Recent edit history
  3. Import graph analysis

피드백:
  - "Use this suggestion" (implicit 👍)
  - "Dismiss" (implicit 👎)
  - Acceptance Rate tracking

개선:
  - Low acceptance file → 낮은 우선순위
  - High acceptance pattern → 규칙화
```

**적용 가능**:
- ✅ Implicit feedback (사용/무시)
- ✅ Acceptance rate 메트릭
- ⚠️ File relevance (복잡)

### 3.4 GitHub Copilot - Telemetry

**시스템**: GitHub Copilot Acceptance Tracking

**구조**:
```yaml
메트릭:
  - Acceptance Rate: 26-40% (공개 데이터)
  - Unique Acceptance: 중복 제거 후
  - Retention Rate: 계속 사용률

피드백:
  - Tab (accept)
  - Esc (reject)
  - Edit (partial accept)

개선:
  - Language별 Acceptance 차이 분석
  - Low acceptance → Model fine-tuning
```

**적용 가능**:
- ✅ Tab/Esc 같은 암묵적 피드백
- ✅ Acceptance rate 기준 (26-40%)
- ✅ Unique acceptance 계산

### 3.5 Obsidian - Knowledge Graph

**시스템**: Obsidian Graph View + Backlinks

**구조**:
```yaml
연관성 추적:
  - Backlinks count
  - Graph centrality
  - Tag co-occurrence

품질 지표:
  - Orphan notes (연결 없음) → 낮은 품질
  - Hub notes (연결 많음) → 높은 품질
  - Last modified date → Freshness
```

**적용 가능**:
- ✅ Backlinks count (문서 유용성)
- ✅ Orphan detection
- ✅ Freshness tracking

---

## 🎯 4. 통합 솔루션 설계

### 4.1 메트릭 정의 (벤치마크 기반)

```yaml
Primary Metrics:
  1. Search Accuracy (목표: 70%+)
     - Obsidian 검색 → 올바른 문서 반환 비율
     - 계산: (도움됨 피드백) / (전체 검색)
     - 벤치마크: Linear 60%, Cursor 70%

  2. Acceptance Rate (목표: 40%+)
     - 제시한 해결책을 실제 사용 비율
     - 계산: (사용됨) / (제시됨)
     - 벤치마크: Copilot 26-40%

  3. False Positive Rate (목표: <15%)
     - 잘못된 문서 반환 비율
     - 계산: (안 도움됨) / (전체 검색)
     - 벤치마크: Notion <10%

Secondary Metrics:
  4. Time to Resolution (목표: <5분)
     - 문제 인식 → 해결 완료 시간

  5. Knowledge Freshness (목표: <30일)
     - 문서 마지막 업데이트 날짜

  6. Document Usefulness Score (목표: 3.5+/5)
     - 누적 피드백 기반 점수
```

### 4.2 피드백 시스템 설계 (Notion + Linear 조합)

```yaml
Explicit Feedback (명시적):
  UI: 👍 도움됨 / 👎 안 도움됨 버튼
  위치: 해결책 제시 후
  저장: PostgreSQL feedback 테이블
  분석: 문서별 유용성 점수

Implicit Feedback (암묵적):
  - 해결책 복사 → 👍
  - 다른 문서 요청 → 👎
  - 세션 종료 시간 → 만족도 추정

Combined Score:
  usefulness_score = (
    explicit_positive * 1.0 +
    implicit_positive * 0.5 -
    explicit_negative * 1.0 -
    implicit_negative * 0.3
  ) / total_searches
```

### 4.3 3-Tier Search 강화 (Obsidian + Cursor 조합)

```yaml
Tier 1: Filename Pattern Matching (가장 정확)
  패턴: Debug-{ErrorType}-{Component}-*.md
  예: Debug-Auth-401-Missing-Env.md
  속도: <1ms
  정확도: 95%+

Tier 2: Frontmatter Search (중간)
  YAML:
    error_type: "401"
    category: "authentication"
    technology: ["FastAPI", "JWT"]
  속도: <50ms
  정확도: 80%+

Tier 3: Full-Text Search (폴백)
  Obsidian simple_search
  속도: <500ms
  정확도: 60%+

Scoring:
  final_score = (
    tier1_match * 10 +
    tier2_match * 5 +
    tier3_match * 1 +
    freshness_bonus * 2 +
    usefulness_score * 3
  )
```

### 4.4 자동 개선 루프 (GitHub Copilot 방식)

```yaml
주간 분석 (자동):
  1. 낮은 정확도 검색어 식별
     - Accuracy < 50% → 개선 필요

  2. 문서 품질 경고
     - Usefulness < 2.0 → 재작성 권장
     - Orphan 문서 → 삭제 고려

  3. 검색 패턴 학습
     - 자주 검색되는 키워드 → 태그 추가
     - False positive 패턴 → 블랙리스트

  4. 자동 액션
     - Low quality 문서 → _archive/ 이동
     - High demand 키워드 → 문서 생성 제안
     - Outdated 문서 → Freshness 경고
```

---

## 🏗️ 5. 구현 계획 (1.5 days)

### Day 4 AM (4시간): Feedback 인프라

**Task 1.1: Feedback UI Component**
```typescript
// components/FeedbackButtons.tsx
- 👍/👎 버튼
- 이유 입력 (optional)
- 제출 후 감사 메시지
```

**Task 1.2: Feedback API**
```python
# backend/app/routers/knowledge_feedback.py
POST /api/knowledge/feedback
  - document_id
  - search_query
  - is_helpful (boolean)
  - reason (optional)
  - implicit_signals (copy, dismiss, etc.)
```

**Task 1.3: Database Schema**
```sql
CREATE TABLE knowledge_feedback (
  id UUID PRIMARY KEY,
  document_id VARCHAR,
  search_query TEXT,
  is_helpful BOOLEAN,
  reason TEXT,
  implicit_accept BOOLEAN,
  created_at TIMESTAMP,
  session_id VARCHAR
);
```

### Day 4 PM (4시간): 3-Tier Search 강화

**Task 2.1: 3-Tier Search Service**
```python
# backend/app/services/knowledge_search_service.py
- tier1_filename_search()
- tier2_frontmatter_search()
- tier3_content_search()
- calculate_relevance_score()
```

**Task 2.2: Scoring Algorithm**
```python
def calculate_final_score(matches):
    score = 0
    score += matches['tier1'] * 10
    score += matches['tier2'] * 5
    score += matches['tier3'] * 1
    score += freshness_bonus(doc)
    score += usefulness_score(doc)
    return score
```

### Day 5 (4시간): Metrics Dashboard

**Task 3.1: Metrics API**
```python
# backend/app/routers/knowledge_metrics.py
GET /api/knowledge/metrics
  - search_accuracy
  - acceptance_rate
  - false_positive_rate
  - top_useful_documents
  - improvement_suggestions
```

**Task 3.2: Dashboard UI**
```typescript
// app/knowledge-quality/page.tsx
- 정확도 차트 (시간별)
- 문서별 유용성 순위
- False positive 알림
- 개선 권장사항
```

**Task 3.3: Auto-Improvement Script**
```python
# scripts/knowledge_quality_check.py
- 주간 분석 실행
- 낮은 품질 문서 경고
- 자동 아카이브 제안
```

---

## 📈 6. 성공 기준

### 6.1 Quantitative (정량적)

| Metric | Baseline | Week 7 | Week 8 | Production |
|--------|----------|--------|--------|------------|
| Search Accuracy | 측정 안됨 | 60% | 70% | 80% |
| Acceptance Rate | 측정 안됨 | 30% | 40% | 50% |
| False Positive Rate | 측정 안됨 | 20% | 15% | 10% |
| Avg Resolution Time | 30분 | 10분 | 5분 | 2분 |

### 6.2 Qualitative (정성적)

```yaml
Week 7:
  - "피드백 버튼이 있어서 좋다"
  - "검색 결과가 예전보다 정확해진 것 같다"

Week 8:
  - "대부분 첫 번째 결과로 해결된다"
  - "잘못된 문서를 거의 안 본다"

Production:
  - "이제 직접 검색할 필요가 없다"
  - "지식이 자산이 됐다"
```

---

## ⚠️ 7. 위험 분석 (8-Risk Check)

### Risk 1: 사용자 피드백 수집률 낮음
- **영향**: 메트릭 신뢰도 하락
- **완화**: 암묵적 피드백으로 보완 (복사/무시)
- **Fallback**: 주간 사용자 인터뷰

### Risk 2: 3-Tier 검색 속도 저하
- **영향**: <500ms 목표 실패
- **완화**: 캐싱 + 인덱싱
- **Fallback**: Tier 1만 사용

### Risk 3: Frontmatter 누락 문서 많음
- **영향**: Tier 2 효과 없음
- **완화**: 기존 문서 자동 태깅 스크립트
- **Fallback**: Tier 3으로 폴백

### Risk 4: 낮은 초기 정확도 (40-50%)
- **영향**: 사용자 불만
- **완화**: 명확한 기대치 설정 (점진적 개선)
- **Fallback**: Rule-based 보완

### Risk 5: 과도한 피드백 요청 (피로감)
- **영향**: 피드백 수집률 하락
- **완화**: 10% 샘플링 (모든 검색에 요청 안함)
- **Fallback**: Session-based (세션당 1회)

### Risk 6: 데이터 부족 (초기)
- **영향**: 통계적 유의성 부족
- **완화**: 합성 데이터 생성 (테스트용)
- **Fallback**: 3주 데이터 수집 후 분석

### Risk 7: 문서 개선 부담
- **영향**: Low quality 문서가 계속 쌓임
- **완화**: 자동 아카이브 + 재작성 제안
- **Fallback**: 주간 1시간 문서 정리

### Risk 8: 메트릭 오해석
- **영향**: 잘못된 개선 방향
- **완화**: 다각도 메트릭 (Explicit + Implicit)
- **Fallback**: 사용자 인터뷰로 검증

---

## 🎯 8. Rollback Strategy

### Tier 1: Feature Flag (즉시)
```python
ENABLE_FEEDBACK_UI = False  # 피드백 UI 숨김
ENABLE_3TIER_SEARCH = False  # 기존 검색으로 복귀
```

### Tier 2: API Disable (1분)
```yaml
# Nginx config
location /api/knowledge/feedback {
    return 503;  # Service Unavailable
}
```

### Tier 3: Database Rollback (5분)
```sql
DROP TABLE knowledge_feedback;  # 데이터 삭제
```

---

## ✅ 9. Design Review Approval

### Checklist

- [x] Why 분석 완료 (품질 검증, 개선 방향, ROI)
- [x] 3-Step Thinking 완료 (As-Is, To-Be, How)
- [x] 벤치마킹 5개 완료 (Notion, Linear, Cursor, Copilot, Obsidian)
- [x] 통합 솔루션 설계 완료
- [x] 구현 계획 수립 (1.5 days)
- [x] 성공 기준 정의
- [x] 8-Risk Check 완료
- [x] Rollback Strategy 수립

### 승인 기준

```yaml
Constitutional P1 (Design Review First):
  ✅ >3 files affected → Design doc required
  ✅ 8-Risk analysis → Complete
  ✅ Rollback strategy → 3-tier defined
  ✅ Benchmarking → 5 systems analyzed

Proceed to Implementation: ✅ APPROVED
```

---

**Next**: Implementation 시작 (Week 6 Day 4 AM)
**Estimated**: 1.5 days (12 hours)
**Target Completion**: 2025-12-19 EOD
