# Git Safety Guide - 절대 잊지 말아야 할 규칙

**작성일**: 2025-12-23
**경위**: git clean incident로 1,000+ lines 코드 손실
**목적**: 다시는 같은 실수를 반복하지 않기 위한 필수 가이드

---

## 🚨 절대 금지 명령어 (NEVER USE)

### 1. `git clean -fd` - 가장 위험한 명령어

```bash
❌ git clean -fd           # 모든 untracked 파일 영구 삭제 (복구 불가)
❌ git clean -fdx          # .gitignore 파일까지 모두 삭제
❌ git clean -ffdx         # 강제 삭제 (더 위험)
```

**왜 위험한가?**
- Git에 추가(`git add`)하지 않은 모든 파일을 **영구 삭제**
- **복구 불가능** (Git 히스토리에 없음)
- 작업 중인 새 파일들이 순식간에 사라짐

**실제 피해 사례 (2025-12-22)**:
- 삭제된 파일: 5개 (ErrorBoundary.tsx, useKanbanWebSocket.ts, ConnectionStatusIndicator.tsx, PartialFailureHandler.tsx, performance-optimizations.spec.ts)
- 손실된 코드: 1,000+ lines
- 복구 시간: 6시간

---

## ✅ 안전한 대안 명령어

### NUL 파일 또는 불필요한 파일 제거

```bash
✅ rm NUL                  # 특정 파일만 삭제 (안전)
✅ rm -i unwanted.txt      # 삭제 전 확인 프롬프트
✅ git clean -n -fd        # DRY RUN (실제로 삭제하지 않고 미리보기)
```

### Untracked 파일 확인

```bash
✅ git status              # Untracked 파일 목록 확인
✅ git ls-files --others --exclude-standard  # 상세 목록
```

### 파일 복구가 필요한 경우

```bash
✅ git stash -u            # Untracked 파일 포함 임시 저장
✅ git stash pop           # 저장된 파일 복구
```

---

## 🔒 3중 안전장치 시스템

### Tier 1: Git Pre-commit Hook (자동 차단)

**위치**: `.git/hooks/pre-commit`

**기능**:
- 10개 이상 파일 삭제 시 자동 차단
- Critical 파일 3개 이상 삭제 시 차단
- Untracked 중요 파일 경고
- NUL 파일 자동 .gitignore 추가

**우회 방법** (정말 필요한 경우만):
```bash
git commit --no-verify    # Hook 우회 (100% 확신할 때만!)
```

### Tier 2: 자동 백업 시스템

**스크립트**: `scripts/auto_backup_untracked.py`

**사용법**:
```bash
# 백업 생성 (30분마다 실행 권장)
python scripts/auto_backup_untracked.py --backup

# 백업 목록 확인
python scripts/auto_backup_untracked.py --list

# 백업 복구
python scripts/auto_backup_untracked.py --restore backup_20251223_143000
```

**백업 위치**: `D:/git-untracked-backups/`

**자동화** (Windows Task Scheduler):
```bash
# 30분마다 자동 백업
schtasks /create /tn "Git Untracked Backup" /tr "python C:\Users\user\Documents\GitHub\UDO-Development-Platform\scripts\auto_backup_untracked.py --backup" /sc minute /mo 30
```

### Tier 3: 안전한 워크플로우 (습관화)

**작업 전 체크리스트**:
1. ✅ `git status` - 현재 상태 확인
2. ✅ `git add .` - 새 파일 모두 추가
3. ✅ `git commit -m "message"` - 커밋
4. ✅ `git push` - 원격 저장소에 백업

**절대 하지 말아야 할 것**:
1. ❌ Untracked 파일이 있는 상태에서 `git clean` 실행
2. ❌ 확인 없이 대량 파일 삭제
3. ❌ `--force`, `-f` 옵션 남용
4. ❌ 피곤하거나 급할 때 위험한 명령어 실행

---

## 🆘 긴급 복구 가이드

### 실수로 `git clean` 실행한 경우

**즉시 실행**:
```bash
# 1. 추가 손실 방지 - 작업 중단
# 2. 백업에서 복구
python scripts/auto_backup_untracked.py --restore <최신_백업>

# 3. 백업이 없는 경우
# - Windows: 휴지통 확인
# - Recovery 도구: Recuva, TestDisk
# - IDE 임시 파일: .vscode/*, .idea/*
```

### Git 히스토리에 있는 파일 복구

```bash
# 특정 커밋에서 파일 복구
git checkout <commit-hash> -- path/to/file

# 이전 커밋으로 전체 롤백
git reset --hard <commit-hash>
```

---

## 📚 추가 안전 수칙

### .gitignore 관리

```bash
# NUL 파일은 항상 .gitignore에 추가
echo "NUL" >> .gitignore
echo "nul" >> .gitignore

# 중요한 설정 파일
echo ".env" >> .gitignore
echo "*.log" >> .gitignore
```

### Git Alias로 안전한 명령어만 사용

```bash
# ~/.gitconfig 또는 .git/config
[alias]
    # 안전한 clean (dry-run 먼저)
    clean-safe = clean -n -fd

    # Untracked 파일 확인
    untracked = ls-files --others --exclude-standard

    # 백업 포함 stash
    backup = stash -u
```

### IDE/Editor 설정

**VS Code**: 자동 저장 활성화
```json
{
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000
}
```

**Git 작업 전 항상**:
1. 파일 저장 확인
2. `git status` 확인
3. 중요 파일은 `git add` 먼저

---

## 🎯 황금 규칙 (Golden Rules)

### 규칙 1: Untracked 파일은 항상 위험하다
- 새 파일 작성 후 **즉시** `git add`
- 작업 끝날 때까지 커밋하지 않아도 OK, **add는 필수**

### 규칙 2: 삭제 명령은 두 번 확인
- `git clean` → **절대 사용 금지**
- `rm -rf` → 정말 필요한가? 다시 생각
- `-f`, `--force` → 왜 필요한지 5초 생각

### 규칙 3: 백업은 생명줄
- 30분마다 자동 백업
- 중요 작업 전 수동 백업: `python scripts/auto_backup_untracked.py --backup`
- 원격 저장소에 자주 push

### 규칙 4: 실수는 즉시 보고
- 파일 삭제 사고 발생 → 즉시 복구 시도
- 시간이 지날수록 복구 어려워짐
- 부끄러워하지 말고 도움 요청

### 규칙 5: 피곤할 땐 위험한 작업 금지
- 새벽 작업 → 위험한 Git 명령 금지
- 급할 때 → 더 신중하게
- 확신 없으면 → 하지 않기

---

## ✅ 일일 체크리스트

**매일 작업 시작 시**:
- [ ] `git status` 확인
- [ ] Untracked 파일 있으면 `git add` 또는 백업
- [ ] 백업 시스템 작동 확인

**매일 작업 종료 시**:
- [ ] 모든 새 파일 `git add`
- [ ] 커밋 또는 stash로 저장
- [ ] 수동 백업 실행 (중요한 작업한 경우)

---

## 🔗 관련 문서

- **사고 기록**: `claudedocs/completion/2025-12-22-GIT-CLEAN-INCIDENT.md`
- **복구 과정**: Git log commit `a0852ab`
- **Pre-commit Hook**: `.git/hooks/pre-commit`
- **백업 스크립트**: `scripts/auto_backup_untracked.py`

---

## 📞 긴급 연락

**파일 손실 사고 발생 시**:
1. **즉시 작업 중단** (추가 손실 방지)
2. **백업 복구 시도**: `python scripts/auto_backup_untracked.py --list`
3. **Git 히스토리 확인**: `git reflog`
4. **도움 요청**: GitHub Issues, Stack Overflow

---

**⚠️ 이 문서는 실제 사고 경험을 바탕으로 작성되었습니다.**
**절대 잊지 마세요: "git clean -fd는 영구 삭제, 복구 불가"**

**마지막 업데이트**: 2025-12-23
**다음 리뷰**: 매월 1일
