# 3-Tier 자동 해결 시스템 구현 - 불확실성 지도 기반 보완책

## 📅 메타데이터
- **생성일**: 2025-11-21
- **UDO 단계**: Implementation → Testing
- **불확실성 수준**: QUANTUM (30-60%) → PROBABILISTIC (10-30%)
- **목표 자동화율**: 95% (현재 0% → 목표 95%)

## 🎯 핵심 목표

### Primary Goal
**3-Tier 자동 해결 시스템을 100% 자동으로 실행하여 95% 자동화 달성**

### Success Criteria
- ✅ 모든 에러 발생 시 자동으로 3-Tier cascade 실행
- ✅ Tier 1 (Obsidian) 히트율 70%+
- ✅ Tier 2 (Context7) 히트율 25%+
- ✅ Tier 3 (User) 개입 5% 이하
- ✅ 평균 해결 시간 <1초 (Tier 1/2), <5분 (Tier 3)

## 🌊 불확실성 분석 (Quantum State → Probabilistic)

### 현재 상태: 🟠 QUANTUM (30-60% 불확실성)

**불확실성 요인**:
1. **AI 습관 패턴 변경 실패** (40% 불확실성)
   - 위험: 규칙 알아도 자동 실행 안함
   - 영향: 3-Tier 시스템 우회, 수동 디버깅 반복

2. **트리거 메커니즘 부재** (50% 불확실성)
   - 위험: 에러 발생 시 자동 감지/실행 안됨
   - 영향: 시스템이 사실상 비활성화 상태

3. **책임감/점검 부재** (60% 불확실성)
   - 위험: 위반해도 피드백 없음
   - 영향: 반복적 규칙 무시

### 목표 상태: 🔵 PROBABILISTIC (10-30% 불확실성)

**완화 전략**:
1. **강제 체크포인트 시스템** → 15% 불확실성
2. **자동 트리거 메커니즘** → 10% 불확실성
3. **세션 종료 검증** → 20% 불확실성

## 📋 Phase-Aware 구현 계획

### Phase 1: Foundation (즉시 적용) - DETERMINISTIC (<10%)

**목표**: 자동 트리거 메커니즘 구축

#### 1.1 에러 감지 래퍼 생성
```python
# scripts/auto_3tier_wrapper.py
from typing import Any, Callable
from scripts.unified_error_resolver import UnifiedErrorResolver
import functools

class Auto3TierWrapper:
    """
    모든 도구 호출을 자동으로 래핑하여 3-Tier 시스템 적용
    """
    def __init__(self):
        self.resolver = UnifiedErrorResolver()
        self.stats = {
            "total_calls": 0,
            "auto_resolved": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier3_escalations": 0
        }

    def wrap_tool(self, tool_func: Callable) -> Callable:
        """도구 함수를 3-Tier 자동 해결로 래핑"""
        @functools.wraps(tool_func)
        def wrapper(*args, **kwargs):
            self.stats["total_calls"] += 1

            try:
                result = tool_func(*args, **kwargs)

                # 에러 체크 (exit_code, error 필드 등)
                if self._is_error(result):
                    error_msg = self._extract_error(result)

                    # 🔥 AUTOMATIC 3-TIER CASCADE
                    solution = self.resolver.resolve_error(
                        error_msg,
                        context={
                            "tool": tool_func.__name__,
                            "args": str(args)[:100],
                            "kwargs": str(kwargs)[:100]
                        }
                    )

                    if solution:
                        # Tier 1 or 2 hit
                        stats = self.resolver.get_statistics()
                        if stats["tier1"] > self.stats["tier1_hits"]:
                            self.stats["tier1_hits"] += 1
                            self.stats["auto_resolved"] += 1
                            print(f"✅ [TIER 1] Auto-resolved from Obsidian")
                        elif stats["tier2"] > self.stats["tier2_hits"]:
                            self.stats["tier2_hits"] += 1
                            self.stats["auto_resolved"] += 1
                            print(f"✅ [TIER 2] Auto-resolved from Context7")

                        # 해결책 적용 후 재시도
                        return self._apply_and_retry(solution, tool_func, args, kwargs)
                    else:
                        # Tier 3: User escalation
                        self.stats["tier3_escalations"] += 1
                        print(f"❌ [TIER 3] No automated solution - escalating to user")
                        raise Exception(f"No solution found: {error_msg}")

                return result

            except Exception as e:
                # 예외도 3-Tier로 처리
                error_msg = str(e)
                solution = self.resolver.resolve_error(error_msg, context={
                    "tool": tool_func.__name__,
                    "exception": type(e).__name__
                })

                if solution:
                    return self._apply_and_retry(solution, tool_func, args, kwargs)
                else:
                    # 재발생 (사용자에게 알림)
                    raise

        return wrapper

    def _is_error(self, result: Any) -> bool:
        """결과에서 에러 감지"""
        if isinstance(result, dict):
            return result.get("exit_code", 0) != 0 or "error" in result
        return False

    def _extract_error(self, result: Any) -> str:
        """에러 메시지 추출"""
        if isinstance(result, dict):
            return result.get("stderr", "") or result.get("error", "")
        return str(result)

    def _apply_and_retry(self, solution: str, func: Callable, args, kwargs):
        """해결책 적용 후 재시도"""
        # 해결책 실행 (예: Bash 명령)
        import subprocess
        subprocess.run(solution, shell=True, capture_output=True)

        # 원래 도구 재실행
        return func(*args, **kwargs)

    def get_automation_rate(self) -> float:
        """자동화율 계산"""
        if self.stats["total_calls"] == 0:
            return 0.0
        return (self.stats["auto_resolved"] / self.stats["total_calls"]) * 100

# 전역 인스턴스
_wrapper = Auto3TierWrapper()

def auto_3tier(func):
    """데코레이터: 함수에 3-Tier 자동 해결 적용"""
    return _wrapper.wrap_tool(func)
```

**불확실성**: 🟢 DETERMINISTIC (5%)
- 위험: 코드 작성은 확실
- 완화: 단위 테스트로 검증

#### 1.2 세션 시작/종료 체크포인트
```python
# scripts/session_checkpoint.py
from datetime import datetime
from typing import Dict, List
import json

class SessionCheckpoint:
    """세션 시작/종료 시 3-Tier 시스템 검증"""

    def __init__(self):
        self.checkpoint_file = ".claude/session_checkpoint.json"
        self.violations = []

    def session_start(self):
        """세션 시작 체크리스트"""
        print("🔍 Session Start Checkpoint")
        checks = {
            "obsidian_auto_search_enabled": self._check_obsidian_enabled(),
            "unified_resolver_available": self._check_resolver_available(),
            "auto_wrapper_active": self._check_wrapper_active()
        }

        if not all(checks.values()):
            failed = [k for k, v in checks.items() if not v]
            raise RuntimeError(f"❌ Session start failed: {failed}")

        print("✅ All systems active")
        return checks

    def session_end(self) -> Dict:
        """세션 종료 검증"""
        print("🔍 Session End Checkpoint")

        stats = _wrapper.stats
        automation_rate = _wrapper.get_automation_rate()

        report = {
            "timestamp": datetime.now().isoformat(),
            "automation_rate": automation_rate,
            "total_errors": stats["total_calls"],
            "auto_resolved": stats["auto_resolved"],
            "tier1_hits": stats["tier1_hits"],
            "tier2_hits": stats["tier2_hits"],
            "tier3_escalations": stats["tier3_escalations"],
            "violations": self.violations
        }

        # 목표 미달 시 경고
        if automation_rate < 90:
            print(f"⚠️  Automation rate: {automation_rate:.1f}% (Goal: 95%)")
        else:
            print(f"✅ Automation rate: {automation_rate:.1f}%")

        # Obsidian 동기화 확인
        obsidian_synced = self._check_obsidian_sync()
        if not obsidian_synced:
            print("❌ Obsidian sync incomplete!")
            report["obsidian_synced"] = False
        else:
            report["obsidian_synced"] = True

        # 체크포인트 저장
        self._save_checkpoint(report)

        return report

    def record_violation(self, violation_type: str, details: str):
        """규칙 위반 기록"""
        self.violations.append({
            "timestamp": datetime.now().isoformat(),
            "type": violation_type,
            "details": details
        })

    def _check_obsidian_enabled(self) -> bool:
        """Obsidian 자동 검색 활성화 확인"""
        # TODO: 실제 확인 로직
        return True

    def _check_resolver_available(self) -> bool:
        """Unified resolver 사용 가능 확인"""
        try:
            from scripts.unified_error_resolver import UnifiedErrorResolver
            return True
        except ImportError:
            return False

    def _check_wrapper_active(self) -> bool:
        """Auto wrapper 활성화 확인"""
        return _wrapper is not None

    def _check_obsidian_sync(self) -> bool:
        """Obsidian 동기화 완료 확인"""
        # 오늘 날짜 폴더에 파일이 있는지 확인
        from pathlib import Path
        today = datetime.now().strftime("%Y-%m-%d")
        vault_path = Path("C:/Users/user/Documents/Obsidian Vault/개발일지")
        today_folder = vault_path / today

        if not today_folder.exists():
            return False

        # 오늘 생성된 .md 파일이 있는지
        md_files = list(today_folder.glob("*.md"))
        return len(md_files) > 0

    def _save_checkpoint(self, report: Dict):
        """체크포인트 저장"""
        with open(self.checkpoint_file, "w") as f:
            json.dump(report, f, indent=2)

checkpoint = SessionCheckpoint()
```

**불확실성**: 🟢 DETERMINISTIC (8%)
- 위험: 체크 로직 누락 가능성
- 완화: 각 체크 항목 테스트

---

### Phase 2: Integration (1주 내) - PROBABILISTIC (10-30%)

**목표**: 실제 워크플로우에 통합

#### 2.1 모든 도구 호출에 자동 적용
```python
# .claude/hooks/tool_wrapper.py
"""
모든 도구 호출을 자동으로 래핑하는 훅
"""
from scripts.auto_3tier_wrapper import auto_3tier

# Bash 도구 래핑
original_bash = Bash
@auto_3tier
def Bash(*args, **kwargs):
    return original_bash(*args, **kwargs)

# Read 도구 래핑
original_read = Read
@auto_3tier
def Read(*args, **kwargs):
    return original_read(*args, **kwargs)

# Edit 도구 래핑
original_edit = Edit
@auto_3tier
def Edit(*args, **kwargs):
    return original_edit(*args, **kwargs)

# ... 모든 도구 래핑
```

**불확실성**: 🔵 PROBABILISTIC (20%)
- 위험: 일부 도구에서 작동 안 할 수 있음
- 완화: 점진적 적용, 도구별 테스트

#### 2.2 Obsidian 자동 검색 통합
```python
# scripts/obsidian_auto_resolver.py
"""
에러 발생 시 자동으로 Obsidian 검색
"""
def search_obsidian_for_error(error_msg: str) -> Optional[str]:
    """
    Tier 1: Obsidian 지식 베이스 검색
    """
    # 1. 파일명 기반 검색 (빠름, 80% 히트율)
    keywords = extract_keywords(error_msg)
    filename_pattern = f"*{'-'.join(keywords)}*.md"

    files = glob_obsidian_vault(filename_pattern)
    if files:
        # 가장 최근 파일 읽기
        latest = max(files, key=lambda f: f.stat().st_mtime)
        return extract_solution(latest)

    # 2. Frontmatter 검색 (중간, 15% 추가)
    # 3. 전체 텍스트 검색 (느림, 5% 추가)

    return None
```

**불확실성**: 🔵 PROBABILISTIC (25%)
- 위험: 검색 정확도 낮을 수 있음
- 완화: 3단계 검색 (파일명→Frontmatter→전체)

---

### Phase 3: Validation (2주 내) - PROBABILISTIC (10-20%)

**목표**: 95% 자동화율 달성 검증

#### 3.1 자동화율 모니터링 대시보드
```python
# web-dashboard/app/automation-metrics/page.tsx
"""
3-Tier 시스템 성능 대시보드
"""
- Tier 1/2/3 히트율 차트
- 시간대별 자동화율 추이
- 에러 유형별 해결 방법
- 평균 해결 시간
```

#### 3.2 A/B 테스트
- **Group A**: 3-Tier 자동 (목표)
- **Group B**: 수동 디버깅 (기존)
- **메트릭**: 해결 시간, 성공률, 사용자 만족도

**불확실성**: 🔵 PROBABILISTIC (15%)
- 위험: 목표 미달 (95% 안 나올 수 있음)
- 완화: 점진적 개선, 임계값 조정

---

## 🛡️ 보완책 (Safety Net)

### Rollback 전략 (4단계)

#### Level 1: 즉시 롤백 (<1분)
**트리거**: 3-Tier 시스템이 반복적으로 실패 (3회 연속)
```python
if auto_3tier_failures >= 3:
    disable_auto_3tier()
    fallback_to_manual_debug()
    alert_user("3-Tier 시스템 일시 비활성화")
```

#### Level 2: 부분 롤백 (<5분)
**트리거**: 특정 Tier에서만 문제
```python
if tier2_failures >= 5:
    disable_tier2_only()
    use_tier1_and_tier3_only()
```

#### Level 3: 완전 롤백 (<1시간)
**트리거**: 시스템 전체 오작동
```bash
git revert <commit-hash>
rm -rf scripts/auto_3tier_wrapper.py
# 기존 수동 방식으로 복귀
```

#### Level 4: 근본 재설계 (<1주)
**트리거**: 불확실성 60% 이상 지속
- 아키텍처 재검토
- 대안 접근 방식 탐색

### Circuit Breaker 패턴
```python
class CircuitBreaker:
    """3-Tier 시스템 보호"""
    def __init__(self, failure_threshold=3):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func):
        if self.state == "OPEN":
            raise Exception("Circuit breaker OPEN - system disabled")

        try:
            result = func()
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.threshold:
                self.state = "OPEN"
                alert_user("Circuit breaker OPEN!")
            raise
```

---

## 📊 예상 ROI

### 시간 절약
```
현재 (수동):
- 에러당 평균 10분 디버깅
- 하루 10개 에러 = 100분

자동화 후 (95%):
- Tier 1 (70%): 7개 × <10ms = <1초
- Tier 2 (25%): 2.5개 × <500ms = <2초
- Tier 3 (5%): 0.5개 × 10분 = 5분
- 총: 약 5분

절감: 95분/일 = 24일/년
```

### 품질 향상
- 일관성: 100% (과거 검증된 해결책)
- 재발 방지: 90%+ (Obsidian 축적)
- 학습 속도: 3x (자동 문서화)

---

## ✅ Implementation Checklist

### Immediate (오늘)
- [x] 불확실성 분석 완료
- [ ] `auto_3tier_wrapper.py` 작성
- [ ] `session_checkpoint.py` 작성
- [ ] 단위 테스트 작성

### Week 1
- [ ] 모든 도구에 래퍼 적용
- [ ] Obsidian 자동 검색 통합
- [ ] Circuit breaker 구현
- [ ] 첫 자동화율 측정

### Week 2
- [ ] 95% 목표 달성 검증
- [ ] A/B 테스트 완료
- [ ] 대시보드 생성
- [ ] 문서화 완료

---

## 🎯 Success Metrics

| 메트릭 | 현재 | 목표 (1주) | 목표 (2주) |
|--------|------|-----------|-----------|
| 자동화율 | 0% | 70% | 95% |
| Tier 1 히트율 | 0% | 50% | 70% |
| Tier 2 히트율 | 0% | 15% | 25% |
| 평균 해결 시간 | 10분 | 2분 | <1분 |
| 불확실성 수준 | QUANTUM (50%) | PROBABILISTIC (20%) | PROBABILISTIC (10%) |

---

**최종 업데이트**: 2025-11-21 23:55
**불확실성 상태**: 🟠 QUANTUM → 🔵 PROBABILISTIC (예상)
**다음 검토**: 2025-11-28
