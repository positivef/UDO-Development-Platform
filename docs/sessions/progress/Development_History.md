# Development History & Context

## 1. 프로젝트 배경
- **UDO Development Platform**은 AI 협업, 불확실성 지도(Uncertainty Map), Kanban 등 다양한 모듈을 통합하는 플랫폼입니다.
- 현재 백엔드(FastAPI)와 프론트엔드(Next.js) 환경에서 동작하고 있으며, 최근 **시간 추적 대시보드**의 React hydration 오류를 해결했습니다.

## 2. 최근 진행 상황 (2025‑12‑04 ~ 2025‑12‑05)
| 날짜 | 주요 작업 | 비고 |
|------|-----------|------|
| 2025‑12‑04 | `CLAUDE.md`에 **Refactoring Validation & Next Steps** 섹션 추가 | 우선순위 10가지 개선 항목 정의
| 2025‑12‑04 | `docs/OBSIDIAN_LOG_2025-12-04.md`에 오류 해결 과정 기록 | 한국어·영어 혼용 없이 정리
| 2025‑12‑05 | `docs/Refactoring_Validation_Summary.md`에 동일 요약 저장 (프로젝트 내부) | Claude가 바로 참고 가능하도록 함
| 2025‑12‑05 | **워크스페이스에 Obsidian Vault 폴더 추가** 요청 → 아직 적용 전 (사용자 확인 필요) |

## 3. 현재 목표 및 작업 순서
1. **계획 검증** – 전체 구조를 먼저 검토하고 `implementation_plan.md`에 정리 후 팀(멀티‑에이전트) 리뷰.
2. **핵심 모듈 TDD 적용** – 라우터 모듈화, DI 컨테이너, Kanban 모델에 대해 테스트‑우선 개발.
3. **보조 파일 구현** – 설정(`app/config.py`), 서비스 컨테이너, 프론트엔드 스토어·API·컴포넌트.
4. **CI/CD 파이프라인** – GitHub Actions에 테스트·린트·벤치마크 자동화.
5. **벤치마크 스크립트** – `scripts/benchmark_kanban.py`로 성능 목표 검증.
6. **Walkthrough 기록** – `walkthrough.md`에 진행 상황을 단계별로 기록.

## 4. 멀티‑에이전트 & MCP 전략
- **Architect (Antigravity)** – 전체 설계·전략 수립
- **Builder (Claude Code)** – 실제 코드 구현 (이 파일을 참고)
- **Prophet (MCP‑Sequential)** – 순차적 작업 흐름 관리
- **Reviewer (MCP‑Codex)** – 코드 리뷰·품질 검증
- **Tester (MCP‑Playwright)** – 자동화 테스트·UI 검증

## 5. 부작용 방지 체크리스트
- 기존 라우터에 직접 추가된 Kanban 라우터를 **모듈화 헬퍼**로 교체
- 설정 파일(`app/config.py`)에 CORS, 로그 레벨, DB URL 명시
- DI 컨테이너에 서비스 인스턴스 등록 후 FastAPI `Depends` 사용
- 모든 신규 파일은 **테스트**와 **CI**에 포함되어 회귀 방지
- 한국어 외 문자(중국어·일본어) 사용 금지 – 모든 문서는 순수 한국어와 영어 키워드만 사용

## 6. 참고 파일 목록 (Claude가 바로 열어볼 수 있음)
- `docs/Refactoring_Validation_Summary.md` – 현재 요약
- `CLAUDE.md` – 전체 프로젝트 현황 및 검증 체크리스트
- `docs/OBSIDIAN_LOG_2025-12-04.md` – 오류 해결 상세 로그
- `docs/Implementation_Plan.md` (예정) – 향후 구현 계획
- `walkthrough.md` – 진행 단계별 기록

---

*이 파일은 Claude가 개발 히스토리와 현재 컨텍스트를 빠르게 파악하도록 만든 참고용 문서입니다.*
