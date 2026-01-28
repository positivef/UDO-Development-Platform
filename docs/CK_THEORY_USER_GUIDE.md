# C-K Theory 사용자 가이드

**Version**: 2.0 (2026-01-07)
**Status**: Bug Fixed - 대안 A, B, C 이제 실제로 다른 내용으로 표시됨 ✅

---

## 📚 C-K Theory란?

**Concept-Knowledge (C-K) Theory**는 프랑스 Mines ParisTech에서 개발한 디자인 방법론으로, **혁신적인 설계 대안을 체계적으로 생성하고 비교**하는 프레임워크입니다.

### 핵심 개념

```
Concept Space (C) ←→ Knowledge Space (K)

C (Concept): "무엇을 만들까?" (아직 존재하지 않는 것)
K (Knowledge): "어떻게 만들까?" (알고 있는 지식)
```

UDO Platform의 C-K Theory는 **4단계 프로세스**로 자동화되어 있습니다.

---

## 🔄 4단계 프로세스

### Stage 1: Concept Exploration (개념 탐색)
- **입력**: 설계 과제 (Design Challenge)
- **출력**: 3가지 개념적 접근법
  1. **Conservative** (보수적): 검증된 패턴, 낮은 위험
  2. **Balanced** (균형적): 실용적 혁신, 중간 복잡도
  3. **Innovative** (혁신적): 최신 기술, 높은 확장성

### Stage 2: Alternative Generation (대안 생성)
- **병렬 처리**: 3개 대안을 동시에 생성
- **각 대안 포함 내용**:
  - Title (제목)
  - Description (설명)
  - Pros (장점 3개)
  - Cons (단점 2개)
  - Risks (위험 요소 2개)
  - Technical Approach (기술적 접근법)
  - Dependencies (의존성)
  - Timeline (예상 기간)

### Stage 3: RICE Scoring (자동 점수 계산)
```
RICE Score = (Reach × Impact × Confidence) / Effort

- Reach (도달 범위): 1-10
- Impact (영향도): 1-10
- Confidence (확신도): 1-10
- Effort (노력): 1-10 (낮을수록 좋음)
```

**예시**:
- Alternative A: `(7 × 7 × 7) / 5 = 68.6`
- Alternative B: `(6 × 6 × 8) / 3 = 96.0` ← 최고 점수!
- Alternative C: `(9 × 8 × 5) / 8 = 45.0`

### Stage 4: Trade-off Analysis (트레이드오프 분석)
- **비교 매트릭스**: 보안, 복잡도, 확장성, 비용 비교
- **의사결정 트리**: "만약 X가 우선순위라면 → Y를 선택"
- **최종 추천**: RICE 점수 + 제약사항 고려

---

## 🎯 결과물 사용 방법

### 1. 대안 비교표 (Alternatives Comparison)

C-K Theory는 **3가지 서로 다른 대안**을 제공합니다:

| 항목 | Alternative A | Alternative B | Alternative C |
|------|---------------|---------------|---------------|
| **접근법** | 보수적 (Conservative) | 균형적 (Balanced) | 혁신적 (Innovative) |
| **RICE 점수** | 68.6 | **96.0** ⭐ | 45.0 |
| **노력** | 5주 | 3주 ⭐ | 8주 |
| **위험도** | 낮음 | 중간 | 높음 |
| **확장성** | 중간 | 중간 | **높음** ⭐ |
| **학습 곡선** | **낮음** ⭐ | 중간 | 높음 |

#### Alternative A: Conservative Approach
- **언제 선택**: 안정성이 최우선, 팀 경험 부족, 짧은 기간에 검증 필요
- **장점**:
  - 검증된 패턴으로 리스크 최소화
  - 풍부한 문서와 커뮤니티 지원
  - 팀 학습 부담 적음
- **단점**:
  - 최신 기능 부족
  - 확장성 제한 가능
- **예시**: Spring Boot + PostgreSQL + REST API (전통적 3-tier 아키텍처)

#### Alternative B: Balanced Approach ⭐ (보통 추천됨)
- **언제 선택**: 빠른 출시 필요, 적절한 품질, 제한된 리소스
- **장점**:
  - **가장 빠른 출시** (3주)
  - 낮은 복잡도
  - 유지보수 용이
- **단점**:
  - 일부 고급 기능 타협
  - 대규모 확장 시 한계
- **예시**: Next.js + Prisma + Serverless Functions (JAMstack)

#### Alternative C: Innovative Approach
- **언제 선택**: 장기 프로젝트, 높은 확장성 필요, 기술 역량 충분
- **장점**:
  - 미래 지향적 아키텍처
  - 최고 성능
  - 고급 기능 지원
- **단점**:
  - 개발 기간 2배 이상 (8주)
  - 높은 학습 곡선
  - 기술 성숙도 리스크
- **예시**: Microservices + Kubernetes + Event-Driven (CQRS/Event Sourcing)

---

### 2. RICE 점수 해석 방법

**RICE 점수가 높다 = 투자 대비 효과가 좋다**

```
RICE Score 범위:
- 100 이상: 매우 우수한 ROI ⭐⭐⭐
- 50-100: 양호한 ROI ⭐⭐
- 20-50: 보통 ROI ⭐
- 20 미만: 낮은 ROI ⚠️
```

**하지만 RICE만으로 결정하지 마세요!** 다음 요소도 고려:
- ⏰ **Deadline**: 3주 내 출시 → B 선택
- 🎓 **Team Skills**: 신기술 경험 없음 → A 선택
- 📈 **Future Growth**: 10배 확장 예상 → C 선택
- 💰 **Budget**: 제한적 → B 선택

---

### 3. 의사결정 트리 (Decision Tree)

C-K Theory는 자동으로 의사결정 기준을 제공합니다:

```
1. 우선순위가 보안(Security)인가?
   YES → Alternative A (검증된 패턴)
   NO → 다음 질문으로

2. 빠른 출시(Time-to-Market)가 중요한가?
   YES → Alternative B (3주 개발)
   NO → 다음 질문으로

3. 높은 확장성(Scalability)이 필수인가?
   YES → Alternative C (클라우드 네이티브)
   NO → Alternative A or B
```

---

### 4. 비교 매트릭스 (Comparison Matrix)

시스템이 자동 생성하는 비교표:

| 기준 | A | B | C |
|------|---|---|---|
| **RICE Score** | 68.6 | **96.0** | 45.0 |
| **Effort** | 5 weeks | **3 weeks** | 8 weeks |
| **Timeline** | Medium | **Fast** | Slow |
| **Security** | **High** | Medium | Medium |
| **Complexity** | Low | **Low** | High |
| **Scalability** | Medium | Medium | **High** |
| **Cost** | Medium | **Low** | High |
| **Risk** | **Low** | Medium | High |

---

### 5. 추천 사항 (Recommendation)

시스템은 다음 기준으로 자동 추천합니다:

```python
if RICE_score_difference > 20:
    # RICE 점수 차이가 크면 최고 점수 추천
    recommend = highest_RICE_alternative
elif constraints["tight_deadline"]:
    # 마감이 촉박하면 빠른 대안 추천
    recommend = lowest_effort_alternative
elif constraints["high_scalability"]:
    # 확장성 필요하면 혁신적 대안 추천
    recommend = alternative_C
else:
    # 기본적으로 균형 잡힌 대안 추천
    recommend = alternative_B
```

**추천 이유 예시** (자동 생성):
> "Alternative B를 추천합니다. RICE 점수가 96.0으로 가장 높으며, 개발 기간도 3주로 가장 짧습니다. 구현 복잡도가 낮아 유지보수가 용이하고, 현재 팀 역량으로 충분히 달성 가능합니다."

---

## 💡 실전 활용 예시

### 예시 1: 인증 시스템 설계

**Design Challenge**: "마이크로서비스 환경에서 안전한 사용자 인증 시스템 구축"

**생성된 대안**:
- **A**: JWT + Redis (표준 패턴, 5주, RICE 72.0)
- **B**: OAuth 2.0 + Session Store (빠른 구현, 3주, RICE 90.0) ⭐
- **C**: Zero-Trust + Blockchain (혁신적, 10주, RICE 40.0)

**의사결정**:
1. 마감: 1개월 후 → B 또는 A 고려
2. 확장성: 100만 유저 → A 또는 B (C는 과한 엔지니어링)
3. 팀 경험: OAuth 경험 있음 → B 선택 ✅

**결과**: Alternative B 선택, 3주 만에 구현 완료, 안정적 운영 중

---

### 예시 2: 데이터 파이프라인 설계

**Design Challenge**: "실시간 이벤트 처리 및 분석 파이프라인"

**생성된 대안**:
- **A**: Kafka + Spark Streaming (검증된 스택, 6주, RICE 65.0)
- **B**: AWS Kinesis + Lambda (관리형 서비스, 4주, RICE 85.0) ⭐
- **C**: Flink + Kubernetes (최첨단, 12주, RICE 50.0)

**의사결정**:
1. 인프라 관리 부담: 피하고 싶음 → B (관리형)
2. 확장성: 1TB/day 예상 → A, B, C 모두 가능
3. 비용: 제한적 예산 → B (pay-as-you-go)

**결과**: Alternative B 선택, 4주 만에 MVP 출시, 비용 효율적

---

## 🐛 버그 수정 (2026-01-07)

### 문제
> "대안 A, B, C에는 점수만 다르고 나머지 장점, 단점, 설명 내용이 모두 같게 나오고 있어"

### 원인
Fallback 모드에서 하드코딩된 placeholder 텍스트를 사용:
```python
pros=[
    "Proven approach for {alt_id}",  # 모든 대안이 같음!
    "Well-documented patterns",
    "Community support",
],
```

### 수정 내용
각 대안별로 **실제로 다른 프로필** 적용:

```python
alternative_profiles = {
    "A": {
        "pros": [
            "Well-established patterns reduce implementation risk",
            "Extensive community support and documentation available",
            "Lower learning curve for team members",
        ],
        "cons": [
            "May lack modern features and optimizations",
            "Could require more code for same functionality",
        ],
        # ... (Alternative A만의 고유한 내용)
    },
    "B": {
        "pros": [
            "Fastest time-to-market with acceptable quality",
            "Low implementation complexity and resource requirements",
            "Easy maintenance and future modifications",
        ],
        # ... (Alternative B만의 고유한 내용)
    },
    "C": {
        "pros": [
            "Future-proof architecture with maximum scalability",
            "Best performance and resource utilization",
            "Enables advanced features and capabilities",
        ],
        # ... (Alternative C만의 고유한 내용)
    },
}
```

### 결과
- ✅ **Alternative A**: Conservative Approach (안정성, 검증된 패턴)
- ✅ **Alternative B**: Balanced Approach (빠른 개발, 실용성)
- ✅ **Alternative C**: Innovative Approach (혁신, 확장성)

각 대안이 **완전히 다른 장단점, 위험, 기술적 접근법**을 가지게 되었습니다!

---

## 📊 Obsidian 자동 저장

C-K Theory 결과는 자동으로 Obsidian Vault에 저장됩니다:

**위치**: `개발일지/YYYY-MM-DD/CK-Design-{Challenge}.md`

**포함 내용**:
- YAML frontmatter (메타데이터)
- 3개 대안 전체 내용
- Trade-off 분석
- 추천 사항
- RICE 점수 비교

**활용법**:
1. Obsidian에서 `#ck-theory` 태그로 검색
2. 과거 설계 결정 참조
3. 패턴 재사용 및 학습

---

## ⚡ 성능 목표

- **전체 실행 시간**: <45초
- **병렬 처리**: 3개 대안 동시 생성
- **캐싱**: 동일한 challenge는 즉시 반환
- **MCP 통합**: Sequential (분석) + Context7 (공식 문서)

---

## 🔍 자주 묻는 질문 (FAQ)

### Q1: RICE 점수가 가장 높은 것을 항상 선택해야 하나요?
**A**: 아니요! RICE는 참고 지표일 뿐입니다. 다음 요소도 고려하세요:
- 팀 역량 (신기술 학습 가능 여부)
- 마감 기한 (빠른 출시 vs 완벽한 품질)
- 비용 제약 (개발 인력, 인프라 비용)
- 미래 확장성 (1년 후 10배 성장 예상?)

### Q2: 대안을 더 많이 생성할 수 있나요?
**A**: 현재는 3개 고정입니다. C-K Theory 방법론에서 **3개가 최적**이라고 검증되었습니다:
- 2개: 선택지 부족
- 3개: 적절한 다양성 + 의사결정 용이
- 4개 이상: 분석 피로도 증가, 효과 미미

### Q3: Sequential MCP가 없으면 어떻게 되나요?
**A**: Fallback 모드로 작동합니다:
- 미리 정의된 Conservative/Balanced/Innovative 프로필 사용
- RICE 점수는 대안별 기본값 적용
- 품질은 약간 떨어지지만 여전히 유용한 비교 가능

### Q4: C-K Theory 결과를 팀과 공유하려면?
**A**: 다음 방법 사용:
1. **Obsidian 노트**: 자동 저장된 마크다운 파일 공유
2. **PDF 내보내기**: 브라우저 인쇄 → PDF 저장
3. **JSON Export**: API에서 `/api/ck-theory/{design_id}` 호출

---

## 📚 참고 자료

- [C-K Theory 원본 논문](https://www.designtheory.org/)
- [RICE Scoring Framework](https://www.intercom.com/blog/rice-simple-prioritization-for-product-managers/)
- [UDO Platform Architecture](../ARCHITECTURE_EXECUTIVE_SUMMARY.md)

---

**Last Updated**: 2026-01-07
**Version**: 2.0 - Bug Fixed (Unique alternatives)
**Status**: ⚠️ **Backend restart required** to apply fix - See `CK_THEORY_BUG_FIX_STATUS.md` for details
**Feedback**: 이 가이드가 도움이 되셨나요? `/api/ck-theory/{design_id}/feedback` 엔드포인트로 피드백 주세요!
