# Week 0 프로세스 개선 계획

**Date**: 2025-12-07
**Purpose**: 개발 및 검증 프로세스 보완 검토
**Status**: 📋 PLANNING

---

## 현재 프로세스 (접근법 C) ✅

### Week 0 (Day 1-5): 백엔드 검증 집중

```yaml
검증 전략:
  - 매 Day: pytest로 백엔드 단위 테스트
  - Week 0 완료: Playwright로 웹 통합 테스트 1회
  - Week 1+: 매 기능별 Playwright 검증

강점:
  - ✅ 효율적 (레이어별 적절한 도구)
  - ✅ 빠른 피드백 (pytest <1분)
  - ✅ 정확한 검증 (백엔드/프론트 분리)

현재 적용 중:
  - Day 1: pytest --cov (408 tests, 58% coverage)
  - Day 2: pytest test_unified_error_resolver.py (14/22 passing)
  - Git commit 전 수동 pytest 실행
```

---

## 🔍 프로세스 갭 분석

### 1. CI/CD 파이프라인 부재 ⚠️

**현재 상태**:
- ❌ GitHub Actions / GitLab CI 없음
- ❌ 자동 테스트 실행 없음
- ❌ 자동 배포 없음
- ✅ Git hooks만 있음 (post-commit Obsidian sync)

**문제점**:
- 커밋 전 테스트 실패해도 푸시 가능
- PR 없이 main에 직접 커밋
- 품질 게이트 없음

**영향**:
- 테스트 실패한 코드가 main에 머지될 위험
- 다른 개발자와 협업 시 충돌 위험

### 2. 품질 게이트 부재 ⚠️

**현재 상태**:
- ❌ Pre-commit hooks 없음 (pytest, lint)
- ❌ 커버리지 임계값 강제 없음
- ✅ Constitutional guard (P1: Design Review First)

**문제점**:
- 테스트 실패 코드 커밋 가능
- 커버리지 하락 감지 못함 (58% → 40% 가능)

**영향**:
- 품질 저하 조기 감지 불가

### 3. 성능 벤치마크 추적 부재 ⚠️

**현재 상태**:
- ❌ 성능 테스트 자동화 없음
- ❌ 성능 저하 감지 없음
- ✅ 수동 벤치마크만 있음 (backend/benchmark_api.py)

**문제점**:
- 코드 변경으로 성능 저하되어도 모름
- Tier 1 <10ms, Tier 2 <500ms 목표 검증 안 됨

### 4. 보안 스캔 부재 ⚠️

**현재 상태**:
- ❌ 의존성 취약점 스캔 없음
- ❌ 코드 보안 스캔 없음
- ✅ Constitutional guard로 수동 검증

**문제점**:
- CVE 취약점 있는 패키지 사용 가능
- SQL injection, XSS 위험 감지 못함

### 5. 문서 자동 생성 부재 ⚠️

**현재 상태**:
- ❌ API 문서 자동 생성 없음 (FastAPI /docs만)
- ❌ 코드 변경 시 문서 자동 업데이트 없음
- ✅ 수동 마크다운 문서 작성

**문제점**:
- 코드-문서 불일치 위험
- 문서 업데이트 누락 가능

### 6. 통합 테스트 자동화 부재 ⚠️

**현재 상태**:
- ❌ E2E 테스트 자동 실행 없음
- ❌ 백엔드-프론트 통합 테스트 자동화 없음
- ✅ 수동 Playwright 테스트만

**문제점**:
- 통합 회귀(regression) 감지 못함
- 백엔드-프론트 불일치 늦게 발견

---

## 📋 개선 계획 (우선순위별)

### P0: 즉시 적용 (Week 0 Day 3-5)

#### 1. Pre-commit Hooks 설정 (30분)

**목적**: 커밋 전 자동 품질 검증

**구현**:
```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "🔍 Running pre-commit checks..."

# 1. Pytest 실행 (백엔드만)
echo "Running pytest..."
.venv/Scripts/python.exe -m pytest backend/tests/ -q --tb=line
if [ $? -ne 0 ]; then
    echo "❌ Tests failed! Commit aborted."
    exit 1
fi

# 2. 커버리지 체크 (최소 55% - 현재보다 낮아지면 안 됨)
echo "Checking coverage..."
COVERAGE=$(pytest --cov=backend --cov=src --cov-report=term | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
if [ "$COVERAGE" -lt 55 ]; then
    echo "❌ Coverage dropped below 55% (current: $COVERAGE%). Commit aborted."
    exit 1
fi

# 3. Linting (fast)
echo "Running linters..."
black --check backend/ src/ || exit 1
flake8 backend/ src/ || exit 1

echo "✅ All checks passed!"
exit 0
```

**효과**:
- 테스트 실패 코드 커밋 방지
- 커버리지 하락 방지 (55% 최소 유지)
- 코드 스타일 일관성 유지

**ROI**: 30분 투자 → 품질 사고 방지 (무한 ROI)

#### 2. 성능 벤치마크 베이스라인 (1시간)

**목적**: 성능 저하 조기 감지

**구현**:
```python
# backend/tests/test_performance_baseline.py
import time
from backend.app.services.unified_error_resolver import UnifiedErrorResolver

def test_tier2_resolution_speed():
    """Tier 2 resolution must be <1ms (pattern matching)"""
    resolver = UnifiedErrorResolver()

    start = time.time()
    result = resolver.resolve_error("ModuleNotFoundError: No module named 'pandas'")
    duration = (time.time() - start) * 1000

    assert duration < 1.0, f"Tier 2 too slow: {duration:.2f}ms (target <1ms)"

def test_statistics_overhead():
    """Statistics tracking overhead must be <5ms"""
    resolver = UnifiedErrorResolver()

    start = time.time()
    stats = resolver.get_statistics()
    duration = (time.time() - start) * 1000

    assert duration < 5.0, f"Stats too slow: {duration:.2f}ms (target <5ms)"
```

**효과**:
- 성능 회귀 자동 감지
- Tier 1 <10ms, Tier 2 <1ms 목표 강제

**ROI**: 1시간 투자 → 성능 저하 방지 (사용자 경험 보호)

#### 3. 커버리지 트렌드 추적 (30분)

**목적**: 커버리지 변화 시각화

**구현**:
```python
# scripts/track_coverage.py
import json
from datetime import datetime
from pathlib import Path

def record_coverage(coverage_percent: float):
    """Record coverage to trend file"""
    trend_file = Path("data/coverage_trend.json")
    trend_file.parent.mkdir(exist_ok=True)

    if trend_file.exists():
        data = json.load(open(trend_file))
    else:
        data = {"history": []}

    data["history"].append({
        "date": datetime.now().isoformat(),
        "coverage": coverage_percent
    })

    # Keep last 100 records
    data["history"] = data["history"][-100:]

    json.dump(data, open(trend_file, 'w'), indent=2)
    print(f"📊 Coverage recorded: {coverage_percent}%")

# Git hook에서 호출
# python scripts/track_coverage.py --coverage 58
```

**효과**:
- 커버리지 변화 추적 (58% → 75% 목표 모니터링)
- 주간 트렌드 분석 가능

### P1: Week 1 MVP 시작 전 적용 (Week 0 완료 후)

#### 4. GitHub Actions CI/CD (2시간)

**목적**: 자동 테스트 + 배포

**구현**:
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r backend/requirements.txt
      - name: Run pytest
        run: pytest backend/tests/ --cov=backend --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd web-dashboard
          npm install
      - name: Run linting
        run: npm run lint
      - name: Build
        run: npm run build

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    steps:
      - uses: actions/checkout@v3
      - name: Run E2E tests
        run: |
          cd web-dashboard
          npm run test:e2e

  deploy:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend, e2e-tests]
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: echo "Deploy logic here"
```

**효과**:
- PR마다 자동 테스트 (품질 게이트)
- main 머지 전 E2E 검증
- 자동 배포 (수동 개입 최소화)

**ROI**: 2시간 투자 → 회귀 방지 + 자동화 95%

#### 5. 의존성 보안 스캔 (1시간)

**목적**: CVE 취약점 자동 감지

**구현**:
```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  schedule:
    - cron: '0 0 * * 0'  # 매주 일요일
  push:
    branches: [main]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Snyk
        uses: snyk/actions/python@master
        with:
          args: --severity-threshold=high

  code-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit (Python)
        run: |
          pip install bandit
          bandit -r backend/ src/
      - name: Run CodeQL
        uses: github/codeql-action/analyze@v2
```

**효과**:
- CVE 취약점 자동 감지
- SQL injection, XSS 등 보안 위험 검출

**ROI**: 1시간 투자 → 보안 사고 방지 (무한 ROI)

#### 6. 통합 테스트 자동화 (3시간)

**목적**: 백엔드-프론트 통합 회귀 방지

**구현**:
```yaml
# .github/workflows/e2e.yml
name: E2E Integration Tests

on:
  pull_request:
    branches: [main]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # 백엔드 시작
      - name: Start backend
        run: |
          .venv/Scripts/python.exe -m uvicorn backend.main:app &
          sleep 5

      # 프론트엔드 시작
      - name: Start frontend
        run: |
          cd web-dashboard
          npm run dev &
          sleep 10

      # Playwright E2E
      - name: Run E2E tests
        run: |
          cd web-dashboard
          npm run test:e2e

      # 실패 시 스크린샷 저장
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-screenshots
          path: web-dashboard/test-results/
```

**효과**:
- PR마다 자동 E2E 검증
- 통합 회귀 조기 감지
- 실패 시 스크린샷으로 디버깅

**ROI**: 3시간 투자 → 통합 버그 방지 (사용자 영향 최소화)

### P2: Week 2 이후 적용 (최적화)

#### 7. 메트릭 대시보드 (4시간)

**목적**: 실시간 품질/성능 모니터링

**구현**:
- Grafana + Prometheus
- 메트릭: 테스트 커버리지, 성능, 에러율, 자동화율

#### 8. 자동 문서 생성 (2시간)

**목적**: 코드-문서 일관성

**구현**:
- Sphinx (Python API 문서)
- TypeDoc (TypeScript 문서)
- Git hook으로 자동 업데이트

---

## 📊 개선 효과 예측

### 현재 (Week 0 Day 2)

```yaml
자동화율: 52%
품질 게이트: 수동 (Constitutional guard만)
CI/CD: 없음
보안 스캔: 없음
성능 추적: 수동
문서 동기화: 수동
```

### P0 적용 후 (Week 0 Day 5)

```yaml
자동화율: 65%
품질 게이트: 자동 (pre-commit hooks)
  - pytest 자동 실행
  - 커버리지 55% 최소 강제
  - linting 자동
CI/CD: 없음 (Week 1에 적용)
보안 스캔: 없음 (Week 1에 적용)
성능 추적: 베이스라인 설정 ✅
문서 동기화: 수동
```

### P1 적용 후 (Week 1 시작 전)

```yaml
자동화율: 85%
품질 게이트: 완전 자동화
  - PR마다 자동 테스트
  - E2E 자동 실행
  - 커버리지 트렌드 추적
CI/CD: GitHub Actions ✅
  - 자동 테스트
  - 자동 배포
보안 스캔: 주간 자동 스캔 ✅
성능 추적: 자동 벤치마크 ✅
문서 동기화: 수동
```

### P2 적용 후 (Week 2+)

```yaml
자동화율: 95%
품질 게이트: 완전 자동화 + 시각화
CI/CD: 완전 자동화
보안 스캔: 실시간 모니터링
성능 추적: 실시간 대시보드
문서 동기화: 자동 생성 ✅
메트릭 대시보드: Grafana ✅
```

---

## 🎯 실행 계획

### Week 0 Day 3-5 (P0 적용)

**Day 3**:
- ✅ Pre-commit hooks 설정 (30분)
- ✅ 성능 벤치마크 베이스라인 (1시간)
- ✅ Prediction accuracy formula 정의

**Day 4**:
- ✅ 커버리지 트렌드 추적 구현 (30분)
- ✅ RL hypothesis 검증

**Day 5**:
- ✅ Timeline 확정
- ✅ Week 0 종합 검증 (pytest + Playwright 1회)

**총 투자 시간**: 2시간 (프로세스 개선)

### Week 0 완료 후 → Week 1 시작 전 (P1 적용)

**준비 기간**: 1일 (6시간)

**작업**:
- ✅ GitHub Actions CI/CD 설정 (2시간)
- ✅ 의존성 보안 스캔 (1시간)
- ✅ 통합 테스트 자동화 (3시간)

**효과**: Week 1 MVP 개발 시작 시 완전 자동화 인프라 준비

### Week 2 이후 (P2 적용)

**작업**:
- ✅ 메트릭 대시보드 (4시간)
- ✅ 자동 문서 생성 (2시간)

---

## 📋 체크리스트

### Week 0 Day 3 (오늘)
- [ ] Pre-commit hooks 설정
- [ ] 성능 벤치마크 베이스라인
- [ ] Prediction accuracy formula

### Week 0 Day 4
- [ ] 커버리지 트렌드 추적
- [ ] RL hypothesis 검증

### Week 0 Day 5
- [ ] Week 0 종합 검증 (pytest + Playwright)
- [ ] Timeline 확정

### Week 1 시작 전
- [ ] GitHub Actions CI/CD
- [ ] 보안 스캔 자동화
- [ ] E2E 자동화

### Week 2+
- [ ] 메트릭 대시보드
- [ ] 문서 자동 생성

---

## 🎯 결론

**현재 접근법 C는 올바름** ✅

**추가 보완사항**:
1. **P0 (즉시)**: Pre-commit hooks, 성능 베이스라인, 커버리지 추적
   - 투자: 2시간
   - 효과: 품질 게이트 자동화, 회귀 방지

2. **P1 (Week 1 전)**: CI/CD, 보안 스캔, E2E 자동화
   - 투자: 6시간 (1일)
   - 효과: 완전 자동화, 95% 자동화율

3. **P2 (Week 2+)**: 메트릭 대시보드, 문서 자동화
   - 투자: 6시간
   - 효과: 실시간 모니터링, 문서 일관성

**총 ROI**: 14시간 투자 → 자동화율 52% → 95% (+43pp)
**연간 절약**: 197시간 (에러 해결) + 100시간 (수동 테스트) = 297시간 = 37.1일

**Week 0 Day 3 시작하시겠습니까?**
