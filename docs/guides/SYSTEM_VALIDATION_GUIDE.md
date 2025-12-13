# System Validation Guide

**규칙-구현 일치성 자동 검증 시스템**

## 개요

`.claude/` 폴더의 규칙 파일과 실제 구현 간의 불일치를 자동으로 감지하는 시스템입니다.

## 검증 레벨

### 🔴 CRITICAL (필수)
시스템 작동에 필수적인 요소. 실패 시 커밋이 차단됩니다.

**예시**:
- Git hooks 존재 (`post-commit`, `pre-commit`)
- 필수 스크립트 존재 (`obsidian_auto_sync.py`, `unified_error_resolver.py`)
- 3-Tier Error Resolution 구조 구현

### 🟡 IMPORTANT (중요)
기능 정상 작동에 필요한 요소. 실패 시 경고가 표시되지만 커밋은 허용됩니다.

**예시**:
- 트리거 조건 일치성
- Obsidian 개발일지 폴더 존재
- 자동화 스크립트 구현 상태

### 🟢 RECOMMENDED (권장)
최적화 및 개선 사항. 실패해도 경고 없이 통과합니다.

**예시**:
- Documentation 폴더 구조 (`docs/sessions/`, `docs/guides/`)
- Git hooks 폴더 존재

## 사용 방법

### 수동 실행

```bash
# 전체 규칙 검증
python scripts/validate_system_rules.py

# 결과 예시:
# [VALIDATION] System Rules Validation Starting...
# Repository: C:\Users\user\Documents\GitHub\UDO-Development-Platform
# Rules Location: C:\Users\user\Documents\GitHub\UDO-Development-Platform\.claude
#
# [SUMMARY] Validation Summary
# [!] CRITICAL: 2/2 passed (0 failed)
# [*] IMPORTANT: 6/7 passed (1 failed)
# [+] RECOMMENDED: 5/5 passed (0 failed)
#
# [RESULT] Overall Pass Rate: 13/14 (92.9%)
```

### 자동 실행 (Pre-commit Hook)

매 커밋 전에 자동으로 실행됩니다.

```bash
# Git commit 시 자동 실행
git commit -m "feat: 새 기능 추가"

# Pre-commit hook에서 검증 실행
# CRITICAL 실패 시 커밋 차단
# IMPORTANT/RECOMMENDED 실패 시 경고만 표시
```

**우회 방법** (권장하지 않음):
```bash
git commit --no-verify -m "긴급 수정"
```

## 검증 대상

### 현재 검증 중인 규칙 파일 (5/19)

1. **OBSIDIAN_SYNC_RULES.md**
   - Git hook 존재 (`post-commit`)
   - Hook에 Obsidian 동기화 코드 포함
   - 트리거 조건 구현 (3+ files OR feat:/fix: message)
   - 필수 스크립트 존재 (`obsidian_auto_sync.py`, `obsidian_append.py`)

2. **RULES.md**
   - Pre-commit hook 존재
   - Documentation 폴더 구조 (`docs/sessions/`, `docs/guides/`, `docs/features/`, `docs/architecture/`)

3. **INNOVATION_SAFETY_PRINCIPLES.md**
   - 자동화 스크립트 존재 (`obsidian_auto_sync.py`, `validate_system_rules.py`)
   - Git hooks 폴더 존재

4. **OBSIDIAN_AUTO_SEARCH.md**
   - 3-Tier Error Resolution 스크립트 존재 (`unified_error_resolver.py`)
   - Tier 1/2/3 구조 구현 확인
   - Obsidian 개발일지 폴더 존재

5. **기타 Git Workflow**
   - Feature branch 사용
   - Commit message conventions

### 향후 확장 가능 규칙 (14/19)

- MODE_* 파일: 행동 가이드라인 (자동 검증 어려움)
- MCP_* 파일: MCP 서버 사용 가이드 (자동 검증 어려움)
- FLAGS.md: 실행 플래그 (자동 검증 어려움)
- PRINCIPLES.md: 설계 원칙 (자동 검증 어려움)

## 검증 결과 해석

### Exit Code

- `0`: 검증 통과 (CRITICAL 모두 통과)
- `1`: CRITICAL 실패 (커밋 차단)

### 통과율 계산

```
통과율 = (통과한 항목 수 / 전체 항목 수) × 100%
```

**예시**:
- 13/14 통과 = 92.9%
- 8/9 통과 = 88.9%

### 실패 항목 확인

실패한 항목은 `[DETAILS] Detailed Results` 섹션에 표시됩니다.

```
[*] [IMPORTANT] 트리거 조건 구현
   Rule: OBSIDIAN_SYNC_RULES.md / 트리거 조건
   [WARN] 1/2 트리거 조건만 구현됨
   Fix: Manual: Add missing trigger conditions to hook
```

## 문제 해결

### CRITICAL 실패: obsidian_auto_sync.py 없음

**증상**:
```
[!] [CRITICAL] obsidian_auto_sync.py 존재
   [FAIL] AI v2.0 자동 동기화 스크립트 없음: scripts/obsidian_auto_sync.py
   Fix: Implement scripts/obsidian_auto_sync.py
```

**해결**:
1. `scripts/obsidian_auto_sync.py` 구현
2. UTF-8 인코딩 사용
3. 트리거 조건 구현 (3+ files OR feat:/fix: message)
4. AI 인사이트 자동 생성 기능 포함

### CRITICAL 실패: 3-Tier 구조 미구현

**증상**:
```
[!] [CRITICAL] 3-Tier 구조 구현
   [FAIL] 일부 Tier 누락 (T1:True, T2:False, T3:True)
   Fix: Complete 3-Tier implementation
```

**해결**:
1. `scripts/unified_error_resolver.py` 구현
2. Tier 1 (Obsidian): 과거 솔루션 검색
3. Tier 2 (Context7): 공식 문서 검색
4. Tier 3 (User): 사용자 입력

### IMPORTANT 실패: 트리거 조건 부분 구현

**증상**:
```
[*] [IMPORTANT] 트리거 조건 구현
   [WARN] 1/2 트리거 조건만 구현됨
   Fix: Manual: Add missing trigger conditions to hook
```

**해결**:
1. `.git/hooks/post-commit` 확인
2. 누락된 패턴 추가 (analyze, analysis 등)
3. Hook 재설치

## 베스트 프랙티스

### 1. 규칙 추가 시

새 규칙을 `.claude/` 폴더에 추가한 후:

1. `scripts/validate_system_rules.py`에 검증 메서드 추가
2. 검증 레벨 결정 (CRITICAL/IMPORTANT/RECOMMENDED)
3. Fix command 제공
4. 테스트 실행

### 2. 구현 전 검증

새 기능 구현 전:

1. 관련 규칙 파일 확인
2. 검증 스크립트가 해당 규칙을 검증하는지 확인
3. 구현 후 검증 통과 확인

### 3. 정기 검증

```bash
# 매주 금요일 검증 실행
python scripts/validate_system_rules.py

# 통과율 추적
# Week 1: 88.9% (8/9)
# Week 2: 92.9% (13/14)
# Week 3: 95.0% (19/20) <- 목표
```

## 통계

### 검증 커버리지 진행 상황

| 날짜 | 규칙 파일 | 검증 항목 | 통과율 | 커밋 |
|------|----------|---------|-------|------|
| 2025-12-13 | 2/19 (10.5%) | 9개 | 88.9% | 초기 구현 |
| 2025-12-14 | 5/19 (26.3%) | 14개 | 92.9% | P2 확대 |

### 목표

- **Week 0 완료**: 5/19 규칙 파일 (26.3%)
- **Week 1 목표**: 8/19 규칙 파일 (42.1%)
- **Week 2 목표**: 12/19 규칙 파일 (63.2%)
- **최종 목표**: 핵심 규칙 100% 커버리지

## FAQ

### Q: 모든 19개 규칙 파일을 검증해야 하나요?

A: 아니요. MODE_*, MCP_*, FLAGS.md 등은 행동 가이드라인이므로 자동 검증이 어렵습니다. 핵심 규칙(OBSIDIAN_SYNC, INNOVATION_SAFETY, ERROR_RESOLUTION, RULES)만 검증해도 충분합니다.

### Q: CRITICAL 실패가 발생했는데 긴급 커밋이 필요합니다.

A: `git commit --no-verify`로 우회할 수 있지만, 반드시 다음 커밋에서 수정하세요.

### Q: 검증 스크립트를 수정했는데 테스트는 어떻게 하나요?

A: `python scripts/validate_system_rules.py`를 실행하여 즉시 확인할 수 있습니다.

### Q: 새 규칙을 추가했는데 검증이 안 됩니다.

A: `validate_system_rules.py`의 `validate_all()` 메서드에 새 검증 메서드를 추가해야 합니다.

## 관련 문서

- [OBSIDIAN_SYNC_RULES.md](../../.claude/OBSIDIAN_SYNC_RULES.md) - Obsidian 동기화 규칙
- [INNOVATION_SAFETY_PRINCIPLES.md](../../.claude/INNOVATION_SAFETY_PRINCIPLES.md) - 혁신 안전 원칙
- [OBSIDIAN_AUTO_SEARCH.md](../../.claude/OBSIDIAN_AUTO_SEARCH.md) - 3-Tier Error Resolution
- [scripts/validate_system_rules.py](../../scripts/validate_system_rules.py) - 검증 스크립트

## 지원

문제가 발생하면:
1. 검증 로그 확인
2. Fix command 실행
3. 여전히 실패 시 해당 규칙 파일 확인

---

**Last Updated**: 2025-12-14
**Version**: 2.0
**Coverage**: 5/19 규칙 파일 (26.3%)
