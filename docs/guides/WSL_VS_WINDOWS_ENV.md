# Windows vs WSL 환경 정리

## 표준 경로 (Windows)
- PowerShell/cmd에서 리포지토리로 이동
- venv 활성화: `.venv\Scripts\activate`
- 테스트 실행: `python -m pytest tests -v` (또는 `python tests\run_udo_phase1.py`)
- WSL에서 Windows venv 실행 금지 (vsock 오류)

## WSL에서 필요할 때
- `python3 -m venv .venv_wsl` (Python 3.13 권장)
- `source .venv_wsl/bin/activate`
- `pip install -r requirements.txt -r backend/requirements.txt`
- `pytest tests -v`
- 현재 WSL은 pip/네트워크 차단 상태라 설치 불가. 가능해지면 진행.

## 주의
- Windows venv를 WSL에서 호출하면 `UtilBindVsockAnyPort socket failed` 발생
- 환경 섞이지 않게 셸/venv를 일치시킬 것
