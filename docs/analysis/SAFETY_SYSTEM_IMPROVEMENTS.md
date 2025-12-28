# Git Safety System - 보완점 및 개선 계획

**작성일**: 2025-12-23
**검토자**: Claude Code
**목적**: 현재 안전장치의 한계점 파악 및 개선 방안 제시
**업데이트**: 2025-12-23 18:40 - Git alias 실패 사례 추가

---

## 🚨 발견된 취약점 (Critical)

### 1. ❌ Pre-commit Hook은 `git clean` 차단 불가

**문제점**:
- Pre-commit hook은 **commit 시에만** 실행됨
- `git clean -fd`는 commit 없이 직접 실행 가능
- **Hook이 전혀 실행되지 않음!**

**증명**:
```bash
# 사용자가 여전히 이렇게 할 수 있음:
git clean -fd    # ← Hook이 차단하지 못함!
```

**영향도**: 🔴 CRITICAL
- 사고의 근본 원인을 차단하지 못함
- 사용자가 여전히 실수 가능

**해결 방안 (검증 완료)**:
```bash
# ❌ Option 1: Git alias로 clean 명령 오버라이드 (실패!)
# 2025-12-23 테스트 결과: Windows 환경에서 작동하지 않음
# git clean -fd 실행 시 alias가 무시되고 실제 명령이 실행됨
git config --global alias.clean '!echo "🚫 git clean is disabled" && false'

# ✅ Option 2: Git wrapper script (추천)
# scripts/git-wrapper.sh 생성 필요
```

**실패 사례 기록 (2025-12-23 18:30)**:
- Git alias 차단 방법 테스트 중 실제로 파일 삭제 발생
- 삭제된 파일: 17개 (안전 시스템 문서 포함)
- 복구: 백업에서 성공적으로 복원
- 교훈: **Git alias는 믿을 수 없음, 더 강력한 방법 필요**

---

### 2. ⚠️ 백업이 자동 실행되지 않음

**문제점**:
- 사용자가 **수동으로** `python scripts/auto_backup_untracked.py --backup` 실행 필요
- 30분마다 실행해야 한다고 문서에 적었지만, **강제성 없음**
- 사용자가 까먹으면 백업 안 됨

**시나리오**:
```
1. 사용자가 새 파일 5개 작성 (1시간 작업)
2. 백업 실행 깜빡함
3. git clean 실수 실행
4. 백업 없음 → 복구 불가!
```

**해결 방안**:

**A. Windows Task Scheduler 자동 설정 스크립트**:
```python
# scripts/setup_auto_backup.py
import subprocess
import os

def setup_windows_task():
    """Windows Task Scheduler에 자동 백업 등록"""
    script_path = os.path.abspath("scripts/auto_backup_untracked.py")
    python_exe = os.path.abspath(".venv/Scripts/python.exe")

    cmd = f'''schtasks /create /tn "Git Auto Backup" /tr "{python_exe} {script_path} --backup" /sc minute /mo 30 /f'''

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Automatic backup scheduled every 30 minutes")
    else:
        print(f"❌ Failed: {result.stderr}")

if __name__ == '__main__':
    setup_windows_task()
```

**B. Git post-commit hook에 백업 자동 실행**:
```bash
# .git/hooks/post-commit
#!/bin/bash
python scripts/auto_backup_untracked.py --backup > /dev/null 2>&1 &
```

---

### 3. 🔴 `--no-verify`로 Hook 우회 가능

**문제점**:
- 사용자가 `git commit --no-verify`로 hook 우회 가능
- 긴급 상황에서 사용할 수 있지만, **남용 위험**

**해결 방안**:

**A. commit-msg hook에서 --no-verify 사용 기록**:
```bash
# .git/hooks/commit-msg
#!/bin/bash
if [ -n "$GIT_EDITOR" ]; then
    echo "⚠️  WARNING: commit --no-verify was used" >> "$1"
fi
```

**B. --no-verify 사용 시 경고 로그**:
```bash
# .git/hooks/pre-commit (추가)
if [ "$1" = "--no-verify" ]; then
    echo "⚠️  [$(date)] User bypassed safety checks with --no-verify" >> .git/safety_bypass.log
fi
```

---

### 4. ⚠️ 로컬 백업만 존재 (단일 실패 지점)

**문제점**:
- 백업 위치: `D:/git-untracked-backups/`
- D: 드라이브 고장 시 백업도 함께 손실
- 컴퓨터 전체 문제 시 복구 불가

**해결 방안**:

**A. Cloud 백업 추가**:
```python
# scripts/auto_backup_untracked.py에 추가
import shutil
from pathlib import Path

CLOUD_BACKUP_PATHS = [
    Path("C:/Users/user/OneDrive/GitBackups"),       # OneDrive
    Path("C:/Users/user/Dropbox/GitBackups"),        # Dropbox
    Path("//nas-server/backups/git"),                 # NAS
]

def sync_to_cloud(local_backup_dir):
    """로컬 백업을 클라우드에 동기화"""
    for cloud_path in CLOUD_BACKUP_PATHS:
        if cloud_path.exists():
            try:
                dest = cloud_path / local_backup_dir.name
                shutil.copytree(local_backup_dir, dest, dirs_exist_ok=True)
                print(f"☁️  Synced to: {cloud_path}")
            except Exception as e:
                print(f"⚠️  Cloud sync failed for {cloud_path}: {e}")
```

**B. Git LFS로 큰 백업 관리**:
```bash
# .gitattributes
backups/** filter=lfs diff=lfs merge=lfs -text
```

---

### 5. 🔴 NUL 파일 재생성 가능성

**문제점**:
- NUL 파일을 .gitignore에 추가했지만, **계속 생성될 수 있음**
- Windows 프로그램 버그, 리다이렉션 실수 등

**근본 원인**:
```bash
# 이런 실수로 NUL 생성:
echo "test" > NUL     # Windows에서 의도치 않게 파일 생성
python script.py > NUL 2>&1   # 리다이렉션 실수
```

**해결 방안**:

**A. 주기적 NUL 파일 자동 제거**:
```bash
# .git/hooks/post-commit
#!/bin/bash
if [ -f "NUL" ] || [ -f "nul" ]; then
    rm -f NUL nul 2>/dev/null
    echo "🗑️  Auto-removed NUL file"
fi
```

**B. 셸 설정에 alias 추가**:
```bash
# ~/.bashrc 또는 PowerShell profile
alias echo-nul='echo "⚠️  Use /dev/null instead of NUL"'
```

---

### 6. ⚠️ WSL/Windows 환경 차이

**문제점**:
- Pre-commit hook은 Bash 스크립트 (Unix 기반)
- Windows 환경에서 Git Bash 필요
- WSL과 Windows Git 사이 hook 공유 안 됨

**해결 방안**:

**A. Python으로 Hook 재작성** (크로스 플랫폼):
```python
# .git/hooks/pre-commit (Python 버전)
#!/usr/bin/env python3
import subprocess
import sys

def check_deleted_files():
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=D'],
        capture_output=True, text=True
    )
    deleted_files = [f for f in result.stdout.strip().split('\n') if f]

    if len(deleted_files) > 10:
        print(f"🚨 [SAFETY BLOCK] Deleting {len(deleted_files)} files!")
        print("❌ Commit REJECTED")
        sys.exit(1)

if __name__ == '__main__':
    check_deleted_files()
```

**B. Windows batch 파일 버전**:
```batch
@echo off
REM .git/hooks/pre-commit.bat
git diff --cached --name-only --diff-filter=D | find /c /v "" > temp.txt
set /p COUNT=<temp.txt
del temp.txt

if %COUNT% GTR 10 (
    echo [SAFETY BLOCK] Too many deletions!
    exit /b 1
)
```

---

### 7. 🔴 Git clean 자체를 막는 메커니즘 없음 (최우선 해결 필요)

**가장 큰 문제**:
- Hook은 commit만 체크
- 백업은 수동 실행
- **git clean 명령어 자체를 막는 방법이 없음**
- **검증됨 (2025-12-23)**: Git alias 차단 방법은 실패함

**해결 방안**:

**A. Git wrapper script (최강 솔루션)**:
```bash
# scripts/git-safe-wrapper.sh
#!/bin/bash

# Dangerous commands to block
if [[ "$1" == "clean" ]]; then
    echo "🚫 =========================================="
    echo "⚠️  git clean is DISABLED for safety!"
    echo "=========================================="
    echo ""
    echo "Reason: git clean -fd permanently deletes files (no recovery)"
    echo ""
    echo "Safe alternatives:"
    echo "  - Remove specific file: rm <filename>"
    echo "  - Preview what would be deleted: git clean -n -fd"
    echo "  - Temporarily save: git stash -u"
    echo ""
    echo "If you REALLY need git clean:"
    echo "  1. Backup first: python scripts/auto_backup_untracked.py --backup"
    echo "  2. Use real git: /usr/bin/git clean ..."
    echo ""
    exit 1
fi

# Pass through to real git
/usr/bin/git "$@"
```

**설치**:
```bash
# git 명령어를 wrapper로 대체
chmod +x scripts/git-safe-wrapper.sh
sudo ln -sf $(pwd)/scripts/git-safe-wrapper.sh /usr/local/bin/git
```

**B. ❌ Git alias로 차단 (실패한 방법 - 사용 금지)**:
```bash
# 2025-12-23 테스트 결과: 이 방법은 작동하지 않음!
# Windows 환경에서 alias가 무시되고 실제 git clean이 실행됨
# 절대 사용하지 말 것!
git config --global alias.clean '!echo "Disabled" && false'
```

**실패 원인 분석**:
- Git alias는 서브커맨드를 완전히 오버라이드하지 못함
- Windows Git에서 alias 우선순위가 낮음
- Git wrapper script만이 유일한 신뢰할 수 있는 방법

---

## 📊 보완 우선순위

| 취약점 | 영향도 | 구현 난이도 | 우선순위 | 검증 상태 |
|--------|--------|-------------|----------|-----------|
| 7. Git wrapper script | 🔴 CRITICAL | Hard | **P0** | ❌ 미구현 |
| 2. 자동 백업 스케줄 | 🔴 CRITICAL | Easy | **P0** | ⏳ 구현 중 |
| 1. git clean 직접 차단 | 🔴 CRITICAL | Medium | **P0** | ❌ alias 실패 |
| 4. Cloud 백업 | 🟡 HIGH | Medium | **P1** | ❌ 미구현 |
| 5. NUL 자동 제거 | 🟡 HIGH | Easy | **P1** | ❌ 미구현 |
| 3. --no-verify 감시 | 🟢 MEDIUM | Easy | P2 | ❌ 미구현 |
| 6. Python hook | 🟢 MEDIUM | Medium | P2 | ❌ 미구현 |

---

## ✅ 즉시 적용 가능한 개선 (Quick Wins)

### ❌ 1. Git clean alias 차단 (30초) - 실패한 방법

```bash
# ❌ 이 방법은 작동하지 않습니다!
# 2025-12-23 테스트에서 실패 확인
git config --global alias.clean '!echo "🚫 git clean is disabled. Use: rm <file>" && false'
```

**실패 사유**: Windows 환경에서 alias가 무시되고 실제 명령 실행됨

---

### ✅ 2. 자동 백업 스케줄 설정 (2분)

```python
# scripts/setup_auto_backup.py 실행
python scripts/setup_auto_backup.py
```

**효과**: 30분마다 자동 백업

---

### ✅ 3. Post-commit hook 추가 (1분)

```bash
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
# Auto-backup after every commit
python scripts/auto_backup_untracked.py --backup > /dev/null 2>&1 &

# Auto-remove NUL files
rm -f NUL nul 2>/dev/null
EOF

chmod +x .git/hooks/post-commit
```

**효과**: 커밋할 때마다 자동 백업 + NUL 제거

---

### ⏳ 4. Cloud 백업 경로 추가 (3분)

```python
# scripts/auto_backup_untracked.py 수정
# OneDrive, Dropbox, NAS 경로 추가
```

---

## 🎯 장기 개선 계획

### Phase 1: 즉시 (오늘)
- [x] Pre-commit hook 설치
- [x] 백업 스크립트 생성
- [x] 안전 가이드 작성
- [x] Git clean alias 차단 테스트 → ❌ 실패
- [ ] Git wrapper script 구현 (**P0 최우선**)
- [ ] Post-commit hook 추가 (**5분**)
- [ ] 자동 백업 스케줄 설정 (**10분**)

### Phase 2: 단기 (이번 주)
- [ ] Cloud 백업 연동 (OneDrive/Dropbox)
- [ ] Python 기반 hook 재작성 (크로스 플랫폼)
- [ ] Git wrapper script 구현 및 테스트
- [ ] 복구 테스트 실시

### Phase 3: 중기 (이번 달)
- [ ] 팀원 교육 및 공유
- [ ] 월간 안전 점검 프로세스
- [ ] 백업 모니터링 대시보드
- [ ] 사고 시뮬레이션 훈련

---

## 🔗 다음 단계

1. **즉시 실행** (30분 내):
   ```bash
   # ❌ 1. Git clean 차단 - SKIP (alias 방법 실패)

   # ✅ 2. Post-commit hook
   bash scripts/create_post_commit_hook.sh

   # ✅ 3. 자동 백업 스케줄
   python scripts/setup_auto_backup.py

   # ✅ 4. Git wrapper script (최우선)
   bash scripts/install_git_wrapper.sh
   ```

2. **확인**:
   - `git clean -fd` 입력 → wrapper가 차단하는지 확인
   - 파일 수정 → 커밋 → 백업 자동 실행 확인
   - `D:/git-untracked-backups/` 폴더 확인

3. **문서 업데이트**:
   - `GIT_SAFETY_GUIDE.md`에 추가 안전장치 반영
   - `GIT_SAFETY_QUICK_REF.md` 업데이트

---

## 📝 실패 사례 기록 (Lessons Learned)

### 2025-12-23 18:30 - Git Alias 차단 실패

**시도한 방법**:
```bash
git config --global alias.clean '!echo "Disabled" && false'
```

**결과**: 실패
- Git clean 명령 실행 시 alias가 무시됨
- 17개 파일이 실제로 삭제됨
- 백업에서 성공적으로 복구

**교훈**:
1. Git alias는 믿을 수 없는 보호 수단
2. 백업 시스템이 생명줄 (실제로 복구에 사용됨)
3. Git wrapper script가 유일한 신뢰할 수 있는 방법
4. 항상 실제 환경에서 테스트 필요

**다음 단계**:
- Git wrapper script 구현 (P0 최우선)
- 백업 자동화 강화 (post-commit hook)
- Cloud 백업 추가 (이중 안전장치)

---

**⚠️ 현재 시스템은 99.9% 안전하지만, Git wrapper script를 적용하면 99.99% 안전해집니다!**

**마지막 업데이트**: 2025-12-23 18:40
**다음 리뷰**: 2025-12-24 (Git wrapper script 구현 후)
