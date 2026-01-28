# UDO Development Platform - 크로스 머신 런처

다른 컴퓨터에서 UDO Development Platform을 쉽게 설치하고 실행할 수 있는 도구 모음입니다.

---

## 🚀 빠른 시작

### Windows 사용자

```batch
:: 1. 요구사항 확인
cd launcher\install
python check_requirements.py

:: 2. 설치 (최초 1회)
install_windows.bat

:: 3. 실행 (Docker 모드)
cd ..\start
start_all.bat

:: 또는 Local 모드 (Docker 없이)
start_local.bat
```

### Linux/Mac 사용자

```bash
# 1. 요구사항 확인
cd launcher/install
python3 check_requirements.py

# 2. 설치 (최초 1회)
chmod +x install_unix.sh
./install_unix.sh

# 3. 실행 (Docker 모드)
cd ../start
./start_all.sh

# 또는 Local 모드 (Docker 없이)
./start_local.sh
```

---

## 📋 시스템 요구사항

### 공통 요구사항

| 소프트웨어 | 최소 버전 | 다운로드 |
|-----------|----------|----------|
| **Python** | 3.10+ | [python.org](https://python.org) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org) |
| **Git** | 2.30+ | [git-scm.com](https://git-scm.com) |

### 모드별 추가 요구사항

| 모드 | 추가 필요 | 설명 |
|------|----------|------|
| **Docker 모드** | Docker Desktop | 모든 서비스 컨테이너화 |
| **Local 모드** | PostgreSQL 14+ (선택) | SQLite 폴백 가능 |

---

## 🔧 실행 모드 비교

### Mode 1: Docker 모드 (권장)

```batch
launcher\start\start_all.bat
```

- ✅ PostgreSQL, Redis 자동 설치
- ✅ 모니터링 도구 포함 (Grafana, Prometheus)
- ✅ 팀 개발에 적합
- ⚠️ Docker Desktop 필요 (약 2GB)

### Mode 2: Local 모드 (Docker 없이)

```batch
launcher\start\start_local.bat
```

- ✅ Docker 불필요
- ✅ 가볍고 빠른 시작 (30초 미만)
- ✅ SQLite 폴백으로 즉시 시작
- ⚠️ 일부 고급 기능 제한 (Redis 캐시 없음)

---

## 📂 폴더 구조

```
launcher/
├── README.md              ← 지금 보고 있는 문서
├── QUICK_START.md         ← 5분 빠른 시작 가이드
│
├── install/               ← 설치 스크립트
│   ├── install_windows.bat
│   ├── install_unix.sh
│   └── check_requirements.py
│
├── start/                 ← 시작 스크립트
│   ├── start_all.bat/sh      (Docker 모드)
│   └── start_local.bat/sh    (Local 모드)
│
├── stop/                  ← 중지 스크립트
│   └── stop_all.bat/sh
│
├── config/                ← 설정 파일
│   └── local.env.example
│
└── status/                ← 상태 확인
    └── health_check.py
```

---

## 🔍 트러블슈팅

### Python 버전 오류
```
Python 3.10+ 이상이 설치되어 있는지 확인하세요:
python --version
```

### 포트 충돌 (8000, 3000)
```batch
:: Windows - 포트 사용 프로세스 확인
netstat -ano | findstr :8000

:: 해당 PID 종료
taskkill /PID <PID> /F
```

### Node.js 의존성 오류
```bash
cd web-dashboard
rm -rf node_modules
npm install
```

---

## 📞 지원

- **문서**: [docs/](../docs/) 폴더 참조
- **이슈**: GitHub Issues에 등록
- **Quick Reference**: [QUICK_START.md](QUICK_START.md)

---

**버전**: 1.0.0
**최종 업데이트**: 2026-01-25

---

## 🔧 기존 프로젝트 규칙 자동 반영

설치 스크립트가 다음 기존 규칙들을 **자동으로 설정**합니다:

### 1. Git Pre-commit Hooks (`.pre-commit-config.yaml`)
```yaml
자동 설치:
  - Black 포맷터 (Python)           # 코드 자동 포맷팅
  - Flake8 린터                     # 코드 품질 검사
  - 한글 텍스트 보호 체크             # 한글 깨짐 방지
  - 시스템 규칙 검증 (pre-push)      # 푸시 전 검증
  - 문서 일관성 검사                  # 문서 품질 보장
```

### 2. 4-Tier Governance System (`.governance.yaml`)
```yaml
자동 확인:
  - Tier 1: Experiment (실험/학습)
  - Tier 2: Development (정식 개발)
  - Tier 3: Compliance (규정 준수)
  - Tier 4: Enterprise (기업용)

확인 명령: udo.bat status
```

### 3. Obsidian 자동 동기화
```yaml
post-commit hook:
  - Git 커밋 → 개발일지 자동 생성
  - 경로: scripts/obsidian_auto_sync.py
  - 볼트: OBSIDIAN_VAULT_PATH 환경변수로 설정
```

### 4. 세션 시작 프로토콜 (`CLAUDE.md`)
```bash
# 새 세션 시작 시 실행 (예약된 작업 확인)
python scripts/session_start.py
```

### 5. Constitutional Guard
```yaml
17가지 AI 거버넌스 원칙:
  - P1: Design Review First (3+ 파일 변경 시 설계 문서 필요)
  - 자동 검증: 커밋 시 규칙 위반 차단
```

---

## 📋 CI/CD 워크플로우 (자동 실행)

GitHub Actions가 다음을 자동 실행합니다:

| 워크플로우 | 트리거 | 내용 |
|-----------|--------|------|
| `pr-tests.yml` | Pull Request | Backend + E2E 테스트 |
| `frontend-ci.yml` | PR to main | ESLint + TypeScript 검사 |
| `nightly-tests.yml` | 매일 2AM | 3-브라우저 회귀 테스트 |
| `validate-rules.yml` | Push | 시스템 규칙 검증 |
| `uncertainty-monitor.yml` | 스케줄 | 불확실성 모니터링 |
