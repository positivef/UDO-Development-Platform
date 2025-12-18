---
date: 2025-11-20
tags: ["devlog", "udo", "quality", "cli", "tests"]
status: "in-progress"
project: "[[UDO Development Platform]]"
---

# 2025-11-20 UDO 품질 계층 하드닝

## 📌 오늘 작업
- quality_service 서브프로세스 호출을 shell=False로 통일하고 exit code/에러 메시지 노출 개선
- Pylint 평점을 stderr에서도 파싱하도록 수정하고, 출력 없음/명령 미설치 시 명확한 에러 반환
- ESLint/pytest 커버리지 호출에서 결과 없을 때의 에러 메시지와 실패 시그널 보강
- 품질 서비스 회복력 단위 테스트 추가(`backend/tests/test_quality_service_resilience.py`)
- 빌드 산출물/의존성(.next, node_modules, coverage 파일, .mypy_cache) gitignore 적용

## 🔧 코드 변경 경로
- backend/app/services/quality_service.py
- backend/tests/test_quality_service_resilience.py
- .gitignore

## 🔍 테스트/검증
- 로컬 python shim 경로 깨짐(pyenv-win)으로 전체 테스트 미실행; python3는 정상. ci 환경 또는 복구 후 `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && pytest` 필요

## 💬 다음 단계
- python 실행 경로 복구 후 quality/컨텍스트 API 통합 테스트 실행
- ESLint/pytest 실제 결과 반영되는지 대시보드 연동 확인
- 빌드 산출물 정리 및 CI에서 gitignore 누락 확인
## 추가 메모
- ESLint 호출에 Windows 환경용 shell 토글 추가(use_shell_on_windows), WSL/리눅스는 shell=False 유지.
- venv 설치 실패: 시스템 python이 pip을 제공하지 않고 ensurepip 비활성화(Debian/Ubuntu), venv pip도 pip._vendor.packaging 누락으로 실행 불가. 테스트/설치 진행하려면 pip 설치 또는 오프라인 wheel 필요.
- 차단 해법: 시스템 pip 설치(예: apt install python3-pip) 또는 pip/setuptools/packaging 오프라인 wheel 제공 후 venv 재설치 및 pytest 실행.
- pip 설치 시도: `sudo apt-get update && sudo apt-get install -y python3-pip` 실행했으나 효과 없음, venv pip 업그레이드도 동일 오류(pip._vendor.packaging 누락). 추가 설치 수단 필요.
- 재시도: `sudo apt-get update` 180s 대기했으나 응답 없음(네트워크/apt 차단 추정). 로컬 GitHub 경로 내 wheel 없음. 네트워크 허용 또는 pip/setuptools/packaging wheel 제공 필요.
- 오픈 블로커: pip 부재로 의존성/테스트 미실행. 네트워크/apt 허용 또는 pip·setuptools·packaging wheel 제공 필요.
- 환경 정렬: Windows(pyenv-win 3.13) venv가 유효, WSL(3.12.3)은 Windows venv 사용 불가. 테스트는 Windows 셸에서 실행하거나, pip 가능 시 WSL 전용 3.13 venv를 별도로 생성해야 함.
- 상태/다음 단계: 당분간 Windows 셸+pyenv-win 3.13 venv에서 테스트/실행, WSL은 pip 가능해지면 별도 .venv_wsl(3.13) 생성 후 진행.
- WSL 경고: WSL에서 Windows venv 실행 시 `UtilBindVsockAnyPort socket failed` 오류 발생. 교차 실행 금지.
- WSL에서 Windows venv pytest 시도 → `UtilBindVsockAnyPort socket failed` 동일. 모든 테스트는 Windows 셸에서만 실행하도록 고정.
- 터미널 안내 노트 추가: Windows 셸(.venv\Scripts\activate)에서만 테스트 실행, WSL은 pip 가능 시 별도 .venv_wsl 생성. 상세는 TERMINAL_MISMATCH.md 참조.
- WSL에서 Windows venv pytest 추가 시도 → 동일 vsock 오류, 더 이상 WSL 시도 안함. Windows 셸 전용으로 고정.
- Pending 단계 업데이트: Windows venv에서 run_udo_phase1.py 실행 예정, resilience test 버그는 Windows 셸에서 수정 예정. TERMINAL_MISMATCH.md/WSL_VS_WINDOWS_ENV.md 참조.
- WebSocket 핸들러 개선: redis_client/pubsub None 가드 및 UnboundLocal 방지, redis 미가용 시에도 연결 유지.
- 백엔드 기동 명령(Windows): .venv\Scripts\activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
