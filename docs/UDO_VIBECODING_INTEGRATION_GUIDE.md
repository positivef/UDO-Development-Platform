# UDO Platform + VibeCoding 통합 실용 가이드

**작성일**: 2026-01-18
**목적**: UDO Development Platform과 VibeCoding 스킬을 효과적으로 결합하여 바이브코딩 개발 워크플로우 최적화

---

## 1. 핵심 요약: 어떻게 함께 쓰면 좋을까?

### 1.1 역할 분담

| 시스템 | 역할 | 언제 사용 |
|--------|------|----------|
| **UDO Platform** | 모니터링 + 실시간 대시보드 | 개발 중 상태 확인, 품질 추적 |
| **VibeCoding 스킬** | 워크플로우 자동화 + 지식 축적 | 프로젝트 시작, 에러 해결, 문서화 |
| **Obsidian** | 지식 저장소 + 3-Tier 에러 해결 | 모든 세션에서 백그라운드로 |

### 1.2 시너지 포인트

```
VibeCoding 스킬 (워크플로우)
    ↓ 자동 동기화
Obsidian (지식 저장소)
    ↓ 3-Tier Error Resolution
UDO Platform (모니터링)
    ↓ 실시간 피드백
개발자 (Flow 유지)
```

---

## 2. 일일 워크플로우 (Daily Workflow)

### 2.1 아침: 세션 시작

```bash
# Step 1: UDO 세션 시작 체크
python scripts/session_start.py

# Step 2: VibeCoding으로 컨텍스트 로드
/vibe "UDO-Development-Platform" status

# Step 3: 어제 작업 확인 (Obsidian 자동 참조)
# → 개발일지/YYYY-MM-DD/ 폴더 자동 검색
```

**결과**:
- 예정된 작업 확인 (session_start.py)
- 프로젝트 상태 파악 (VibeCoding status)
- 어제 맥락 복원 (Obsidian 3-Tier)

### 2.2 작업 중: Flow 유지

```bash
# 에러 발생 시 → 자동 3-Tier 해결
# Tier 1 (Obsidian): <10ms, 70% 해결
# Tier 2 (Context7): <500ms, 25% 해결
# Tier 3 (User): 5%만 개입 필요

# 큰 기능 개발 시
/vibe "기능명" mvp --model sonnet

# 아키텍처 결정 시 (Opus 필요)
/vibe "기능명" insight --model opus
```

**UDO 대시보드 활용**:
- `http://localhost:3000/kanban` → 작업 진행 상황
- `http://localhost:3000/uncertainty` → 불확실성 모니터링
- `http://localhost:3000/confidence` → 신뢰도 추적

### 2.3 저녁: 세션 종료

```bash
# Git 커밋 시 자동 동기화 (post-commit hook)
git add . && git commit -m "feat: 기능 구현"

# → Obsidian에 개발일지 자동 생성
# → 배운 점, 시행착오 AI 자동 추출
```

---

## 3. VibeCoding 스킬 활용 가이드

### 3.1 사용 가능한 스킬 목록

| 스킬명 | 트리거 | 용도 |
|--------|--------|------|
| `/vibe` | 명시적 실행 | 프로젝트 전체 워크플로우 |
| `/vibeselector` | 시스템 선택 필요 시 | 최적 VibeCoding 시스템 자동 선택 |
| `/vc` (Constitution) | 체계적 개발 필요 시 | 13조항 기반 엄격한 개발 |
| `/vibecoding` | 자연어 트리거 | Enhanced 자동화 (95%) |
| `/vibe-coding-fusion` | 복합 프로젝트 | Constitution + Enhanced 결합 |

### 3.2 스킬 선택 의사결정 트리

```
프로젝트 시작?
├─ 새 프로젝트 → /vibeselector (자동 선택)
├─ 기존 프로젝트 계속 → /vibe "프로젝트" status
└─ 아키텍처 결정 → /vibe "프로젝트" insight --model opus

개발 단계?
├─ Ideation → /vibe insight (GI Formula)
├─ Design → /vibe design (C-K Theory, 3개 대안)
├─ MVP → /vibe mvp --model sonnet
├─ Implementation → /vibe implement
└─ Testing → /vibe test --model haiku

에러 발생?
├─ 자동 해결 대기 (3-Tier)
├─ 해결 안됨 → Obsidian에 수동 저장
└─ 다음부터 자동 해결 (<10ms)
```

### 3.3 모델 선택 가이드 (비용 최적화)

```yaml
# 20/60/20 황금률
Opus (20%): $15/MTok
  - 아키텍처 설계
  - 복잡한 문제 분석
  - 전략적 결정

Sonnet (60%): $3/MTok
  - 코드 생성
  - 일반 구현
  - 리팩토링

Haiku (20%): $0.25/MTok
  - 단순 작업
  - 테스트 실행
  - 문서화

# ROI 계산
점수 = (복잡도×5) + (비즈니스영향×3) + (재사용성×2)
점수 > 7 → Opus
점수 5-7 → Sonnet
점수 < 5 → Haiku
```

---

## 4. UDO Platform 기능별 활용

### 4.1 Kanban 보드 (`/kanban`)

**VibeCoding과 연동**:
```bash
# 작업 생성 시 자동 연동
/vibe "기능명" mvp
# → Kanban에 Task 자동 생성 (Phase: MVP)
# → 불확실성 자동 계산

# 작업 완료 시
# → Archive로 자동 이동
# → Obsidian에 ROI 기록
```

**대시보드 확인 포인트**:
- Phase별 작업 분포
- 블로킹된 작업 확인
- AI 제안 작업 검토

### 4.2 Uncertainty Map (`/uncertainty`)

**VibeCoding과 연동**:
```bash
# 높은 불확실성 작업 발견 시
# → /vibe insight로 분석
# → TRIZ 원칙으로 모순 해결

# 예측 상태 확인
🟢 DETERMINISTIC (<10%): 바로 진행
🔵 PROBABILISTIC (10-30%): 주의하며 진행
🟠 QUANTUM (30-60%): 분석 후 진행
🔴 CHAOTIC (60-90%): Opus로 분석 필수
⚫ VOID (>90%): 사용자 개입 필요
```

### 4.3 Confidence Dashboard (`/confidence`)

**Phase별 신뢰도 기준**:
- Ideation: 60% 이상
- Design: 65% 이상
- MVP: 65% 이상
- Implementation: 70% 이상
- Testing: 70% 이상

**활용 방법**:
```bash
# 신뢰도 낮을 때
/vibe "기능명" insight --model opus
# → 근본 원인 분석
# → 대안 설계 (C-K Theory)
```

### 4.4 Governance Dashboard (`/governance`)

**VibeCoding Constitution과 연동**:
```bash
# /vc 사용 시 자동 연동
/vc "프로젝트명"
# → 13조항 규칙 적용
# → Governance Dashboard에 준수 상태 표시

# 위반 시 자동 경고
# → Pre-commit hook이 차단
# → 해결 방법 제시
```

---

## 5. 실전 시나리오별 가이드

### 5.1 새 기능 개발

```bash
# 1. 시스템 선택
/vibeselector "새 기능: 사용자 인증 시스템"
# → VibeCoding Enhanced 추천 (복잡도 중간)

# 2. 인사이트 생성 (Opus)
/vibe "auth-system" insight --model opus
# → GI Formula로 5단계 분석
# → 핵심 고려사항 도출

# 3. 설계 (Sonnet)
/vibe "auth-system" design
# → C-K Theory로 3개 대안 생성
# → RICE 점수로 최적안 선택

# 4. 구현 (Sonnet)
/vibe "auth-system" mvp
# → 코드 생성
# → UDO Kanban에 자동 등록

# 5. 테스트 (Haiku)
/vibe "auth-system" test --model haiku
# → 테스트 코드 생성
# → 커버리지 확인

# 6. 완료 시
git commit -m "feat: auth system"
# → Obsidian에 자동 기록
# → UDO Archive에 ROI 저장
```

### 5.2 버그 수정

```bash
# 1. 에러 발생 시 자동 해결 대기
# Tier 1 (Obsidian): 과거 해결책 검색 (<10ms)
# Tier 2 (Context7): 공식 문서 검색 (<500ms)

# 2. 자동 해결 안됨 → 수동 분석
/vibe "bug-fix" debug
# → 근본 원인 분석
# → 해결책 제시

# 3. 해결 후 저장
# → Obsidian에 자동 저장
# → 다음부터 Tier 1에서 즉시 해결
```

### 5.3 리팩토링

```bash
# 1. 분석
/sc:analyze "리팩토링 대상 코드"
# → 코드 품질 분석
# → 개선 포인트 도출

# 2. 계획
/vibe "refactoring" design
# → 리팩토링 전략 수립
# → 위험 분석 (8-Risk Check)

# 3. 실행
/vibe "refactoring" implement
# → 단계별 리팩토링
# → 테스트 유지

# 4. 검증
/sc:test
# → 회귀 테스트
# → 성능 비교
```

---

## 6. Obsidian 통합 최적화

### 6.1 자동 동기화 설정

```bash
# Git post-commit hook (이미 설치됨)
# 커밋 시 자동으로:
# 1. 개발일지 생성 (개발일지/YYYY-MM-DD/Topic.md)
# 2. 배운 점 AI 추출
# 3. 시행착오 기록
# 4. 다음 단계 제안
```

### 6.2 3-Tier Error Resolution 활용

```python
# 자동 실행됨 (OBSIDIAN_AUTO_SEARCH.md 규칙)

# Tier 1: Obsidian (70% 해결, <10ms)
# - 과거 동일 에러 검색
# - 즉시 해결책 적용

# Tier 2: Context7 (25% 해결, <500ms)
# - 공식 문서 검색
# - 신뢰도 기반 적용 (HIGH: 자동, MEDIUM: 확인)

# Tier 3: User (5%)
# - 사용자 개입
# - 해결 후 Obsidian에 저장 (다음부터 Tier 1)
```

### 6.3 지식 재사용 패턴

```bash
# 과거 솔루션 검색
mcp__obsidian__obsidian_simple_search "에러 키워드"

# 결과 활용
# → Quick Fix (30초)
# → Root Cause (5분)
# → Permanent Fix (30분)
# → Test & Verify
# → Rollback Plan
```

---

## 7. 설정 체크리스트

### 7.1 필수 설정

```bash
# 1. Obsidian Vault 경로
setx OBSIDIAN_VAULT_PATH "C:\Users\user\Documents\Obsidian Vault"

# 2. VibeCoding 스킬 확인
ls C:\Users\user\.claude\skills\
# vibe-coding-enhanced/ 폴더 존재 확인

# 3. MCP 서버 확인
# - obsidian (필수)
# - context7 (권장)
# - sequential (권장)

# 4. Pre-commit hooks 설치
pre-commit install
pre-commit install --hook-type pre-push

# 5. Post-commit hook 확인
ls .git/hooks/post-commit
```

### 7.2 권장 설정

```yaml
# .claude/settings.local.json
{
  "defaultModel": "sonnet",  # 기본 Sonnet (비용 효율)
  "obsidian": {
    "autoSync": true,
    "vault": "C:/Users/user/Documents/Obsidian Vault"
  },
  "vibecoding": {
    "hybridMode": true,  # 20/60/20 황금률
    "autoErrorResolution": true  # 3-Tier 자동 해결
  }
}
```

---

## 8. 문제 해결 (Troubleshooting)

### 8.1 스킬이 작동하지 않을 때

```bash
# 1. Claude Code 버전 확인
/version  # v3.0.0 이상 필요

# 2. 스킬 디렉토리 확인
ls C:\Users\user\.claude\skills\

# 3. Claude Code 재시작
# 완전 종료 후 재시작

# 4. 슬래시 명령어 확인
/  # 사용 가능한 명령어 목록
```

### 8.2 Obsidian 동기화 안될 때

```bash
# 1. MCP 서버 확인
# Obsidian MCP가 실행 중인지 확인

# 2. Vault 경로 확인
echo %OBSIDIAN_VAULT_PATH%

# 3. 권한 확인
# Vault 폴더 쓰기 권한

# 4. 수동 동기화
python scripts/obsidian_auto_sync.py --manual
```

### 8.3 UDO 대시보드 연결 안될 때

```bash
# 1. 백엔드 확인
curl http://localhost:8000/health

# 2. 프론트엔드 확인
curl http://localhost:3000

# 3. 서버 재시작
start-backend.bat  # 백엔드
cd web-dashboard && npm run dev  # 프론트엔드
```

---

## 9. 요약: 최적 워크플로우

```
┌─────────────────────────────────────────────────────────┐
│                    Daily Workflow                        │
├─────────────────────────────────────────────────────────┤
│ 아침                                                     │
│ ├─ python scripts/session_start.py (예정 작업 확인)      │
│ ├─ /vibe "프로젝트" status (상태 파악)                   │
│ └─ UDO Dashboard 확인 (Kanban, Uncertainty)             │
├─────────────────────────────────────────────────────────┤
│ 작업 중                                                  │
│ ├─ /vibe "기능" [단계] (워크플로우 진행)                 │
│ ├─ 에러 → 자동 3-Tier 해결 (95% 자동화)                 │
│ ├─ 아키텍처 → /vibe insight --model opus                │
│ └─ UDO Dashboard로 실시간 모니터링                      │
├─────────────────────────────────────────────────────────┤
│ 저녁                                                     │
│ ├─ git commit (자동 Obsidian 동기화)                    │
│ └─ 개발일지 자동 생성 (배운 점, 시행착오, 다음 단계)     │
└─────────────────────────────────────────────────────────┘

비용 최적화: 20% Opus / 60% Sonnet / 20% Haiku = 70% 비용 절감
자동화율: 95% (3-Tier Error Resolution + VibeCoding)
지식 축적: 100% (Obsidian 자동 동기화)
```

---

## 10. 참고 문서

- [[VibeCoding-FAQ]] - VibeCoding 자주 묻는 질문
- [[OBSIDIAN_SYNC_RULES]] - Obsidian 동기화 규칙
- [[OBSIDIAN_AUTO_SEARCH]] - 3-Tier Error Resolution
- [[CLAUDE.md]] - 프로젝트 컨텍스트
- [[AGENTS.md]] - 코딩 스타일 가이드

---

*UDO Development Platform + VibeCoding Integration Guide v1.0*
*Last Updated: 2026-01-18*
