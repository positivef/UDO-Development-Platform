# Git Wrapper Windows 설치 가이드

**작성일**: 2025-12-23
**목적**: Windows 환경에서 git clean 차단 기능 설치
**중요도**: 🔴 CRITICAL (P0)

---

## 📋 요약

Git alias 방법은 실패했습니다 (2025-12-23 테스트 결과). Windows에서 git clean을 차단하려면 PowerShell function을 사용해야 합니다.

---

## 🚀 설치 방법 (권장 - PowerShell)

### 방법 1: 자동 설치 (PowerShell 스크립트)

**1단계: PowerShell을 관리자 권한으로 실행**
```powershell
# Windows 검색 → "PowerShell" → 우클릭 → "관리자 권한으로 실행"
```

**2단계: 설치 스크립트 실행**
```powershell
cd C:\Users\user\Documents\GitHub\UDO-Development-Platform
.\scripts\install_git_wrapper.ps1
```

**3단계: PowerShell 재시작 또는 프로필 리로드**
```powershell
# 방법 1: PowerShell 닫고 다시 열기 (권장)

# 방법 2: 현재 세션에서 리로드
. $PROFILE
```

**4단계: 테스트**
```powershell
git clean -fd
# 예상 결과: 🚫 git clean is DISABLED for safety!
```

---

### 방법 2: 수동 설치

**1단계: PowerShell 프로필 열기**
```powershell
notepad $PROFILE
```

만약 파일이 없다는 오류가 나면:
```powershell
New-Item -Path $PROFILE -ItemType File -Force
notepad $PROFILE
```

**2단계: 아래 코드를 프로필에 추가**
```powershell
# Git Safety Wrapper - Block dangerous commands
function git {
    param(
        [Parameter(Position=0)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Args
    )

    # Block 'git clean'
    if ($Command -eq "clean") {
        Write-Host ""
        Write-Host "🚫 ==========================================" -ForegroundColor Red
        Write-Host "⚠️  git clean is DISABLED for safety!" -ForegroundColor Red
        Write-Host "==========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Reason: git clean -fd permanently deletes files (no recovery)"
        Write-Host ""
        Write-Host "Safe alternatives:" -ForegroundColor Green
        Write-Host "  - Remove specific file: rm <filename>" -ForegroundColor Green
        Write-Host "  - Preview: git clean -n -fd" -ForegroundColor Green
        Write-Host "  - Stash: git stash -u" -ForegroundColor Green
        Write-Host ""
        Write-Host "If you REALLY need git clean:" -ForegroundColor Yellow
        Write-Host "  1. Backup: python scripts/auto_backup_untracked.py --backup"
        Write-Host "  2. Use real git: & 'C:\Program Files\Git\cmd\git.exe' clean ..."
        Write-Host ""
        return
    }

    # Pass through to real git
    & "C:\Program Files\Git\cmd\git.exe" $Command @Args
}
```

**3단계: 저장 후 PowerShell 재시작**

---

## ✅ 확인 방법

### 1. 차단 테스트
```powershell
git clean -fd
```

**예상 결과**:
```
🚫 ==========================================
⚠️  git clean is DISABLED for safety!
==========================================

Reason: git clean -fd permanently deletes files (no recovery)

Safe alternatives:
  - Remove specific file: rm <filename>
  - Preview: git clean -n -fd
  - Stash: git stash -u

If you REALLY need git clean:
  1. Backup: python scripts/auto_backup_untracked.py --backup
  2. Use real git: & 'C:\Program Files\Git\cmd\git.exe' clean ...
```

### 2. 다른 git 명령 정상 작동 확인
```powershell
git status
git log
git add .
git commit -m "test"
```

**예상 결과**: 모두 정상 작동

---

## 🔧 문제 해결

### 문제 1: PowerShell에서 "실행할 수 없음" 오류

**오류 메시지**:
```
이 시스템에서 스크립트를 실행할 수 없으므로...
```

**해결 방법**:
```powershell
# 실행 정책 확인
Get-ExecutionPolicy

# RemoteSigned로 변경 (관리자 권한 필요)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### 문제 2: Git 명령이 느려짐

**원인**: PowerShell function 오버헤드

**해결 방법**:
```powershell
# 프로필에서 git function 제거 후
# Git Bash에서만 사용 (Linux/Mac과 동일한 wrapper script)
```

---

### 문제 3: Git Bash에서도 적용하고 싶음

**방법**:
```bash
# Git Bash에서 ~/.bashrc 편집
nano ~/.bashrc

# 아래 내용 추가
alias git='bash /c/Users/user/Documents/GitHub/UDO-Development-Platform/scripts/git-safe-wrapper.sh'

# 저장 후 리로드
source ~/.bashrc
```

---

## 🚫 작동하지 않는 방법 (피할 것)

### ❌ Git Alias (실패 확인됨)

```bash
# 이 방법은 작동하지 않습니다! (2025-12-23 테스트)
git config --global alias.clean '!echo "Disabled" && false'

# Windows에서 alias가 무시되고 실제 git clean이 실행됨
# 절대 사용하지 마세요!
```

**실패 사례**: 2025-12-23 18:30, 17개 파일 삭제 발생

---

## 🔄 제거 방법

PowerShell wrapper를 제거하려면:

```powershell
# 프로필 편집
notepad $PROFILE

# git function 부분 전체 삭제
# 저장 후 PowerShell 재시작
```

---

## 📊 비교표

| 방법 | 효과 | 난이도 | 성능 | 권장 |
|------|------|--------|------|------|
| **PowerShell Function** | ✅ 완벽 차단 | Easy | 약간 느림 | ✅ 권장 |
| Git Wrapper Script | ✅ 완벽 차단 | Hard | 빠름 | Unix only |
| ❌ Git Alias | ❌ 실패 | Easy | 빠름 | 절대 금지 |
| Pre-commit Hook | ⚠️ commit만 | Easy | 빠름 | 보조 수단 |

---

## 🎯 다음 단계

1. **설치 완료 후**:
   - [ ] `git clean -fd` 테스트로 차단 확인
   - [ ] 다른 git 명령 정상 작동 확인
   - [ ] Post-commit hook 작동 확인 (백업 자동 실행)

2. **추가 안전장치**:
   - [ ] Windows Task Scheduler 백업 자동화
   - [ ] Cloud 백업 추가 (OneDrive/Dropbox)

---

**⚠️ 중요**: PowerShell function 방식이 Windows에서 유일하게 신뢰할 수 있는 방법입니다!

**마지막 업데이트**: 2025-12-23
**다음 리뷰**: Git Wrapper 작동 확인 후
