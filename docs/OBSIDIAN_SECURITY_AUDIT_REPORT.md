# Obsidian 통합 보안 감사 보고서

**작성일**: 2026-01-01
**감사 범위**: Obsidian 통합 시스템 (Round 1)
**평가 대상**: 5개 주요 기능
**총 위험도**: MEDIUM (완화 조치 필수)

---

## 전체 요약

| 기능 | 위험도 | 완화 필수 | 상태 |
|------|--------|---------|------|
| MCP Obsidian 접근 | **MEDIUM** | ✅ Yes | 부분 완화됨 |
| Auto-sync 스크립트 | **HIGH** | ✅ Yes | 중대 취약점 |
| Context7 캐싱 | **MEDIUM** | ✅ Yes | 완화 필요 |
| AI 생성 콘텐츠 | **LOW** | ⚠️ Optional | 모니터링 권장 |
| Git Hook 자동 실행 | **HIGH** | ✅ Yes | 즉시 조치 필요 |

**최종 권고**: **현재 상태에서 프로덕션 배포 불가능**. 7개 HIGH/CRITICAL 항목을 해결해야 함.

---

## 1️⃣ MCP Obsidian 접근

### 위험도: **MEDIUM** ⚠️

### 취약점 분석

#### 1-1. Vault 자동 감지 (AUTO-DETECT) 취약성

**파일**: `backend/app/services/obsidian_service.py:68-89`

```python
def _auto_detect_vault(self) -> Optional[Path]:
    """Auto-detect Obsidian vault location"""
    common_paths = [
        Path(r"C:\Users\user\Documents\Obsidian Vault"),
        Path.home() / "Documents" / "Obsidian Vault",
        Path.home() / "Obsidian Vault",
        Path.cwd() / "Obsidian Vault"
    ]
```

**문제점**:
- ❌ **하드코딩된 경로**: `C:\Users\user\Documents\...` (개인 경로 노출)
- ❌ **권한 검증 없음**: 접근 권한 확인 없이 자동 사용
- ❌ **우선순위 조작**: 첫 번째 존재하는 경로 사용 (경로 하이재킹 가능)
- ⚠️ **환경변수 미사용**: 설정 외부화 없음

**공격 시나리오**:
```
공격자가 C:\Users\user\Documents\에 악의적인 "Obsidian Vault" 폴더 생성
→ 우선순위가 높으므로 먼저 감지
→ 악의적인 볼트에 민감한 데이터 저장
```

**영향도**:
- 🔴 **HIGH**: 개발 노트에 API 키, 데이터베이스 자격증명 저장 가능
- 🔴 **HIGH**: Git 커밋 정보 / 아키텍처 결정사항 노출

---

#### 1-2. 파일 쓰기 입력 검증 부족

**파일**: `backend/app/services/obsidian_service.py:445-469`

```python
async def create_daily_note(self, title: str, content: Dict[str, Any]) -> bool:
    # Generate filename (sanitize title)
    safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)
    filename = f"{safe_title}.md"
    filepath = date_dir / filename

    # Build markdown with frontmatter
    markdown_lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            markdown_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
```

**문제점**:
- ❌ **경로 이동(Path Traversal) 미방어**: `../` 문자열이 제거되지 않음
  - `safe_title = "../../sensitive/../file"` → 유효함
  - 실제 경로: `vault/개발일지/2026-01-01/../../sensitive/../file.md` = `vault/sensitive/file.md`

- ❌ **YAML 인젝션 취약성**:
  ```yaml
  title: "value\nmalicious: injected_data"
  # 결과:
  title: value
  malicious: injected_data  # 인젝션된 필드
  ```

- ⚠️ **파일명 길이 제한 없음**: Windows MAX_PATH (260자) 초과 가능

**증명 코드**:
```python
# 공격자 입력
title = "../../../etc/passwd"  # Linux
title = "..\\..\\..\\Windows\\System32"  # Windows (미방어)

# 결과
filepath = vault/개발일지/2026-01-01/../../../etc/passwd.md
# 실제 경로: /etc/passwd.md (Obsidian 범위 외부!)
```

**영향도**:
- 🔴 **CRITICAL**: 시스템 파일 덮어쓰기 가능
- 🔴 **CRITICAL**: Obsidian 범위 외부 임의 파일 생성
- 🔴 **HIGH**: 설정 파일 손상 (`.env`, `config.yaml` 등)

---

#### 1-3. 읽기 권한 검증 부재

**파일**: `backend/app/services/obsidian_service.py:541-609`

```python
async def search_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    for note_file in date_dir.glob("*.md"):
        try:
            content = note_file.read_text(encoding="utf-8")  # 무조건 읽음
```

**문제점**:
- ❌ **접근 제어 없음**: 모든 파일 무조건 읽기 가능
- ⚠️ **민감한 정보 노출**: 개인 노트, 비밀 키, 기술 채무 기록

**영향도**:
- 🟡 **MEDIUM**: 민감 정보 공개

---

#### 1-4. Vault 경로 노출

**파일**: `backend/app/routers/obsidian.py:405-407`

```python
"vault_path": (
    str(obsidian_service.vault_path) if obsidian_service.vault_path else None
),
```

**문제점**:
- ⚠️ **경로 정보 공개**: 누군가 `/api/obsidian/health`를 호출하면 전체 경로 노출
- ⚠️ **정보 수집 공격**: 시스템 구조 파악 용이

---

### 완화 방안

#### 1-A. 환경변수 기반 설정 (필수)

```python
# ✅ 개선된 코드
def _get_vault_path(self) -> Optional[Path]:
    """환경변수에서 vault 경로 가져오기"""

    # 1. 환경변수 우선 (명시적 설정)
    env_vault = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_vault:
        path = Path(env_vault).resolve()
        if not path.exists():
            logger.error(f"OBSIDIAN_VAULT_PATH 설정이 존재하지 않음: {path}")
            return None

        # 권한 검증
        if not os.access(path, os.R_OK):
            logger.error(f"Vault 읽기 권한 없음: {path}")
            return None

        return path

    # 2. 개발 환경에서만 기본값 사용 (production 제외)
    env = os.environ.get("ENVIRONMENT", "development")
    if env == "production":
        logger.error("OBSIDIAN_VAULT_PATH 환경변수 필수 (프로덕션)")
        return None

    # 3. 개발: 사용자 선택 경로만 (auto-detect 제거)
    return None
```

**체크리스트**:
- [ ] `OBSIDIAN_VAULT_PATH` 환경변수 추가
- [ ] 프로덕션: 환경변수 필수
- [ ] 개발: 수동 설정 또는 에러

---

#### 1-B. 경로 이동(Path Traversal) 방어 (필수)

```python
# ✅ 안전한 파일명 생성
def _sanitize_filename(self, filename: str, max_length: int = 200) -> str:
    """
    파일명을 안전하게 정제합니다.
    - 경로 이동 문자 제거
    - 파일명 길이 제한
    - 위험한 문자 제거
    """
    import os.path

    # 1. 경로 이동 문자 제거 (../../ 등)
    filename = os.path.basename(filename)  # 경로 부분 제거

    # 2. 위험한 특수문자 제거
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(dangerous_chars, '-', filename)

    # 3. 숨겨진 파일명 제거
    if filename.startswith('.'):
        filename = filename.lstrip('.')

    # 4. 길이 제한 (Windows MAX_PATH 고려: 260자)
    # 확장자 포함 최대 255자 (NTFS)
    if len(filename) > max_length:
        # 명확한 UUID로 바꾸거나 길이 자르기
        base = filename[:max_length-4]  # .md 예약
        filename = f"{base}.md"

    # 5. 기본값 (완전히 무효한 경우)
    if not filename:
        filename = "note.md"

    return filename

# ✅ 파일 쓰기 보호
async def create_daily_note(self, title: str, content: Dict[str, Any]) -> bool:
    date_dir = self.daily_notes_dir / datetime.now().strftime("%Y-%m-%d")

    # 1. 안전한 파일명 정제
    safe_title = self._sanitize_filename(title)
    filepath = date_dir / safe_title

    # 2. 경로 확인 (vault 범위 내인지 검증)
    try:
        resolved = filepath.resolve()
        vault_resolved = self.vault_path.resolve()

        # 경로가 vault 내부인지 확인
        resolved.relative_to(vault_resolved)  # 범위 외면 exception
    except ValueError:
        logger.error(f"경로 범위 외: {resolved} (vault: {vault_resolved})")
        return False

    # 3. 파일 생성
    filepath.write_text(markdown, encoding="utf-8")
    return True
```

**적용**:
```bash
# Pydantic 입력 검증 추가
class ObsidianAutoSyncRequest(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=50,
                            pattern="^[a-z_]+$")  # 안전한 패턴
    data: Dict[str, Any] = Field(..., description="이벤트 데이터")

    # 커스텀 검증
    @validator('event_type')
    def validate_event_type(cls, v):
        allowed = {"phase_transition", "error_resolution", "task_completion",
                   "architecture_decision", "time_milestone"}
        if v not in allowed:
            raise ValueError(f"Invalid event type: {v}")
        return v
```

---

#### 1-C. Vault 경로 숨김 (권장)

```python
# ✅ API 응답에서 경로 제거
@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "healthy" if obsidian_service.vault_available else "degraded",
        "vault_available": obsidian_service.vault_available,
        # "vault_path": None,  # 제거!
        # "daily_notes_dir": None,  # 제거!
        "pending_events": len(obsidian_service.pending_events),
        "message": (
            "Obsidian vault accessible"
            if obsidian_service.vault_available
            else "Obsidian vault not found"
        ),
    }
```

---

### 완화 후 위험도

✅ **MEDIUM** → **LOW** (환경변수 + 경로 검증 + 입력 검증 후)

---

## 2️⃣ Auto-sync 스크립트 (`obsidian_auto_sync.py`)

### 위험도: **HIGH** 🔴

### 취약점 분석

#### 2-1. 환경변수 경로 검증 부재 (Path Traversal)

**파일**: `scripts/obsidian_auto_sync.py:115-156`

```python
session_file = Path(".udo/session_state.json")

# 문제: .udo/session_state.json은 어디를 가리키나?
# - 현재 작업 디렉토리 기반
# - 심볼릭 링크 추적 가능성
# - 상대 경로 공격 취약
```

**공격 시나리오**:
```bash
# 공격자가 심볼릭 링크 생성
cd /tmp
ln -s /etc/passwd .udo
git commit -m "test"
# → .udo/session_state.json 쓰기 시도
# → /etc/passwd 손상 가능성
```

**증거**:
```python
# 현재 코드 (줄 115, 136)
session_file = Path(".udo/session_state.json")  # ❌ 상대 경로
session_file.parent.mkdir(parents=True, exist_ok=True)  # ❌ 검증 없음
```

**영향도**:
- 🔴 **CRITICAL**: 시스템 파일 손상
- 🔴 **HIGH**: Git 저장소 손상

---

#### 2-2. Git Diff 입력 처리 (Command Injection)

**파일**: `scripts/obsidian_auto_sync.py:300-400 (추정)`

```bash
# post-commit hook에서 (줄 16-17)
COMMIT_MSG=$(git log -1 --pretty=%B)  # 사용자 입력
python scripts/obsidian_auto_sync.py --commit-hash "$COMMIT_HASH" 2>"$ERROR_LOG"
```

**문제점**:
- ⚠️ **Diff 데이터 검증 부재**: `git diff` 결과를 직접 분석
- ⚠️ **정규식 오버플로우 가능**: 큰 파일에서 성능 저하
- ✅ (좋은 점) 인자는 git 명령어를 통해 받으므로 직접 주입은 낮음

**잠재 위험**:
```python
# 예: 매우 큰 diff (50MB) 처리 시
output, error, exit_code = await self._run_command(
    cmd=["git", "diff", "HEAD"],  # 50MB 반환
    use_shell_on_windows=False
)
# → 메모리 부족 → DoS
```

---

#### 2-3. YAML 설정 파일 로드 (Deserialization Attack)

**파일**: `scripts/obsidian_auto_sync.py:200+`

```python
with open(config_file, "r", encoding="utf-8") as f:
    config = yaml.load(f)  # ❌ Unsafe YAML load!
```

**위험성**:
- 🔴 **CRITICAL**: YAML에 Python 코드 실행 가능
  ```yaml
  # malicious.yaml
  !!python/object/apply:os.system
  args: ['rm -rf /']
  ```

**수정**:
```python
# ✅ 안전한 YAML 로드
config = yaml.safe_load(f)  # 변수만 로드, 코드 실행 불가
```

---

#### 2-4. 로깅에 민감 정보 노출

**파일**: `scripts/obsidian_auto_sync.py:69-76`

```python
logger = logging.getLogger(__name__)

if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

**문제점**:
- ⚠️ 커밋 메시지가 로그에 기록됨
- ⚠️ 파일 경로가 노출됨
- ⚠️ Git diff 내용이 일부 노출될 수 있음

**예시**:
```
2025-12-29 10:15:23 - obsidian_auto_sync - INFO - Processing commit with API_KEY=sk-xxxxx...
```

---

### 완화 방안

#### 2-A. 절대 경로 사용 (필수)

```python
# ✅ 개선된 코드
import os

def get_session_file() -> Path:
    """안전한 세션 파일 경로 반환"""

    # 1. Git 저장소 루트 찾기
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True
        ).strip()
        repo_root = Path(git_root).resolve()
    except subprocess.CalledProcessError:
        raise RuntimeError("Not in a git repository")

    # 2. .udo 디렉토리 (git root 기준)
    session_dir = repo_root / ".udo"
    session_file = session_dir / "session_state.json"

    # 3. 경로 검증 (범위 확인)
    session_file_resolved = session_file.resolve()
    try:
        session_file_resolved.relative_to(repo_root.resolve())
    except ValueError:
        raise ValueError(f"Session file outside repo: {session_file_resolved}")

    return session_file
```

**적용**:
```python
# 줄 115 변경
session_file = get_session_file()
```

---

#### 2-B. YAML 안전 로드 (필수)

```python
# ✅ 안전한 YAML 로드
config = yaml.safe_load(f)  # 줄 200 변경

# ❌ 제거
# config = yaml.load(f)  # Unsafe!
```

---

#### 2-C. 로그 새니타이제이션 (권장)

```python
# ✅ 민감 정보 마스킹
def sanitize_commit_msg(msg: str) -> str:
    """커밋 메시지에서 민감 정보 제거"""
    # API 키 마스킹
    msg = re.sub(r'(sk_[a-zA-Z0-9]+)', '***API_KEY***', msg)
    msg = re.sub(r'(password|secret|token)[=:]\s*\S+', r'\1=***', msg)
    return msg

# 사용
safe_msg = sanitize_commit_msg(COMMIT_MSG)
logger.info(f"Processing commit: {safe_msg}")
```

---

### 완화 후 위험도

✅ **HIGH** → **MEDIUM** (절대 경로 + 안전 YAML + 로그 새니타이제이션 후)

---

## 3️⃣ Context7 캐싱

### 위험도: **MEDIUM** ⚠️

### 취약점 분석

#### 3-1. 로컬 캐시 암호화 부재

**파일**: 캐시 위치 (추정) `backend/.env`, `web-dashboard/lib/api-config.ts`

**문제점**:
- ⚠️ **디스크 상 평문**: 캐시된 API 응답이 암호화되지 않음
- ⚠️ **민감 정보 노출**: Context7에서 반환한 보안 관련 문서가 평문 저장

**공격 시나리오**:
```
공격자가 디스크 접근
→ 캐시 디렉토리 읽기
→ API 응답 내용 확인 (프롬프트, 피드백 등)
```

---

#### 3-2. Context7 API 키 관리

**문제점**:
- ⚠️ **환경변수 검증 부재**: `.env`에서 로드되지만 검증 없음
- ⚠️ **키 노출 위험**: Git에 `.env` 커밋 가능성

---

### 완화 방안

#### 3-A. 캐시 암호화 (권장)

```python
# ✅ 암호화 캐시
from cryptography.fernet import Fernet
import os

class EncryptedCache:
    def __init__(self):
        key = os.environ.get("CACHE_ENCRYPTION_KEY")
        if not key:
            raise ValueError("CACHE_ENCRYPTION_KEY 환경변수 필수")
        self.cipher = Fernet(key.encode())

    def save(self, key: str, value: str):
        encrypted = self.cipher.encrypt(value.encode())
        cache_file = Path(f".cache/{key}.enc")
        cache_file.write_bytes(encrypted)

    def load(self, key: str) -> Optional[str]:
        cache_file = Path(f".cache/{key}.enc")
        if not cache_file.exists():
            return None
        encrypted = cache_file.read_bytes()
        return self.cipher.decrypt(encrypted).decode()
```

---

#### 3-B. API 키 관리 (필수)

```bash
# .env.example (커밋)
CONTEXT7_API_KEY=change_me_in_production

# .env.local (git ignore)
CONTEXT7_API_KEY=sk_prod_xxxxx...
```

---

### 완화 후 위험도

✅ **MEDIUM** → **LOW** (캐시 암호화 + API 키 검증 후)

---

## 4️⃣ AI 생성 콘텐츠

### 위험도: **LOW** 🟢

### 취약점 분석

#### 4-1. 프롬프트 인젝션 리스크

**파일**: `backend/app/services/kanban_ai_service.py` (추정)

**문제점**:
- ⚠️ **낮은 확률**: AI가 사용자 입력을 파일에 직접 쓰지 않음
- ✅ (좋은 점) AI 출력은 Markdown 형식으로 정제됨

**시나리오**:
```
사용자가 태스크 제목: "```\nmalicious code\n```" 입력
→ AI가 이를 해석 가능
→ Markdown 파일에 코드 블록 추가
→ 읽는 사람이 코드 블록으로 인식 (문제 없음)
```

**결론**: 콘텐츠는 읽기 전용으로 사용되므로 실행 위험 낮음

---

#### 4-2. AI 오류 정보 노출

**위험성**: 낮음 (모니터링 권장)

---

### 권고사항

- ✅ 현재 상태 양호
- 📋 모니터링: AI 생성 콘텐츠 감시
- 🔍 정기 검토: 민감 정보 누출 여부

---

## 5️⃣ Git Hook 자동 실행

### 위험도: **HIGH** 🔴

### 취약점 분석

#### 5-1. Hook 무조건 실행 (강제성 없음)

**파일**: `.git/hooks/post-commit` (줄 50-116)

```bash
# 문제: 스크립트 실행에 실패해도 커밋은 성공
if [ "$SHOULD_SYNC" = true ]; then
    if python scripts/obsidian_auto_sync.py ... 2>"$ERROR_LOG"; then
        # 성공
    else
        # 실패 → 경고만 출력
        echo "[Obsidian Sync] Auto-sync v${SYNC_VERSION} failed..."
        # 커밋은 계속 진행됨! ❌
    fi
fi

# Hook은 exit code 0 반환 → Git 계속 진행
```

**문제점**:
- ⚠️ **Fallback 메커니즘**: 최대 3단계 재시도 후 포기
- ⚠️ **에러 기록**: `.git/hooks/obsidian_sync_errors.log`에 저장 (Git 관리 외)
- 🟡 **모니터링 부재**: 누가 에러를 보나?

**영향도**:
- 🟡 **MEDIUM**: 동기화 누락 가능 (데이터 손실 X, 기록 손실)
- ✅ (좋은 점) 커밋 자체는 실패하지 않음 (좋은 설계)

---

#### 5-2. 임시 파일 보안 위험

**파일**: `.git/hooks/post-commit:54`

```bash
ERROR_LOG=$(mktemp)  # ❌ 예측 가능한 임시 파일
cat "$ERROR_LOG"
rm -f "$ERROR_LOG"
```

**문제점**:
- ⚠️ **Race Condition**: 다른 프로세스가 파일 개수 중 접근 가능
- ⚠️ **정보 누출**: 에러 메시지가 임시 파일에 남음

**수정**:
```bash
# ✅ 안전한 임시 파일
ERROR_LOG=$(mktemp -d)/error.log  # 디렉토리 먼저 생성
trap "rm -rf $(dirname "$ERROR_LOG")" EXIT  # 정리 보장
```

---

#### 5-3. 스크립트 인젝션 위험

**파일**: `.git/hooks/post-commit:8-10`

```bash
COMMIT_MSG=$(git log -1 --pretty=%B)  # ❌ 저장
python scripts/session_automation.py checkpoint --notes "Commit: ${COMMIT_MSG:0:50}"
```

**위험성**:
- ⚠️ **저수준**: Git 명령어로 인자를 받으므로 직접 실행은 아님
- ✅ (좋은 점) `${COMMIT_MSG:0:50}` - 길이 제한 있음

---

### 완화 방안

#### 5-A. 에러 로깅 개선 (권장)

```bash
# ✅ 안전한 에러 기록
LOG_DIR=".git/hooks/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/$(date +%Y%m%d-%H%M%S)-obsidian.log"

# 에러 기록
{
    echo "=== Obsidian Sync Log ==="
    echo "Time: $(date)"
    echo "Commit: $COMMIT_HASH"
    echo "Files changed: $FILES_CHANGED"
    echo ""
    echo "Error output:"
    cat "$ERROR_LOG"
} >> "$LOG_FILE"

# 정리
rm -f "$ERROR_LOG"

# 로그 회전 (30일 이상 삭제)
find "$LOG_DIR" -name "*.log" -mtime +30 -delete
```

---

#### 5-B. Hook 실패 감지 대시보드 (권장)

```python
# ✅ Hook 에러 모니터링
@router.get("/api/obsidian/hook-health")
async def hook_health_check():
    """Git hook 건강도 확인"""
    log_dir = Path(".git/hooks/logs")

    if not log_dir.exists():
        return {"hook_status": "unknown", "recent_errors": []}

    # 최근 에러 로그 확인
    recent_logs = sorted(log_dir.glob("*.log"))[-10:]

    errors = []
    for log_file in recent_logs:
        content = log_file.read_text()
        if "failed" in content.lower():
            errors.append({
                "timestamp": log_file.stem,
                "preview": content[:200]
            })

    return {
        "hook_status": "healthy" if not errors else "degraded",
        "recent_errors": errors,
        "last_check": datetime.now().isoformat()
    }
```

---

### 완화 후 위험도

✅ **HIGH** → **MEDIUM** (에러 로깅 + 모니터링 대시보드 후)

---

## 종합 위험 매트릭스

| # | 기능 | 위협 | 영향 | 확률 | 위험도 | 완화 | 우선순위 |
|---|------|------|------|------|--------|------|---------|
| 1 | Vault 자동 감지 | Path Hijacking | CRITICAL | HIGH | CRITICAL | 환경변수 | **P0** |
| 2 | 경로 이동(Path Traversal) | 파일 손상 | CRITICAL | MEDIUM | HIGH | 입력 검증 | **P0** |
| 3 | YAML 불안전 로드 | Code Execution | CRITICAL | LOW | MEDIUM | safe_load | **P0** |
| 4 | 세션 파일 상대 경로 | Symlink Attack | CRITICAL | MEDIUM | HIGH | 절대 경로 | **P1** |
| 5 | Git Diff DoS | Service Outage | HIGH | LOW | MEDIUM | 크기 제한 | **P2** |
| 6 | 캐시 암호화 부재 | 정보 노출 | HIGH | MEDIUM | MEDIUM | 암호화 | **P1** |
| 7 | 로그 민감정보 | 정보 노출 | MEDIUM | MEDIUM | MEDIUM | 새니타이제이션 | **P2** |

---

## 즉시 조치 필요 (P0 - CRITICAL)

### ✅ 체크리스트 (생산성 배포 전 필수)

```
[  ] 1. Vault 경로 검증
    - OBSIDIAN_VAULT_PATH 환경변수 추가
    - 프로덕션: 강제
    - 권한 검증 구현

[  ] 2. Path Traversal 방어
    - os.path.basename() 사용
    - 경로 범위 검증 (resolve().relative_to())
    - 파일명 길이 제한 (255자)

[  ] 3. YAML 안전 로드
    - yaml.load() → yaml.safe_load()
    - 모든 YAML 로드 포인트 확인

[  ] 4. 세션 파일 절대 경로
    - git rev-parse --show-toplevel 사용
    - symlink 방어
    - 경로 검증

[  ] 5. 입력 검증 추가
    - Pydantic 패턴 검증
    - event_type 화이트리스트
    - 파일명 정제 함수 생성
```

---

## 권장 사항 (P1-P2)

```
[  ] 6. 캐시 암호화 (Fernet)
[  ] 7. 로그 새니타이제이션
[  ] 8. Hook 에러 모니터링 대시보드
[  ] 9. API 경로 정보 숨김 (/health)
[  ] 10. 정기 보안 감사 (월 1회)
```

---

## 테스트 계획

### Unit Tests (Path Traversal)

```python
def test_path_traversal_defense():
    """경로 이동 공격 방어 테스트"""

    # 테스트 케이스
    test_cases = [
        ("../../../etc/passwd", "etcpasswd"),  # 경로 제거
        ("./../../sensitive", "sensitive"),     # ./ 제거
        ("file\nmalicious", "filemalicious"),  # 줄바꿈 제거
        ("", "note"),  # 기본값
        ("a" * 300, "a" * 200),  # 길이 제한
    ]

    for input_title, expected in test_cases:
        result = sanitize_filename(input_title)
        assert result == expected, f"Failed for {input_title}"

def test_path_containment():
    """파일이 vault 범위 내인지 확인"""

    vault = Path("/vault").resolve()

    # 범위 내
    filepath = (vault / "note.md").resolve()
    assert is_within_vault(filepath, vault)

    # 범위 외
    filepath = (Path("/etc/passwd")).resolve()
    assert not is_within_vault(filepath, vault)

def test_symlink_attack():
    """심볼릭 링크 공격 방어"""

    # 임시 디렉토리 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir) / "vault"
        vault.mkdir()

        # 심볼릭 링크 생성
        os.symlink("/etc", vault / "evil")

        # 공격 시도
        filepath = (vault / "evil" / "passwd")

        # 검증 실패해야 함
        assert not is_within_vault(filepath.resolve(), vault)
```

---

## 배포 전 체크리스트

```
[ ] 코드 검토
    - 모든 file write 포인트 확인
    - 모든 YAML load 포인트 확인
    - 환경변수 검증 확인

[ ] 테스트
    - Unit tests: Path traversal (10개 케이스)
    - Unit tests: YAML safe_load (5개 케이스)
    - Integration tests: 전체 Obsidian 플로우
    - Security tests: Symlink, race condition

[ ] 문서화
    - 환경변수 가이드 (.env.example)
    - 보안 가정 문서화
    - 운영 가이드 (Hook 에러 처리)

[ ] 모니터링
    - Hook 에러 대시보드 활성화
    - 로그 수집 (Sentry/CloudWatch)
    - 알림 설정 (daily summary)
```

---

## 결론

### 현재 상태
- ❌ **프로덕션 배포 불가능**: 3개 CRITICAL 취약점
- ⚠️ **개발 환경 사용 가능**: 로컬 개발 + 신뢰할 수 있는 사용자
- 🔴 **팀 협업 위험**: 여러 개발자 환경에서 문제 가능

### 권고 로드맵

**Phase 1 (1주)**: P0 항목 수정
- Vault 경로 검증
- Path Traversal 방어
- YAML safe_load

**Phase 2 (2주)**: 테스트 + 배포
- Unit/Integration 테스트
- 코드 리뷰
- Staging 환경 검증

**Phase 3 (진행형)**: 모니터링
- Hook 대시보드
- 정기 감사
- 보안 업데이트

---

## 참고 자료

- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
- [OWASP YAML Injection](https://cheatsheetseries.owasp.org/cheatsheets/YAML_Injection_Cheat_Sheet.html)
- [Python pathlib Security](https://docs.python.org/3/library/pathlib.html)
- [Git Hooks Security](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

---

**감사 완료**: 2026-01-01
**담당**: Security Engineer (AI)
**상태**: 검토 대기 중
