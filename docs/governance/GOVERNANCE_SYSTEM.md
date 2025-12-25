# UDO 거버넌스 시스템 - 완성 문서

> **버전**: 1.0.0  
> **최종 수정**: 2025-12-23

---

## 🎯 개요

UDO 거버넌스 시스템은 개발 규칙을 UDO 플랫폼에 내장하여 모든 프로젝트에 자동으로 적용합니다.

### 3-Layer 아키텍처

```
Layer 1: UDO 플랫폼 자체 개발에 규칙 적용
Layer 2: UDO 플랫폼의 기능으로 규칙 시스템 내장
Layer 3: UDO로 생성한 모든 프로젝트에 자동 적용
```

---

## 📦 주요 구성요소

### 문서

| 파일 | 설명 |
|------|------|
| `docs/governance/UNIFIED_RULES.md` | 통합 개발 규칙 문서 |
| `docs/governance/QUICK_START.md` | 빠른 시작 가이드 |
| `.governance.yaml` | 프로젝트 거버넌스 설정 |

### 템플릿

| 템플릿 | 용도 |
|--------|------|
| `templates/minimal/` | 개인/실험용 (최소 규칙) |
| `templates/standard/` | 팀 프로젝트용 (표준 규칙) |
| `templates/full/` | 기업용 (전체 규칙 + 보안) |

### CLI 도구

| 스크립트 | 설명 |
|----------|------|
| `scripts/create_project.py` | 프로젝트 생성 CLI |
| `scripts/governance_auto_update.py` | 거버넌스 자동 업데이트 |
| `scripts/validate_system_rules.py` | 규칙 검증 |

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/governance/rules` | GET | 규칙 목록 |
| `/api/governance/validate` | POST | 규칙 검증 |
| `/api/governance/templates` | GET | 템플릿 목록 |
| `/api/governance/apply` | POST | 템플릿 적용 |
| `/api/governance/config` | GET | 설정 조회 |

### MCP 도구

| 도구 | 설명 |
|------|------|
| `validate_project_rules()` | 프로젝트 규칙 검증 |
| `get_governance_templates()` | 템플릿 목록 조회 |
| `apply_governance_template()` | 템플릿 적용 |

### UI 컴포넌트

| 컴포넌트 | 설명 |
|----------|------|
| `GovernanceDashboard` | 거버넌스 대시보드 |
| `ComplianceReport` | 규칙 준수 리포트 |

---

## 🚀 사용법

### 1. 새 프로젝트 생성

```bash
# 기본 (standard 템플릿)
python scripts/create_project.py --name my-app

# 템플릿 지정
python scripts/create_project.py --name my-app --template minimal

# 인터랙티브 모드
python scripts/create_project.py --guided
```

### 2. 규칙 검증

```bash
# 시스템 규칙 검증
python scripts/validate_system_rules.py

# 거버넌스 상태 확인
python scripts/governance_auto_update.py --check

# 규칙 준수 리포트
python scripts/governance_auto_update.py --report
```

### 3. Pre-commit 훅

```bash
# 설치
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push

# 수동 실행
pre-commit run --all-files

# 스킵 (긴급 시)
git commit --no-verify
```

---

## 📊 검증 결과

### 시스템 규칙

```
Pass Rate: 14/14 (100%)
```

### 거버넌스 상태

```
Compliance: 5/5 (100%)
  ✅ governance_config
  ✅ pre_commit
  ✅ claude_md
  ✅ templates
  ✅ mcp_server
```

### 불확실성 지도

```
State: QUANTUM
Magnitude: 50.1%
```

---

## 🔧 설정 옵션

### .governance.yaml

```yaml
version: "1.0.0"

project:
  name: "my-project"
  size: "standard"  # minimal, standard, enterprise

rules:
  strict_mode: true
  skip_rules: []    # 스킵할 규칙

languages:
  python:
    enabled: true
    max_line_length: 127
  typescript:
    enabled: true
    strict_mode: true

uncertainty:
  enabled: true
  alert_threshold: 50
```

---

## 📁 파일 구조

```
.governance.yaml                  # 프로젝트 설정
.pre-commit-config.yaml           # Pre-commit 훅
templates/
  minimal/.governance.yaml        # 최소 템플릿
  standard/.governance.yaml       # 표준 템플릿
  full/.governance.yaml           # 전체 템플릿
scripts/
  create_project.py               # CLI
  governance_auto_update.py       # 자동 업데이트
  validate_system_rules.py        # 규칙 검증
docs/governance/
  UNIFIED_RULES.md                # 통합 규칙
  QUICK_START.md                  # 빠른 시작
  GOVERNANCE_SYSTEM.md            # 이 문서
backend/app/routers/
  governance.py                   # API
web-dashboard/components/governance/
  governance-dashboard.tsx        # 대시보드 UI
  compliance-report.tsx           # 리포트 UI
mcp-server/
  udo-server.py                   # MCP 도구
```

---

## 🔗 관련 문서

- [UNIFIED_RULES.md](./UNIFIED_RULES.md) - 통합 개발 규칙
- [QUICK_START.md](./QUICK_START.md) - 빠른 시작 가이드
- [CLAUDE.md](../../CLAUDE.md) - 프로젝트 컨텍스트
- [AGENTS.md](../../AGENTS.md) - 코딩 스타일 가이드
