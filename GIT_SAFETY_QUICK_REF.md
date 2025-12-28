# Git 안전 수칙 - 빠른 참조 카드

> **벽에 붙여두고 매일 확인하세요!**

---

## 🚫 절대 금지 명령어

```bash
❌ git clean -fd        # 영구 삭제, 복구 불가
❌ git clean -fdx       # .gitignore까지 삭제
❌ rm -rf *             # 모든 파일 삭제
```

**이 명령어들은 파일을 영구 삭제합니다. 복구 불가능!**

---

## ✅ 안전한 대안

```bash
✅ rm <filename>        # 특정 파일만 삭제
✅ git clean -n -fd     # 미리보기 (실제 삭제 안 함)
✅ git stash -u         # Untracked 파일 포함 임시 저장
```

---

## 🔒 자동 안전장치 (설치 완료)

### Tier 1: Pre-commit Hook
- **위치**: `.git/hooks/pre-commit`
- **기능**: 10개 이상 파일 삭제 시 차단

### Tier 2: Post-commit Hook
- **위치**: `.git/hooks/post-commit`
- **기능**: 커밋 후 자동 백업 + NUL 제거

### Tier 3: Git Wrapper (Windows)
- **위치**: PowerShell $PROFILE
- **기능**: `git clean` 명령 직접 차단
- **설치**: `.\scripts\install_git_wrapper.ps1`

### Tier 4: 자동 백업 스케줄
- **위치**: Windows Task Scheduler
- **기능**: 30분마다 자동 백업
- **설치**: `python scripts/setup_auto_backup.py`

---

## 📋 일일 체크리스트

### 작업 시작 시
- [ ] `git status` - 현재 상태 확인
- [ ] Untracked 파일 있으면 `git add` 또는 백업

### 작업 중
- [ ] 새 파일 작성 후 즉시 `git add`
- [ ] 30분마다 자동 백업 (Task Scheduler가 실행)

### 작업 종료 시
- [ ] 모든 새 파일 `git add`
- [ ] `git commit` 또는 `git stash`로 저장
- [ ] 중요 작업 시 수동 백업 실행

---

## 🆘 긴급 상황

### 실수로 파일 삭제한 경우

```bash
# 1. 즉시 작업 중단!
# 2. 백업에서 복구
python scripts/auto_backup_untracked.py --list
python scripts/auto_backup_untracked.py --restore backup_YYYYMMDD_HHMMSS

# 3. Git 히스토리 확인
git reflog
git checkout <commit-hash> -- <file>
```

---

## 🔒 안전장치 작동 확인

```bash
# Pre-commit hook 테스트
bash .git/hooks/pre-commit

# 백업 생성
python scripts/auto_backup_untracked.py --backup

# 백업 목록
python scripts/auto_backup_untracked.py --list

# Git wrapper 테스트 (PowerShell)
git clean -fd
# 예상: 🚫 git clean is DISABLED for safety!
```

---

## 🎯 황금 규칙 (5초 안에 외우기)

1. **새 파일 = 즉시 add**
2. **삭제 = 두 번 생각**
3. **모를 땐 = 검색 먼저**
4. **백업 = 생명줄**
5. **급할 땐 = 더 신중**

---

## 📞 도움말

- **상세 가이드**: `docs/GIT_SAFETY_GUIDE.md`
- **사고 분석**: `claudedocs/analysis/2025-12-23-GIT-CLEAN-INCIDENT-ANALYSIS.md`
- **백업 스크립트**: `scripts/auto_backup_untracked.py`
- **Windows 설치**: `docs/GIT_WRAPPER_WINDOWS_INSTALL.md`
- **개선 계획**: `docs/SAFETY_SYSTEM_IMPROVEMENTS.md`

---

## ⚡ 새로운 기능 (2025-12-23 추가)

### PowerShell Git Wrapper
```powershell
# 설치 (관리자 권한)
.\scripts\install_git_wrapper.ps1

# 테스트
git clean -fd
# → 차단 메시지 표시

# 제거
notepad $PROFILE
# → git function 부분 삭제
```

### 자동 백업 스케줄
```bash
# 설치 (관리자 권한)
python scripts/setup_auto_backup.py

# 확인
schtasks /query /tn "Git Auto Backup - UDO Platform"

# 제거
schtasks /delete /tn "Git Auto Backup - UDO Platform" /f
```

---

**⚠️ 이 카드는 실제 사고 (1,000+ lines 손실) 경험을 바탕으로 작성되었습니다.**

**절대 잊지 마세요: "git clean -fd는 영구 삭제, 복구 불가"**

**마지막 업데이트**: 2025-12-23
**다음 리뷰**: 매월 1일
