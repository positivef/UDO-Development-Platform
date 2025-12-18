# 엔터프라이즈 기능 로드맵 - 언제, 왜 필요한가?

## Executive Summary

1인 개발자용으로는 과도하지만, **특정 시나리오에서는 필수**인 기능들의 활용 가이드.

**핵심 인사이트**: "지금은 아니지만, 나중에는 반드시 필요"한 기능들을 단계별로 도입하는 전략.

---

## 1. Multi-User Authentication & User Storage

### ❌ 현재 판단: "1인 개발자는 단일 사용자만 필요"

### ✅ 실제로 필요한 시나리오

#### Scenario 1: 팀 확장 (3-6개월 후)
**상황**:
- 프로젝트가 성장하여 파트타임 개발자 1-2명 추가
- 각자 다른 프로젝트를 담당하지만 UDO 플랫폼 공유
- "누가 어떤 태스크를 했는지" 추적 필요

**필요 기능**:
- User table (id, username, email, role)
- 태스크 생성/수정 시 `created_by`, `updated_by` 기록
- 간단한 역할 기반 접근 제어 (RBAC)

**구현 난이도**: 중간 (2-3일)
- PostgreSQL에 `users` 테이블 추가
- JWT 토큰에 user_id 포함
- 태스크 모델에 `created_by`, `updated_by` 추가

**점진적 도입 경로**:
```
Phase 1: 로컬 단일 사용자 (현재) - In-memory user
  → 데이터: {id: "default", name: "Me"}
  → 토큰: localStorage에 저장

Phase 2: 로컬 멀티 사용자 (팀 확장 시) - SQLite user table
  → 3명 이하: SQLite로 충분
  → 토큰: 여전히 localStorage
  → 회원가입 불필요 (admin이 CLI로 추가)

Phase 3: 클라우드 배포 (SaaS 고려 시) - PostgreSQL + OAuth
  → 회원가입/로그인 UI
  → OAuth (Google, GitHub)
  → 토큰 revocation table
```

#### Scenario 2: 지식 공유 (Obsidian 동기화)
**상황**:
- 여러 개발자가 같은 Obsidian vault 사용
- "누가 이 인사이트를 발견했는지" 추적하여 크레딧 제공
- 지식 재사용 시 기여자 표시

**필요 기능**:
- Obsidian 문서에 `author` 메타데이터
- 지식 재사용 시 "Original: @username" 표시
- 기여도 통계 (주간 리포트)

**가치**:
- 팀원 동기 부여 (내 지식이 10번 재사용됨!)
- 전문가 식별 (React 질문은 @alice에게)
- 온보딩 가속 (신입이 누구한테 물어봐야 할지 명확)

#### Scenario 3: 클라이언트 협업 (프리랜서)
**상황**:
- 프리랜서가 여러 클라이언트 프로젝트 관리
- 클라이언트에게 "실시간 진행 상황" 보여주기
- 클라이언트가 직접 피드백/승인

**필요 기능**:
- 클라이언트용 read-only 계정
- 태스크 상태 실시간 공유
- 댓글/피드백 기능
- 타임 트래킹 투명성

**비즈니스 가치**:
- 신뢰 구축 (클라이언트가 진행 상황 직접 확인)
- 커뮤니케이션 비용 감소 (이메일 대신 댓글)
- 청구 투명성 (시간 추적 공유)

### 💡 활용 전략

**지금 할 일** (1인 개발자 단계):
- User 모델을 **추상화**하여 설계
  ```python
  # backend/app/core/user_context.py
  def get_current_user() -> User:
      # Phase 1: 고정값 반환
      return User(id="default", name="Me", role="owner")

      # Phase 2: JWT에서 추출
      # return extract_user_from_jwt(request.headers["Authorization"])

      # Phase 3: Database 조회
      # return db.query(User).filter_by(id=user_id).first()
  ```
- 모든 태스크에 `created_by`, `updated_by` 필드 추가 (일단 "default" 저장)
- 나중에 Phase 2/3로 전환 시 마이그레이션 스크립트만 실행

**언제 전환할지** (트리거):
- 팀원 1명 이상 추가될 때
- 클라이언트 협업 필요할 때
- SaaS 전환 고려할 때

---

## 2. Token Revocation System

### ❌ 현재 판단: "로컬 환경에서 토큰 탈취 위험 낮음"

### ✅ 실제로 필요한 시나리오

#### Scenario 1: 로그아웃 후 즉시 차단
**상황**:
- 공용 컴퓨터에서 UDO 플랫폼 사용
- 로그아웃했지만 JWT 토큰이 여전히 유효 (24시간)
- 다음 사용자가 브라우저 히스토리에서 토큰 복사 가능

**현재 방식의 문제**:
```javascript
// 현재: 프론트엔드에서만 삭제
localStorage.removeItem('auth_token')

// 문제: 누군가 토큰을 복사했다면 여전히 사용 가능
const stolenToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
fetch('/api/kanban/tasks', {
  headers: { 'Authorization': `Bearer ${stolenToken}` }
}) // ✅ 여전히 작동함!
```

**Token Revocation으로 해결**:
```python
# backend/app/core/security.py
async def verify_token(token: str):
    # 1. JWT 서명 검증
    payload = jwt.decode(token, SECRET_KEY)

    # 2. Revocation 체크 (Redis 또는 DB)
    if await redis.exists(f"revoked:{token}"):
        raise HTTPException(401, "Token revoked")

    return payload

# 로그아웃 API
@router.post("/logout")
async def logout(token: str = Depends(get_current_token)):
    # Redis에 토큰 추가 (TTL = 토큰 만료 시간)
    await redis.setex(f"revoked:{token}", ttl=86400, value="1")
    return {"message": "Logged out"}
```

**구현 난이도**: 쉬움 (1일)
- Redis 추가 (Docker Compose)
- Revocation 체크 미들웨어
- 로그아웃 API 업데이트

#### Scenario 2: 보안 사고 대응
**상황**:
- GitHub에 `.env` 파일 실수로 커밋 (JWT_SECRET 노출)
- 모든 발급된 토큰이 위험
- **즉시 모든 사용자 로그아웃** 필요

**Token Revocation 없이**:
- JWT_SECRET 변경 → 모든 토큰 무효화 (OK)
- 하지만 사용자가 재로그인하기 전까지 앱 사용 불가

**Token Revocation 있으면**:
```python
# 긴급 조치: 특정 시간 이전 토큰 모두 차단
REVOKE_BEFORE = "2025-12-18T10:00:00Z"

async def verify_token(token: str):
    payload = jwt.decode(token, SECRET_KEY)
    if payload['iat'] < REVOKE_BEFORE:
        raise HTTPException(401, "Please re-login (security update)")
    return payload
```

#### Scenario 3: 역할 변경 즉시 반영
**상황**:
- 개발자 A의 역할을 DEVELOPER → VIEWER로 강등
- A가 현재 로그인 중 (JWT에 role=DEVELOPER 저장)
- 역할 변경이 즉시 반영되지 않음

**JWT의 근본적 한계**:
```
JWT는 self-contained (자체 포함)
→ 발급 후에는 서버가 수정할 수 없음
→ 만료될 때까지 기다려야 함
```

**Token Revocation + 짧은 TTL로 해결**:
```python
# 전략 1: Access Token (15분) + Refresh Token (7일)
access_token = create_jwt(user_id, expires_in=15*60)
refresh_token = create_jwt(user_id, expires_in=7*24*3600)

# 역할 변경 시
@router.post("/users/{user_id}/role")
async def change_role(user_id: str, new_role: str):
    # 1. DB 업데이트
    await db.execute("UPDATE users SET role = ? WHERE id = ?", new_role, user_id)

    # 2. 해당 사용자의 모든 토큰 revoke
    await redis.sadd(f"revoked_user:{user_id}", "*")

    # 3. 15분 이내 자동 재발급 시 새 역할 반영
    return {"message": "Role changed, will take effect in 15 min"}
```

### 💡 활용 전략

**지금 할 일** (1인 개발자 단계):
- JWT TTL을 **짧게** 설정 (15분)
- Refresh Token 패턴 미리 구현
  ```python
  # 지금은 revocation 체크 안 하지만, 구조는 준비
  async def verify_token(token: str, check_revocation: bool = False):
      payload = jwt.decode(token, SECRET_KEY)

      if check_revocation:
          # TODO: Phase 2에서 활성화
          # if await redis.exists(f"revoked:{token}"):
          #     raise HTTPException(401, "Token revoked")
          pass

      return payload
  ```

**언제 전환할지** (트리거):
- 팀원 2명 이상일 때
- 클라이언트 협업 시작할 때
- 공용 컴퓨터 사용할 때
- 보안 감사 필요할 때

---

## 3. Centralized Logging & APM

### ❌ 현재 판단: "파일 기반 로깅으로 충분"

### ✅ 실제로 필요한 시나리오

#### Scenario 1: 프로덕션 디버깅 (원격 서버)
**상황**:
- UDO 플랫폼을 AWS EC2에 배포
- 사용자가 "태스크 생성이 안 돼요" 리포트
- 서버에 SSH 접속하여 로그 확인 필요

**파일 로깅의 한계**:
```bash
# 서버에 SSH 접속
ssh ubuntu@ec2-xxx.amazonaws.com

# 로그 파일 찾기
cd /var/log/udo
tail -f app.log  # 😓 5GB 파일, grep 느림

# 특정 사용자 에러만 보고 싶은데...
grep "user_id=abc123" app.log  # 😓 10분 걸림
```

**Centralized Logging으로 해결** (예: ELK Stack, Grafana Loki):
```
1. 모든 서버의 로그 → 중앙 집중
2. 웹 UI에서 실시간 검색
3. 필터링: user_id, error_code, timestamp
4. 알림: 특정 에러 발생 시 Slack 알림
```

**실제 사용 예**:
```
Grafana Loki UI에서:
{app="udo"} |= "error" |= "user_id=abc123" | json

→ 2초 만에 해당 사용자의 모든 에러 확인
→ 원인: DB connection timeout (AWS RDS 재시작 필요)
```

#### Scenario 2: 성능 병목 지점 찾기 (APM)
**상황**:
- 사용자: "Kanban 보드 로딩이 너무 느려요 (10초)"
- 어디가 느린지 모름 (Frontend? API? DB? AI 호출?)

**파일 로깅으로는 불가능**:
```python
# 로그만으로는 전체 흐름 추적 어려움
logger.info("Fetching tasks...")  # 🤷 얼마나 걸렸는지?
logger.info("AI suggestion...")   # 🤷 병목인지 확인 어려움
```

**APM으로 해결** (예: DataDog, New Relic, OpenTelemetry):
```
Request ID: req-12345
├─ API /api/kanban/tasks (10.2s total)
│  ├─ DB query: SELECT tasks (8.5s) ← 🚨 병목!
│  ├─ AI suggestion (0.5s)
│  └─ Response serialization (1.2s)

→ 원인: DB에 인덱스 없음
→ 해결: CREATE INDEX idx_tasks_phase_id ON tasks(phase_id)
→ 결과: 10.2s → 0.3s (97% 개선)
```

#### Scenario 3: 비즈니스 메트릭 추적
**상황**:
- "AI 제안 기능이 실제로 사용되는가?"
- "지식 재사용률이 목표(95%)를 달성하는가?"
- "어떤 단계에서 사용자가 이탈하는가?"

**APM + Custom Metrics**:
```python
from datadog import statsd

# AI 제안 사용률
statsd.increment('ai.suggestion.shown')
statsd.increment('ai.suggestion.accepted')

# 지식 재사용 성공률
statsd.increment('knowledge.tier1.hit')  # Obsidian
statsd.increment('knowledge.tier2.hit')  # Context7
statsd.increment('knowledge.tier3.hit')  # User

# 대시보드에서 실시간 확인
AI Acceptance Rate: 72% (목표 80%)
Knowledge Automation: 95% (목표 달성 ✅)
```

### 💡 활용 전략

**지금 할 일** (1인 개발자 단계):
- **구조화된 로깅** 도입 (JSON 포맷)
  ```python
  import structlog

  logger = structlog.get_logger()
  logger.info("task_created",
              task_id="abc-123",
              user_id="default",
              phase="ideation",
              duration_ms=125)

  # 출력 (JSON):
  # {"event":"task_created","task_id":"abc-123","timestamp":"2025-12-18T..."}

  # 나중에 Loki/ELK로 전환 시 파싱 불필요
  ```

- **OpenTelemetry 준비** (프레임워크만)
  ```python
  from opentelemetry import trace

  tracer = trace.get_tracer(__name__)

  async def create_task(task_data):
      with tracer.start_as_current_span("create_task"):
          # 지금은 로컬에만 기록
          # 나중에 Jaeger/Zipkin으로 전송
          result = await db.insert(task_data)
          return result
  ```

**언제 전환할지** (트리거):
- 클라우드 배포할 때 (Phase 1)
- 서버 2대 이상일 때 (Phase 2)
- 사용자 10명 이상일 때 (Phase 3)
- 성능 문제 디버깅 필요할 때 (즉시)

**비용 고려**:
```
Self-hosted (무료):
- Grafana Loki + Prometheus + Jaeger
- Docker Compose로 로컬 실행
- 학습 목적으로 충분

Managed (유료):
- DataDog: $15/호스트/월 (소규모)
- New Relic: $99/월 (100GB)
- SaaS 전환 시 고려
```

---

## 4. GDPR / Privacy Compliance

### ❌ 현재 판단: "개인 사용, 타인 데이터 처리 없음"

### ✅ 실제로 필요한 시나리오

#### Scenario 1: EU 클라이언트 협업
**상황**:
- 프리랜서가 독일 회사와 프로젝트 진행
- 클라이언트의 비즈니스 데이터를 UDO에 저장
- 클라이언트: "GDPR 준수 증명서 제출하세요"

**GDPR 필수 요구사항**:
1. **데이터 처리 동의** (Consent)
   - 사용자 데이터 수집 시 명시적 동의
   - 언제든지 철회 가능

2. **데이터 이동권** (Data Portability)
   - 사용자가 자신의 데이터 JSON/CSV로 export
   - 다른 시스템으로 이동 가능

3. **삭제권** (Right to be Forgotten)
   - 사용자 요청 시 30일 이내 모든 데이터 삭제
   - 백업에서도 제거

4. **데이터 위치** (Data Residency)
   - EU 사용자 데이터는 EU 서버에 저장
   - AWS eu-west-1, GCP europe-west1

**비즈니스 영향**:
```
GDPR 미준수 시:
- 클라이언트와 계약 불가
- 벌금: 최대 €20M 또는 연 매출 4%
- 유럽 시장 진입 불가
```

#### Scenario 2: SaaS 전환 (다중 테넌트)
**상황**:
- UDO 플랫폼을 SaaS로 전환 (월 $29/사용자)
- 전 세계 개발자가 사용
- 각국 개인정보보호법 준수 필요

**준수해야 할 법률**:
- **GDPR** (EU): 가장 엄격
- **CCPA** (California): 캘리포니아 거주자
- **LGPD** (Brazil): 브라질
- **PIPEDA** (Canada): 캐나다

**공통 요구사항**:
- Privacy Policy 명시
- Cookie 동의 배너
- 데이터 암호화 (전송/저장)
- 보안 사고 72시간 내 신고
- DPO (Data Protection Officer) 지정

#### Scenario 3: 기업 고객 (B2B)
**상황**:
- 대기업이 UDO를 내부 팀에 도입
- IT 보안팀의 compliance 체크리스트

**필수 요구사항**:
- SOC 2 Type II 인증
- ISO 27001 인증
- GDPR/CCPA 준수
- 침투 테스트 결과
- 데이터 백업/복구 계획
- SLA 보장 (99.9% uptime)

**준수하지 않으면**:
- 대기업 고객 확보 불가
- 매출 기회 상실 (B2B SaaS 시장)

### 💡 활용 전략

**지금 할 일** (1인 개발자 단계):
- **데이터 최소화** 원칙 적용
  ```python
  # 불필요한 개인정보 수집 안 함
  class User(BaseModel):
      id: str
      username: str  # ✅ 필요
      email: str     # ✅ 필요 (로그인)
      # phone: str   # ❌ 불필요하므로 수집 안 함
      # address: str # ❌ 불필요
  ```

- **데이터 export 기능** 미리 구현
  ```python
  @router.get("/api/users/me/export")
  async def export_my_data(user: User = Depends(get_current_user)):
      data = {
          "user": user.dict(),
          "tasks": await get_user_tasks(user.id),
          "projects": await get_user_projects(user.id),
      }
      return JSONResponse(data)
  ```

- **삭제 API** 준비
  ```python
  @router.delete("/api/users/me")
  async def delete_my_account(user: User = Depends(get_current_user)):
      # Phase 1: 소프트 삭제 (deleted_at 기록)
      await db.execute("UPDATE users SET deleted_at = NOW() WHERE id = ?", user.id)

      # Phase 2: 30일 후 하드 삭제 (cron job)
      # Phase 3: 백업에서도 제거 (GDPR 준수)
      return {"message": "Account deleted"}
  ```

**언제 전환할지** (트리거):
- EU 클라이언트와 협업 시 (즉시)
- SaaS 전환 계획 시 (6개월 전)
- 기업 고객 타겟팅 시 (인증 획득)

**비용**:
```
GDPR 준수 비용:
- 법률 자문: $5,000 (초기)
- Privacy Policy 작성: $1,000
- SOC 2 인증: $15,000-$50,000/년
- ISO 27001: $10,000-$30,000/년

대안 (초기):
- Termly.io: Privacy Policy 자동 생성 ($10/월)
- Vanta: Compliance 자동화 ($3,000/년)
```

---

## 5. Load / Stress Testing

### ❌ 현재 판단: "1인 사용자, 동시 요청 제한적"

### ✅ 실제로 필요한 시나리오

#### Scenario 1: AI Batch Processing
**상황**:
- 100개 태스크에 대해 AI 제안 일괄 생성
- Claude API 호출 100번 (각 3초)
- 총 5분 소요 → **사용자 대기 불가**

**성능 문제**:
```python
# 현재: 순차 처리
for task in tasks:
    suggestion = await ai_suggest(task)  # 3s each
    await db.save(suggestion)

# 문제: 100개 × 3s = 5분 대기
```

**Load Testing으로 발견**:
```python
# k6 스크립트
import http from 'k6/http';

export default function() {
    http.post('http://localhost:8000/api/ai/batch-suggest', {
        task_ids: [...Array(100).keys()]
    });
}

// 결과:
// ✅ 1개: 3s
// ⚠️ 10개: 30s (순차)
// ❌ 100개: timeout (5분)

// 개선: 병렬 처리 + 스트리밍
// ✅ 100개: 15s (20x faster)
```

**해결책**:
```python
# 병렬 처리 (asyncio.gather)
import asyncio

async def batch_suggest(task_ids: List[str]):
    # 10개씩 배치 (API rate limit 고려)
    batches = [task_ids[i:i+10] for i in range(0, len(task_ids), 10)]

    for batch in batches:
        suggestions = await asyncio.gather(*[
            ai_suggest(task_id) for task_id in batch
        ])
        await db.bulk_insert(suggestions)

# 5분 → 15초 (20배 개선)
```

#### Scenario 2: Database Query Optimization
**상황**:
- Kanban 보드에 1,000개 태스크
- "모든 태스크 불러오기" 쿼리가 느림
- 사용자 불만: "로딩 10초 걸림"

**Load Testing으로 병목 발견**:
```bash
# k6로 부하 테스트
k6 run --vus 10 --duration 30s load_test.js

# 결과:
# ✅ 10 tasks: 50ms
# ⚠️ 100 tasks: 500ms
# ❌ 1,000 tasks: 8,000ms (timeout)

# 원인: N+1 쿼리
```

**N+1 쿼리 문제**:
```python
# 현재 (BAD):
tasks = await db.query("SELECT * FROM tasks")
for task in tasks:
    # 각 태스크마다 DB 쿼리 발생 (N번)
    dependencies = await db.query(
        "SELECT * FROM dependencies WHERE task_id = ?", task.id
    )
    task.dependencies = dependencies

# 1,000개 태스크 → 1,001번 쿼리 (1 + 1,000)
```

**최적화**:
```python
# 개선 (GOOD):
tasks = await db.query("SELECT * FROM tasks")
task_ids = [t.id for t in tasks]

# 한 번에 모든 의존성 가져오기
dependencies = await db.query(
    "SELECT * FROM dependencies WHERE task_id IN (?)", task_ids
)

# 메모리에서 그룹핑
deps_by_task = {}
for dep in dependencies:
    deps_by_task.setdefault(dep.task_id, []).append(dep)

for task in tasks:
    task.dependencies = deps_by_task.get(task.id, [])

# 1,001번 쿼리 → 2번 쿼리 (500배 개선)
# 8초 → 16ms
```

#### Scenario 3: Concurrent User Spike
**상황**:
- Reddit에 UDO 플랫폼 소개 글 올림
- 갑자기 100명이 동시 접속
- 서버 다운

**Stress Testing으로 한계 파악**:
```bash
# Locust로 부하 테스트
locust -f locustfile.py --users 100 --spawn-rate 10

# 결과:
# ✅ 10 users: 모든 요청 성공
# ⚠️ 50 users: 응답 시간 3초
# ❌ 100 users: 502 Bad Gateway (서버 죽음)

# 원인: DB connection pool 부족
```

**해결책**:
```python
# 현재: connection pool = 10
DATABASE_URL = "postgresql://...?pool_size=10"

# 개선: connection pool = 50 + queue
DATABASE_URL = "postgresql://...?pool_size=50&max_overflow=100"

# 결과:
# ✅ 100 users: 모든 요청 성공
# ⚠️ 500 users: 응답 시간 5초
# ✅ Auto-scaling 트리거 설정 (CPU 70%)
```

### 💡 활용 전략

**지금 할 일** (1인 개발자 단계):
- **간단한 벤치마크** 스크립트 작성
  ```python
  # scripts/benchmark.py
  import asyncio
  import time

  async def benchmark_create_task(n=100):
      start = time.time()
      tasks = []
      for i in range(n):
          task = await create_task(f"Task {i}")
          tasks.append(task)
      duration = time.time() - start

      print(f"{n} tasks created in {duration:.2f}s")
      print(f"Average: {duration/n*1000:.0f}ms per task")

  # 목표: <100ms per task
  # 실제: 250ms per task
  # → N+1 쿼리 발견 → 최적화
  ```

- **성능 테스트를 CI에 포함**
  ```yaml
  # .github/workflows/performance.yml
  name: Performance Tests
  on: [pull_request]
  jobs:
    benchmark:
      runs-on: ubuntu-latest
      steps:
        - run: python scripts/benchmark.py
        - run: |
            if [ $DURATION -gt 10000 ]; then
              echo "❌ Performance regression detected"
              exit 1
            fi
  ```

**언제 전환할지** (트리거):
- 클라우드 배포 전 (필수)
- 사용자 10명 이상 (권장)
- 성능 문제 리포트 시 (즉시)
- SaaS 전환 시 (필수)

**도구 선택**:
```
로컬 개발:
- pytest-benchmark: Python 벤치마크
- hyperfine: CLI 성능 측정

클라우드 배포 전:
- k6: 간단한 HTTP 부하 테스트
- Locust: Python 기반, UI 제공

프로덕션:
- Artillery: CI/CD 통합 쉬움
- Gatling: 대규모 테스트 (1,000+ users)
```

---

## 결론: 단계별 도입 전략

### Phase 0: 1인 개발자 (현재)
```yaml
필수:
  - 구조화된 로깅 (JSON)
  - User 추상화 계층
  - 데이터 export API
  - 간단한 벤치마크

불필요:
  - APM (DataDog)
  - Token revocation
  - GDPR 인증
  - Load testing (k6)
```

### Phase 1: 팀 확장 (3-6개월 후, 팀원 2-3명)
```yaml
추가:
  - Multi-user auth (SQLite)
  - Token revocation (Redis)
  - Centralized logging (Loki)
  - 간단한 RBAC

여전히 불필요:
  - APM (파일 로그로 충분)
  - GDPR 인증 (내부 사용)
  - Stress testing (트래픽 낮음)
```

### Phase 2: 클라우드 배포 (6-12개월 후, SaaS 고려)
```yaml
추가:
  - APM (OpenTelemetry + Jaeger)
  - Load testing (k6)
  - Auto-scaling
  - Health checks

여전히 불필요:
  - GDPR 인증 (아직 EU 고객 없음)
  - SOC 2 (B2B 아님)
```

### Phase 3: SaaS 전환 (12-24개월 후, 유료 고객)
```yaml
추가:
  - GDPR 준수 (Privacy Policy)
  - Security audit
  - Managed APM (DataDog)
  - 24/7 monitoring

고려:
  - SOC 2 인증 (B2B 타겟팅 시)
  - ISO 27001 (대기업 고객)
```

---

## 핵심 메시지

1. **"지금은 아니지만, 언제가는 필요"** - 준비는 해두되 구현은 늦춰라
2. **"추상화 계층 먼저"** - 나중에 전환 쉽게 (User, Logging, Metrics)
3. **"트리거 기반 도입"** - 팀 확장, 클라우드 배포, 유료 전환 시점에 추가
4. **"Self-hosted 먼저"** - Managed 서비스는 비용이 발생하므로 수익 후 고려

**ROI 계산**:
- Phase 0 → Phase 1: 투자 3일, 절감 시간 월 20시간 (팀 협업 효율)
- Phase 1 → Phase 2: 투자 5일, 절감 시간 월 40시간 (디버깅 효율)
- Phase 2 → Phase 3: 투자 $20K, 매출 증가 $50K/년 (B2B 고객)

---

**작성일**: 2025-12-18
**버전**: 1.0
**다음 검토**: Phase 1 전환 시점 (팀원 추가 3개월 전)
