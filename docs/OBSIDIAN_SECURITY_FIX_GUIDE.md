# Obsidian 보안 취약점 수정 가이드

**대상**: 개발팀
**난이도**: Intermediate
**예상 시간**: 8-12시간
**우선순위**: P0 (배포 전 필수)

---

## 빠른 시작 (30분)

3개 CRITICAL 취약점만 수정하는 최소 경로:

### 1단계: YAML 안전 로드 (5분)

**파일**: `scripts/obsidian_auto_sync.py`

```diff
- config = yaml.load(f)
+ config = yaml.safe_load(f)
```

### 2단계: 환경변수 설정 (5분)

**파일**: `.env` 생성/수정

```bash
# 프로덕션
OBSIDIAN_VAULT_PATH=/absolute/path/to/vault
ENVIRONMENT=production

# 개발
ENVIRONMENT=development
```

### 3단계: 경로 검증 추가 (20분)

**파일**: `backend/app/services/obsidian_service.py`

복사/붙여넣기로 아래 함수를 추가합니다:

```python
def _sanitize_filename(self, filename: str, max_length: int = 200) -> str:
    """파일명을 안전하게 정제합니다."""
    import os.path
    filename = os.path.basename(filename)
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(dangerous_chars, '-', filename)
    if filename.startswith('.'):
        filename = filename.lstrip('.')
    if len(filename) > max_length:
        filename = f"{filename[:max_length-4]}.md"
    if not filename:
        filename = "note.md"
    return filename
```

그리고 `create_daily_note()` 메서드에서:

```diff
- safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)
+ safe_title = self._sanitize_filename(title)
```

---

## 상세 수정 가이드

### 수정 1: YAML 안전 로드 (CRITICAL)

**파일**: `scripts/obsidian_auto_sync.py`
**행**: ~200 (config 로드 부분)

#### 현재 코드 (위험)
```python
import yaml

with open(config_file, "r") as f:
    config = yaml.load(f)  # ❌ 위험!
    # YAML에 Python 코드 실행 가능
    # !!python/object/apply:os.system
    # args: ['rm -rf /']
```

#### 수정된 코드 (안전)
```python
import yaml

with open(config_file, "r") as f:
    config = yaml.safe_load(f)  # ✅ 안전!
    # YAML 데이터만 로드, 코드 실행 불가
```

#### 검증 테스트
```bash
# 이전: 악의적인 YAML로 테스트
cat > /tmp/test.yaml << 'EOF'
!!python/object/apply:os.system
args: ['touch /tmp/pwned']
EOF

python -c "
import yaml
with open('/tmp/test.yaml') as f:
    yaml.load(f, Loader=yaml.FullLoader)  # ❌ /tmp/pwned 생성됨
"

# 이후: safe_load로 테스트
python -c "
import yaml
with open('/tmp/test.yaml') as f:
    yaml.safe_load(f)  # ✅ 에러 (구성할 수 없음)
"
```

---

### 수정 2: Vault 경로 검증 (CRITICAL)

**파일**: `backend/app/services/obsidian_service.py`
**현재 위험**: 하드코딩된 경로 + 자동 감지

#### 문제 분석

```python
# 현재 코드 (줄 68-89)
def _auto_detect_vault(self) -> Optional[Path]:
    common_paths = [
        Path(r"C:\Users\user\Documents\Obsidian Vault"),  # ❌ 개인 경로
        Path.home() / "Documents" / "Obsidian Vault",      # ❌ auto-detect
        # ...
    ]
    for path in common_paths:
        if path.exists():  # ❌ 권한 검증 없음
            return path
```

**문제점**:
1. 하드코딩된 개인 경로 노출
2. 경로 하이재킹 (공격자가 같은 경로에 악의적 폴더 생성)
3. 권한 검증 없음
4. 우선순위 기반 선택 (조작 가능)

#### 수정 방법

**1단계**: `__init__` 메서드 수정

```python
def __init__(self, vault_path: Optional[Path] = None, debounce_window: int = 3):
    """Initialize Obsidian Service"""

    if vault_path:
        self.vault_path = self._validate_vault_path(vault_path)
    else:
        # 환경변수 우선, auto-detect 제거
        self.vault_path = self._get_vault_from_env()

    # Validate vault exists
    if not self.vault_path or not self.vault_path.exists():
        logger.warning(f"Obsidian vault not found at: {self.vault_path}")
        self.vault_available = False
    else:
        logger.info(f"Obsidian vault detected at: {self.vault_path}")
        self.vault_available = True

    # ... 나머지 코드
```

**2단계**: 새 헬퍼 메서드 추가

```python
def _validate_vault_path(self, path: Path) -> Optional[Path]:
    """Vault 경로 검증"""
    try:
        resolved = path.resolve()

        # 1. 경로 존재 확인
        if not resolved.exists():
            logger.error(f"Vault path does not exist: {resolved}")
            return None

        # 2. Obsidian 폴더 마커 확인 (.obsidian 디렉토리)
        if not (resolved / ".obsidian").exists():
            logger.error(f"Not a valid Obsidian vault (no .obsidian directory): {resolved}")
            return None

        # 3. 읽기 권한 확인
        if not os.access(resolved, os.R_OK):
            logger.error(f"No read permission for vault: {resolved}")
            return None

        # 4. 쓰기 권한 확인
        if not os.access(resolved, os.W_OK):
            logger.error(f"No write permission for vault: {resolved}")
            return None

        logger.info(f"Vault path validated: {resolved}")
        return resolved

    except Exception as e:
        logger.error(f"Error validating vault path: {e}")
        return None


def _get_vault_from_env(self) -> Optional[Path]:
    """환경변수에서 Vault 경로 가져오기"""
    import os

    env_vault = os.environ.get("OBSIDIAN_VAULT_PATH")

    if not env_vault:
        # 프로덕션에서는 필수
        env = os.environ.get("ENVIRONMENT", "development")
        if env == "production":
            logger.error("OBSIDIAN_VAULT_PATH environment variable required in production")
            return None

        # 개발 환경: auto-detect 제거 (명시적 요청 필요)
        logger.warning("OBSIDIAN_VAULT_PATH not set. Please set it explicitly.")
        return None

    return self._validate_vault_path(Path(env_vault))
```

**3단계**: auto-detect 메서드 제거

```diff
- def _auto_detect_vault(self) -> Optional[Path]:
-     """Auto-detect Obsidian vault location"""
-     # ... 모두 제거
```

#### 테스트

```python
def test_vault_validation():
    """Vault 경로 검증 테스트"""
    import tempfile
    import os

    # 임시 vault 생성
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir) / "Vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        # 1. 유효한 경로
        service = ObsidianService(vault_path=vault)
        assert service.vault_available
        assert service.vault_path == vault.resolve()

        # 2. .obsidian 없는 경로
        no_marker = Path(tmpdir) / "NoMarker"
        no_marker.mkdir()
        service = ObsidianService(vault_path=no_marker)
        assert not service.vault_available

        # 3. 존재하지 않는 경로
        service = ObsidianService(vault_path=Path("/nonexistent"))
        assert not service.vault_available
```

---

### 수정 3: Path Traversal 방어 (CRITICAL)

**파일**: `backend/app/services/obsidian_service.py`
**행**: `create_daily_note()` 메서드 (줄 425-469)

#### 현재 문제 코드

```python
# ❌ 위험한 코드
safe_title = re.sub(r'[<>:"/\\|?*]', '-', title)  # 불완전한 정제
filename = f"{safe_title}.md"
filepath = date_dir / filename  # 경로 검증 없음
filepath.write_text(markdown)  # 범위 외부 쓰기 가능
```

**공격 예시**:
```
title = "../../../etc/passwd"
safe_title = "../../../etc/passwd"  # 정규식이 이것을 통과시킴
filepath = vault/개발일지/2026-01-01/../../../etc/passwd.md
실제 경로 = /etc/passwd.md  # Vault 범위 외!
```

#### 수정된 코드

```python
async def create_daily_note(self, title: str, content: Dict[str, Any]) -> bool:
    """Create structured daily note in Obsidian vault (SECURE)"""

    if not self.vault_available:
        logger.warning("Obsidian vault not available")
        return False

    try:
        # 1. 안전한 파일명 생성
        safe_title = self._sanitize_filename(title)

        # 2. 경로 구성 (날짜 기반 안전한 위치)
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_dir = self.daily_notes_dir / date_str
        filepath = date_dir / safe_title

        # 3. ✅ 경로 범위 검증 (CRITICAL)
        try:
            # resolve(): 심볼릭 링크 해석, 상대 경로 절대화
            resolved_filepath = filepath.resolve()
            resolved_vault = self.vault_path.resolve()

            # 파일이 vault 내부인지 확인
            # 범위 외면 ValueError 발생
            resolved_filepath.relative_to(resolved_vault)

        except ValueError:
            # 범위 외부 접근 시도
            logger.error(
                f"Path traversal detected! "
                f"Attempted: {resolved_filepath} "
                f"Vault: {resolved_vault}"
            )
            return False

        # 4. 디렉토리 생성
        date_dir.mkdir(parents=True, exist_ok=True)

        # 5. 마크다운 생성
        markdown_lines = ["---"]

        frontmatter = content.get("frontmatter", {})
        for key, value in frontmatter.items():
            if isinstance(value, list):
                markdown_lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
            else:
                markdown_lines.append(f"{key}: {value}")

        markdown_lines.append("---")
        markdown_lines.append("")
        markdown_lines.append(f"# {title}")
        markdown_lines.append("")
        markdown_lines.append(content.get("content", ""))

        # 6. 파일 쓰기 (경로 검증 후에만 실행)
        filepath.write_text("\n".join(markdown_lines), encoding="utf-8")

        logger.info(f"Created daily note: {filepath}")
        return True

    except Exception as e:
        logger.error(f"Failed to create daily note: {e}", exc_info=True)
        return False


def _sanitize_filename(self, filename: str, max_length: int = 200) -> str:
    """
    파일명을 안전하게 정제합니다.

    1. 경로 이동 제거 (../, .\\, 등)
    2. 위험한 특수문자 제거
    3. 길이 제한
    4. 숨겨진 파일명 제거

    Args:
        filename: 정제할 파일명
        max_length: 최대 길이 (기본 200자)

    Returns:
        정제된 파일명
    """
    import os.path

    # 1. 경로 부분 제거 (os.path.basename이 핵심!)
    # "../../etc/passwd" → "passwd"
    # "subfolder/file" → "file"
    filename = os.path.basename(filename)

    # 2. 위험한 특수문자 제거
    # Windows: < > : " / \ | ? *
    # Unix/Linux: NUL (\x00) 문자
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(dangerous_chars, '-', filename)

    # 3. 숨겨진 파일명 제거 (.bashrc, .env 등)
    while filename.startswith('.'):
        filename = filename[1:]

    # 4. 길이 제한 (Windows NTFS: 255자)
    # ".md" (3자) + 콘텐츠 + 경로 길이 고려
    if len(filename) > max_length:
        # 안전하게 자르기
        base = filename[:max_length-4]  # .md 예약
        filename = f"{base}.md"

    # 5. 기본값 (완전히 정제된 후에도 비어있으면)
    if not filename or filename == '.md':
        filename = "note.md"

    return filename
```

#### 테스트 케이스

```python
def test_path_traversal_defense():
    """경로 이동 공격 방어 테스트"""
    from backend.app.services.obsidian_service import ObsidianService

    service = ObsidianService()

    # 테스트 케이스: (입력, 기대 출력)
    test_cases = [
        # 기본 케이스
        ("my-note", "my-note.md"),
        ("my note with spaces", "my-note-with-spaces.md"),

        # 경로 이동 공격
        ("../../../etc/passwd", "passwd.md"),  # ✅ 경로 제거
        ("..\\..\\..\\Windows\\System32", "System32.md"),  # Windows
        ("./../../sensitive", "sensitive.md"),
        ("folder/file", "file.md"),  # 폴더 부분 제거

        # 위험한 특수문자
        ('<script>alert("xss")</script>', '-script-alert--xss---script-.md'),
        ('file:///etc/passwd', 'fileetcpasswd.md'),
        ('file\x00null', 'file-null.md'),

        # 여러 점
        ("......./file", "file.md"),

        # 길이 제한
        ("a" * 300, "a" * 196 + ".md"),  # 200자 제한

        # 기본값
        ("", "note.md"),  # 빈 문자열
        ("...", "note.md"),  # 점만 있음
    ]

    for input_filename, expected in test_cases:
        result = service._sanitize_filename(input_filename)
        assert result == expected, f"Failed for '{input_filename}': got '{result}', expected '{expected}'"
        print(f"✅ {input_filename} → {result}")

    print("All path traversal tests passed!")


async def test_path_containment():
    """파일이 vault 범위 내인지 확인"""
    import tempfile
    from pathlib import Path
    from backend.app.services.obsidian_service import ObsidianService

    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir) / "Vault"
        vault.mkdir()
        (vault / ".obsidian").mkdir()

        service = ObsidianService(vault_path=vault)

        # 정상 경로
        date_dir = vault / "개발일지" / "2026-01-01"
        date_dir.mkdir(parents=True, exist_ok=True)

        # 공격: ../ 포함
        title = "../../../etc/passwd"
        success = await service.create_daily_note(title, {
            "frontmatter": {},
            "content": "test"
        })

        # create_daily_note가 실패해야 함
        # (내부에서 경로 검증으로 인해)
        # 또는 safely sanitized 파일이 생성되어야 함

        # 생성된 파일 확인
        files = list(date_dir.glob("*.md"))
        print(f"Created files: {[f.name for f in files]}")

        # passwd.md가 /etc/passwd로 생성되지 않았는지 확인
        assert not Path("/etc/passwd.md").exists(), "Path traversal succeeded!"
        print("✅ Path containment test passed")
```

---

### 수정 4: 세션 파일 절대 경로 (CRITICAL)

**파일**: `scripts/obsidian_auto_sync.py`
**행**: ~115, 136

#### 현재 문제

```python
# ❌ 상대 경로 (현재 작업 디렉토리 기반)
session_file = Path(".udo/session_state.json")
session_file.parent.mkdir(parents=True, exist_ok=True)  # .udo 디렉토리 생성
```

**Symlink 공격 시나리오**:
```bash
# 공격자가 심볼릭 링크 생성
cd /tmp
ln -s /etc .udo
git commit -m "test"
# → .udo/session_state.json 쓰기 시도
# → 실제로 /etc/session_state.json에 쓰여짐!
```

#### 수정 방법

```python
import subprocess
import os
from pathlib import Path

def get_git_repo_root() -> Path:
    """Git 저장소 루트 경로를 안전하게 가져옵니다."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        repo_root = Path(result.stdout.strip()).resolve()
        return repo_root
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        raise RuntimeError("Not in a Git repository or Git not found")


def get_session_file() -> Path:
    """세션 상태 파일 경로를 안전하게 가져옵니다."""

    # 1. Git 루트 가져오기 (symlink 해석됨)
    repo_root = get_git_repo_root()

    # 2. .udo 디렉토리 (절대 경로!)
    session_dir = repo_root / ".udo"
    session_file = session_dir / "session_state.json"

    # 3. 경로 범위 검증 (범위 외부 symlink 확인)
    try:
        resolved = session_file.resolve()
        resolved.relative_to(repo_root)  # 범위 내인지 확인
    except ValueError:
        raise ValueError(
            f"Session file outside repository: {resolved}\n"
            f"Repository: {repo_root}\n"
            "Possible symlink attack detected!"
        )

    return session_file


# 사용 예시
# 이전:
# session_file = Path(".udo/session_state.json")  # ❌

# 이후:
session_file = get_session_file()  # ✅
```

#### 테스트

```bash
#!/bin/bash
# 테스트: Symlink 공격 시나리오

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
TEST_DIR=$(mktemp -d)

trap "rm -rf $TEST_DIR" EXIT

cd "$TEST_DIR"

# 1. 공격 시뮬레이션: 심볼릭 링크 생성
mkdir -p evil_vault
ln -s evil_vault .udo  # ❌ .udo → evil_vault 심볼릭 링크

# 2. 스크립트 실행 (안전해야 함)
if python "$REPO_ROOT/scripts/obsidian_auto_sync.py" ... 2>/dev/null; then
    echo "❌ VULNERABLE: Symlink attack succeeded!"
    exit 1
else
    echo "✅ SAFE: Symlink attack blocked"
    exit 0
fi
```

---

### 수정 5: 입력 검증 강화 (권장)

**파일**: `backend/app/models/obsidian_sync.py`

```python
from pydantic import BaseModel, Field, validator

class ObsidianAutoSyncRequest(BaseModel):
    """✅ 입력 검증이 추가된 모델"""

    # 이전: 제약 없음
    # event_type: str

    # 이후: 제약 추가
    event_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern="^[a-z_]+$",  # 소문자 + 언더스코어만
        description="Event type (lowercase_with_underscores)"
    )

    data: dict = Field(
        ...,
        max_items=100,  # 최대 100개 필드
        description="Event data"
    )

    @validator('event_type')
    def validate_event_type(cls, v):
        """화이트리스트 기반 검증"""
        allowed = {
            "phase_transition",
            "error_resolution",
            "task_completion",
            "architecture_decision",
            "time_milestone"
        }
        if v not in allowed:
            raise ValueError(f"Invalid event_type: {v}. Allowed: {allowed}")
        return v

    @validator('data')
    def validate_data_size(cls, v):
        """Data 크기 제한"""
        import json
        size = len(json.dumps(v))
        max_size = 10_000  # 10KB
        if size > max_size:
            raise ValueError(f"Data too large: {size} > {max_size}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "task_completion",
                "data": {
                    "task_title": "Fix security vulnerability",
                    "duration_minutes": 45
                }
            }
        }
```

---

## 완료 체크리스트

```
[ ] 1. YAML 안전 로드
    - [ ] yaml.load() → yaml.safe_load() 변경
    - [ ] 모든 YAML 로드 포인트 확인
    - [ ] 테스트: safe_load 동작 확인

[ ] 2. Vault 경로 검증
    - [ ] 환경변수 OBSIDIAN_VAULT_PATH 추가
    - [ ] _validate_vault_path() 메서드 구현
    - [ ] _get_vault_from_env() 메서드 구현
    - [ ] auto-detect 제거
    - [ ] 테스트: 유효/무효 경로 테스트

[ ] 3. Path Traversal 방어
    - [ ] _sanitize_filename() 메서드 구현
    - [ ] create_daily_note()에 경로 범위 검증 추가
    - [ ] 테스트: 10개 경로 이동 케이스 확인
    - [ ] 테스트: 범위 내/외 파일 확인

[ ] 4. 세션 파일 절대 경로
    - [ ] get_git_repo_root() 함수 구현
    - [ ] get_session_file() 함수 구현
    - [ ] 모든 .udo/session_state.json 참조 업데이트
    - [ ] 테스트: Symlink 공격 테스트

[ ] 5. 입력 검증 (권장)
    - [ ] ObsidianAutoSyncRequest에 pattern 추가
    - [ ] validate_event_type() 구현
    - [ ] validate_data_size() 구현
    - [ ] 테스트: 유효/무효 이벤트 타입

[ ] 6. .env 파일 업데이트
    - [ ] OBSIDIAN_VAULT_PATH 추가
    - [ ] ENVIRONMENT 추가 (development/production)
    - [ ] .env.example 생성

[ ] 7. 테스트 실행
    - [ ] Unit tests 모두 통과
    - [ ] Integration tests 모두 통과
    - [ ] 보안 테스트 모두 통과

[ ] 8. 코드 리뷰
    - [ ] 수정 사항 리뷰
    - [ ] 보안 리뷰
    - [ ] 성능 영향 확인

[ ] 9. 문서화
    - [ ] README 업데이트 (환경변수 설명)
    - [ ] SECURITY.md 생성
    - [ ] 운영 가이드 생성

[ ] 10. 배포
    - [ ] Staging 환경 배포
    - [ ] 스모크 테스트
    - [ ] Production 배포
```

---

## 문제 해결

### "ModuleNotFoundError: No module named 'yaml'"

```bash
pip install pyyaml
```

### "Path Traversal Test Failed"

경로 정제 함수의 순서 확인:
1. `os.path.basename()` ← **먼저** (경로 부분 제거)
2. `re.sub()` ← 다음 (특수문자 제거)
3. 길이 제한 ← 마지막

### Symlink 테스트 실패

Windows에서는 Symlink 권한 필요:
```powershell
# 관리자 권한으로 실행
New-Item -ItemType SymbolicLink -Path "test_link" -Target "test_target"
```

---

## 참고 자료

- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- Python pathlib 문서: https://docs.python.org/3/library/pathlib.html
- YAML 안전성: https://yaml.org/type/python/
- Symlink 공격: https://owasp.org/www-community/attacks/Insecure_Temporary_File
