# Refactoring Validation & Next Steps

## 우선순위별 개선 사항
1. **Backend Router Modularization** – 라우터를 모듈화하는 헬퍼(`app/routers/__init__.py`)를 사용합니다.
2. **Central Configuration Module** – CORS, 로깅, DB, 기능 플래그 등을 관리하는 `app/config.py`를 도입합니다.
3. **Service Container & DI** – FastAPI `Depends`를 활용해 서비스 컨테이너(`app/services/container.py`)를 제공합니다.
4. **Typed Pydantic Schemas** – 프론트엔드 TypeScript 타입과 일치하도록 API 스키마를 정렬합니다.
5. **Comprehensive Test Suite** – 새로운 Kanban 라우터에 대한 통합 테스트를 작성해 커버리지를 85% 이상 확보합니다.
6. **CI/CD Enhancements** – pre‑commit 훅과 GitHub Actions를 통해 린트, 보안, 성능 검사를 자동화합니다.
7. **Documentation Automation** – OpenAPI 스펙, 아키텍처 다이어그램, 온보딩 가이드를 자동 생성합니다.
8. **Frontend Kanban Integration** – 타입이 지정된 API 클라이언트, Zustand 스토어, lazy‑load UI 컴포넌트를 구현합니다.
9. **Performance Benchmarking** – 1,000개의 작업에 대해 DAG < 50 ms, DB < 50 ms, API p95 < 500 ms를 목표로 벤치마크 스크립트를 실행합니다.
10. **Uncertainty Map Gap Mitigation** – Q5‑1, Q6, Q7의 낮은 신뢰도 항목을 개선합니다.

## 멀티‑에이전트 및 MCP 전략
- **Architect (Antigravity)** – 전체 설계와 전략을 수립합니다.
- **Builder (Claude Code)** – 실제 코드 구현을 담당합니다.
- **Prophet (MCP‑Sequential)** – 순차적인 작업 흐름을 관리합니다.
- **Reviewer (MCP‑Codex)** – 코드 리뷰와 품질 검증을 수행합니다.
- **Tester (MCP‑Playwright)** – 자동화 테스트와 UI 검증을 수행합니다.

## 벤치마크 및 안정성 목표
- **데이터베이스** 응답 시간 < 50 ms
- **API** p95 응답 시간 < 500 ms
- **UI** 첫 화면 로드 시간(TTI) < 3 s, LCP < 2.5 s
- **WebSocket** 지연 시간 < 50 ms
- **AI 제안** 응답 시간 < 3 s

### 적응형 트리거
- 성능이 기준을 초과하면 페이징, 캐시 확대, 기능 플래그 전환 등으로 자동 전환합니다.

---

**부작용 검토**
- 기존 라우터를 모듈화하고 설정 파일을 분리했으며, 모든 변경 사항은 테스트와 CI 파이프라인을 통해 검증됩니다. 현재까지 한국어 외의 문자(중국어, 일본어 등)는 포함되지 않았으며, 모든 문서는 순수 한국어와 영어(키워드)만 사용했습니다.
