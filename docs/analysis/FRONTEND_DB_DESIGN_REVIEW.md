# Frontend DB 연결 설계 검토

**Date**: 2025-12-02
**Reviewer**: Claude Code (VibeCoding Enhanced + Constitution)
**Status**: ✅ APPROVED (조건부)

## 🎯 요구사항

1. Frontend 대시보드를 Real PostgreSQL DB에 연결
2. Tanstack Query 활용
3. 기존 Mock 데이터 대체
4. 실시간 업데이트 유지

## 🛡️ 8-Risk Check (Constitution P1)

### 1. 기존 시스템 영향 ⚠️ MEDIUM
**분석:**
- 현재: Mock 데이터 → 변경: Real DB API 호출
- 영향 범위: 5개 페이지 (/, /quality, /time-tracking, /ck-theory, /gi-formula)
- WebSocket 실시간 업데이트는 유지

**완화 전략:**
- Progressive migration (페이지별 순차 적용)
- Mock fallback 유지 (API 실패 시)
- Feature flag로 제어 가능

**Risk Level**: 🟡 MEDIUM → 🟢 LOW (완화 후)

### 2. Git 충돌 가능성 🟢 LOW
**분석:**
- 신규 파일 생성이 주: `lib/api/`, `lib/hooks/use*Query.ts`
- 기존 컴포넌트 수정: props 타입만 변경
- 병렬 작업 없음 (단독 진행)

**Risk Level**: 🟢 LOW

### 3. 멀티세션 이슈 🟢 LOW
**분석:**
- 프론트엔드 변경만 (파일 잠금 이슈 없음)
- Tanstack Query의 자동 캐시 무효화
- WebSocket으로 실시간 동기화

**Risk Level**: 🟢 LOW

### 4. 성능 영향 🟢 LOW
**분석:**
- Mock (즉시) → API (50-200ms) 응답 시간 증가
- Tanstack Query 캐싱으로 완화
- Stale-while-revalidate 전략

**측정 기준:**
- 초기 로드: <2s (목표)
- 페이지 전환: <500ms (목표)
- API 응답: <200ms (P95)

**Risk Level**: 🟢 LOW

### 5. 복잡도 증가 🟡 MEDIUM
**분석:**
- 새로운 계층 추가: API client + React Query hooks
- 파일 증가: +10-15개
- 학습 곡선: Tanstack Query (팀에 익숙함)

**완화 전략:**
- API client 패턴 표준화
- 커스텀 훅 재사용
- 명확한 폴더 구조

**Risk Level**: 🟡 MEDIUM → 🟢 LOW (표준화 후)

### 6. 사용자 워크플로우 변경 🟢 LOW
**분석:**
- UI/UX 변경 없음
- 기능 동일
- 응답 속도 약간 증가 (Mock → API)

**Risk Level**: 🟢 LOW

### 7. 롤백 가능성 ✅ EXCELLENT
**3단계 롤백:**
1. **즉시 롤백** (<1분): Feature flag OFF → Mock 데이터 복원
2. **1분 롤백**: Git revert → 이전 커밋 복원
3. **5분 롤백**: Docker 재시작 → 전체 복구

**Risk Level**: 🟢 LOW

### 8. 테스트 방법 ✅ CLEAR
**테스트 전략:**
1. Unit: API client functions (Jest)
2. Integration: React Query hooks (React Testing Library)
3. E2E: Critical paths (Playwright) ← 다음 단계

**커버리지 목표:** 80%

**Risk Level**: 🟢 LOW

---

## 📊 종합 위험도 평가

| Risk | Level | 완화 후 |
|------|-------|---------|
| 기존 시스템 영향 | 🟡 MEDIUM | 🟢 LOW |
| Git 충돌 | 🟢 LOW | 🟢 LOW |
| 멀티세션 | 🟢 LOW | 🟢 LOW |
| 성능 | 🟢 LOW | 🟢 LOW |
| 복잡도 | 🟡 MEDIUM | 🟢 LOW |
| 워크플로우 | 🟢 LOW | 🟢 LOW |
| 롤백 | 🟢 LOW | 🟢 LOW |
| 테스트 | 🟢 LOW | 🟢 LOW |

**Overall Risk**: 🟢 **LOW** (안전하게 진행 가능)

---

## 🎨 GI Formula 평가 (Creative Thinking v3.0)

### 설계 품질 점수

**General Inventive (GI) = (Novel × Useful × Feasible) / Risk**

#### 1. Novelty (새로움) - 6/10
- Tanstack Query 패턴: 업계 표준 (낮은 새로움)
- Real DB 연결: 프로젝트에는 새로움 (높은 새로움)
- **평균**: 6/10

#### 2. Usefulness (유용성) - 9/10
- 데이터 지속성 확보 (Mock → Real DB)
- 실시간 협업 가능
- 확장성 향상
- **점수**: 9/10

#### 3. Feasibility (실현 가능성) - 9/10
- 기술 스택 준비 완료 (Tanstack Query 설치됨)
- 백엔드 API 완성 (4/4 테스트 통과)
- 팀 경험 충분
- **점수**: 9/10

#### 4. Risk (위험도) - 2/10 (낮을수록 좋음)
- 8-Risk Check 결과: 대부분 LOW
- 롤백 전략 명확
- **점수**: 2/10

### GI Formula 계산
```
GI = (6 × 9 × 9) / 2 = 243

기준:
- 0-100: Poor (재설계 필요)
- 101-200: Good (진행 가능)
- 201-300: Excellent (강력 추천) ← 현재
- 301+: Outstanding
```

**결과**: 🎯 **243점 (Excellent)** - 강력 추천!

---

## 🏗️ 설계 아키텍처

### 폴더 구조
```
web-dashboard/
├── lib/
│   ├── api/
│   │   ├── client.ts          # Axios instance + interceptors
│   │   ├── endpoints.ts       # API endpoint definitions
│   │   ├── projects.ts        # Project API calls
│   │   ├── quality.ts         # Quality metrics API
│   │   └── time-tracking.ts  # Time tracking API
│   ├── hooks/
│   │   ├── useProjects.ts     # Project React Query hooks
│   │   ├── useQuality.ts      # Quality React Query hooks
│   │   └── useTimeTracking.ts # Update existing with API
│   └── types/
│       ├── api.ts             # API response types
│       └── [existing].ts
```

### API Client Pattern
```typescript
// lib/api/client.ts
export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Interceptors for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Fallback to mock on error
    if (error.response?.status >= 500) {
      return fallbackToMock(error.config);
    }
    throw error;
  }
);
```

### React Query Pattern
```typescript
// lib/hooks/useProjects.ts
export const useProjects = () => {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
    retry: 2,
    onError: (error) => {
      // Fallback to mock
      return mockProjectsData;
    }
  });
};
```

### WebSocket Integration
```typescript
// Keep existing WebSocket for real-time updates
useEffect(() => {
  socket.on('project_updated', (data) => {
    queryClient.invalidateQueries(['projects']);
  });
}, []);
```

---

## 🚀 구현 순서

### Phase 1: API Client 기반 (30분)
1. API client setup (axios + interceptors)
2. Endpoint definitions
3. Type definitions

### Phase 2: React Query 통합 (45분)
1. Custom hooks 작성 (useProjects, useQuality)
2. 기존 useTimeTracking 업데이트
3. Mock fallback 구현

### Phase 3: 컴포넌트 연결 (30분)
1. 메인 대시보드 (/page.tsx)
2. Quality 페이지
3. Time Tracking 페이지

### Phase 4: 검증 (15분)
1. 로컬 테스트
2. Error case 확인
3. Performance check

**Total**: ~2시간

---

## 🔒 안전장치 (Safety Net)

### 1. Feature Flag
```typescript
const USE_REAL_DB = process.env.NEXT_PUBLIC_USE_DB === 'true';

export const useProjects = () => {
  if (!USE_REAL_DB) {
    return useMockProjects();
  }
  return useQuery(/* real API */);
};
```

### 2. Graceful Degradation
```typescript
onError: (error) => {
  console.warn('API failed, falling back to mock', error);
  return MOCK_DATA;
}
```

### 3. Circuit Breaker
```typescript
let failureCount = 0;
const MAX_FAILURES = 3;

if (failureCount >= MAX_FAILURES) {
  // Auto switch to mock mode
  USE_REAL_DB = false;
}
```

---

## ✅ 승인 조건

### Required Before Implementation
- [x] 8-Risk Check 완료 (Overall: LOW)
- [x] GI Formula 평가 (243점: Excellent)
- [x] 롤백 전략 수립 (3단계)
- [x] 아키텍처 설계 완료
- [x] 안전장치 설계 완료

### Approval Decision
**Status**: ✅ **APPROVED**

**Conditions**:
1. Progressive migration (페이지별 순차 적용)
2. Mock fallback 반드시 구현
3. Feature flag로 제어
4. E2E 테스트 다음 단계에서 수행

---

## 📝 참고 문서

- Backend API: `docs/DATABASE_INTEGRATION_COMPLETE.md`
- API Endpoints: `http://localhost:8000/docs`
- Tanstack Query Docs: https://tanstack.com/query/latest
- Constitution P1: Design Review First 원칙 적용 완료

---

**Reviewed By**: Claude Code (VibeCoding Enhanced + Constitution P1 + GI Formula)
**Next Action**: 구현 시작 (Phase 1: API Client 기반)
