기술 아키텍처 명세서: UDO (Unified Development Orchestrator) v3.0

문서 버전: 2.1 (Final Integrated Version)
작성 일자: 2025-11-20
작성자: 수석 시스템 아키텍트 (Senior System Architect)
상태: 개발 착수 승인 (READY FOR DEVELOPMENT)
보안 등급: 대외비 (Internal Use Only)

1. 개요 (Executive Summary)

1.1 프로젝트 목표

본 문서는 UDO v3.0의 베타 단계(45%)를 프로덕션 단계(85%+)로 전환하기 위한 기술적 청사진이다. 현재 메모리 기반의 Mock 서비스로 작동하는 데이터 계층을 PostgreSQL 15 기반의 영구 저장소로 마이그레이션하고, 동시 접속자 10,000명을 수용할 수 있는 확장 가능한 아키텍처를 수립한다.

1.2 핵심 기술 전략

비동기 이벤트 기반 아키텍처: AI의 긴 응답 시간으로 인한 병목을 제거하기 위해 Task Queue를 도입한다.

RAG (검색 증강 생성): 토큰 비용 절감과 정확도 향상을 위해 pgvector 기반의 하이브리드 검색을 적용한다.

범용 불확실성 프로토콜: 모든 AI 응답에 '판단의 근거와 한계'를 명시하는 Uncertainty Map을 강제한다.

2. 시스템 아키텍처 (System Architecture)

2.1 아키텍처 다이어그램 (Asynchronous & Event-Driven)

시스템은 모놀리식 마이크로서비스(Micro-service like Monolith) 구조를 기반으로 하되, 무거운 AI 작업은 백그라운드 워커로 분리하여 API 서버의 응답성(Responsiveness)을 < 50ms로 유지한다.

graph TD
    Client[웹 대시보드\n(Next.js 14)] -->|REST API| API[FastAPI 서버 클러스터]
    Client -->|WebSocket| SocketSvc[실시간 알림 서비스]

    subgraph "애플리케이션 계층 (Application Layer)"
        API -->|Enqueue Job| Redis[(Redis Task Queue)]

        subgraph "백그라운드 워커 (Celery Workers)"
            Worker[AI 처리 워커]
            Worker -->|Pop Job| Redis
            Worker -->|RAG Search| VectorDB[(PostgreSQL + pgvector)]
            Worker -->|Generate| Bridge[AI 브리지 (Circuit Breaker)]

            subgraph "지능형 처리 엔진"
                Bridge --> Claude
                Bridge --> Codex
                Bridge --> Gemini
                Bridge -->|Validation| Validator[응답 검증기]
            end
        end

        Worker -->|Push Result| SocketSvc
    end

    subgraph "데이터 계층 (Data Layer)"
        Worker -->|Save Log| MasterDB[(PostgreSQL 15)]
        API -->|Query| MasterDB
    end


2.2 핵심 프로세스 흐름

Non-blocking 요청: 사용자가 AI 작업을 요청하면 서버는 즉시 Task ID를 반환하고 연결을 해제한다.

백그라운드 처리: 워커 노드가 큐에서 작업을 가져와 RAG 검색 및 AI 추론을 수행한다.

검증 및 알림: 생성된 답변이 '불확실성 지도'를 포함하는지 검증 후, WebSocket을 통해 클라이언트 UI를 업데이트한다.

3. 데이터베이스 아키텍처 (PostgreSQL + pgvector)

3.1 설계 원칙

벡터 검색 내재화: 별도 벡터 DB 도입 없이 PostgreSQL의 pgvector 확장을 사용하여 관리 포인트를 단일화한다.

데이터 무결성: 정형 데이터는 3NF로 정규화하고, 비정형 메타데이터는 JSONB로 유연하게 관리한다.

3.2 스키마 설계 (Core Schema)

1. 프로젝트 (projects)
| 컬럼명 | 타입 | 설명 |
| :--- | :--- | :--- |
| id | UUID | PK, 프로젝트 ID |
| owner_id | UUID | FK(users), 소유자 |
| current_phase | ENUM | 현재 개발 단계 (Ideation ~ Testing) |
| settings | JSONB | 프로젝트별 AI 설정 |

2. 프로젝트 컨텍스트 (project_contexts) - RAG 지원
소스 코드와 문서를 벡터화하여 저장하는 테이블이다.

컬럼명

타입

설명

id

UUID

PK

project_id

UUID

FK(projects)

file_path

VARCHAR

파일 경로

content_chunk

TEXT

분할된 텍스트 청크

embedding

VECTOR(1536)

[핵심] OpenAI Ada-002 임베딩 벡터

3. 불확실성 로그 (uncertainty_logs)
AI의 모든 판단과 메타 인지 데이터를 기록한다.

컬럼명

타입

설명

id

BIGSERIAL

PK (시계열 성능 최적화)

project_id

UUID

FK(projects)

state

VARCHAR

5단계 퀀텀 상태 (DETERMINISTIC ~ VOID)

score

FLOAT

불확실성 점수 (0~100)

decision_metadata

JSONB

[필수] 불확실성 지도 데이터

created_at

TIMESTAMPTZ

생성 시간

4. 불확실성 피드백 (uncertainty_feedback) - RLHF 지원
사용자가 AI의 판단을 평가하여 모델을 개선하기 위한 데이터셋이다.

컬럼명

타입

설명

id

BIGSERIAL

PK

log_id

BIGINT

FK(uncertainty_logs)

rating

INT

1 (유용함) / -1 (틀림)

correction

TEXT

사용자 피드백 코멘트

4. 범용 AI 응답 프로토콜 (Universal AI Response Protocol)

4.1 프로토콜 정의

시스템의 **모든 AI 출력(단일 대화, 멀티 에이전트 토론 포함)**은 반드시 아래의 JSON 스키마를 준수해야 한다. 이 구조가 깨지거나 누락될 경우 시스템은 이를 '오류'로 간주하고 재생성을 시도한다.

4.2 응답 스키마 (JSON Schema)

{
  "content": "AI의 실제 답변 텍스트 (Markdown 포맷 지원)",
  "uncertainty_map": {
    "least_confident_area": {
      "description": "답변 중 가장 추측에 의존하거나 확신이 없는 부분",
      "value": "예: 레거시 시스템의 API 명세가 문서와 다를 수 있음"
    },
    "over_simplifications": {
      "description": "복잡한 문제를 단순화하기 위해 도입한 가정",
      "value": ["네트워크 지연이 0ms라고 가정", "모든 DB 트랜잭션이 성공한다고 가정"]
    },
    "pivot_questions": {
      "description": "답변의 방향을 크게 바꿀 수 있는 결정적 질문",
      "value": ["현재 AWS를 사용 중이신가요, On-premise인가요?", "예산 한도가 월 $1,000 미만인가요?"]
    }
  }
}


5. 적응형 토큰 및 컨텍스트 전략 (Adaptive Context Strategy)

비용 효율성과 답변 품질의 균형을 맞추기 위해 상황에 따라 모델과 컨텍스트 로딩 방식을 이원화한다.

5.1 기본 모드 (Standard Mode)

대상: 일상 대화, 단순 코드 조회, 불확실성 상태 DETERMINISTIC.

모델: GPT-4o-mini 또는 Gemini Flash.

전략: Summary Only. 프로젝트 구조 트리와 최근 변경된 파일 요약본만 로드.

비용: 요청당 약 $0.01 미만.

5.2 심층 추론 모드 (Deep Reasoning Mode)

대상: 아키텍처 설계, 멀티 에이전트 합의, 불확실성 상태 CHAOTIC 이상.

모델: Claude 3.5 Sonnet 또는 Claude 3 Opus (사용자 승인 후).

전략: Hybrid RAG. 질문과 유사도(Cosine Similarity)가 높은 상위 20개 코드 청크(pgvector 검색) + 핵심 아키텍처 문서를 조합.

비용: 요청당 약 $0.05 ~ $0.50.

6. 보안 및 인프라 (DevOps & Security)

6.1 로컬 개발 환경 (docker-compose.yml)

팀원 간 환경 일치를 위해 즉시 실행 가능한 컨테이너 구성을 제공한다.

version: '3.8'
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    ports: ["8000:8000"]
    depends_on: [db, redis]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://udo_dev:dev_pass@db:5432/udo_v3

  worker: # AI 처리 전담 워커
    build: .
    command: celery -A app.worker worker --loglevel=info
    depends_on: [db, redis]
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  db:
    image: ankane/pgvector:v0.5.1 # pgvector 내장 이미지
    ports: ["5432:5432"]
    environment:
      POSTGRES_USER: udo_dev
      POSTGRES_PASSWORD: dev_pass
      POSTGRES_DB: udo_v3
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:alpine
    ports: ["6379:6379"]

volumes:
  postgres_data:


6.2 보안 전략

Circuit Breaker: 외부 AI API 5회 연속 실패 시 차단 및 Fallback 로직 가동.

Token Rotation: Refresh Token(14일)은 HttpOnly 쿠키에 저장하여 XSS 방지.

Rate Limiting: 사용자별 AI 요청 빈도 제한 (Redis Leaky Bucket).

7. 실행 계획 (Action Plan)

이 문서는 최종 승인되었으므로, 개발팀은 즉시 다음 순서로 작업을 진행한다.

Day 1: docker-compose 실행 및 Alembic을 이용한 PostgreSQL 스키마(pgvector 포함) 생성.

Day 2: Uncertainty Map 스키마가 적용된 기본 AI 브리지 구현 및 테스트.

Day 3: Celery 기반의 비동기 큐 연동 및 RAG 파이프라인 구축.

승인: Senior System Architect
최종 검토일: 2025. 11. 20.
