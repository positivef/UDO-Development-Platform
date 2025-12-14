# 🔬 Week 1 Day 1 Research Report

## 1. PostgreSQL Dual-write Patterns

**목표**: 데이터 일관성을 유지하면서 PostgreSQL과 외부 시스템(예: 검색 엔진, 캐시) 간의 데이터 동기화.

### 주요 패턴 비교

| 패턴 | 설명 | Latency | 장점 | 단점 |
| :--- | :--- | :--- | :--- | :--- |
| **Outbox Pattern** | 트랜잭션 내에서 'Outbox' 테이블에 이벤트 저장, 별도 워커가 발행 | High (수초~수분) | **원자성 보장**, 구현 단순 | 워커 폴링 부하, 실시간성 부족 |
| **CDC (Change Data Capture)** | DB 로그(WAL)를 읽어 변경사항 스트리밍 (예: Debezium) | Low (ms~수초) | **실시간성**, 애플리케이션 코드 수정 불필요 | 인프라 복잡도 증가 (Kafka 등 필요) |
| **Application Dual-write** | 애플리케이션에서 두 시스템에 각각 쓰기 | Lowest (즉시) | 구현 가장 단순 | **데이터 불일치 위험 높음** (하나만 성공 시) |

### 🏆 추천: Outbox Pattern (Lite Version)
*   **이유**: 4주 프로젝트의 규모와 복잡도를 고려할 때, CDC(Kafka 등) 도입은 오버엔지니어링입니다.
*   **구현**: `events` 테이블을 만들고, 간단한 Python 백그라운드 워커(Celery)가 이를 처리하도록 합니다.
*   **프로덕션 사례**: 수많은 MSA 환경에서 표준으로 사용됨.

---

## 2. mypy Auto-fix Tools

**목표**: 7개의 타입 오류를 빠르고 정확하게 수정.

### 도구 비교

| 도구 | 방식 | 특징 | 추천 대상 |
| :--- | :--- | :--- | :--- |
| **MonkeyType** | Runtime Tracing | 코드를 실제 실행하여 타입 추론 | 테스트 커버리지가 높은 경우 |
| **Pytype** | Static Analysis | 정적 분석으로 타입 추론 및 병합 | 대규모 레거시 코드 |
| **Mypy (Manual)** | Static Checking | 직접 수정 (AI 보조) | **소규모 오류 (현재 상황)** |

### 🏆 추천: Mypy + AI (Claude/Antigravity)
*   **이유**: 오류가 단 7개뿐입니다. 자동화 도구를 설정하고 배우는 시간보다, **Claude/Antigravity가 직접 수정하는 것이 훨씬 빠르고 정확**합니다.
*   **전략**: `mypy` 실행 결과를 AI에게 주고 "고쳐줘"라고 명령.

---

## 3. Docker Compose Security Best Practices

**목표**: 개발 환경이지만 프로덕션 수준의 보안 습관 적용.

### 핵심 체크리스트

1.  **Secrets Management**:
    *   ❌ 환경 변수(`ENV`)에 비밀번호 평문 저장 금지.
    *   ✅ `.env` 파일은 `.gitignore`에 포함하고, `docker-compose`의 `secrets` 기능 활용 권장.
2.  **Network Isolation**:
    *   ✅ `backend-network`와 `frontend-network` 분리. DB는 `backend-network`에만 연결.
3.  **Volume Permissions**:
    *   ✅ 컨테이너를 `non-root` 유저로 실행.
    *   ✅ 호스트 볼륨 마운트 시 권한(`uid:gid`) 일치 주의.
4.  **Image Security**:
    *   ✅ `latest` 태그 대신 구체적 버전(`postgres:15.3`) 사용.
    *   ✅ 신뢰할 수 있는 공식 이미지 사용.

### 🏆 적용 계획
*   `docker-compose.yml`에 `networks` 섹션 추가하여 격리.
*   PostgreSQL 비밀번호는 `.env` 파일로 관리하고 로컬에서만 로드.

---

## 📝 결론 (Action Plan)

1.  **Dual-write**: 일단 **Application Dual-write**로 시작하되, `Outbox` 테이블 스키마만 미리 생성 (Future-proof).
2.  **Mypy**: 도구 설치 없이 **AI가 직접 수정**.
3.  **Docker**: **Network 분리**와 **.env 관리** 즉시 적용.

이 방향으로 구현을 시작하시겠습니까?
