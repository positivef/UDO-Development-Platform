#!/usr/bin/env python
"""
Obsidian Auto-Sync v2.0 - AI-Enhanced Development Log Generator

자동으로 Git commit 정보를 분석하여 Obsidian 개발일지를 생성합니다.

Features (v2.0):
- 트리거 조건 자동 감지 (3+ 파일, feat:/fix: 메시지)
- AI 인사이트 자동 생성 (배운 점, 시행착오, 다음 단계)
- 시간대별 작업 내역 추론
- YAML frontmatter 자동 생성

Usage:
  python scripts/obsidian_auto_sync.py --commit-hash <hash>
  python scripts/obsidian_auto_sync.py --commit-hash HEAD

Requirements:
- Git repository
- Obsidian vault configured in environment or default location

Author: System Automation Team
Date: 2025-12-14
Version: 2.0.0
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ObsidianAutoSync:
    """Obsidian 자동 동기화 클래스"""

    def __init__(self, repo_root: Path, vault_path: Optional[Path] = None):
        self.repo_root = repo_root
        self.vault_path = vault_path or self._get_default_vault_path()
        self.dev_log_dir = self.vault_path / "개발일지"

    def _get_default_vault_path(self) -> Path:
        """기본 Obsidian vault 경로 가져오기"""
        # 환경 변수에서 먼저 확인
        vault_env = os.getenv("OBSIDIAN_VAULT_PATH")
        if vault_env:
            return Path(vault_env)

        # Windows 기본 경로
        default_path = Path.home() / "Documents" / "Obsidian Vault"
        if default_path.exists():
            return default_path

        # Fallback
        return Path.home() / "obsidian-vault"

    def get_commit_info(self, commit_hash: str) -> Dict:
        """커밋 정보 가져오기"""
        try:
            # 커밋 메시지
            message = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%B", commit_hash],
                cwd=self.repo_root,
                encoding='utf-8',
                errors='replace'
            ).strip()

            # 커밋 시간
            commit_time = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%ai", commit_hash],
                cwd=self.repo_root,
                encoding='utf-8',
                errors='replace'
            ).strip()

            # 변경 파일 목록
            files_changed = subprocess.check_output(
                ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                cwd=self.repo_root,
                encoding='utf-8',
                errors='replace'
            ).strip().split('\n')

            # 통계
            stats = subprocess.check_output(
                ["git", "log", "-1", "--stat", commit_hash],
                cwd=self.repo_root,
                encoding='utf-8',
                errors='replace'
            ).strip()

            # diff (간단한 버전)
            diff = subprocess.check_output(
                ["git", "show", "--stat", commit_hash],
                cwd=self.repo_root,
                encoding='utf-8',
                errors='replace'
            ).strip()

            return {
                "hash": commit_hash,
                "message": message,
                "time": commit_time,
                "files_changed": [f for f in files_changed if f],
                "stats": stats,
                "diff": diff
            }
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to get commit info: {e}", file=sys.stderr)
            return {}

    def check_trigger_conditions(self, commit_info: Dict) -> Tuple[bool, str]:
        """트리거 조건 확인"""
        files_count = len(commit_info.get("files_changed", []))
        message = commit_info.get("message", "")

        # 조건 1: 3개 이상 파일 변경
        if files_count >= 3:
            return True, f"{files_count} files changed (>=3)"

        # 조건 2: feat:/fix:/docs: 등 커밋 메시지
        trigger_patterns = [
            r"^feat:", r"^feature:", r"^fix:", r"^bug:",
            r"^docs:", r"^refactor:", r"^analyze:", r"^analysis:"
        ]

        for pattern in trigger_patterns:
            if re.match(pattern, message, re.IGNORECASE):
                return True, f"Commit message matches: {pattern}"

        return False, f"No trigger (files: {files_count}, message: {message[:30]}...)"

    def generate_ai_insights(self, commit_info: Dict) -> Dict[str, List[str]]:
        """AI 인사이트 자동 생성 (패턴 기반)"""
        files = commit_info.get("files_changed", [])
        message = commit_info.get("message", "")
        diff = commit_info.get("diff", "")

        insights = {
            "learned": [],
            "challenges": [],
            "next_steps": []
        }

        # 배운 점 추출
        if any("test" in f.lower() for f in files):
            insights["learned"].append("TDD 방식으로 테스트 우선 작성")

        if "refactor" in message.lower():
            insights["learned"].append("코드 구조 개선을 통한 유지보수성 향상")

        if any(keyword in message.lower() for keyword in ["performance", "optimize"]):
            insights["learned"].append("성능 최적화 기법 적용")

        if any(keyword in message.lower() for keyword in ["security", "auth"]):
            insights["learned"].append("보안 강화 방법 학습")

        if len(files) >= 5:
            insights["learned"].append("체계적인 개발 프로세스 적용 (다수 파일 동시 작업)")

        # 시행착오 감지
        if "fix" in message.lower():
            insights["challenges"].append(f"문제 발견: {message.split(':')[0]} → 해결 완료")

        if len(files) > 10:
            insights["challenges"].append("대규모 변경으로 인한 복잡도 관리")

        # 다음 단계 (TODO 주석 추출)
        todo_pattern = r"#\s*TODO:?\s*(.+)"
        todos_found = re.findall(todo_pattern, diff)
        if todos_found:
            insights["next_steps"].extend([f"TODO: {todo}" for todo in todos_found[:3]])

        # 기본 다음 단계
        if "feat" in message.lower():
            insights["next_steps"].append("통합 테스트 실행")

        if "fix" in message.lower():
            insights["next_steps"].append("회귀 테스트로 재발 방지 확인")

        return insights

    def categorize_work_type(self, commit_info: Dict) -> str:
        """작업 유형 분류"""
        message = commit_info.get("message", "").lower()

        if any(kw in message for kw in ["feat", "feature", "add"]):
            return "feature"
        elif any(kw in message for kw in ["fix", "bug", "resolve"]):
            return "bugfix"
        elif "refactor" in message:
            return "refactor"
        elif any(kw in message for kw in ["docs", "document"]):
            return "documentation"
        elif "test" in message:
            return "testing"
        else:
            return "maintenance"

    def generate_frontmatter(self, commit_info: Dict, work_type: str) -> str:
        """YAML frontmatter 생성"""
        commit_time = datetime.fromisoformat(commit_info["time"].split("+")[0].strip())
        today = commit_time.strftime("%Y-%m-%d")
        time_str = commit_time.strftime("%H:%M")

        # 파일 분류
        files = commit_info.get("files_changed", [])
        tags = ["commit"]

        if any("test" in f.lower() for f in files):
            tags.append("testing")
        if any("docs" in f.lower() for f in files):
            tags.append("documentation")
        if work_type not in tags:
            tags.append(work_type)

        # Topic 생성 (커밋 메시지 첫 줄에서)
        topic = commit_info.get("message", "").split('\n')[0]
        if ':' in topic:
            topic = topic.split(':', 1)[1].strip()

        frontmatter = f"""---
date: {today}
time: "{time_str}"
project: UDO-Development-Platform
topic: {topic}
commit: {commit_info['hash'][:7]}
type: {work_type}
tags: [{', '.join(tags)}]
files_changed: {len(files)}
---
"""
        return frontmatter

    def generate_dev_log(self, commit_info: Dict) -> str:
        """개발일지 마크다운 생성"""
        work_type = self.categorize_work_type(commit_info)
        frontmatter = self.generate_frontmatter(commit_info, work_type)
        insights = self.generate_ai_insights(commit_info)

        # 커밋 메시지
        message = commit_info.get("message", "")
        message_lines = message.split('\n')
        title = message_lines[0]
        description = '\n'.join(message_lines[1:]).strip() if len(message_lines) > 1 else ""

        # 파일 변경 사항
        files = commit_info.get("files_changed", [])
        files_by_category = {
            "Backend": [f for f in files if f.startswith("backend/")],
            "Frontend": [f for f in files if f.startswith("web-dashboard/")],
            "Docs": [f for f in files if f.startswith("docs/")],
            "Scripts": [f for f in files if f.startswith("scripts/")],
            "Tests": [f for f in files if "test" in f.lower()],
            "Other": []
        }

        # Other 카테고리 채우기
        categorized = sum(files_by_category.values(), [])
        files_by_category["Other"] = [f for f in files if f not in categorized]

        # 마크다운 생성
        content = frontmatter + f"\n# {title}\n\n"

        if description:
            content += f"{description}\n\n"

        content += "## 변경 사항\n\n"
        for category, category_files in files_by_category.items():
            if category_files:
                content += f"### {category} ({len(category_files)})\n"
                for file in category_files[:10]:  # 최대 10개만
                    content += f"- `{file}`\n"
                if len(category_files) > 10:
                    content += f"- ... and {len(category_files) - 10} more\n"
                content += "\n"

        # AI 인사이트
        if insights["learned"]:
            content += "## 💡 배운 점\n\n"
            for item in insights["learned"]:
                content += f"- {item}\n"
            content += "\n"

        if insights["challenges"]:
            content += "## 🔧 시행착오\n\n"
            for item in insights["challenges"]:
                content += f"- {item}\n"
            content += "\n"

        if insights["next_steps"]:
            content += "## 📋 다음 단계\n\n"
            for item in insights["next_steps"]:
                content += f"- {item}\n"
            content += "\n"

        # 커밋 통계
        content += "## 📊 통계\n\n"
        content += f"```\n{commit_info.get('stats', '')}\n```\n\n"

        content += f"**커밋 해시**: `{commit_info['hash'][:7]}`  \n"
        content += f"**작성 시각**: {commit_info['time']}  \n"
        content += f"**자동 생성**: Obsidian Auto-Sync v2.0  \n"

        return content

    def sync(self, commit_hash: str) -> bool:
        """Obsidian 동기화 실행"""
        try:
            # 1. 커밋 정보 가져오기
            commit_info = self.get_commit_info(commit_hash)
            if not commit_info:
                print("[ERROR] Failed to get commit info", file=sys.stderr)
                return False

            # 2. 트리거 조건 확인
            triggered, reason = self.check_trigger_conditions(commit_info)
            if not triggered:
                print(f"[SKIP] Trigger condition not met: {reason}")
                return True  # 에러는 아님

            print(f"[TRIGGER] {reason}")

            # 3. 개발일지 생성
            dev_log_content = self.generate_dev_log(commit_info)

            # 4. Obsidian에 저장
            commit_time = datetime.fromisoformat(commit_info["time"].split("+")[0].strip())
            date_folder = commit_time.strftime("%Y-%m-%d")
            topic = commit_info.get("message", "").split('\n')[0].replace(":", "-").replace("/", "-")[:50]
            filename = f"{topic}.md"

            # 날짜 폴더 생성
            date_dir = self.dev_log_dir / date_folder
            date_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            file_path = date_dir / filename
            file_path.write_text(dev_log_content, encoding='utf-8')

            print(f"[OK] Obsidian dev log created: {date_folder}/{filename}")
            return True

        except Exception as e:
            print(f"[ERROR] Sync failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Obsidian Auto-Sync v2.0")
    parser.add_argument("--commit-hash", default="HEAD", help="Commit hash to sync")
    parser.add_argument("--vault", help="Obsidian vault path (optional)")
    args = parser.parse_args()

    # Repo root 찾기
    repo_root = Path(__file__).resolve().parents[1]

    # Vault 경로
    vault_path = Path(args.vault) if args.vault else None

    # 동기화 실행
    syncer = ObsidianAutoSync(repo_root, vault_path)
    success = syncer.sync(args.commit_hash)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
