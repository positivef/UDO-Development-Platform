# 동적 포트 할당 가이드

## 개요
UDO 플랫폼은 백엔드 서버의 포트 충돌을 방지하기 위해 동적 포트 할당 시스템을 사용합니다.

## 작동 방식

### 1. 포트 우선순위
1. **환경 변수** (`API_PORT` 또는 `BACKEND_PORT`)
2. **기본 포트** (8001)
3. **자동 탐색** (8001~8010 범위에서 사용 가능한 포트)

### 2. 구성 요소

#### `backend/app/utils/port_finder.py`
- 사용 가능한 포트를 자동으로 찾는 Python 유틸리티
- 환경 변수 확인 → 기본 포트 시도 → 범위 내 탐색

#### `start-backend.bat`
- 백엔드 서버를 자동으로 시작하는 Windows 배치 스크립트
- `port_finder.py`를 사용하여 포트를 찾음
- `web-dashboard/.env.local`을 자동으로 업데이트

#### `.env.example`
- 환경 변수 템플릿 (기본 포트: 8001)

#### `web-dashboard/.env.local`
- 프론트엔드 API URL 설정
- `start-backend.bat`에 의해 자동 업데이트됨

## 사용 방법

### 자동 시작 (권장)
```bash
start-backend.bat
```
1. 가상 환경 활성화
2. 사용 가능한 포트 찾기
3. `.env.local` 업데이트
4. uvicorn 서버 시작

### 수동 포트 지정
```bash
# 환경 변수로 지정
set API_PORT=8001
python -m uvicorn backend.main:app --reload

# 또는 .env 파일 생성
echo API_PORT=8001 > backend/.env
python -m uvicorn backend.main:app --reload

# 또는 명령줄 인자
python -m uvicorn backend.main:app --reload --port 8001
```

## 환경 변수

### Backend (`.env`)
```bash
API_PORT=8001         # 백엔드 서버 포트
API_HOST=0.0.0.0      # 바인딩 호스트
```

### Frontend (`web-dashboard/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8001  # 백엔드 API URL
```

## 포트 충돌 해결

### 증상
- `Address already in use` 에러
- Server startup 실패

### 해결 방법

#### Option 1: 자동 해결 (권장)
```bash
start-backend.bat
```
→ 자동으로 다른 포트 찾음

#### Option 2: 포트 변경
```bash
set API_PORT=8002
python -m uvicorn backend.main:app --reload
```

#### Option 3: 기존 프로세스 종료
```powershell
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8001

# PID로 프로세스 종료
taskkill /PID <PID> /F
```

## 프론트엔드 연동

### 자동 연동
`start-backend.bat` 사용 시 `.env.local`이 자동 업데이트됩니다.

### 수동 연동
1. 백엔드 포트 확인
2. `web-dashboard/.env.local` 수정:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:<PORT>
   ```
3. Next.js 재시작 (환경 변수 다시 로드)
   ```bash
   cd web-dashboard
   npm run dev
   ```

## 문제 해결

### port_finder.py 실행 실패
```bash
# Python 경로 확인
.venv\Scripts\python.exe backend/app/utils/port_finder.py
```

### .env.local 업데이트 실패
수동으로 수정:
```bash
echo NEXT_PUBLIC_API_URL=http://localhost:8001 > web-dashboard\.env.local
```

### 여러 인스턴스 실행
각 인스턴스에 다른 포트 할당:
```bash
# Instance 1
set API_PORT=8001
python -m uvicorn backend.main:app --reload

# Instance 2 (새 터미널)
set API_PORT=8002
python -m uvicorn backend.main:app --reload
```

## 베스트 프랙티스

1. **개발 환경**: `start-backend.bat` 사용
2. **CI/CD**: 환경 변수로 포트 지정
3. **Production**: Docker Compose로 포트 매핑
4. **팀 협업**: `.env.example` 공유, `.env` 제외 (`.gitignore`)

## 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/app/utils/port_finder.py` | 포트 탐색 유틸리티 |
| `start-backend.bat` | 자동 시작 스크립트 |
| `backend/.env.example` | 환경 변수 템플릿 |
| `web-dashboard/.env.local` | 프론트엔드 API URL |
| `CLAUDE.md` | 전체 개발 가이드 |
