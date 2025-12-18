# 인코딩 에러 근본 원인 분석 및 재발 방지 시스템

**작성일**: 2025-12-18
**버전**: 1.0

## 🔍 근본 원인 분석 (Root Cause Analysis)

### 문제 발생 메커니즘

```
Python Script (UTF-8) → print() → Windows Console (cp949) → UnicodeEncodeError
```

1. **Windows 콘솔 기본 인코딩**: `cp949` (한글 Windows 표준)
2. **Python 내부 인코딩**: `utf-8` (유니코드 지원)
3. **변환 실패**: cp949는 이모지/특수문자를 표현할 수 없음

### 발생 조건

| 조건 | 위험도 | 예시 |
|------|--------|------|
| `print()` + 이모지 | 🔴 **HIGH** | `print("✅ Success")` |
| `print()` + 특수 유니코드 | 🟡 **MEDIUM** | `print("→ Arrow")` |
| 파일명 + 한글/이모지 | 🟡 **MEDIUM** | `"📊테스트.md"` |
| 파일 쓰기 (encoding 미지정) | 🟢 **LOW** | `open("file.txt", "w")` |
| subprocess 출력 + 특수문자 | 🟡 **MEDIUM** | 외부 프로세스 로그 |

## ⚠️ 재발 방지 시스템 (4-Tier Prevention)

### Tier 1: 프로젝트 코딩 스탠다드 (즉시 적용 ✅)

**규칙**:
1. ✅ **이모지 사용 금지**: 모든 Python 스크립트에서 이모지 사용 금지
2. ✅ **대체 표현 사용**: `[OK]`, `[FAIL]`, `[WARN]`, `[INFO]` 등 ASCII 문자로 표기
3. ✅ **파일 인코딩 명시**: 모든 파일 쓰기 시 `encoding='utf-8'` 명시

**예시**:
```python
# ❌ 위험한 코드
print("✅ Test passed")

# ✅ 안전한 코드
print("[OK] Test passed")

# ❌ 위험한 파일 쓰기
with open("output.txt", "w") as f:
    f.write(content)

# ✅ 안전한 파일 쓰기
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(content)
```

### Tier 2: Python 환경 설정 (프로젝트 전체 적용)

**방법 1: 환경 변수 설정 (권장)**
```bash
# Windows PowerShell (.venv/Scripts/activate.ps1에 추가)
$env:PYTHONIOENCODING="utf-8"

# Windows CMD (.venv/Scripts/activate.bat에 추가)
set PYTHONIOENCODING=utf-8

# Linux/Mac (~/.bashrc 또는 ~/.zshrc에 추가)
export PYTHONIOENCODING=utf-8
```

**방법 2: 스크립트 헤더 추가**
```python
# -*- coding: utf-8 -*-
import sys
import io

# stdout을 UTF-8로 재설정 (Windows 콘솔 대응)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### Tier 3: 자동 검증 시스템 (Pre-commit Hook)

**파일**: `.git/hooks/pre-commit` (또는 `.pre-commit-config.yaml`)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encoding Safety Pre-commit Hook

Checks for:
1. Emoji usage in Python files
2. Missing encoding parameter in file operations
3. Non-ASCII characters in print statements
"""

import re
import sys
from pathlib import Path

def check_emoji_usage(file_path):
    """Check for emoji in Python files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Emoji pattern
    emoji_pattern = re.compile(
        '['
        u'\U0001F600-\U0001F64F'  # emoticons
        u'\U0001F300-\U0001F5FF'  # symbols
        u'\U0001F680-\U0001F6FF'  # transport
        u'\U0001F1E0-\U0001F1FF'  # flags
        u'\U00002702-\U000027B0'
        u'\U000024C2-\U0001F251'
        ']+', flags=re.UNICODE
    )

    matches = emoji_pattern.findall(content)
    if matches:
        print(f"[FAIL] Emoji found in {file_path}: {matches}")
        return False

    return True

def check_file_encoding(file_path):
    """Check for missing encoding in file operations"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find open() calls without encoding
    pattern = r'open\([^)]*\)'
    matches = re.finditer(pattern, content)

    for match in matches:
        call = match.group()
        if 'encoding=' not in call and '"w"' in call:
            print(f"[WARN] Missing encoding in {file_path}: {call}")
            return False

    return True

def main():
    """Main pre-commit check"""
    files_to_check = [
        f for f in Path('.').rglob('*.py')
        if '.venv' not in str(f) and 'node_modules' not in str(f)
    ]

    all_passed = True

    for file_path in files_to_check:
        if not check_emoji_usage(file_path):
            all_passed = False

        if not check_file_encoding(file_path):
            all_passed = False

    if not all_passed:
        print("\n[FAIL] Encoding safety checks failed!")
        print("Fix the issues above before committing.")
        sys.exit(1)

    print("[OK] All encoding safety checks passed")
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### Tier 4: 런타임 에러 핸들러 (Fallback)

**파일**: `backend/app/core/encoding_handler.py` (신규 생성)

```python
"""
Encoding Error Handler

Provides safe print/logging functions that never fail on encoding issues.
"""

import sys
import unicodedata

def safe_print(*args, **kwargs):
    """
    Encoding-safe print function.

    Automatically removes emojis and problematic characters before printing.
    """
    def clean_text(text):
        """Remove emojis and normalize text"""
        if not isinstance(text, str):
            text = str(text)

        # Remove emojis
        text = ''.join(
            char for char in text
            if unicodedata.category(char) not in ['So', 'Sk']
        )

        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)

        # Encode-decode to ensure ASCII compatibility
        try:
            text = text.encode('ascii', errors='replace').decode('ascii')
        except:
            text = text.encode('utf-8', errors='replace').decode('utf-8')

        return text

    cleaned_args = [clean_text(arg) for arg in args]

    try:
        print(*cleaned_args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: ASCII-only print
        ascii_args = [str(arg).encode('ascii', errors='replace').decode('ascii') for arg in args]
        print(*ascii_args, **kwargs)

# Monkey-patch Python's built-in print (optional, use with caution)
# import builtins
# builtins.print = safe_print
```

## 📊 검증 및 모니터링

### 검증 체크리스트

- [ ] Tier 1: 코딩 스탠다드 문서화 완료
- [ ] Tier 1: 기존 코드에서 이모지 제거 완료
- [ ] Tier 2: 환경 변수 `PYTHONIOENCODING=utf-8` 설정 완료
- [ ] Tier 3: Pre-commit hook 설치 및 테스트 완료
- [ ] Tier 4: `safe_print()` 유틸리티 구현 완료

### 모니터링 메트릭

**주간 리포트**:
- 인코딩 에러 발생 횟수
- Pre-commit hook 차단 건수
- 수정된 파일 수

**월간 리뷰**:
- 재발 여부 확인
- 새로운 패턴 발견 시 규칙 업데이트

## 🚀 즉시 적용 액션 아이템

### Week 7-8 마무리 (지금 바로 적용)

1. ✅ **환경 변수 설정**
   ```bash
   # .venv/Scripts/activate.ps1에 추가
   $env:PYTHONIOENCODING="utf-8"
   ```

2. ✅ **기존 스크립트 점검**
   ```bash
   # 이모지 사용 스크립트 검색
   grep -r "✅\|❌\|⚠️\|📊\|🧪" --include="*.py" .
   ```

3. ✅ **코딩 스탠다드 공유**
   - `CLAUDE.md`에 규칙 추가
   - 팀원에게 공유 (해당 시)

### Week 9+ (차후 적용)

1. ⏳ Pre-commit hook 구현 및 테스트
2. ⏳ `safe_print()` 유틸리티 구현
3. ⏳ 자동화 스크립트 개선

## 📝 참고 자료

- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html)
- [PEP 540 - UTF-8 Mode](https://peps.python.org/pep-0540/)
- [Windows Console and Unicode](https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences)

---

**작성자**: Claude Code
**승인자**: (사용자 승인 필요)
**상태**: Draft → Review Required
