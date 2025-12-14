# PRD vNext 검토 분석 보고서
**Date**: 2025-11-25
**Reviewer**: Claude Code Analysis
**Status**: Design Review Complete

---

## 📋 Executive Summary

PRD vNext(Uncertainty-First & Second Brain)와 워크로그를 종합 분석한 결과, **전체적인 방향성은 우수**하나 몇 가지 **구현 레벨의 구체화**가 필요합니다.

### 핵심 발견사항
- ✅ **강점**: 예측→완화→적응 흐름이 명확하고, 기존 아키텍처와 잘 통합됨
- ⚠️ **주의**: API 계약이 일부 구현되었으나 PRD 명세와 불일치
- ❌ **보완 필요**: 미티게이션 ACK 엔드포인트(`/ack/{id}`)가 미구현
- ❌ **보완 필요**: Bayesian 통합 진입점이 스켈레톤 수준
- ⚠️ **주의**: 세컨 브레인(Obsidian) 자동 로그 스펙 불명확

### 권장 조치
1. **즉시**: 미티게이션 ACK 엔드포인트 구현 (Phase 1 완료 조건)
2. **단기(1-2주)**: Bayesian 통합 초기화 로직 완성
3. **중기(2-4주)**: Obsidian 자동 로그 파이프라인 구현
4. **장기(1-2개월)**: PRD 업로드/멀티모달 기능 추가

---

## 1. 요구사항 명확성 평가

### 1.1 API 계약 완전성 검증

#### ✅ 구현 완료된 엔드포인트
| 엔드포인트 | PRD 명세 | 구현 상태 | 비고 |
|-----------|---------|---------|------|
| `GET /api/uncertainty/status` | ✅ | ✅ 완료 | 상태/신뢰도/예측/미티게이션 모두 반환 |
| `POST /api/uncertainty/analyze` | ✅ | ✅ 완료 | 컨텍스트 분석 기능 구현 |
| `GET /api/uncertainty/health` | ⚠️ 암시적 | ✅ 완료 | PRD에 명시되지 않았으나 필수 |
| `POST /api/uncertainty/track-with-uncertainty` | ⚠️ 암시적 | ✅ 완료 | 타임트래킹 연동 (Phase 2) |
| `POST /api/uncertainty/adjusted-baseline/{task_type}/{phase}` | ⚠️ 암시적 | ✅ 완료 | 불확실성 기반 시간 조정 |

#### ❌ 미구현 엔드포인트
| 엔드포인트 | PRD 명세 | 구현 상태 | 우선순위 |
|-----------|---------|---------|---------|
| `GET /api/uncertainty/mitigations` | ✅ | ❌ 미구현 | **HIGH** - Phase 1 |
| `POST /api/uncertainty/ack/{id}` | ✅ | ❌ 미구현 | **HIGH** - Phase 1 |
| PRD 업로드 엔드포인트 | ✅ | ❌ 미구현 | LOW - Phase 5 |

**분석**:
- `/status` 엔드포인트에서 미티게이션 목록을 이미 반환하므로, 별도 `/mitigations` 엔드포인트는 **중복**
- **권장**: `/status`를 주요 엔드포인트로 사용하고, `/mitigations`는 제거 또는 선택적 구현
- `POST /ack/{id}`는 **필수** - 미티게이션 적용 후 리스크 하향 기록을 위해 구현 필요

### 1.2 응답 스키마 일관성

#### 현재 구현 (backend/app/models/uncertainty.py)
```python
class UncertaintyStatusResponse(BaseModel):
    vector: UncertaintyVectorResponse
    state: UncertaintyStateEnum
    confidence_score: float
    prediction: PredictiveModelResponse
    mitigations: List[MitigationStrategyResponse]
    timestamp: datetime
```

#### PRD 기대값 vs 실제 구현
| 필드 | PRD 명세 | 구현 상태 | 평가 |
|-----|---------|---------|------|
| `vector` (5차원) | ✅ | ✅ | 완벽 일치 |
| `state` (Quantum State) | ✅ | ✅ | 완벽 일치 |
| `confidence_score` | ✅ | ✅ | 완벽 일치 |
| `prediction` (24h) | ✅ | ✅ | 완벽 일치 |
| `mitigations` (ROI 정렬) | ✅ | ✅ | 완벽 일치 (line 145 참조) |
| `timestamp` | ⚠️ 암시적 | ✅ | PRD에 명시되지 않았으나 모범 사례 |

**결론**: 응답 스키마는 PRD 요구사항을 **완전히 충족**하며, timestamp 추가는 긍정적

### 1.3 비기능 요구사항 분석

#### PRD 명시된 비기능 요구사항
1. **회로차단(Circuit Breaker)**: ✅ PRD 3.1절, 3.6절에 명시
2. **캐시(TTL)**: ✅ PRD 3.1절에 명시
3. **보안(JWT/CORS)**: ✅ PRD 3.9절에 명시
4. **모니터링(계측)**: ✅ PRD 3.9절에 명시

#### 실제 구현 상태 (uncertainty.py 기준)
| 비기능 요구사항 | 구현 상태 | 코드 위치 | 평가 |
|---------------|---------|---------|------|
| 회로차단 | ❌ 미구현 | N/A | **HIGH PRIORITY** |
| 캐시/TTL | ❌ 미구현 | N/A | **HIGH PRIORITY** |
| 에러 핸들링 | ✅ 부분 구현 | Line 198-200, 289-290 | try-except만 있음, 폴백 없음 |
| 로깅 | ✅ 구현 | Line 28, 199, 289 | logger 활용 적절 |
| 입력 검증 | ✅ 구현 | Pydantic 모델 | 자동 검증 활용 |
| CORS | ⚠️ 전역 설정 | main.py | 라우터 레벨 검증 필요 |
| JWT 인증 | ❌ 미구현 | N/A | 선택적 요구사항 |

**권장 개선 사항**:

```python
# 1. 회로차단 패턴 추가
from app.core.circuit_breaker import CircuitBreaker

uncertainty_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

@router.get("/status")
@uncertainty_breaker
async def get_uncertainty_status(...):
    # 기존 로직
    pass

# 2. 캐시 TTL 추가
from fastapi_cache import cache
from app.models.uncertainty import UncertaintyStateEnum

def get_cache_ttl(state: UncertaintyStateEnum) -> int:
    """불확실성 상태별 TTL (초)"""
    ttl_map = {
        UncertaintyStateEnum.DETERMINISTIC: 3600,    # 1시간
        UncertaintyStateEnum.PROBABILISTIC: 1800,    # 30분
        UncertaintyStateEnum.QUANTUM: 900,           # 15분
        UncertaintyStateEnum.CHAOTIC: 300,           # 5분
        UncertaintyStateEnum.VOID: 60                # 1분
    }
    return ttl_map.get(state, 300)

@router.get("/status")
@cache(expire=lambda result: get_cache_ttl(result['state']))
async def get_uncertainty_status(...):
    pass
```

---

## 2. 구현 순서 검증 및 최적화

### 2.1 워크로그 7단계 vs PRD 우선순위 비교

| 워크로그 순서 | PRD 우선순위 | 일치 여부 | 분석 |
|------------|------------|---------|------|
| 1) 불확실성 브리지 완성 | 1) 동일 | ✅ | 완벽 일치 |
| 2) 미티게이션 액션/타임트래킹 | 2) 동일 | ✅ | 완벽 일치 |
| 3) Bayesian 통합 | 3) 동일 | ✅ | 완벽 일치 |
| 4) Guided Tips / 세컨 브레인 | 4) PRD 업로드 먼저 | ⚠️ | **순서 조정 필요** |
| 5) PRD 업로드/멀티모달 | 5) 모니터링 먼저 | ⚠️ | **순서 조정 필요** |
| 6) 모니터링/알림 | - | ⚠️ | PRD에서 더 높은 우선순위 |
| 7) 테스트/운영 게이트 | - | ✅ | 최종 단계로 적절 |

**권장 순서 조정**:
```
1) 불확실성 브리지 완성 ✅
2) 미티게이션 ACK + 타임트래킹 연동 ✅
3) Bayesian 통합 (적응형 임계치) ✅
4) 모니터링/알림 (회로차단, 비용 지표) ⬆️ 우선순위 상향
5) Guided Tips / 세컨 브레인 로그 ⬇️
6) PRD 업로드/멀티모달 (옵션) ⬇️
7) 테스트/운영 게이트 ✅
```

**이유**:
- 모니터링/회로차단은 **시스템 안정성**에 직결 → 조기 구현 필요
- Guided Tips는 **UX 개선** 요소 → 핵심 기능 후 추가 가능
- PRD 업로드는 **복잡도 높음** (파싱/임베딩) → 후순위 적절

### 2.2 각 단계별 Definition of Done (DoD)

#### Phase 1: 불확실성 브리지 완성
**목표**: API ↔ 대시보드 연동, 실시간 상태 표시

**DoD**:
- [ ] `GET /api/uncertainty/status` 200 OK 응답
- [ ] `POST /api/uncertainty/ack/{mitigation_id}` 구현 완료
  ```python
  @router.post("/ack/{mitigation_id}")
  async def acknowledge_mitigation(
      mitigation_id: str,
      uncertainty_map = Depends(get_uncertainty_map)
  ):
      """미티게이션 적용 확인 → 리스크 하향 기록"""
      # 1. 미티게이션 검증
      # 2. 리스크 벡터 재산정 (estimated_impact만큼 하향)
      # 3. Obsidian 로그 기록
      pass
  ```
- [ ] 대시보드 `/uncertainty/status` Query 연결 (tanstack-query)
- [ ] 로딩/에러/폴백 UX 구현 완료
- [ ] 회로차단/캐시 TTL 적용 (코드 예시 섹션 1.3 참조)
- [ ] E2E 테스트: "불확실성 상태 조회 → 미티게이션 표시 → ACK → 리스크 하향" 시나리오 통과

#### Phase 2: 미티게이션 액션 & 타임트래킹 연동
**목표**: 실행 → 리스크 변화 타임라인 구축

**DoD**:
- [ ] 타임트래킹 1.2x 초과 시 `POST /api/uncertainty/risk-event` 호출
  ```python
  @router.post("/risk-event")
  async def record_risk_event(
      event: RiskEventRequest,  # task_id, dimension, delta
      uncertainty_map = Depends(get_uncertainty_map)
  ):
      """타임트래킹 이벤트 → 불확실성 재산정"""
      # 1. 현재 벡터 조회
      # 2. event.dimension에 delta 적용 (예: timeline +0.2)
      # 3. 재산정 결과 저장
      # 4. 타임라인에 기록
      pass
  ```
- [ ] 대시보드 타임라인 컴포넌트에 "실행 → 리스크 변화" 표시
- [ ] Obsidian 자동 로그: "Task X → 1.2x 초과 → Timeline risk +20%" 기록
- [ ] 테스트: 타임트래킹 초과 → 리스크 상승 → 대시보드 반영 확인

#### Phase 3: Bayesian 통합 (UDO v2)
**목표**: 적응형 임계치로 GO/NO_GO 결정 자동화

**DoD**:
- [ ] `src/udo_bayesian_integration.py` 초기화 완료
  ```python
  class UDOBayesianIntegration:
      def __init__(self, udo_v2, uncertainty_map):
          self.udo = udo_v2
          self.uncertainty = uncertainty_map

      def adaptive_threshold(self, phase: str) -> float:
          """Phase별 적응형 임계치 계산"""
          # 현재 불확실성 상태 기반 임계치 조정
          # Chaotic → 임계치 상향 (더 보수적)
          # Deterministic → 임계치 하향 (더 공격적)
          pass

      def decide_with_uncertainty(self, plan):
          """불확실성 고려한 GO/NO_GO 결정"""
          threshold = self.adaptive_threshold(plan.phase)
          confidence = self.udo.evaluate_plan(plan)

          if confidence >= threshold:
              return "GO"
          elif confidence >= threshold * 0.8:
              return "GO_WITH_CHECKPOINTS"
          else:
              return "NO_GO"
  ```
- [ ] UDO v2 orchestrator에서 Bayesian 통합 호출
- [ ] 학습 루프: 실행 결과 피드백 → confidence 업데이트
- [ ] 테스트: Chaotic 상태 → 임계치 상향 → NO_GO 결정 검증

#### Phase 4: 모니터링/알림/비용 지표
**목표**: 시스템 안정성 및 비용 가시화

**DoD**:
- [ ] 회로차단 상태 대시보드 카드 추가
- [ ] AI 호출 비용/토큰 추적 (`POST /api/metrics/ai-usage`)
- [ ] 리스크 급등 알림 (WebSocket 브로드캐스트)
  ```python
  @router.websocket("/ws/alerts")
  async def alert_websocket(websocket: WebSocket):
      await websocket.accept()
      # 리스크 변화 감지 시 푸시
      # {type: "risk_surge", dimension: "timeline", delta: 0.3}
      pass
  ```
- [ ] Slack/웹훅 옵션 설정 (`config/alerts.yaml`)
- [ ] 테스트: 리스크 급등 → WebSocket 푸시 → 대시보드 알림 표시

#### Phase 5: Guided Tips / 세컨 브레인
**목표**: 행동 지침 제공 및 지식 축적

**DoD**:
- [ ] 대시보드 Tips 패널 구현 (`/components/dashboard/guided-tips.tsx`)
- [ ] Phase/리스크별 지침 JSON 설정 (`config/guided_tips.yaml`)
- [ ] "적용/무시" 액션 → Obsidian 로그 기록
- [ ] Obsidian 자동 append: `vault/UDO/YYYY-MM-DD_session.md`
  ```markdown
  ## 14:30 - Mitigation Applied
  - Action: Increase test coverage
  - Risk Before: timeline=0.6 → After: timeline=0.4
  - Decision: Applied (manual)

  #uncertainty #mitigation #timeline
  ```
- [ ] 테스트: Tip 적용 → Obsidian 파일 생성 → 태그 검색 가능

#### Phase 6: PRD 업로드/멀티모달 (옵션)
**목표**: PRD 문서 자동 분석 및 리스크 재산정

**DoD**:
- [ ] 드래그앤드롭 UI (`/upload`)
- [ ] 파일 파싱 (MD/PDF/TXT) → 임베딩 → PostgreSQL+pgvector 저장
- [ ] 이미지 OCR (옵션, Tesseract/Google Vision API)
- [ ] 업로드 후 리스크 재산정 트리거
- [ ] 변경 diff 표시 (Before/After 비교 카드)
- [ ] 테스트: PRD 업로드 → 리스크 변화 → 대시보드 반영

#### Phase 7: 테스트/운영 게이트
**목표**: 회귀 방지 및 프로덕션 준비

**DoD**:
- [ ] Backend: `pytest tests/ --cov=backend --cov-report=html` 80% 이상
- [ ] Frontend: `npm run lint && npm run build` 성공
- [ ] E2E: `tests/run_udo_phase1.py` 모든 시나리오 통과
- [ ] 성능 테스트: `/api/uncertainty/status` 응답 시간 < 500ms (P95)
- [ ] 문서화: `docs/API_REFERENCE.md` 업데이트 (Swagger 자동 생성)
- [ ] 배포 준비: Docker Compose + 환경변수 분리

---

## 3. 아키텍처 통합 방안

### 3.1 기존 시스템과의 통합 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                      UDO v2 Orchestrator                     │
│  (Phase-Aware Evaluation, GO/NO_GO Decision)                │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
             │ 1. Get Uncertainty           │ 4. Update Learning
             ▼                              ▼
┌────────────────────────┐      ┌────────────────────────────┐
│  Uncertainty Map v3    │      │  Bayesian Integration      │
│  - Analyze Context     │◄─────┤  - Adaptive Threshold      │
│  - Predict Evolution   │      │  - Confidence Update       │
│  - Generate Mitigations│      └────────────────────────────┘
└────────────┬───────────┘
             │ 2. Broadcast State
             ▼
┌────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                    │
│  /api/uncertainty/* ─► WebSocket ─► Cache/Circuit Breaker  │
└────────────┬───────────────────────────────────────────────┘
             │ 3. Query/Subscribe
             ▼
┌────────────────────────────────────────────────────────────┐
│              Dashboard (Next.js + Tanstack Query)           │
│  - Uncertainty Map Component                                │
│  - Mitigation Cards                                         │
│  - Timeline Visualization                                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 데이터 흐름 및 상태 관리

#### 상태 동기화 전략
1. **폴링 방식** (현재 구현):
   - Tanstack Query: `refetchInterval: 5000` (5초)
   - 장점: 구현 간단, 캐시 활용 가능
   - 단점: 실시간성 떨어짐 (최대 5초 지연)

2. **WebSocket 방식** (권장):
   ```typescript
   // web-dashboard/lib/useUncertaintyWebSocket.ts
   export function useUncertaintyWebSocket() {
     const { data, setData } = useStore()

     useEffect(() => {
       const ws = new WebSocket('ws://localhost:8000/api/uncertainty/ws')

       ws.onmessage = (event) => {
         const update = JSON.parse(event.data)
         // {type: "status_change", state: "chaotic", confidence: 0.3}
         setData(update)
       }

       return () => ws.close()
     }, [])

     return data
   }
   ```

3. **하이브리드 방식** (최적):
   - WebSocket: 상태 변경 시 푸시
   - 폴링: WebSocket 끊김 시 폴백 (30초 간격)
   - 캐시: TTL 기반 재검증

#### 캐시 일관성 보장
```python
# backend/app/core/cache_manager.py
class UncertaintyCacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def invalidate_on_state_change(self, old_state, new_state):
        """상태 변경 시 캐시 무효화"""
        if old_state != new_state:
            await self.redis.delete("uncertainty:status")
            # WebSocket 푸시
            await broadcast_state_change(new_state)

    async def get_with_ttl(self, state: UncertaintyStateEnum):
        """상태별 TTL 적용"""
        ttl = self._get_ttl(state)
        cached = await self.redis.get("uncertainty:status")

        if cached and not self._is_expired(cached, ttl):
            return cached

        # 캐시 미스 → 재계산
        fresh_data = await self._compute_status()
        await self.redis.setex("uncertainty:status", ttl, fresh_data)
        return fresh_data
```

---

## 4. 리스크 및 완화 전략

### 4.1 기술 리스크 분석

| 리스크 항목 | 확률 | 영향 | 심각도 | 완화 전략 |
|-----------|------|------|-------|---------|
| **Bayesian 통합 복잡도** | 70% | HIGH | **HIGH** | 1) 단순 임계치 조정부터 시작<br>2) 점진적 학습 루프 추가<br>3) 롤백 가능한 설계 |
| **Obsidian 동기화 성능** | 50% | MEDIUM | MEDIUM | 1) 비동기 append (파일락 경합 최소화)<br>2) 배치 처리 (1분 단위 누적)<br>3) 실패 시 재시도 큐 |
| **멀티모달 파싱 정확도** | 60% | MEDIUM | MEDIUM | 1) PDF: PyPDF2 → Tesseract 폴백<br>2) 이미지: 선택적 OCR<br>3) 파싱 실패 시 원본 보존 |
| **WebSocket 연결 불안정** | 40% | MEDIUM | LOW | 1) 자동 재연결 (exponential backoff)<br>2) 폴링 폴백<br>3) 하트비트 (30초) |
| **회로차단 오동작** | 30% | HIGH | MEDIUM | 1) 임계값 튜닝 (dev: 10회, prod: 5회)<br>2) 반개방 상태 (partial open)<br>3) 수동 리셋 API |

### 4.2 워크로그 체크리스트 검증

#### 즉시 액션 체크리스트 재평가

| 항목 | 원래 우선순위 | 현재 상태 | 재평가 우선순위 | 비고 |
|-----|-------------|---------|---------------|------|
| UncertaintyMap 의존성 DI 정리 | HIGH | ✅ 완료 | - | `get_uncertainty_map()` 구현됨 |
| 상태/예측/미티게이션 응답 스키마 | HIGH | ✅ 완료 | - | Pydantic 모델 정의 완료 |
| 대시보드 Query 연결 | HIGH | ✅ 완료 | - | Tanstack Query 통합 |
| **Bayesian 통합 진입점 설계** | HIGH | ⚠️ 미착수 | **CRITICAL** | Phase 3 시작 조건 |
| Obsidian 동기화 메모 | MEDIUM | ❌ 미완료 | LOW | Phase 5로 이동 |

**권장 조치**:
1. ✅ **즉시**: Bayesian 통합 스켈레톤 생성 (`src/udo_bayesian_integration.py`)
2. ✅ **1주 내**: 미티게이션 ACK 엔드포인트 구현
3. ⚠️ **2주 내**: 회로차단/캐시 TTL 적용
4. ⬇️ **나중**: Obsidian 동기화 (Phase 5)

### 4.3 타임트래킹 1.2x 초과 로직 상세화

#### 현재 PRD 명세 (불명확)
> "타임트래킹 초과(1.2x) → 기술 불확실성 상승 훅 설계 필요"

#### 구체적 구현 제안
```python
# backend/app/services/time_tracking_service.py
class TimeTrackingService:
    async def on_task_complete(self, session_id: UUID):
        session = await self.get_session(session_id)
        baseline = self._get_baseline_seconds(session.task_type)
        actual = (session.end_time - session.start_time).total_seconds()

        ratio = actual / baseline

        if ratio > 1.2:
            # 1.2배 초과 → 불확실성 상승 이벤트
            await self._trigger_uncertainty_event(
                session=session,
                risk_delta={
                    "technical": min(0.3, (ratio - 1.2) * 0.5),  # 최대 +0.3
                    "timeline": min(0.2, (ratio - 1.2) * 0.3)   # 최대 +0.2
                }
            )

    async def _trigger_uncertainty_event(self, session, risk_delta):
        """불확실성 재산정 트리거"""
        # 1. 현재 벡터 조회
        current_vector = await uncertainty_map.get_current_vector()

        # 2. Delta 적용
        new_vector = current_vector.copy()
        new_vector.technical = min(1.0, current_vector.technical + risk_delta["technical"])
        new_vector.timeline = min(1.0, current_vector.timeline + risk_delta["timeline"])

        # 3. 재분류
        new_state = uncertainty_map.classify_state(new_vector)

        # 4. 타임라인 기록
        await self.timeline_service.add_event({
            "type": "risk_surge",
            "trigger": "time_tracking_exceeded",
            "task_id": session.task_id,
            "ratio": ratio,
            "delta": risk_delta,
            "state_before": current_state,
            "state_after": new_state
        })

        # 5. Obsidian 로그
        await self.obsidian_service.append_log(
            f"## {datetime.now()} - Time Tracking Alert\n"
            f"Task: {session.task_id} took {ratio:.1f}x baseline\n"
            f"Risk increased: technical +{risk_delta['technical']:.0%}, "
            f"timeline +{risk_delta['timeline']:.0%}\n"
            f"New state: {new_state}\n\n"
            f"#time-tracking #risk-surge #uncertainty\n"
        )
```

**핵심 결정사항**:
- **1.2배 기준**: 합리적 (통계적으로 20% 오차는 정상 범위)
- **리스크 증가량**: 선형 비례 (1.5배 초과 시 technical +0.3, timeline +0.2)
- **상한선**: technical/timeline은 각각 1.0을 초과하지 않음
- **타임라인 기록**: 모든 이벤트를 시각화 가능하도록 저장

---

## 5. 세컨 브레인(Obsidian) 통합 시나리오 구체화

### 5.1 PRD 명세 (불명확한 부분)
> "실행/결정/미티게이션/팁 로그를 태그와 함께 자동 append"

**문제점**:
- 파일 경로 미정의 (어느 vault? 어느 폴더?)
- 파일 명명 규칙 미정의 (daily? session 단위?)
- 충돌 해결 방안 미정의 (동시 append 시)
- 검색 인터페이스 미정의 (태그 검색 어떻게?)

### 5.2 구체적 구현 제안

#### 파일 구조
```
Obsidian Vault/
├── UDO/
│   ├── 2025/
│   │   ├── 11/
│   │   │   ├── 2025-11-25_session_001.md  # 세션 단위
│   │   │   ├── 2025-11-25_session_002.md
│   │   │   └── 2025-11-25_daily_summary.md  # 일일 요약
│   │   └── 12/
│   ├── templates/
│   │   ├── session_template.md
│   │   └── daily_summary_template.md
│   └── MOC_Uncertainty.md  # Map of Contents
```

#### 세션 로그 템플릿
```markdown
---
session_id: uuid-xxxx
project: UDO-Development-Platform
phase: implementation
start_time: 2025-11-25T10:00:00
end_time: 2025-11-25T12:30:00
tags: [uncertainty, mitigation, time-tracking]
---

# Session 2025-11-25 Morning

## Initial State
- **Uncertainty**: Probabilistic (confidence: 65%)
- **Dominant Risk**: Timeline (0.5)
- **Phase**: Implementation

## Events Timeline

### 10:15 - Mitigation Applied
- **Action**: Increase test coverage to 80%
- **Priority**: 1 (HIGH)
- **ROI**: 2.5
- **Result**: Timeline risk 0.5 → 0.3 ✅

### 11:30 - Time Tracking Alert
- **Task**: auth_refactor_001
- **Expected**: 60 min, **Actual**: 85 min (1.4x)
- **Risk Surge**: Technical +0.2, Timeline +0.15
- **New State**: Quantum (confidence: 50%)

### 12:00 - Guided Tip Applied
- **Tip**: "Add integration tests for auth flow"
- **Decision**: Applied manually
- **Notes**: Discovered edge case in OAuth flow

## End State
- **Uncertainty**: Quantum (confidence: 50%)
- **Dominant Risk**: Technical (0.6)
- **Next Actions**:
  - [ ] Add OAuth edge case tests
  - [ ] Review timeline estimate

## Key Learnings
- Auth refactoring more complex than estimated
- Integration tests reveal OAuth edge cases early

#session #2025-11-25 #implementation #auth
```

#### Obsidian Service 구현
```python
# backend/app/services/obsidian_service.py
from pathlib import Path
from datetime import datetime
import filelock

class ObsidianService:
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path) / "UDO"
        self.vault.mkdir(parents=True, exist_ok=True)

    def get_session_file(self, session_id: str) -> Path:
        """세션 파일 경로 생성"""
        today = datetime.now()
        year_month_dir = self.vault / str(today.year) / f"{today.month:02d}"
        year_month_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{today.strftime('%Y-%m-%d')}_session_{session_id[:8]}.md"
        return year_month_dir / filename

    async def append_event(self, session_id: str, event: dict):
        """이벤트 로그 append (파일락 사용)"""
        filepath = self.get_session_file(session_id)
        lock_path = filepath.with_suffix('.lock')

        async with filelock.FileLock(lock_path, timeout=5):
            # 파일이 없으면 템플릿으로 초기화
            if not filepath.exists():
                await self._initialize_session_file(filepath, session_id)

            # 이벤트 append
            event_md = self._format_event(event)
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n{event_md}\n")

    def _format_event(self, event: dict) -> str:
        """이벤트를 Markdown으로 포맷"""
        timestamp = event.get('timestamp', datetime.now())
        event_type = event.get('type', 'unknown')

        if event_type == 'mitigation_applied':
            return (
                f"### {timestamp.strftime('%H:%M')} - Mitigation Applied\n"
                f"- **Action**: {event['action']}\n"
                f"- **ROI**: {event['roi']:.2f}\n"
                f"- **Result**: {event['result']}\n"
            )
        elif event_type == 'risk_surge':
            return (
                f"### {timestamp.strftime('%H:%M')} - Time Tracking Alert\n"
                f"- **Task**: {event['task_id']}\n"
                f"- **Ratio**: {event['ratio']:.1f}x\n"
                f"- **Risk Surge**: {event['delta']}\n"
            )
        # ... 다른 이벤트 타입

    async def generate_daily_summary(self, date: datetime):
        """일일 요약 생성 (모든 세션 통합)"""
        sessions = self._get_sessions_for_date(date)

        summary = {
            'total_sessions': len(sessions),
            'mitigations_applied': 0,
            'risk_surges': 0,
            'state_changes': []
        }

        # 세션별 통계 집계
        for session in sessions:
            events = self._parse_session_events(session)
            summary['mitigations_applied'] += len([e for e in events if e['type'] == 'mitigation_applied'])
            summary['risk_surges'] += len([e for e in events if e['type'] == 'risk_surge'])

        # 요약 파일 생성
        summary_path = self.vault / str(date.year) / f"{date.month:02d}" / f"{date.strftime('%Y-%m-%d')}_daily_summary.md"
        await self._write_summary(summary_path, summary)
```

#### MOC (Map of Contents) 자동 업데이트
```python
async def update_moc(self):
    """MOC 파일 업데이트 (검색 인덱스)"""
    moc_path = self.vault / "MOC_Uncertainty.md"

    # 최근 30일 세션 목록
    recent_sessions = self._get_recent_sessions(days=30)

    moc_content = """# Uncertainty Management MOC

## Quick Links
- [[templates/session_template|Session Template]]
- [[templates/daily_summary_template|Daily Summary Template]]

## Recent Sessions (Last 30 Days)
"""

    for session in recent_sessions:
        date = session['date']
        session_id = session['id']
        phase = session['phase']
        state = session['final_state']

        moc_content += f"- [[{date}_session_{session_id[:8]}|{date} - {phase}]] - {state}\n"

    moc_content += """
## Search by Tags
- #mitigation - All mitigation actions
- #risk-surge - Risk increase events
- #time-tracking - Time tracking alerts
- #guided-tips - Applied tips

## Stats
- Total Sessions: {total}
- Mitigations Applied: {mitigations}
- Risk Surges: {surges}
""".format(
        total=len(recent_sessions),
        mitigations=sum(s['mitigations'] for s in recent_sessions),
        surges=sum(s['surges'] for s in recent_sessions)
    )

    with open(moc_path, 'w', encoding='utf-8') as f:
        f.write(moc_content)
```

---

## 6. 액션 아이템 (우선순위별)

### 🔴 CRITICAL (1주 내 완료)
1. **미티게이션 ACK 엔드포인트 구현**
   - 파일: `backend/app/routers/uncertainty.py`
   - 추가: `POST /api/uncertainty/ack/{mitigation_id}`
   - 기능: 리스크 하향 기록, Obsidian 로그
   - 담당: Backend 개발자
   - DoD: 테스트 통과 + API 문서 업데이트

2. **회로차단/캐시 TTL 적용**
   - 파일: `backend/app/core/circuit_breaker.py`, `backend/app/core/cache_manager.py`
   - 기능: 상태별 TTL, 실패율 임계 회로차단
   - 담당: Backend 개발자
   - DoD: 부하 테스트 통과 (실패율 >50% 시 회로 열림 확인)

3. **Bayesian 통합 스켈레톤 생성**
   - 파일: `src/udo_bayesian_integration.py`
   - 기능: `adaptive_threshold()`, `decide_with_uncertainty()` 메서드
   - 담당: ML 엔지니어 / Backend 개발자
   - DoD: Unit test 3개 통과 (Deterministic/Chaotic/Void 상태별)

### 🟡 HIGH (2-3주 내 완료)
4. **타임트래킹 1.2x 초과 로직 구현**
   - 파일: `backend/app/services/time_tracking_service.py`
   - 기능: `_trigger_uncertainty_event()` 메서드
   - 담당: Backend 개발자
   - DoD: Integration test 통과 (초과 → 리스크 상승 → 대시보드 반영)

5. **WebSocket 상태 푸시 구현**
   - 파일: `backend/app/routers/uncertainty.py`, `web-dashboard/lib/useUncertaintyWebSocket.ts`
   - 기능: 상태 변경 시 실시간 푸시
   - 담당: Fullstack 개발자
   - DoD: 연결 안정성 테스트 (재연결, 하트비트)

6. **모니터링 대시보드 카드 추가**
   - 파일: `web-dashboard/components/dashboard/monitoring-panel.tsx`
   - 기능: 회로차단 상태, AI 비용, 토큰 사용량 표시
   - 담당: Frontend 개발자
   - DoD: 디자인 시스템 준수, 반응형

### 🟢 MEDIUM (4-6주 내 완료)
7. **Bayesian 학습 루프 구현**
   - 파일: `src/udo_bayesian_integration.py`
   - 기능: 실행 결과 피드백 → confidence 업데이트
   - 담당: ML 엔지니어
   - DoD: 5회 실행 후 임계치 수렴 확인

8. **Guided Tips 패널 구현**
   - 파일: `web-dashboard/components/dashboard/guided-tips.tsx`, `config/guided_tips.yaml`
   - 기능: Phase/리스크별 지침, 적용/무시 액션
   - 담당: Frontend + Content 팀
   - DoD: 10개 팁 작성 + UX 피드백 반영

9. **Obsidian 자동 로그 파이프라인**
   - 파일: `backend/app/services/obsidian_service.py`
   - 기능: 세션 파일 생성, 이벤트 append, MOC 업데이트
   - 담당: Backend 개발자
   - DoD: 동시 append 테스트 (파일락 경합 없음)

### ⚪ LOW (2-3개월 내 완료)
10. **PRD 업로드/멀티모달 파싱**
    - 파일: `backend/app/routers/prd_upload.py`
    - 기능: 드래그앤드롭, MD/PDF 파싱, 임베딩
    - 담당: Backend + ML 팀
    - DoD: 파싱 정확도 >90% (샘플 10개 PRD)

11. **Slack/웹훅 알림 통합**
    - 파일: `backend/app/services/notification_service.py`
    - 기능: 리스크 급등/회로차단 시 Slack 푸시
    - 담당: DevOps
    - DoD: Slack 채널 테스트 성공

---

## 7. 결론 및 권장사항

### 7.1 PRD vNext 평가
| 평가 항목 | 점수 | 평가 |
|---------|------|------|
| 비전 명확성 | ⭐⭐⭐⭐⭐ | 예측→완화→적응 흐름 명확 |
| 요구사항 구체성 | ⭐⭐⭐⭐ | API 계약 대부분 정의, 일부 보완 필요 |
| 구현 가능성 | ⭐⭐⭐⭐ | 기존 아키텍처와 잘 통합, 복잡도 관리 필요 |
| 우선순위 명확성 | ⭐⭐⭐⭐ | 7단계 순서 타당, 일부 조정 권장 |
| 테스트 전략 | ⭐⭐⭐ | 기본 전략 있으나 상세화 필요 |

**종합 평점**: 4.2/5.0 ⭐⭐⭐⭐

### 7.2 핵심 권장사항

1. **즉시 조치 필요**:
   - ✅ 미티게이션 ACK 엔드포인트 구현 (Phase 1 완료 조건)
   - ✅ 회로차단/캐시 TTL 적용 (시스템 안정성)
   - ✅ Bayesian 통합 스켈레톤 생성 (Phase 3 시작 조건)

2. **구현 순서 조정**:
   - 원래: 1→2→3→4→5→6→7
   - 권장: 1→2→3→**4(모니터링)**→5(Tips)→6(PRD)→7

3. **명세 보완 필요**:
   - 타임트래킹 1.2x 초과 로직 상세화 (섹션 4.3 참조)
   - Obsidian 파일 구조 및 템플릿 정의 (섹션 5.2 참조)
   - 회로차단 임계값 설정 가이드 (dev vs prod)

4. **아키텍처 개선**:
   - WebSocket 하이브리드 방식 도입 (폴링 폴백)
   - 캐시 일관성 보장 (상태 변경 시 무효화)
   - 파일락 기반 Obsidian append (경합 방지)

### 7.3 성공 확률 평가

| Phase | 구현 난이도 | 리스크 | 성공 확률 | 비고 |
|-------|----------|-------|---------|------|
| 1. 불확실성 브리지 | ⭐⭐ (Low) | 낮음 | 95% | 대부분 구현 완료 |
| 2. 미티게이션/타임트래킹 | ⭐⭐⭐ (Medium) | 중간 | 85% | 로직 상세화 필요 |
| 3. Bayesian 통합 | ⭐⭐⭐⭐ (High) | 높음 | 70% | 복잡도 높음, 점진적 접근 권장 |
| 4. 모니터링/알림 | ⭐⭐ (Low) | 낮음 | 90% | 표준 패턴 활용 가능 |
| 5. Guided Tips | ⭐⭐⭐ (Medium) | 중간 | 80% | 콘텐츠 작성 시간 필요 |
| 6. PRD 업로드 | ⭐⭐⭐⭐⭐ (Very High) | 높음 | 60% | 멀티모달 파싱 복잡, 후순위 권장 |
| 7. 테스트/운영 | ⭐⭐⭐ (Medium) | 낮음 | 85% | 기존 테스트 인프라 활용 |

**전체 프로젝트 성공 확률**: **78%** (High-Risk 항목 제외 시 85%)

### 7.4 다음 단계

1. **이 분석 보고서 리뷰** (팀 미팅, 30분)
2. **액션 아이템 할당** (담당자 지정, JIRA 티켓 생성)
3. **Phase 1 완료** (미티게이션 ACK + 회로차단, 1주)
4. **Phase 2 착수** (타임트래킹 연동, 2-3주)
5. **주간 체크포인트** (매주 금요일, 진행상황 리뷰)

---

**문서 작성자**: Claude Code Analysis Engine
**최종 검토**: 2025-11-25
**다음 리뷰 예정**: Phase 1 완료 시 (1주 후)
