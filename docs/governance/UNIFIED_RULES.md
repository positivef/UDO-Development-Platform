# UDO 개발 규칙 통합 문서 (Unified Rules)

> **버전**: 1.0.0  
> **최종 수정**: 2025-12-23  
> **관련 설정 파일**: mypy.ini, eslint.config.mjs, .pre-commit-config.yaml

---

## 🎯 문서 목적

이 문서는 UDO 플랫폼 개발 및 UDO로 생성된 모든 프로젝트에 적용되는 **개발 규칙의 단일 참조점**입니다.

### 3-Layer 적용 구조

```
Layer 1: UDO 플랫폼 자체 개발에 적용
Layer 2: UDO 플랫폼의 기능으로 내장
Layer 3: UDO로 생성한 모든 프로젝트에 자동 적용
```

---

## 📋 Python 코딩 규칙

### 1. 언어 버전
- **Python 3.13+** 필수
- Type hints 권장 (점진적 적용)

### 2. 포맷팅 (Black)
```yaml
도구: Black
설정:
  line-length: 127
  target-version: py313
  
명령:
  black backend src scripts tests
```

### 3. 린트 (Flake8)
```yaml
도구: Flake8
설정:
  max-line-length: 127
  max-complexity: 10
  select: E9,F63,F7,F82  # 커밋 시 (빠른 검사)
  
명령:
  flake8 backend src --show-source
```

### 4. 타입 체킹 (mypy)
```yaml
도구: mypy
설정: (mypy.ini)
  python_version: 3.13
  disallow_untyped_defs: false  # 점진적 적용
  warn_return_any: false
  warn_unused_ignores: true
  warn_redundant_casts: true
  show_error_context: true
  show_column_numbers: true
  
명령:
  mypy src
```

### 5. 네이밍 규칙
| 대상 | 규칙 | 예시 |
|------|------|------|
| 클래스 | PascalCase | `UncertaintyMapV3` |
| 함수/변수 | snake_case | `analyze_context()` |
| 상수 | SCREAMING_SNAKE | `DEFAULT_STORAGE_DIR` |
| 모듈 | snake_case | `uncertainty_map_v3.py` |

### 6. Docstring
```python
def function_name(param: str) -> dict:
    """
    함수 설명 (한 줄)
    
    Args:
        param: 파라미터 설명
        
    Returns:
        반환값 설명
        
    Raises:
        ValueError: 예외 상황 설명
    """
```

---

## 📋 TypeScript/React 코딩 규칙

### 1. 언어 버전
- **TypeScript 5.x+**
- **React 19.x+**
- **Next.js 16.x+**

### 2. 린트 (ESLint)
```yaml
도구: ESLint (v9)
설정: (eslint.config.mjs)
  extends:
    - eslint-config-next/core-web-vitals
    - eslint-config-next/typescript
  
명령:
  npm run lint
```

### 3. 타입 체킹 (TypeScript)
```yaml
설정: (tsconfig.json)
  strict: true
  target: ES2017
  module: esnext
  moduleResolution: bundler
  jsx: react-jsx
  
명령:
  npx tsc --noEmit
```

### 4. 네이밍 규칙
| 대상 | 규칙 | 예시 |
|------|------|------|
| 컴포넌트 | PascalCase | `UncertaintyMap.tsx` |
| 훅 | camelCase + use | `useUncertainty.ts` |
| 유틸리티 | camelCase | `formatDate.ts` |
| 타입/인터페이스 | PascalCase | `UncertaintyState` |

---

## 📋 Git 규칙

### 1. 브랜치 전략
```
main      ← 프로덕션 (보호됨)
develop   ← 개발 통합
feature/* ← 기능 개발
hotfix/*  ← 긴급 수정
```

### 2. 커밋 메시지 형식
```
<scope>: <concise outcome>

예시:
  feat: 불확실성 예측 API 추가
  fix: Kanban 서비스 DI 문제 해결
  docs: UNIFIED_RULES.md 작성
  refactor: uncertainty_map_v3 모듈화
  test: E2E 테스트 18개 추가
```

### 3. PR 가이드라인
- 동기(motivation) 설명
- 해결책 요약
- 관련 이슈 링크
- 테스트 결과 첨부

---

## 📋 테스트 규칙

### 1. 백엔드 (pytest)
```yaml
위치: backend/tests/
패턴: test_*.py
명령: cd backend && pytest tests/ -v

커버리지 목표: 80%+
현재 상태: 496/496 (100%)
```

### 2. 프론트엔드 (Playwright)
```yaml
위치: web-dashboard/tests/
명령:
  npm run test:e2e
  npm run test:e2e:ui  # UI 모드

현재 상태: 18/18 (100%)
```

---

## 📋 문서화 규칙

### 1. 3계층 문서 시스템
| 계층 | 위치 | 내용 |
|------|------|------|
| Tier 1 | `docs/` | 사람이 읽는 문서 |
| Tier 2 | `claudedocs/` | AI 생성 문서 |
| Tier 3 | Obsidian | 개발 로그 동기화 |

### 2. 필수 문서
- `CLAUDE.md` - 프로젝트 컨텍스트
- `AGENTS.md` - 코딩/Git 규칙 요약
- `README.md` - 프로젝트 소개

---

## 📋 자동 검증

### Pre-commit 훅 (커밋 시)
```yaml
실행 시간: 1-3초
검사 항목:
  - Black (Python 포맷팅)
  - Flake8 (구문 오류)
  - 공백/EOF 정리
  - YAML/JSON 검증
```

### Pre-push 훅 (푸시 시)
```yaml
실행 시간: 10-30초
검사 항목:
  - 시스템 규칙 검증 (validate_system_rules.py)
  - Full Flake8 (복잡도 포함)
```

### CI/CD (GitHub Actions)
```yaml
워크플로우: 10개
  - backend-ci.yml
  - frontend-ci.yml
  - validate-rules.yml
  - nightly-tests.yml
  - ...
```

---

## 📋 불확실성 관리

### 불확실성 지도 (Uncertainty Map v3)
```yaml
파일: src/uncertainty_map_v3.py
5차원 벡터:
  - Technical (기술적)
  - Market (시장)
  - Resource (리소스)
  - Timeline (일정)
  - Quality (품질)

상태 분류:
  - DETERMINISTIC: <10% (안전)
  - PROBABILISTIC: 10-30% (양호)
  - QUANTUM: 30-60% (주의)
  - CHAOTIC: 60-90% (위험)
  - VOID: >90% (미지)
```

### MCP 도구
```yaml
서버: mcp-server/udo-server.py
도구:
  - get_uncertainty_state(phase)
  - predict_risk_impact(change, phase)
  - log_work_session(task_id, duration)
```

---

## 🔗 관련 문서

| 문서 | 경로 |
|------|------|
| CLAUDE.md | 루트 |
| AGENTS.md | 루트 |
| .pre-commit-config.yaml | 루트 |
| mypy.ini | 루트 |
| eslint.config.mjs | web-dashboard/ |
| tsconfig.json | web-dashboard/ |
| pytest.ini | backend/ |

---

**이 문서는 모든 개발 규칙의 단일 참조점입니다.**
