# Codex 리팩토링을 위한 컨텍스트

## 프로젝트 현재 상태 (2025-11-18 19:43)

### 최근 작업 (Git 커밋 590754e)
- **해결한 문제**: 503 Service Unavailable 에러
- **근본 원인**: 포트 8000에 4개 백엔드 서버 동시 실행
- **해결 방법**:
  - 모든 Python 프로세스 종료 (wmic 사용)
  - Mock Service 초기화 순서 수정 (라우터 import 이전으로)
  - Pydantic 검증 필드 추가 (current_phase, is_archived)

### 현재 시스템 구성
```
UDO-Development-Platform/
├── backend/
│   ├── main.py (FastAPI 서버, Mock Service 활성화)
│   ├── app/
│   │   ├── routers/ (project_context, quality_metrics, version_history, modules)
│   │   ├── services/ (mock_project_service, session_manager_v2, redis_client)
│   │   └── models/ (project_context, quality_metrics, version_history)
│   └── async_database.py (PostgreSQL 연동 - 현재 비활성)
├── src/
│   ├── unified_development_orchestrator_v2.py (UDO 메인)
│   ├── uncertainty_map_v3.py (불확실성 맵)
│   └── three_ai_collaboration_bridge.py (AI 협업)
├── web-dashboard/ (Next.js 프론트엔드)
└── tests/
```

### 현재 작동 중인 서비스
- ✅ Backend API (http://localhost:8000) - Mock Service 모드
- ✅ Frontend Dashboard (http://localhost:3000)
- ❌ PostgreSQL (미설치 - Mock Service로 대체)
- ❌ Redis (선택적 - 분산 기능 비활성)

### Playwright 테스트 결과 (100% PASS)
- 콘솔 에러: 0개
- 네트워크 에러: 0개
- API 요청: 5/5 성공 (200 OK)

---

## Codex 리팩토링 피드백 정리

### 우선순위 HIGH (즉시 수정 필요)

#### 1. Import 실패 조용히 잠재화
**위치**: `src/unified_development_orchestrator_v2.py`

**문제**:
```python
try:
    from adaptive_system_selector_v2 import AdaptiveSystemSelector
except:
    # 광범위한 except, 조용히 실패
    AdaptiveSystemSelector = None  # fallback
```

**위험**: 런타임에서 None 객체 사용 시 AttributeError

**해결 방안**:
- 예외를 명시적으로 로깅
- 필수/선택 모듈 구분
- 명확한 설정 플래그로 제어

#### 2. print 기반 로깅
**위치**: 모든 src/ 파일

**문제**:
- 운영 환경에서 로깅 레벨/채널 제어 불가
- 비ASCII 메시지 혼재 (인코딩 문제)

**해결 방안**:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("...")  # print 대체
```

#### 3. 파일 경쟁 조건
**위치**: `_save_learning_data`, `save_state`

**문제**:
- 동시 실행 시 파일 덮어쓰기 위험
- Lock 없음
- 경로 고정

**해결 방안**:
- 파일 경로를 호출자가 주입
- tempfile 사용
- filelock 라이브러리 사용

#### 4. 하드코딩된 비즈니스 로직
**위치**: `calculate_weighted_confidence`

**문제**:
- 가중치/threshold가 코드에 하드코딩
- 테스트 불가
- 조정 어려움

**해결 방안**:
```python
# config.yaml
phase_weights:
  ideation: 0.3
  design: 0.5
  implementation: 0.7
```

#### 5. ASCII 아트 깨짐
**위치**: `src/uncertainty_map_v3.py:visualize_map`

**문제**:
```python
bars = "█" * filled + "░" * empty  # 비ASCII, Windows에서 깨짐
state_icons = {"??"...}  # 인코딩 문제
```

**해결 방안**:
- ASCII 전용 심볼 사용: `[====    ]`
- 또는 텍스트 요약으로 축소

#### 6. ML 모델 미학습
**위치**: `src/uncertainty_map_v3.py`

**문제**:
- `is_trained` 플래그만 설정, 실제 `fit()` 호출 없음
- 예측 품질 불명

**해결 방안**:
- 학습 데이터 수집/fit 경로 추가
- 또는 비학습 시 규칙 기반으로 고정

#### 7. 파일 경로 CWD 의존
**위치**: `uncertainty_history_<project>.json`

**문제**:
- 패키지로 쓸 때 권한/경로 문제

**해결 방안**:
```python
from pathlib import Path
data_dir = Path.home() / ".udo" / "data"
history_file = data_dir / f"uncertainty_history_{project}.json"
```

#### 8. Mock AI 응답
**위치**: `src/three_ai_collaboration_bridge.py`

**문제**:
- 실제 Codex/Gemini API 연동 없음
- 가용성 체크가 조용히 실패

**해결 방안**:
- 가용성 체크 에러를 호출자에 반환
- 결과에 availability 메타 포함

#### 9. 테스트 비ASCII 깨짐
**위치**: `tests/run_udo_phase1.py`, `tests/test_udo_v3_integration.py`

**문제**:
- UTF-8 인코딩 표시 문제

**해결 방안**:
- 소스 파일 UTF-8로 재저장
- 또는 ASCII로 정리

#### 10. 테스트 단언 부족
**위치**: 모든 tests/

**문제**:
- 데모/출력 확인에 집중
- 실제 assert 거의 없음

**해결 방안**:
```python
def test_calculate_confidence():
    udo = UnifiedDevelopmentOrchestrator("test")
    result = udo.calculate_weighted_confidence(phase="design")
    assert 0 <= result <= 1.0
    assert isinstance(result, float)
```

---

## 빠른 개선 우선순위 (Codex 작업 순서)

### Step 1: 로깅 정비 (30분)
- [ ] print → logging 전환
- [ ] 외부 의존성 로딩 실패 warning
- [ ] 필수 모듈 즉시 실패

### Step 2: 설정 분리 (30분)
- [ ] `config/udo_config.yaml` 생성
- [ ] Phase별 가중치/threshold/패턴 이동
- [ ] 입력 검증 추가

### Step 3: ASCII 문제 해결 (15분)
- [ ] `visualize_map` ASCII-only로 교체
- [ ] 테스트 파일 UTF-8 재저장

### Step 4: ML 분기 명확화 (20분)
- [ ] `predict_evolution`에서 비학습 시 규칙 기반 사용
- [ ] fit 경로 추가 (데이터 shape 검증)

### Step 5: 파일 경로 개선 (20분)
- [ ] 모든 파일 저장 함수에 인자 주입
- [ ] 기본값은 `~/.udo/` 사용
- [ ] filelock 추가

### Step 6: Import 실패 처리 (30분)
- [ ] try/except에 명시적 logging.warning
- [ ] 필수 모듈과 선택 모듈 구분
- [ ] None 체크 추가

### Step 7: 테스트 보강 (1시간)
- [ ] `test_calculate_weighted_confidence` 단위 테스트
- [ ] `test_analyze_context` 패턴별 검증
- [ ] `test_collaborate` mock 결과 단언

### Step 8: 타입/검증 추가 (20분)
- [ ] Optional 방어 (project_name, phase 등)
- [ ] ValueError raise

---

## 중기 리팩토링 (이후 작업)

### 의존성 주입
```python
class UnifiedDevelopmentOrchestrator:
    def __init__(
        self,
        project_name: str,
        uncertainty_map=None,  # 주입 가능
        selector=None,
        ai_bridge=None
    ):
        self.uncertainty_map = uncertainty_map or UncertaintyMap()
        self.selector = selector or AdaptiveSystemSelector()
        self.ai_bridge = ai_bridge or ThreeAICollaborationBridge()
```

### 전략 패턴
```python
# 단계별 로직 분리
class PhaseStrategy(ABC):
    @abstractmethod
    def calculate_confidence(self, context): pass

class IdeationStrategy(PhaseStrategy):
    def calculate_confidence(self, context):
        return context.get("innovation", 0.5) * 0.3
```

### 도메인 상수
```python
# constants.py
PHASES = ["ideation", "design", "mvp", "implementation", "testing"]
PHASE_THRESHOLDS = {
    "ideation": 0.3,
    "design": 0.5,
    # ...
}
```

---

## 제약사항 및 주의사항

### 유지해야 할 것
- ✅ Mock Service 모드 (PostgreSQL 없어도 작동)
- ✅ FastAPI 라우터 구조
- ✅ Pydantic 모델 검증
- ✅ Playwright 테스트 통과 상태

### 변경하면 안 되는 것
- ❌ API 엔드포인트 경로 (`/api/health`, `/api/projects/current` 등)
- ❌ Pydantic 모델 필드명 (프론트엔드 의존)
- ❌ Mock Service 인터페이스

### 테스트 필수
- 리팩토링 후 `pytest tests/` 전체 통과
- Playwright 테스트 재실행 (`python test_dashboard.py`)
- API 엔드포인트 200 OK 확인

---

## 현재 알려진 이슈

1. **여러 백그라운드 서버 실행 중** (13개 프로세스)
   - 해결: 작업 전 `wmic process where "name='python.exe'" delete`
   - 단일 서버만 시작

2. **Windows 인코딩 (cp949)**
   - UTF-8 wrapper 필수: `sys.stdout = io.TextIOWrapper(...)`

3. **프론트엔드 빌드 경고**
   - Next.js hydration 경고 (무시 가능)
   - Tailwind config 경고 (무시 가능)

---

## 성공 기준

### 리팩토링 완료 조건
- [ ] 모든 print → logging 전환
- [ ] config.yaml로 설정 분리
- [ ] 파일 경로 주입 가능
- [ ] Import 실패 명시적 로깅
- [ ] ASCII 문제 해결
- [ ] 테스트 80% 이상 커버리지
- [ ] pytest 전체 통과
- [ ] Playwright 테스트 통과
- [ ] API 엔드포인트 정상 작동

### 품질 지표
- 로깅 레벨 일관성: INFO/WARNING/ERROR
- 타입 힌팅 커버리지: 80%+
- 테스트 커버리지: 80%+
- 순환 복잡도: <10 (함수당)

---

## 참고 자료

- Git 커밋: 590754e
- Obsidian 개발일지: `개발일지/2025-11-18/UDO-503-Error-Root-Cause-Fix.md`
- Playwright 테스트: `test_dashboard.py`
- API 문서: http://localhost:8000/docs (FastAPI Swagger)

---

**작업 시작 전 확인**:
1. 모든 백그라운드 서버 종료
2. Git 브랜치 생성: `git checkout -b refactor/codex-improvements`
3. 테스트 베이스라인 확인: `pytest tests/ -v`
