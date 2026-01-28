# UDO Development Platform - 빠른 시작 가이드

5분 안에 UDO 개발 환경을 설정하고 실행합니다.

---

## 🚀 Step 1: 요구사항 확인 (30초)

```batch
:: Windows
cd launcher\install
python check_requirements.py
```

```bash
# Linux/Mac
cd launcher/install
python3 check_requirements.py
```

모든 항목이 ✓ PASS로 표시되어야 합니다.

---

## 🔧 Step 2: 설치 (2-3분)

```batch
:: Windows
launcher\install\install_windows.bat
```

```bash
# Linux/Mac
chmod +x launcher/install/install_unix.sh
./launcher/install/install_unix.sh
```

---

## ▶️ Step 3: 실행 (10초)

### Local 모드 (Docker 없이 - 권장)

```batch
:: Windows
launcher\start\start_local.bat
```

```bash
# Linux/Mac
./launcher/start/start_local.sh
```

### Docker 모드

```batch
launcher\start\start_all.bat
```

---

## ✅ Step 4: 접속 확인

| 서비스 | URL | 설명 |
|--------|-----|------|
| **Dashboard** | http://localhost:3000 | 메인 대시보드 |
| **API Docs** | http://localhost:8000/docs | Swagger API 문서 |
| **API Health** | http://localhost:8000/api/health | 상태 확인 |

---

## 🔍 헬스체크

```batch
python launcher\status\health_check.py
```

---

## ⏹️ 종료

```batch
launcher\stop\stop_all.bat
```

---

## ❓ 문제 해결

### 포트 이미 사용 중
```batch
:: 포트 사용 프로세스 확인
netstat -ano | findstr :8000

:: 프로세스 종료
taskkill /PID <PID> /F
```

### 의존성 오류
```batch
:: Backend 재설치
pip install -r backend\requirements.txt

:: Frontend 재설치
cd web-dashboard && npm install
```

---

**자세한 내용**: [README.md](README.md)
