# 역할별 액션 플랜 (Role-Based Action Plans)

> **생성일**: 2025-11-28
> **기반**: 통합 개발 가이드 (INTEGRATED_DEVELOPMENT_GUIDE.md)
> **목적**: 각 역할이 즉시 시작할 수 있는 구체적인 작업 목록

---

## 목차

1. [Backend Developer 액션 플랜](#backend-developer-액션-플랜)
2. [Frontend Developer 액션 플랜](#frontend-developer-액션-플랜)
3. [DevOps Engineer 액션 플랜](#devops-engineer-액션-플랜)
4. [AI/ML Engineer 액션 플랜](#aiml-engineer-액션-플랜)
5. [팀 협업 체크포인트](#팀-협업-체크포인트)

---

## Backend Developer 액션 플랜

### 🎯 핵심 목표
- Week 1: API-UI Bridge 완성 (사용자가 데이터 볼 수 있게)
- Week 2: 자동화 루프 완성 (Time Tracking → Uncertainty 자동 업데이트)
- Week 3: AI 기반 Mitigation Strategy
- Week 4: 성능 + 보안 최적화

### Week 1: Foundation (24시간)

#### Day 1 - Monday

**오전 (9am-12pm)** - 4시간

**Task 1.1: mypy 타입 오류 수정** (4시간)
```bash
# Terminal 1
cd C:\Users\user\Documents\GitHub\UDO-Development-Platform
.venv\Scripts\activate
mypy --strict src/ backend/ > mypy_errors.txt

# 오류 파일 분석
# 예상 오류:
# 1. src/unified_development_orchestrator_v2.py:45 - Optional[str] vs str
# 2. backend/app/services/quality_service.py:123 - Dict[str, Any] vs TypedDict
# 3. src/uncertainty_map_v3.py:67 - List[float] vs np.ndarray

# 수정 방법:
# - Optional 타입 명시
# - TypedDict 사용
# - numpy typing (from numpy.typing import NDArray)

# 검증
mypy --strict src/ backend/  # 오류 0개 목표
```

**오후 (1pm-5pm)** - 4시간

**Task 1.2: PostgreSQL + Dual-Write** (4시간)
```bash
# PostgreSQL 시작
docker-compose up -d db

# 연결 테스트
psql -h localhost -U udo_user -d udo_dev

# Alembic 마이그레이션
cd backend
alembic upgrade head

# 테이블 확인
psql -h localhost -U udo_user -d udo_dev -c '\dt'
# 예상 테이블: projects, tasks, time_tracking_sessions, uncertainty_history 등

# Dual-write 매니저 확인
cat app/db/dual_write_manager.py
# 로직:
# - write() → PostgreSQL (primary) + SQLite (shadow)
# - read() → PostgreSQL
# - sync_check() → 매시간 데이터 정합성 확인

# 테스트
.venv\Scripts\python.exe -c "
from backend.app.db.dual_write_manager import DualWriteManager
dm = DualWriteManager()
dm.write('projects', {'name': 'Test', 'id': 1})
print('PostgreSQL:', dm.read_postgres('projects', 1))
print('SQLite:', dm.read_sqlite('projects', 1))
# 결과: 양쪽에 동일한 데이터 존재
"
```

**Evening Review (5pm-6pm)** - 1시간
```yaml
체크리스트:
  - ✅ mypy 오류 0개
  - ✅ PostgreSQL 연결 성공
  - ✅ Alembic 마이그레이션 완료
  - ✅ Dual-write 작동 확인

git_commit:
  message: "feat(week1-day1): PostgreSQL setup + mypy fixes complete"
  files: [src/, backend/, alembic/]
```

---

#### Day 2 - Tuesday

**오전 (9am-12pm)** - 4시간

**Task 2.1: Uncertainty API 엔드포인트** (3시간)
```python
# 파일: backend/app/routers/uncertainty.py

from fastapi import APIRouter, Depends
from app.models.uncertainty import UncertaintyResponse
from src.uncertainty_map_v3 import UncertaintyMapV3

router = APIRouter(prefix="/api/uncertainty", tags=["uncertainty"])

@router.get("/status", response_model=UncertaintyResponse)
async def get_uncertainty_status(project_id: str = "default"):
    """
    불확실성 현재 상태 조회

    Returns:
        uncertainty_vector: [기술, 일정, 예산, 품질, 팀] 5D 벡터
        quantum_state: DETERMINISTIC/PROBABILISTIC/QUANTUM/CHAOTIC/VOID
        confidence: 0.0-1.0 (Bayesian confidence)
        last_updated: ISO timestamp
        mitigation_suggestions: [] (나중에 구현)
    """
    uncertainty_map = UncertaintyMapV3(project_id=project_id)

    # 5D 벡터 계산
    vector = uncertainty_map.calculate_current_vector()

    # 양자 상태 분류
    state = uncertainty_map.classify_quantum_state(vector)

    # Bayesian 신뢰도
    confidence = uncertainty_map.calculate_confidence(vector)

    return UncertaintyResponse(
        uncertainty_vector=vector.tolist(),
        quantum_state=state,
        confidence=confidence,
        last_updated=uncertainty_map.get_last_update_time(),
        mitigation_suggestions=[]
    )

# 테스트
# curl http://localhost:8000/api/uncertainty/status
# 예상 응답:
# {
#   "uncertainty_vector": [0.3, 0.5, 0.2, 0.4, 0.1],
#   "quantum_state": "PROBABILISTIC",
#   "confidence": 0.72,
#   "last_updated": "2025-11-28T09:30:00Z",
#   "mitigation_suggestions": []
# }
```

**Task 2.2: Friendly Error Formatter** (1시간)
```python
# 파일: backend/app/core/error_formatter.py

from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.exc import DatabaseError, IntegrityError

class FriendlyErrorFormatter:
    """사용자 친화적인 에러 메시지 변환"""

    ERROR_MESSAGES = {
        # 데이터베이스 에러
        "DatabaseError": "데이터베이스 연결에 실패했습니다. 잠시 후 다시 시도해주세요.",
        "IntegrityError": "이미 존재하는 데이터입니다. 다른 값을 입력해주세요.",

        # 검증 에러
        "ValidationError": "입력값을 확인해주세요: {field}",

        # AI API 에러
        "AIAPIError": "AI 서비스가 일시적으로 응답하지 않습니다. 캐시된 결과를 사용합니다.",
        "RateLimitError": "요청이 너무 많습니다. {retry_after}초 후 다시 시도해주세요.",

        # 권한 에러
        "AuthenticationError": "로그인이 필요합니다.",
        "AuthorizationError": "이 작업을 수행할 권한이 없습니다.",
    }

    @classmethod
    def format(cls, error: Exception) -> Dict[str, Any]:
        """에러를 친화적인 메시지로 변환"""
        error_type = type(error).__name__

        if error_type in cls.ERROR_MESSAGES:
            message = cls.ERROR_MESSAGES[error_type]
            # 플레이스홀더 치환
            if hasattr(error, 'field'):
                message = message.format(field=error.field)
            elif hasattr(error, 'retry_after'):
                message = message.format(retry_after=error.retry_after)
        else:
            message = "알 수 없는 오류가 발생했습니다. 관리자에게 문의해주세요."

        return {
            "error": True,
            "message": message,
            "detail": str(error),  # 디버깅용 (프로덕션에서는 제거)
            "error_type": error_type
        }

# FastAPI exception handler
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def friendly_exception_handler(request: Request, exc: Exception):
    formatted = FriendlyErrorFormatter.format(exc)
    return JSONResponse(
        status_code=500,
        content=formatted
    )
```

**오후 (1pm-5pm)** - 4시간

**Task 2.3: Uncertainty 계산 검증** (4시간)
```bash
# 테스트 파일 작성
# backend/tests/test_uncertainty_integration.py

pytest backend/tests/test_uncertainty_integration.py -v

# 예상 테스트:
# 1. test_uncertainty_vector_calculation
#    - 입력: 작업 3개 (2개 지연, 1개 정시)
#    - 예상: technical_risk > 0.5
#
# 2. test_quantum_state_classification
#    - 입력: vector = [0.1, 0.2, 0.1, 0.15, 0.05]
#    - 예상: DETERMINISTIC (총합 < 0.1)
#
# 3. test_bayesian_confidence
#    - 입력: historical_accuracy = 0.85, vector_magnitude = 0.4
#    - 예상: confidence ≈ 0.68
#
# 4. test_api_endpoint
#    - GET /api/uncertainty/status
#    - 응답 코드: 200
#    - 응답 구조: uncertainty_vector (list), quantum_state (str), confidence (float)

# 커버리지 확인
pytest --cov=backend --cov-report=html
# 목표: 80% 이상
```

---

#### Day 3 - Wednesday

**전체 (9am-5pm)** - 8시간

**Task 3.1: Prometheus + Monitoring** (4시간)
```python
# 파일: backend/app/monitoring.py (이미 존재, 개선)

from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
import time

# 메트릭 정의
api_latency_seconds = Histogram(
    'api_latency_seconds',
    'API latency in seconds',
    ['endpoint', 'method'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

uncertainty_updates_total = Counter(
    'uncertainty_updates_total',
    'Total number of uncertainty updates',
    ['quantum_state']
)

ai_api_calls_total = Counter(
    'ai_api_calls_total',
    'Total number of AI API calls',
    ['model', 'status']  # model: claude/codex/gemini, status: success/failure
)

current_uncertainty = Gauge(
    'current_uncertainty',
    'Current uncertainty magnitude',
    ['project_id']
)

# 데코레이터
def measure_latency(func):
    """API 레이턴시 측정"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            latency = time.time() - start
            api_latency_seconds.labels(
                endpoint=func.__name__,
                method='GET'  # request에서 가져오기
            ).observe(latency)
    return wrapper

# 사용 예시
@router.get("/uncertainty/status")
@measure_latency
async def get_uncertainty_status(...):
    ...
```

**설정 파일**:
```yaml
# config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'

  - job_name: 'celery'
    static_configs:
      - targets: ['localhost:5555']  # Flower

# Docker Compose에 추가
docker-compose up -d prometheus grafana

# Grafana 대시보드 확인
# http://localhost:3001 (admin/admin)
```

**Task 3.2: Celery + Redis** (4시간)
```python
# 파일: backend/app/background_tasks.py (이미 존재, 개선)

from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

celery_app = Celery(
    'udo_tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Celery 설정
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,  # 5분
)

# AI 오케스트레이션 태스크
@celery_app.task(name='ai_orchestration', bind=True, max_retries=3)
def orchestrate_ai(self, query: str, context: dict):
    """3-AI 오케스트레이션을 비동기로 처리"""
    from src.three_ai_collaboration_bridge import ThreeAICollaborationBridge

    try:
        bridge = ThreeAICollaborationBridge()
        result = bridge.orchestrate(query, context)

        # 메트릭 기록
        ai_api_calls_total.labels(
            model='claude',  # 또는 실제 사용된 모델
            status='success'
        ).inc()

        return result
    except Exception as exc:
        logger.error(f"AI orchestration failed: {exc}")
        ai_api_calls_total.labels(
            model='unknown',
            status='failure'
        ).inc()
        # 재시도
        raise self.retry(exc=exc, countdown=60)

# Celery worker 시작
# celery -A backend.app.background_tasks worker --loglevel=info --concurrency=3
```

---

#### Day 4 - Thursday

**오전 (9am-12pm)** - 4시간

**Task 4.1: Notification Service** (4시간)
```python
# 파일: backend/app/services/notification_service.py (신규)

from typing import List, Dict, Any
from datetime import datetime, timedelta
import aiohttp
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class NotificationService:
    """알림 서비스 (Email + Slack)"""

    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.rate_limiter = {}  # {category: last_sent_time}
        self.rate_limit_minutes = 15

    async def send_notification(
        self,
        category: str,  # 'uncertainty_spike', 'budget_warning', 'task_overrun'
        title: str,
        message: str,
        channels: List[str] = ['email', 'slack'],
        severity: str = 'info'  # 'info', 'warning', 'critical'
    ):
        """알림 전송 (Rate Limiting 적용)"""

        # Rate Limiting 체크
        if not self._can_send(category):
            logger.info(f"Rate limit: Skipping {category} (sent within {self.rate_limit_minutes} minutes)")
            return

        # 이메일 전송
        if 'email' in channels:
            await self._send_email(title, message, severity)

        # 슬랙 전송
        if 'slack' in channels:
            await self._send_slack(title, message, severity)

        # Rate Limiter 업데이트
        self.rate_limiter[category] = datetime.now()

    def _can_send(self, category: str) -> bool:
        """Rate Limiting 체크"""
        if category not in self.rate_limiter:
            return True

        last_sent = self.rate_limiter[category]
        elapsed = (datetime.now() - last_sent).total_seconds() / 60
        return elapsed >= self.rate_limit_minutes

    async def _send_email(self, title: str, message: str, severity: str):
        """SendGrid 이메일 전송"""
        mail = Mail(
            from_email='noreply@udo-platform.com',
            to_emails='dev-team@company.com',
            subject=f"[{severity.upper()}] {title}",
            html_content=f"""
            <h2>{title}</h2>
            <p>{message}</p>
            <p><a href="http://localhost:3000">대시보드 확인</a></p>
            """
        )

        try:
            response = self.sendgrid_client.send(mail)
            logger.info(f"Email sent: {response.status_code}")
        except Exception as e:
            logger.error(f"Email failed: {e}")

    async def _send_slack(self, title: str, message: str, severity: str):
        """Slack Webhook 전송"""
        emoji_map = {
            'info': ':information_source:',
            'warning': ':warning:',
            'critical': ':rotating_light:'
        }

        payload = {
            "text": f"{emoji_map[severity]} *{title}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{title}*"}
                },
                {
                    "type": "section",
                    "text": {"type": "plain_text", "text": message}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "대시보드 확인"},
                            "url": "http://localhost:3000"
                        }
                    ]
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.slack_webhook_url, json=payload) as resp:
                if resp.status == 200:
                    logger.info("Slack notification sent")
                else:
                    logger.error(f"Slack failed: {resp.status}")

# 트리거 예시
notification_service = NotificationService()

async def on_uncertainty_spike(quantum_state: str):
    """불확실성 급증 시 알림"""
    if quantum_state in ['QUANTUM', 'CHAOTIC', 'VOID']:
        await notification_service.send_notification(
            category='uncertainty_spike',
            title='불확실성 임계값 초과',
            message=f'프로젝트의 불확실성이 {quantum_state} 상태입니다. 즉시 확인이 필요합니다.',
            channels=['email', 'slack'],
            severity='warning' if quantum_state == 'QUANTUM' else 'critical'
        )
```

**오후 (1pm-5pm)** - 4시간

**Task 4.2: 테스트 커버리지 80%** (4시간)
```bash
# 테스트 파일 추가
# backend/tests/test_uncertainty_api.py
# backend/tests/test_notification_service.py
# backend/tests/test_dual_write.py

pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term

# 커버리지 목표:
# - backend/app/routers/: 85%
# - backend/app/services/: 80%
# - backend/app/models/: 90%
# - 전체: 80%+

# 커버리지 리포트 확인
# htmlcov/index.html
```

---

### Week 2-4: 자세한 계획은 통합 개발 가이드 참조

---

## Frontend Developer 액션 플랜

### 🎯 핵심 목표
- Week 1: API 연동 + 시각적 피드백
- Week 2: Uncertainty 시각화 + 실시간 업데이트
- Week 3: Mitigation Panel + AI Persona
- Week 4: E2E 테스트 + 문서화

### Week 1: API Connection (16시간)

#### Day 1 - Monday

**오전 (9am-12pm)** - 4시간

**Task 1.1: One-Click Start 스크립트** (2시간)
```json
// 파일: web-dashboard/package.json

{
  "scripts": {
    "dev": "next dev",
    "dev:full": "concurrently \"cd ../backend && .venv/Scripts/python.exe -m uvicorn main:app --reload\" \"npm run dev\"",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "devDependencies": {
    "concurrently": "^8.0.0"  // 추가
  }
}

// npm install concurrently

// 테스트
// npm run dev:full
// → Backend (http://localhost:8000) + Frontend (http://localhost:3000) 동시 시작
```

**Task 1.2: Scripts 크로스 플랫폼** (2시간)
```bash
# 파일: scripts/dev-start.sh (Unix)
#!/bin/bash
cd "$(dirname "$0")/.."
source .venv/bin/activate
concurrently "cd backend && uvicorn main:app --reload" "cd web-dashboard && npm run dev"

# 파일: scripts/dev-start.ps1 (Windows)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
cd "$scriptPath/.."
.venv\Scripts\activate
concurrently "cd backend && uvicorn main:app --reload" "cd web-dashboard && npm run dev"

# 실행 권한
chmod +x scripts/dev-start.sh

# 테스트
# Windows: ./scripts/dev-start.ps1
# Mac/Linux: ./scripts/dev-start.sh
```

---

#### Day 2 - Tuesday

**오전 (9am-12pm)** - 4시간

**Task 2.1: API Integration** (4시간)
```typescript
// 파일: web-dashboard/app/page.tsx

"use client"

import { useQuery } from '@tanstack/react-query'
import { UncertaintyMap } from '@/components/dashboard/uncertainty-map'
import { UncertaintyMapSkeleton } from '@/components/dashboard/skeleton'
import { ErrorFallback } from '@/components/ErrorFallback'

interface UncertaintyData {
  uncertainty_vector: number[]  // [기술, 일정, 예산, 품질, 팀]
  quantum_state: 'DETERMINISTIC' | 'PROBABILISTIC' | 'QUANTUM' | 'CHAOTIC' | 'VOID'
  confidence: number  // 0.0-1.0
  last_updated: string
  mitigation_suggestions: any[]
}

export default function Dashboard() {
  const { data, isLoading, error, refetch } = useQuery<UncertaintyData>({
    queryKey: ['uncertainty'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/uncertainty/status')
      if (!response.ok) {
        throw new Error('Failed to fetch uncertainty data')
      }
      return response.json()
    },
    refetchInterval: 5000,  // 5초마다 자동 새로고침
    retry: 3,
    retryDelay: 1000,
  })

  if (isLoading) {
    return <UncertaintyMapSkeleton />
  }

  if (error) {
    return <ErrorFallback error={error} onRetry={refetch} />
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">UDO Dashboard</h1>
      <UncertaintyMap data={data!} />
    </div>
  )
}
```

**오후 (1pm-5pm)** - 4시간

**Task 2.2: Connection Status UI** (3시간)
```typescript
// 파일: web-dashboard/components/ConnectionStatus.tsx

import { Loader2, AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function UncertaintyMapSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/4"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
      <div className="flex items-center space-x-2 text-gray-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>데이터를 불러오는 중...</span>
      </div>
    </div>
  )
}

export function ErrorFallback({
  error,
  onRetry
}: {
  error: Error
  onRetry: () => void
}) {
  return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <AlertCircle className="h-12 w-12 text-red-500" />
      <h2 className="text-xl font-semibold text-gray-900">데이터를 불러올 수 없습니다</h2>
      <p className="text-gray-600 text-center max-w-md">
        서버 연결에 문제가 발생했습니다. 네트워크 연결을 확인하거나 잠시 후 다시 시도해주세요.
      </p>
      <p className="text-sm text-gray-500 font-mono bg-gray-100 p-2 rounded">
        {error.message}
      </p>
      <Button onClick={onRetry} className="flex items-center space-x-2">
        <RefreshCw className="h-4 w-4" />
        <span>다시 시도</span>
      </Button>
    </div>
  )
}

export function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-64 space-y-4">
      <div className="text-6xl">📊</div>
      <h2 className="text-xl font-semibold text-gray-900">아직 데이터가 없습니다</h2>
      <p className="text-gray-600 text-center max-w-md">
        첫 작업을 시작하면 불확실성 지도가 자동으로 생성됩니다.
      </p>
      <Button>작업 시작하기</Button>
    </div>
  )
}
```

**Task 2.3: Toast Notifications** (1시간)
```bash
# 설치
npm install react-hot-toast

# 파일: web-dashboard/components/ToastNotifications.tsx
```

```typescript
import toast, { Toaster } from 'react-hot-toast'

// Layout에 추가
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  )
}

// 사용 예시
export function showNotifications(event: string, data: any) {
  switch (event) {
    case 'uncertainty_spike':
      toast.error(`⚠️ 불확실성이 증가했습니다! (${data.quantum_state})`, {
        duration: 5000,
      })
      break

    case 'task_overrun':
      toast.warning(`⏱️ 작업이 예상보다 ${data.overrun_pct}% 지연되고 있습니다`, {
        duration: 4000,
      })
      break

    case 'budget_warning':
      toast(`💰 AI 비용이 임계값에 도달했습니다 ($${data.current}/$${data.limit})`, {
        icon: '💰',
        duration: 6000,
      })
      break
  }
}
```

---

### Week 2-4: 자세한 계획은 통합 개발 가이드 참조

---

## DevOps Engineer 액션 플랜

### Week 1: Infrastructure (20시간)

#### Day 1 - 설정 검증 및 개선 (4시간)

**Task 1.1: docker-compose.yml 점검** (2시간)
```yaml
# 파일: docker-compose.yml

version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_USER: udo_user
      POSTGRES_PASSWORD: udo_pass
      POSTGRES_DB: udo_dev
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - udo-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - udo-network

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    networks:
      - udo-network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - udo-network

volumes:
  db-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  udo-network:
    driver: bridge

# 테스트
# docker-compose up -d
# docker-compose ps
```

---

## AI/ML Engineer 액션 플랜

### Week 2: 알고리즘 구현 (20시간)

#### Sprint 3: Bayesian 시스템 (12시간)

**Task: Bayesian Update 알고리즘**
```python
# 파일: src/adaptive_bayesian_uncertainty.py

import numpy as np
from scipy.stats import beta
from typing import List, Tuple

class AdaptiveBayesianUncertainty:
    """적응형 Bayesian 불확실성 시스템"""

    def __init__(self):
        self.prior = np.array([0.5] * 5)  # 5D prior (neutral)
        self.historical_accuracy = 0.7  # 초기 정확도

    def update_uncertainty(
        self,
        observed_vector: np.ndarray,
        likelihood: float = 0.8
    ) -> np.ndarray:
        """
        Bayesian update

        Args:
            observed_vector: 관측된 5D 벡터
            likelihood: 관측 신뢰도

        Returns:
            posterior: 업데이트된 불확실성 벡터
        """
        # Bayes' Theorem: P(H|E) = P(E|H) * P(H) / P(E)
        evidence = self._calculate_evidence(observed_vector)
        posterior = (likelihood * observed_vector * self.prior) / evidence

        # Prior 업데이트 (다음 반복을 위해)
        self.prior = posterior

        return posterior

    def _calculate_evidence(self, observed: np.ndarray) -> float:
        """주변 확률 계산"""
        # Normalization constant
        return np.sum(observed * self.prior)

    def calculate_confidence(
        self,
        uncertainty_vector: np.ndarray
    ) -> float:
        """
        Bayesian confidence 계산

        Returns:
            confidence: 0.0-1.0 (높을수록 확신)
        """
        magnitude = np.linalg.norm(uncertainty_vector)
        # 불확실성이 낮을수록 confidence 높음
        base_confidence = 1 / (1 + magnitude)
        # Historical accuracy 반영
        adjusted_confidence = base_confidence * self.historical_accuracy
        return np.clip(adjusted_confidence, 0.0, 1.0)

    def process_rlhf_feedback(
        self,
        decision_id: str,
        rating: int,  # 1 (긍정) or 0 (부정)
        uncertainty_at_decision: float
    ):
        """
        RLHF 피드백 처리

        - 긍정 피드백: 불확실성 감소, accuracy 증가
        - 부정 피드백: 불확실성 증가, accuracy 감소
        """
        if rating == 1:  # 긍정
            # 불확실성 10% 감소
            self.prior = np.maximum(self.prior - 0.1, 0.1)
            # Accuracy 5% 증가
            self.historical_accuracy = min(self.historical_accuracy + 0.05, 1.0)
        else:  # 부정
            # 불확실성 20% 증가
            self.prior = np.minimum(self.prior + 0.2, 0.9)
            # Accuracy 5% 감소
            self.historical_accuracy = max(self.historical_accuracy - 0.05, 0.5)

        logger.info(f"RLHF feedback processed: rating={rating}, new_accuracy={self.historical_accuracy:.2f}")

# 테스트
# pytest tests/test_adaptive_bayesian.py -v
```

---

## 팀 협업 체크포인트

### Week 1 Friday 5pm - 전체 팀 검증

**참석자**: Backend, Frontend, DevOps, AI/ML (전원)

**안건**:
1. ✅ 각 역할 Week 1 작업 완료 확인
2. ✅ 통합 테스트 (`npm run dev:full` + API 호출)
3. ✅ 성능 베이스라인 측정 (k6)
4. ✅ Week 2 경로 선택 (Optimistic/Realistic/Pessimistic)

**준비물**:
- Backend: API 엔드포인트 리스트 + Swagger UI
- Frontend: 브라우저 데모 (localhost:3000)
- DevOps: Prometheus/Grafana 대시보드 (localhost:9090, :3001)
- AI/ML: 불확실성 계산 검증 결과

**체크리스트**:
```yaml
infrastructure:
  - ✅ PostgreSQL 연결
  - ✅ Redis 연결
  - ✅ Prometheus 메트릭 수집
  - ✅ Grafana 대시보드 표시

backend:
  - ✅ GET /api/uncertainty/status 작동
  - ✅ Friendly Error 메시지 작동
  - ✅ 테스트 커버리지 >= 80%
  - ✅ mypy 오류 0개

frontend:
  - ✅ npm run dev:full 작동
  - ✅ API 데이터 렌더링
  - ✅ 로딩/에러/빈 상태 UI
  - ✅ Toast 알림 작동

integration:
  - ✅ Backend → Frontend 데이터 흐름
  - ✅ WebSocket 연결 (준비)
  - ✅ CI/CD 파이프라인 작동
```

**Week 2 경로 선택**:
```
IF all_checkboxes == TRUE AND velocity >= 1.2x:
  → Optimistic Path (추가 기능 가능)
ELSIF velocity >= 0.8x:
  → Realistic Path (계획대로)
ELSE:
  → Pessimistic Path (Scope 축소)
```

---

**생성일**: 2025-11-28
**다음 업데이트**: Week 1 Day 5 (체크포인트 후)
