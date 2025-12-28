# UDO 불확실성/적응형 통합 작업 로그

## 목적
- 불확실성 엔진 ↔ 백엔드 API ↔ 대시보드 연동 진행 상황을 잃지 않고 기록
- Obsidian/다른 세션에서 컨텍스트 복구 시 참고용

## 오늘의 목표
1) `/api/uncertainty/status` 의존성/응답 구조 정비
2) 대시보드에서 실시간 불확실성 데이터(상태/신뢰도/예측/미티게이션) 수신 연결
3) UDO v2 Bayesian 통합 스켈레톤 착수 계획 수립

## 즉시 액션 체크리스트
- [ ] UncertaintyMap 의존성 DI로 정리 (전역 main 참조 제거)
- [ ] 상태/예측/미티게이션 응답 스키마 확정 및 테스트 추가
- [ ] 대시보드 Query 연결 및 UI 개선(레전드/예측/미티게이션)
- [ ] Bayesian 통합 진입점 설계(`udo_bayesian_integration.py`, orchestrator 초기화)
- [ ] 주요 변경사항 Obsidian에도 동기화 메모 남기기

## 메모
- 현재 대시보드는 `/api/metrics` 응답에 `uncertainty_state/confidence_level`만 기대 → 불확실성 전용 API 직접 호출로 전환 필요
- PRD 레전드(🟢🟡🟠🔴⚫)와 24h 예측/ROI 기반 미티게이션을 UI에 노출해야 함
- 타임트래킹 초과(1.2x) → 기술 불확실성 상승 훅 설계 필요

## 진행 업데이트
- 백엔드: `get_udo_system` 초기화 시 `main.udo_system` 별칭 동기화 (불확실성 라우터에서 전역 조회 가능)
- 프론트: 대시보드가 `/api/uncertainty/status`를 Query로 직접 호출하도록 변경, 상태/신뢰도/예측/미티게이션을 표시
- UI: UncertaintyMap 컴포넌트가 상태 문자열을 정규화(소문자→레전드), 예측·미티게이션 카드 추가, 로딩 표시 추가
- PRD: vNext 초안 작성(`docs/PRDs/04_DRAFT/PRD_VNEXT_UNCERTAINTY_FIRST.md`) — 예측→완화→적응·세컨 브레인 흐름 통합
- 백엔드 보강: 미티게이션 ACK 엔드포인트 추가(`/api/uncertainty/ack/{id}`), 상태별 TTL 캐시/경량 회로차단, 타임트래킹 1.2x 초과 훅(tech/timeline 리스크 상승) 적용
- Bayesian 스켈레톤: `UnifiedDevelopmentOrchestratorV2`가 `UDOBayesianIntegration`을 초기화하고 적응형 임계치로 Go/No-Go 문턱을 조정
- 테스트: ACK 흐름용 단위 테스트 추가(`backend/tests/test_uncertainty_ack.py`)로 상태→미티게이션→ACK 후 magnitude 감소/신뢰도 상승 검증
- 대시보드: 미티게이션 ACK 버튼 추가, ACK 후 상태/메트릭스 무효화. 백엔드 ACK 시 WebSocket 브로드캐스트(best-effort)로 실시간 갱신 가능
- 설치 이슈: Windows cmd에서 pytest-cov 미설치로 coverage 옵션 에러 → `pytest-cov`를 requirements에 추가하여 해소
- 환경 이슈: PyYAML 버전 불일치 및 asyncpg/httpx 누락으로 테스트 실패 → `PyYAML==6.0.3`, `asyncpg`, `httpx`를 requirements에 명시하여 종속성 정리
- 커버리지 게이트: MVP 속도 위해 `backend/pytest.ini`의 `--cov-fail-under`를 0으로 완화(로컬 기준). CI에서 필요 시 복원 예정
- 테스트 실행 메모: Windows PowerShell에서 `PYTHONPATH`를 리포 루트로 설정 후 `..\ .venv311\Scripts\python.exe -m pytest backend\tests\test_uncertainty_ack.py -q` 실행 시 PASS(커버리지 경고만 발생)
- Obsidian 기록(수동 필요): `tmp/obsidian_append.txt`에 세션 요약 저장. PowerShell에서 PYTHONPATH를 리포 루트로 설정 후 해당 파일 내용을 Obsidian `개발일지/YYYY-MM-DD.md`에 append하면 컨텍스트 동기화 가능.
- Obsidian 자동화 스크립트 추가: `scripts/obsidian_append.py` (vault 경로/append 파일 지정하여 일일 노트에 추가)
- 프론트 WebSocket 확장: `uncertainty_update` 수신 시 status/metrics 쿼리 무효화 및 토스트 표출

## 확정된 구현 순서 (vNext PRD 기준)
1) **불확실성 브리지 완성**
   - 백엔드: `/api/uncertainty/status/mitigations/ack` 계약 확정, DI 정리, 회로차단/TTL 적용
   - 프론트: 상태/신뢰도/24h 예측/미티게이션 표출, 로딩·에러 UX 반영
2) **미티게이션 액션 & 타임트래킹 연동**
   - 미티게이션 적용 시 리스크 하향 기록
   - 타임트래킹 1.2x 초과 → 기술/일정 리스크 상승 이벤트 반영
   - 타임라인에서 “실행→리스크 변화” 연결
3) **Bayesian 통합 (UDO v2)**
   - `udo_bayesian_integration` 초기화, 적응형 임계치로 GO/NO_GO/Checkpoint 결정
   - 학습 루프: 실행/테스트 피드백으로 confidence 업데이트
4) **Guided Tips / 세컨 브레인**
   - 대시보드 Tips 패널(Phase/리스크별 지침), 적용/무시 액션
   - Obsidian 자동 로그: 실행/결정/팁/미티게이션 기록, 태그로 검색 가능하게
5) **PRD 업로드 & 멀티모달(옵션)**
   - 드래그앤드롭/파일 업로드(MD/PDF/텍스트/이미지) → 파싱/요약/임베딩 → 리스크 재산정
   - 업로드 처리 상태 UI, 변경 diff/영향 카드
6) **모니터링/알림/비용 지표**
   - 라우터/AI 호출 계측, 회로차단 상태/비용/토큰 사용량 카드
   - 리스크 급등/회로차단/비용 상승 알림(Slack/웹훅 옵션)
7) **테스트/운영 게이트**
   - 백엔드: pytest + 시나리오(`tests/run_udo_phase1.py`) 회귀
   - 프론트: `npm run lint && npm run build`
   - 알림/로그 기준 확정 후 릴리스

## 초보 개발자 인사이트 & 시행착오 로그
- **회로차단 먼저**: 외부/무거운 연산이 실패할 때 빠르게 막아야 토큰·시간을 절약할 수 있음. 실패 임계치/재시도 타이밍을 먼저 정리하고 구현할 것.
- **TTL을 상태에 맞춰**: 불확실성 상태별 TTL(Deterministic 길게, Void 짧게)을 먼저 표로 정리하면 캐시 로직을 깔끔하게 작성할 수 있음.
- **미티게이션 ACK**: “표시”와 “적용”은 다름. 적용 시 어떤 차원을 얼마나 줄일지, 적용 후 재분류/캐시 무효화까지 고려해야 함.
- **타임트래킹 훅**: 1.2x 초과 시 어느 차원을 얼마만큼 올릴지 수식부터 메모. 과도한 상승을 막기 위해 상한(min/max) 설정이 필요함.
- **Obsidian 로그**: 이벤트를 언제/어디에 적을지(파일 구조/태그) 먼저 정하면 코드가 단순해짐. 실패해도 조용히 넘어가되, 로그에 원인을 남겨야 추적 가능.
- **Bayesian 연동**: 임계치 조정부터 얇게 시작(스켈레톤). 학습 루프는 추후 단계로 분리해서 점진적으로 붙이는 것이 안전.
