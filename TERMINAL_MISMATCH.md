# 터미널 안내 (Windows vs WSL)

운영하는 환경이 WSL인지 Windows인지 확실치 않습니다. 아래 중 하나를 선택해 실행하세요.

## 1) Windows PowerShell/cmd (추천)
- 리포지토리 위치로 이동
- venv 활성화: `.venv\Scripts\activate`
- 테스트: `python -m pytest tests -v` (또는 `python tests\run_udo_phase1.py`)
- 주의: WSL에서 Windows venv를 호출하지 마세요 (vsock 오류 발생)
- 백엔드 기동: `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` (루트 경로에서 실행)

## 2) WSL에서 실행하려면 (pip 필요)
- `python3 -m venv .venv_wsl` (Python 3.13 권장)
- `source .venv_wsl/bin/activate`
- `pip install -r requirements.txt -r backend/requirements.txt`
- `pytest tests -v`
- 현재 WSL은 pip/네트워크 차단으로 설치 불가 상태이니, pip 가능해지면 시도하세요.
