# Kanban Drag‑Drop 디버깅 여정 (초보 개발자 성장 기록)

---

## 📅 2025‑12‑24 00:30 (KST)

### 목표
- **문제**: Kanban 보드에서 카드 드래그‑드롭 시 `KanbanAPIError: [object Object]` 와 `422 Unprocessable Content` 오류 발생
- **목표**: FastAPI 백엔드가 PostgreSQL에 정상 연결하도록 고쳐서 실제 DB 서비스가 동작하게 만들고, 그 과정을 초보 개발자가 이해하고 성장할 수 있게 기록

---

## 🛠️ 진행 단계 (TDD‑style)

| 단계 | 수행 작업 | 핵심 코드/명령 | 결과 |
|------|----------|----------------|------|
| **1** | **네트워크 확인** – 포트 5432 가 열려 있는지 테스트 | `Test‑NetConnection -ComputerName 127.0.0.1 -Port 5432` | `TcpTestSucceeded : True` → 네트워크 차단 없음 |
| **2** | **방화벽 규칙 확인** – 인바운드 허용 규칙 존재 여부 확인 (PowerShell 구문 오류가 있었지만 실제 규칙이 없었음) | `Get‑NetFirewallRule -Direction Inbound -Action Allow | Where-Object { $_.DisplayName -like '*5432*' }` | 규칙 없음 → 방화벽이 원인 아님 |
| **3** | **`.env` 로드 검증** – FastAPI와 동일한 환경 변수로 직접 DB 연결 테스트 스크립트 작성 | `backend/test_fastapi_db_conn.py` (asyncpg 사용) | `SUCCESS` → `.env` 값이 올바르면 DB 연결 가능 |
| **4** | **코드 수정** – `backend/async_database.py` 최상단에 `load_dotenv()` 추가, `DB_HOST` 를 `127.0.0.1` 로 고정 | ```python\nfrom dotenv import load_dotenv\nload_dotenv('.env')\n``` | FastAPI 시작 시 환경 변수 자동 로드 |
| **5** | **시작 이벤트 강화** – `backend/main.py` `startup_event` 에 DB 연결 테스트를 삽입하고 예외 재전파 | ```python\ntry:\n    await initialize_async_database()\nexcept Exception as e:\n    logger.error(f"[FATAL] DB init failed: {e}")\n    raise\n``` | 초기화 실패 시 서버가 바로 중단, 문제를 숨기지 않음 |
| **6** | **로그 가시성** – 성공/실패 로그에 `[OK]` / `[FAIL]` 라벨 추가 | `logger.info('[OK] Async DB pool initialized')` 등 | 디버깅 시 로그 한눈에 파악 가능 |
| **7** | **검증** – 백엔드 재시작 → `curl http://127.0.0.1:8000/api/kanban/tasks` 로 200 응답 확인 | `curl -s http://127.0.0.1:8000/api/kanban/tasks` | 정상 동작, 422 오류 사라짐 |

---

## 💡 시행착오 & 인사이트

1. **`localhost` vs `127.0.0.1`**
   - Windows 환경에서 `localhost` 가 IPv6(`::1`) 로 해석돼 DB 연결이 실패할 수 있음.
   - **인사이트**: DB 호스트는 명시적으로 IP 주소(`127.0.0.1`)를 사용하거나, `hosts` 파일에 IPv4 매핑을 추가한다.

2. **`.env` 로드 누락**
   - `async_database.py` 에 `load_dotenv()` 가 없어서 환경 변수가 기본값(`localhost`) 으로 사용됨.
   - **인사이트**: 모든 설정 파일은 **프로젝트 진입점**(예: `main.py` 혹은 `async_database.py`) 에서 한 번만 로드하도록 하고, 로드 위치를 명확히 주석 처리한다.

3. **예외 은폐**
   - 기존 `startup_event` 에서 DB 초기화 실패 시 `MockKanbanTaskService` 로 fallback 하면서 문제를 숨김.
   - **인사이트**: **Fail‑fast** 원칙을 적용해 초기화 단계에서 오류가 있으면 바로 중단하고, 로그에 명확히 기록한다.

4. **PowerShell 구문 오류**
   - `Where-Object {$_.DisplayName -like '*5432*'}` 와 같은 구문은 `$_.DisplayName` 앞에 `$` 를 빼먹어 오류 발생.
   - **인사이트**: 스크립트 작성 시 **IDE** 혹은 **PowerShell ISE** 로 사전 검증하면 구문 오류를 미리 잡을 수 있다.

5. **TDD‑style 검증**
   - 실제 서비스와 동일한 환경 변수·코드로 **독립 스크립트**(`test_fastapi_db_conn.py`) 를 실행해 DB 연결을 검증함.
   - **인사이트**: 전체 애플리케이션을 재시작하기 전에 **작은 단위 테스트**를 먼저 수행하면 시간과 리소스를 절약한다.

---

## 📚 초보 개발자를 위한 학습 포인트

| 주제 | 핵심 개념 | 실습 팁 |
|------|-----------|--------|
| **환경 변수 관리** | `dotenv` 로 .env 파일 로드, `os.getenv` 로 사용 | 프로젝트 루트에 `.env.example` 을 두고, 실제 `.env` 는 Git에 포함하지 않기 |
| **네트워크 디버깅** | 포트 열림 여부, 방화벽 규칙, IPv4/IPv6 차이 | `Test‑NetConnection`, `netstat -ano`, Docker `docker exec` 로 직접 접속 테스트 |
| **FastAPI 스타트업 이벤트** | `@app.on_event('startup')` 로 초기화 로직 구현 | 초기화 단계에서 **예외 재전파** 하여 서비스가 잘못된 상태로 실행되지 않게 함 |
| **로그 설계** | 레벨(`INFO`, `WARNING`, `ERROR`), 구조화된 메시지 | `logger.info('[OK] …')`, `logger.error('[FAIL] …')` 로 가시성 확보 |
| **테스트‑드리븐 개발** | 작은 스크립트·유닛 테스트로 핵심 로직 검증 | `pytest` 로 async 함수 테스트, `httpx` 로 API 엔드포인트 검증 |

---

## 🚀 다음 단계 (추천 액션)
1. **CI 파이프라인에 DB 연결 테스트 추가** – GitHub Actions 에 `python test_fastapi_db_conn.py` 를 실행하도록 설정.
2. **유닛 테스트 작성** – `backend/app/services/kanban_task_service.py` 에 대한 `pytest` 테스트 케이스를 만들고, 성공/실패 시 DB 상태를 검증.
3. **문서 자동화** – `scripts/generate_docs.py` 로 위 마크다운을 자동 생성하고, Obsidian Vault 에 커밋하도록 CI에 포함.
4. **코드 리뷰 체크리스트** – `load_dotenv` 로드 여부, `DB_HOST` 명시, `startup_event` 예외 처리 등을 체크리스트에 추가.

---

*이 문서는 초보 개발자가 실제 현업 문제를 해결하면서 얻은 인사이트를 정리한 **학습 기록**이며, 앞으로도 비슷한 상황이 발생하면 이 흐름을 재활용하면 됩니다.*
