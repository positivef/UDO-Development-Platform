#!/usr/bin/env python
"""
Obsidian Auto-Sync v3.0 - AI-Enhanced Development Log Generator

자동으로 Git commit 정보를 분석하여 Obsidian 개발일지를 생성합니다.

Features (v3.0):
- 14개 Frontmatter 필드 (기본4 + 플래그7 + AI컨텍스트3 + 자동수집2 + schema1)
- 9개 Daily 섹션 (조건부 렌더링)
- 4개 Weekly 섹션 (주간 집계)
- 플래그 자동 감지 (Git diff 분석)
- 하이브리드 트리거 (Git Hook + session_state.json)
- Schema 버전 관리

Features (v2.0):
- 트리거 조건 자동 감지 (3+ 파일, feat:/fix: 메시지)
- AI 인사이트 자동 생성 (배운 점, 시행착오, 다음 단계)
- 시간대별 작업 내역 추론
- YAML frontmatter 자동 생성

Usage:
  python scripts/obsidian_auto_sync.py --commit-hash <hash>
  python scripts/obsidian_auto_sync.py --commit-hash HEAD
  python scripts/obsidian_auto_sync.py --commit-hash HEAD --version 3

Requirements:
- Git repository
- Obsidian vault configured in environment or default location

Author: System Automation Team
Date: 2025-12-29
Version: 3.0.0
"""

import argparse
import json
import os
import re
import subprocess
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


# =============================================================================
# v3.0: Flag Detection System
# =============================================================================


class FlagDetector:
    """Git diff와 커밋 정보에서 플래그 자동 감지"""

    def __init__(self, diff: str, commit_info: Dict):
        self.diff = diff
        self.commit_info = commit_info
        self.message = commit_info.get("message", "").lower()
        self.files = commit_info.get("files_changed", [])

    def detect_all(self) -> Dict[str, bool]:
        """모든 플래그 감지"""
        return {
            "has_til": self.detect_til(),
            "has_solution": self.detect_solution(),
            "has_pattern": self.detect_pattern(),
            "has_uncertainty": self.detect_uncertainty(),
            "has_rollback": self.detect_rollback(),
            "has_debt": self.detect_debt(),
            "has_decision": self.detect_decision(),
        }

    def detect_til(self) -> bool:
        """배운 점 감지: 새로운 패턴, 테스트 추가, 문서화"""
        patterns = [
            r"def test_",  # 새 테스트 추가
            r"# TIL:",  # 명시적 TIL 주석
            r"learned|학습|배움",  # 키워드
            r"\.md$.*tutorial",  # 튜토리얼 문서
            r"refactor",  # 리팩토링 (학습 포함)
        ]
        # 파일 기반 감지
        if any("test" in f.lower() for f in self.files):
            return True
        # diff 기반 감지
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_solution(self) -> bool:
        """해결책 감지: 버그 수정, 문제 해결"""
        patterns = [
            r"fix:|bug:|resolve:",  # 커밋 메시지 패턴
            r"# Solution:",  # 명시적 주석
            r"해결|수정|고침",  # 한글 키워드
            r"fixed|resolved",  # 영어 키워드
        ]
        if any(p in self.message for p in ["fix", "bug", "resolve", "해결"]):
            return True
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_pattern(self) -> bool:
        """패턴 감지: 디자인 패턴, 아키텍처 패턴"""
        patterns = [
            r"# Pattern:",  # 명시적 주석
            r"패턴|pattern",  # 키워드
            r"singleton|factory|observer|strategy",  # 디자인 패턴
            r"decorator|adapter|facade",  # 디자인 패턴
        ]
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_uncertainty(self) -> bool:
        """불확실성 감지: 미확정 사항, 리스크"""
        patterns = [
            r"# TODO:",  # TODO는 불확실성
            r"# FIXME:",  # FIXME도 불확실성
            r"불확실|uncertain",  # 키워드
            r"\?\?\?|XXX",  # 의문 마커
            r"risk|리스크|위험",  # 리스크 키워드
            r"maybe|perhaps|아마",  # 불확실 표현
        ]
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_rollback(self) -> bool:
        """롤백 계획 감지: 롤백 전략, 복구 계획"""
        patterns = [
            r"# Rollback:",  # 명시적 주석
            r"rollback|롤백",  # 키워드
            r"revert|복구|되돌리",  # 복구 키워드
            r"backup|백업",  # 백업 키워드
            r"feature.?flag",  # 피처 플래그
        ]
        # 마이그레이션 파일이 있으면 롤백 계획 필요
        if any("migration" in f.lower() for f in self.files):
            return True
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_debt(self) -> bool:
        """기술부채 감지: TODO, FIXME, 임시 해결책"""
        patterns = [
            r"#\s*TODO:",  # TODO 주석
            r"#\s*FIXME:",  # FIXME 주석
            r"#\s*HACK:",  # HACK 주석
            r"#\s*XXX:",  # XXX 주석
            r"temporary|임시",  # 임시 키워드
            r"workaround",  # 우회 해결책
            r"@pytest\.mark\.skip",  # 스킵된 테스트
            r"# type:\s*ignore",  # 타입 무시
        ]
        return any(re.search(p, self.diff, re.I) for p in patterns)

    def detect_decision(self) -> bool:
        """의사결정 감지: 아키텍처 변경, 라이브러리 추가"""
        patterns = [
            r"# Decision:",  # 명시적 주석
            r"# Why:",  # 이유 설명
            r"선택|결정|채택",  # 한글 키워드
            r"chose|decided|selected",  # 영어 키워드
        ]
        # requirements.txt 또는 package.json 변경
        if any(f in ["requirements.txt", "package.json", "pyproject.toml"] for f in self.files):
            return True
        # 새 의존성 추가 감지
        if re.search(r"requirements\.txt.*\+", self.diff):
            return True
        return any(re.search(p, self.diff, re.I) for p in patterns)


# =============================================================================
# v3.0: AI Context Generator
# =============================================================================


class AIContextGenerator:
    """AI 컨텍스트 자동 생성"""

    def __init__(self, commit_info: Dict, diff: str):
        self.commit_info = commit_info
        self.diff = diff
        self.message = commit_info.get("message", "")
        self.files = commit_info.get("files_changed", [])

    def generate(self) -> Dict[str, Any]:
        """AI 컨텍스트 생성"""
        return {
            "summary": self._generate_summary(),
            "next_actions": self._extract_next_actions(),
            "warnings": self._extract_warnings(),
        }

    def _generate_summary(self) -> str:
        """1-2문장 요약 생성"""
        # 커밋 메시지 첫 줄 사용
        first_line = self.message.split("\n")[0]

        # 타입 추출
        work_type = "작업"
        if "feat" in first_line.lower():
            work_type = "기능 추가"
        elif "fix" in first_line.lower():
            work_type = "버그 수정"
        elif "refactor" in first_line.lower():
            work_type = "리팩토링"
        elif "docs" in first_line.lower():
            work_type = "문서화"
        elif "test" in first_line.lower():
            work_type = "테스트"

        files_count = len(self.files)
        return f"{work_type}: {files_count}개 파일 변경. {first_line[:50]}"

    def _extract_next_actions(self) -> List[str]:
        """다음 액션 추출"""
        actions = []

        # TODO에서 추출
        todos = re.findall(r"#\s*TODO:?\s*(.+)", self.diff)
        for todo in todos[:3]:
            actions.append(f"TODO: {todo.strip()[:50]}")

        # 커밋 메시지 기반 추론
        if "feat" in self.message.lower():
            actions.append("통합 테스트 실행")
        if "fix" in self.message.lower():
            actions.append("회귀 테스트 확인")
        if not actions:
            actions.append("코드 리뷰 요청")

        return actions[:5]  # 최대 5개

    def _extract_warnings(self) -> List[str]:
        """경고사항 추출"""
        warnings = []

        # FIXME에서 추출
        fixmes = re.findall(r"#\s*FIXME:?\s*(.+)", self.diff)
        for fixme in fixmes[:3]:
            warnings.append(f"FIXME: {fixme.strip()[:50]}")

        # 위험 패턴 감지
        if re.search(r"rm\s+-rf|DROP\s+TABLE|DELETE\s+FROM", self.diff, re.I):
            warnings.append("위험한 명령어 감지 - 주의 필요")

        if re.search(r"password|secret|api.?key", self.diff, re.I):
            warnings.append("민감 정보 노출 가능성 - 확인 필요")

        if len(self.files) > 20:
            warnings.append(f"대규모 변경 ({len(self.files)}개 파일) - 신중한 리뷰 필요")

        return warnings[:5]  # 최대 5개


# =============================================================================
# v3.0: Section Generator (9 Daily Sections + Conditional Rendering)
# =============================================================================


class SectionGenerator:
    """9개 Daily 섹션 생성기 (조건부 렌더링 지원)"""

    def __init__(self, commit_info: Dict, flags: Dict[str, bool], session_state: Dict, diff: str, repo_root: Path):
        self.commit_info = commit_info
        self.flags = flags
        self.session_state = session_state
        self.diff = diff
        self.repo_root = repo_root
        self.message = commit_info.get("message", "")
        self.files = commit_info.get("files_changed", [])

    def generate_all_sections(self) -> str:
        """모든 섹션 생성 (조건부 렌더링 적용)"""
        content = ""

        # 1. Executive Summary (항상)
        content += self._section_executive_summary()

        # 2. Work Timeline (항상)
        content += self._section_work_timeline()

        # 3. TIL (has_til)
        if self.flags.get("has_til"):
            content += self._section_til()

        # 4. Solutions & Patterns (has_solution OR has_pattern)
        if self.flags.get("has_solution") or self.flags.get("has_pattern"):
            content += self._section_solutions_patterns()

        # 5. Uncertainty & Blockers (has_uncertainty)
        if self.flags.get("has_uncertainty"):
            content += self._section_uncertainty()

        # 6. Rollback Plans (has_rollback)
        if self.flags.get("has_rollback"):
            content += self._section_rollback()

        # 7. Related Docs (항상)
        content += self._section_related_docs()

        # 8. Technical Debt Daily (has_debt)
        if self.flags.get("has_debt"):
            content += self._section_tech_debt()

        # 9. Decisions Made (has_decision)
        if self.flags.get("has_decision"):
            content += self._section_decisions()

        return content

    # -------------------------------------------------------------------------
    # Section 1: Executive Summary (항상)
    # -------------------------------------------------------------------------
    def _section_executive_summary(self) -> str:
        """Executive Summary 섹션"""
        title = self.message.split("\n")[0]
        files_count = len(self.files)

        # 작업 유형 추론
        work_type = "작업"
        if "feat" in title.lower():
            work_type = "기능 추가"
        elif "fix" in title.lower():
            work_type = "버그 수정"
        elif "refactor" in title.lower():
            work_type = "리팩토링"
        elif "docs" in title.lower():
            work_type = "문서화"
        elif "test" in title.lower():
            work_type = "테스트"

        content = f"\n# {title}\n\n"
        content += "## Executive Summary\n\n"
        content += f"**작업 유형**: {work_type}  \n"
        content += f"**변경 파일**: {files_count}개  \n"

        # 주요 변경 영역 (카테고리별)
        categories = self._categorize_files()
        if categories:
            areas = [f"{cat} ({count})" for cat, count in categories.items() if count > 0]
            content += f"**변경 영역**: {', '.join(areas[:4])}  \n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 2: Work Timeline (항상)
    # -------------------------------------------------------------------------
    def _section_work_timeline(self) -> str:
        """Work Timeline 섹션 - session_state.json에서 추출"""
        content = "## Work Timeline\n\n"

        checkpoints = self.session_state.get("checkpoints", [])
        if checkpoints:
            content += "| 시간 | 작업 내용 |\n"
            content += "|------|----------|\n"

            for cp in checkpoints[-10:]:  # 최근 10개만
                time_str = cp.get("time", "")[:16]  # YYYY-MM-DD HH:MM
                notes = cp.get("notes", "체크포인트")[:50]
                content += f"| {time_str} | {notes} |\n"

            content += "\n"
        else:
            # session_state가 없으면 커밋 정보 기반
            commit_time = self.commit_info.get("time", "")[:16]
            content += f"- **{commit_time}**: {self.message.split(chr(10))[0][:50]}\n\n"

        return content

    # -------------------------------------------------------------------------
    # Section 3: TIL - Today I Learned (has_til)
    # -------------------------------------------------------------------------
    def _section_til(self) -> str:
        """TIL 섹션 - 배운 점 자동 추출"""
        content = "## Today I Learned (TIL)\n\n"

        learnings = []

        # 테스트 추가 감지
        if any("test" in f.lower() for f in self.files):
            learnings.append("테스트 우선 개발 (TDD) 패턴 적용")

        # 리팩토링 감지
        if "refactor" in self.message.lower():
            learnings.append("코드 구조 개선으로 유지보수성 향상")

        # 새 패턴 감지
        patterns = re.findall(r"(singleton|factory|observer|strategy|decorator|adapter|facade)", self.diff, re.I)
        if patterns:
            learnings.append(f"디자인 패턴 적용: {', '.join(set(patterns))}")

        # 성능 최적화
        if any(kw in self.diff.lower() for kw in ["cache", "optimize", "performance"]):
            learnings.append("성능 최적화 기법 학습")

        # 보안 관련
        if any(kw in self.diff.lower() for kw in ["auth", "security", "token"]):
            learnings.append("보안 강화 기법 적용")

        # 명시적 TIL 주석 추출
        til_comments = re.findall(r"#\s*TIL:?\s*(.+)", self.diff)
        learnings.extend([t.strip()[:80] for t in til_comments[:3]])

        if learnings:
            for item in learnings[:5]:
                content += f"- {item}\n"
        else:
            content += "- (자동 감지된 학습 항목 없음 - 수동 작성 권장)\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 4: Solutions & Patterns (has_solution OR has_pattern)
    # -------------------------------------------------------------------------
    def _section_solutions_patterns(self) -> str:
        """Solutions & Patterns 섹션"""
        content = "## Solutions & Patterns\n\n"

        # 해결책 추출
        if self.flags.get("has_solution"):
            content += "### Solutions\n\n"
            solutions = re.findall(r"#\s*Solution:?\s*(.+)", self.diff)
            if solutions:
                for sol in solutions[:5]:
                    content += f"- {sol.strip()[:80]}\n"
            elif "fix" in self.message.lower():
                content += f"- {self.message.split(chr(10))[0]}\n"
            content += "\n"

        # 패턴 추출
        if self.flags.get("has_pattern"):
            content += "### Patterns Applied\n\n"
            patterns = re.findall(
                r"(singleton|factory|observer|strategy|decorator|adapter|facade|mixin|proxy)", self.diff, re.I
            )
            pattern_comments = re.findall(r"#\s*Pattern:?\s*(.+)", self.diff)

            if patterns:
                for p in set(patterns):
                    content += f"- **{p.capitalize()}** 패턴\n"
            if pattern_comments:
                for pc in pattern_comments[:3]:
                    content += f"- {pc.strip()[:80]}\n"
            content += "\n"

        return content

    # -------------------------------------------------------------------------
    # Section 5: Uncertainty & Blockers (has_uncertainty)
    # -------------------------------------------------------------------------
    def _section_uncertainty(self) -> str:
        """Uncertainty & Blockers 섹션"""
        content = "## Uncertainty & Blockers\n\n"

        uncertainties = []

        # TODO 추출
        todos = re.findall(r"#\s*TODO:?\s*(.+)", self.diff)
        uncertainties.extend([f"TODO: {t.strip()[:60]}" for t in todos[:5]])

        # FIXME 추출
        fixmes = re.findall(r"#\s*FIXME:?\s*(.+)", self.diff)
        uncertainties.extend([f"FIXME: {f.strip()[:60]}" for f in fixmes[:3]])

        # 불확실성 키워드
        if re.search(r"maybe|perhaps|아마|possibly", self.diff, re.I):
            uncertainties.append("불확실한 구현 감지 - 검토 필요")

        # 리스크 키워드
        risks = re.findall(r"#\s*RISK:?\s*(.+)", self.diff)
        uncertainties.extend([f"RISK: {r.strip()[:60]}" for r in risks[:3]])

        if uncertainties:
            for item in uncertainties[:8]:
                content += f"- {item}\n"
        else:
            content += "- (불확실성 항목 감지됨 - 상세 내용 수동 작성 권장)\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 6: Rollback Plans (has_rollback)
    # -------------------------------------------------------------------------
    def _section_rollback(self) -> str:
        """Rollback Plans 섹션"""
        content = "## Rollback Plans\n\n"

        rollbacks = []

        # 명시적 롤백 주석
        rollback_comments = re.findall(r"#\s*Rollback:?\s*(.+)", self.diff)
        rollbacks.extend([r.strip()[:80] for r in rollback_comments[:3]])

        # 마이그레이션 파일 감지
        migrations = [f for f in self.files if "migration" in f.lower()]
        if migrations:
            rollbacks.append(f"DB 마이그레이션 롤백: `python manage.py migrate --reverse` ({len(migrations)}개 파일)")

        # Feature flag 감지
        if re.search(r"feature.?flag", self.diff, re.I):
            rollbacks.append("Feature Flag 비활성화로 즉시 롤백 가능")

        # 백업 전략
        if re.search(r"backup|백업", self.diff, re.I):
            rollbacks.append("백업 복원 전략 준비됨")

        # 기본 롤백 가이드
        if not rollbacks:
            commit_hash = self.commit_info.get("hash", "HEAD")[:7]
            rollbacks = [
                f"Git Revert: `git revert {commit_hash}`",
                "즉시 롤백 가능 (1분 이내)",
            ]

        content += "| 전략 | 설명 |\n"
        content += "|------|------|\n"
        for idx, item in enumerate(rollbacks[:5], 1):
            content += f"| Tier {idx} | {item} |\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 7: Related Docs (항상)
    # -------------------------------------------------------------------------
    def _section_related_docs(self) -> str:
        """Related Docs 섹션 - 관련 문서 자동 링크"""
        content = "## Related Docs\n\n"

        # 변경된 docs 파일
        doc_files = [f for f in self.files if f.startswith("docs/") or f.endswith(".md")]
        if doc_files:
            content += "### 변경된 문서\n"
            for doc in doc_files[:5]:
                content += f"- [[{Path(doc).stem}]] (`{doc}`)\n"
            content += "\n"

        # 관련 링크 추론
        content += "### 관련 링크\n"

        # CLAUDE.md 참조
        if any("claude" in f.lower() for f in self.files):
            content += "- [[CLAUDE]] (프로젝트 컨텍스트)\n"

        # 테스트 관련
        if any("test" in f.lower() for f in self.files):
            content += "- [[Testing Guide]]\n"

        # Backend 관련
        if any("backend" in f.lower() for f in self.files):
            content += "- [[Backend Architecture]]\n"

        # Frontend 관련
        if any("web-dashboard" in f.lower() or "frontend" in f.lower() for f in self.files):
            content += "- [[Frontend Guide]]\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 8: Technical Debt Daily (has_debt)
    # -------------------------------------------------------------------------
    def _section_tech_debt(self) -> str:
        """Technical Debt Daily 섹션"""
        content = "## Technical Debt (Daily)\n\n"

        debts = []

        # TODO 추출
        todos = re.findall(r"#\s*TODO:?\s*(.+)", self.diff)
        debts.extend([{"type": "TODO", "desc": t.strip()[:60]} for t in todos[:5]])

        # FIXME 추출
        fixmes = re.findall(r"#\s*FIXME:?\s*(.+)", self.diff)
        debts.extend([{"type": "FIXME", "desc": f.strip()[:60]} for f in fixmes[:3]])

        # HACK 추출
        hacks = re.findall(r"#\s*HACK:?\s*(.+)", self.diff)
        debts.extend([{"type": "HACK", "desc": h.strip()[:60]} for h in hacks[:2]])

        # 스킵된 테스트
        skips = re.findall(r"@pytest\.mark\.skip\(reason=[\"'](.+?)[\"']\)", self.diff)
        debts.extend([{"type": "SKIP", "desc": s[:60]} for s in skips[:2]])

        # 타입 무시
        ignores = len(re.findall(r"#\s*type:\s*ignore", self.diff))
        if ignores > 0:
            debts.append({"type": "TYPE", "desc": f"type: ignore 주석 {ignores}개"})

        if debts:
            content += "| 유형 | 설명 | 우선순위 |\n"
            content += "|------|------|----------|\n"
            for debt in debts[:8]:
                priority = "P1" if debt["type"] == "FIXME" else "P2"
                content += f"| {debt['type']} | {debt['desc']} | {priority} |\n"
        else:
            content += "- (기술부채 항목 감지됨 - 상세 분석 권장)\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 9: Decisions Made (has_decision)
    # -------------------------------------------------------------------------
    def _section_decisions(self) -> str:
        """Decisions Made 섹션"""
        content = "## Decisions Made (Daily)\n\n"

        decisions = []

        # 명시적 Decision 주석
        decision_comments = re.findall(r"#\s*Decision:?\s*(.+)", self.diff)
        decisions.extend([d.strip()[:80] for d in decision_comments[:5]])

        # Why 주석
        why_comments = re.findall(r"#\s*Why:?\s*(.+)", self.diff)
        decisions.extend([f"이유: {w.strip()[:70]}" for w in why_comments[:3]])

        # 의존성 변경 감지
        if "requirements.txt" in self.files or "package.json" in self.files:
            # 추가된 라이브러리 추출
            added_deps = re.findall(r"\+([a-zA-Z0-9_-]+)==", self.diff)
            if added_deps:
                decisions.append(f"의존성 추가: {', '.join(added_deps[:3])}")

        # pyproject.toml 변경
        if "pyproject.toml" in self.files:
            decisions.append("Python 프로젝트 설정 변경")

        if decisions:
            for idx, decision in enumerate(decisions[:6], 1):
                content += f"{idx}. {decision}\n"
        else:
            content += "- (의사결정 감지됨 - 상세 내용 수동 작성 권장)\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    def _categorize_files(self) -> Dict[str, int]:
        """파일을 카테고리별로 분류"""
        categories = {
            "Backend": 0,
            "Frontend": 0,
            "Tests": 0,
            "Docs": 0,
            "Scripts": 0,
            "Config": 0,
        }

        for f in self.files:
            if f.startswith("backend/"):
                categories["Backend"] += 1
            elif f.startswith("web-dashboard/") or f.startswith("frontend/"):
                categories["Frontend"] += 1
            elif "test" in f.lower():
                categories["Tests"] += 1
            elif f.startswith("docs/") or f.endswith(".md"):
                categories["Docs"] += 1
            elif f.startswith("scripts/"):
                categories["Scripts"] += 1
            elif any(f.endswith(ext) for ext in [".yaml", ".yml", ".json", ".toml", ".env"]):
                categories["Config"] += 1

        return {k: v for k, v in categories.items() if v > 0}


# =============================================================================
# v3.0: Weekly Summary Generator (4 Weekly Sections with Dataview)
# =============================================================================


class WeeklySummaryGenerator:
    """4개 Weekly 섹션 생성기 (Dataview 쿼리 활용)"""

    def __init__(self, week_start: datetime, week_end: datetime, project: str = "UDO-Development-Platform"):
        self.week_start = week_start
        self.week_end = week_end
        self.project = project
        self.week_str = week_start.strftime("%Y-W%W")

    def generate_weekly_note(self) -> str:
        """주간 요약 노트 생성"""
        content = self._generate_frontmatter()
        content += f"\n# Weekly Summary: {self.week_str}\n\n"
        content += f"**기간**: {self.week_start.strftime('%Y-%m-%d')} ~ {self.week_end.strftime('%Y-%m-%d')}\n\n"

        # 4개 Weekly 섹션
        content += self._section_tech_debt_summary()
        content += self._section_decision_audit()
        content += self._section_performance_trends()
        content += self._section_next_week_actions()

        # 푸터
        content += "\n---\n"
        content += f"**자동 생성**: Obsidian Auto-Sync v3.0 Weekly  \n"
        content += f"**생성 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  \n"

        return content

    def _generate_frontmatter(self) -> str:
        """Weekly Frontmatter 생성"""
        frontmatter = f"""---
title: "{self.week_str} Weekly Summary"
created: {datetime.now().strftime('%Y-%m-%d')}
type: weekly
status: completed
week_start: {self.week_start.strftime('%Y-%m-%d')}
week_end: {self.week_end.strftime('%Y-%m-%d')}
project: {self.project}
schema_version: "1.0"
tags: [weekly, summary, review]
---
"""
        return frontmatter

    # -------------------------------------------------------------------------
    # Section 1: Tech Debt Summary (주간 기술부채 집계)
    # -------------------------------------------------------------------------
    def _section_tech_debt_summary(self) -> str:
        """Tech Debt Summary - Dataview 쿼리로 집계"""
        content = "## Tech Debt Summary\n\n"
        content += "> 이번 주 발생한 기술부채를 Dataview로 자동 집계합니다.\n\n"

        # Dataview 쿼리 (has_debt=true인 Daily 노트 집계)
        content += "```dataview\n"
        content += "TABLE WITHOUT ID\n"
        content += '  file.link as "날짜",\n'
        content += '  length(filter(file.outlinks, (l) => contains(string(l), "TODO"))) as "TODO",\n'
        content += '  length(filter(file.outlinks, (l) => contains(string(l), "FIXME"))) as "FIXME"\n'
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "  AND has_debt = true\n"
        content += "SORT created ASC\n"
        content += "```\n\n"

        # 수동 체크리스트
        content += "### 주간 기술부채 액션\n\n"
        content += "- [ ] 이번 주 TODO 정리 (우선순위 P1 먼저)\n"
        content += "- [ ] FIXME 항목 리뷰\n"
        content += "- [ ] 다음 주 이월 항목 결정\n"
        content += "\n"

        return content

    # -------------------------------------------------------------------------
    # Section 2: Decision Audit Summary (주간 의사결정 감사)
    # -------------------------------------------------------------------------
    def _section_decision_audit(self) -> str:
        """Decision Audit - 주간 의사결정 감사"""
        content = "## Decision Audit Summary\n\n"
        content += "> 이번 주 내린 주요 결정들을 추적합니다.\n\n"

        # Dataview 쿼리 (has_decision=true인 Daily 노트)
        content += "```dataview\n"
        content += "TABLE WITHOUT ID\n"
        content += '  file.link as "날짜",\n'
        content += '  context_summary as "요약"\n'
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "  AND has_decision = true\n"
        content += "SORT created ASC\n"
        content += "```\n\n"

        # 결정 검토 체크리스트
        content += "### 결정 검토 체크리스트\n\n"
        content += "| 결정 | 결과 | 후속 조치 |\n"
        content += "|------|------|----------|\n"
        content += "| (수동 입력) | (성공/실패/진행중) | (필요시) |\n"
        content += "\n"

        return content

    # -------------------------------------------------------------------------
    # Section 3: Performance Trends (성능 트렌드)
    # -------------------------------------------------------------------------
    def _section_performance_trends(self) -> str:
        """Performance Trends - 생산성 및 성과 트렌드"""
        content = "## Performance Trends\n\n"
        content += "> 이번 주 개발 생산성을 분석합니다.\n\n"

        # 커밋 통계 Dataview
        content += "### 커밋 통계\n\n"
        content += "```dataview\n"
        content += "TABLE WITHOUT ID\n"
        content += '  file.link as "날짜",\n'
        content += '  files_changed as "파일수",\n'
        content += '  commits as "커밋수"\n'
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "SORT created ASC\n"
        content += "```\n\n"

        # 학습 추적
        content += "### 학습 통계 (TIL)\n\n"
        content += "```dataview\n"
        content += "LIST\n"
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "  AND has_til = true\n"
        content += "SORT created ASC\n"
        content += "```\n\n"

        # 주간 요약 메트릭
        content += "### 주간 메트릭 (수동 입력)\n\n"
        content += "| 지표 | 이번 주 | 지난 주 | 변화 |\n"
        content += "|------|---------|---------|------|\n"
        content += "| 총 커밋 수 | - | - | - |\n"
        content += "| 변경 파일 수 | - | - | - |\n"
        content += "| TIL 항목 수 | - | - | - |\n"
        content += "| 해결된 이슈 | - | - | - |\n"
        content += "\n"

        return content

    # -------------------------------------------------------------------------
    # Section 4: Next Week Actions (다음 주 계획)
    # -------------------------------------------------------------------------
    def _section_next_week_actions(self) -> str:
        """Next Week Actions - 다음 주 계획"""
        content = "## Next Week Actions\n\n"
        content += "> 다음 주 우선순위 작업을 정의합니다.\n\n"

        # 이월 항목 자동 추출 (Dataview)
        content += "### 이월 항목 (자동 집계)\n\n"
        content += "```dataview\n"
        content += "LIST next_actions\n"
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "  AND length(next_actions) > 0\n"
        content += "FLATTEN next_actions\n"
        content += "LIMIT 10\n"
        content += "```\n\n"

        # 주간 경고사항 집계
        content += "### 경고사항 (자동 집계)\n\n"
        content += "```dataview\n"
        content += "LIST warnings\n"
        content += 'FROM "개발일지"\n'
        content += f'WHERE created >= date("{self.week_start.strftime("%Y-%m-%d")}")\n'
        content += f'  AND created <= date("{self.week_end.strftime("%Y-%m-%d")}")\n'
        content += "  AND length(warnings) > 0\n"
        content += "FLATTEN warnings\n"
        content += "LIMIT 5\n"
        content += "```\n\n"

        # 수동 계획
        content += "### 다음 주 우선순위 (수동 입력)\n\n"
        content += "| 우선순위 | 작업 | 예상 시간 | 담당 |\n"
        content += "|----------|------|----------|------|\n"
        content += "| P0 | (필수 작업) | - | - |\n"
        content += "| P1 | (중요 작업) | - | - |\n"
        content += "| P2 | (선택 작업) | - | - |\n"
        content += "\n"

        return content


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
                ["git", "log", "-1", "--pretty=%B", commit_hash], cwd=self.repo_root, encoding="utf-8", errors="replace"
            ).strip()

            # 커밋 시간
            commit_time = subprocess.check_output(
                ["git", "log", "-1", "--pretty=%ai", commit_hash], cwd=self.repo_root, encoding="utf-8", errors="replace"
            ).strip()

            # 변경 파일 목록
            files_changed = (
                subprocess.check_output(
                    ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
                    cwd=self.repo_root,
                    encoding="utf-8",
                    errors="replace",
                )
                .strip()
                .split("\n")
            )

            # 통계
            stats = subprocess.check_output(
                ["git", "log", "-1", "--stat", commit_hash], cwd=self.repo_root, encoding="utf-8", errors="replace"
            ).strip()

            # diff (간단한 버전)
            diff = subprocess.check_output(
                ["git", "show", "--stat", commit_hash], cwd=self.repo_root, encoding="utf-8", errors="replace"
            ).strip()

            return {
                "hash": commit_hash,
                "message": message,
                "time": commit_time,
                "files_changed": [f for f in files_changed if f],
                "stats": stats,
                "diff": diff,
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
        trigger_patterns = [r"^feat:", r"^feature:", r"^fix:", r"^bug:", r"^docs:", r"^refactor:", r"^analyze:", r"^analysis:"]

        for pattern in trigger_patterns:
            if re.match(pattern, message, re.IGNORECASE):
                return True, f"Commit message matches: {pattern}"

        return False, f"No trigger (files: {files_count}, message: {message[:30]}...)"

    def generate_ai_insights(self, commit_info: Dict) -> Dict[str, List[str]]:
        """AI 인사이트 자동 생성 (패턴 기반)"""
        files = commit_info.get("files_changed", [])
        message = commit_info.get("message", "")
        diff = commit_info.get("diff", "")

        insights = {"learned": [], "challenges": [], "next_steps": []}

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
        topic = commit_info.get("message", "").split("\n")[0]
        if ":" in topic:
            topic = topic.split(":", 1)[1].strip()

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

    # =========================================================================
    # v3.0: Extended Frontmatter Generator (14 fields)
    # =========================================================================

    def generate_frontmatter_v3(
        self, commit_info: Dict, work_type: str, flags: Dict[str, bool], ai_context: Dict[str, Any]
    ) -> str:
        """v3.0 Frontmatter 생성 (14개 필드)"""
        commit_time = datetime.fromisoformat(commit_info["time"].split("+")[0].strip())
        today = commit_time.strftime("%Y-%m-%d")

        # Topic 추출 (커밋 메시지 첫 줄)
        topic = commit_info.get("message", "").split("\n")[0]
        if ":" in topic:
            topic = topic.split(":", 1)[1].strip()
        topic = topic[:50]  # 최대 50자

        # 태그 생성
        tags = self._generate_tags_v3(commit_info, work_type, flags)

        # Frontmatter 데이터 구조
        frontmatter_data = {
            # 기본 (4)
            "title": f"{today} {topic}",
            "created": today,
            "type": "daily",
            "status": "completed",
            # 플래그 (7)
            "has_til": flags.get("has_til", False),
            "has_solution": flags.get("has_solution", False),
            "has_pattern": flags.get("has_pattern", False),
            "has_uncertainty": flags.get("has_uncertainty", False),
            "has_rollback": flags.get("has_rollback", False),
            "has_debt": flags.get("has_debt", False),
            "has_decision": flags.get("has_decision", False),
            # AI 컨텍스트 (3)
            "context_summary": ai_context.get("summary", ""),
            "next_actions": ai_context.get("next_actions", []),
            "warnings": ai_context.get("warnings", []),
            # 자동 수집 (2)
            "files_changed": len(commit_info.get("files_changed", [])),
            "commits": self._count_today_commits(commit_time),
            # Schema 버전 (1)
            "schema_version": "1.0",
            # 분류 태그
            "tags": tags,
        }

        # YAML safe dump (배열 이스케이프 처리)
        yaml_content = yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True, sort_keys=False)

        return f"---\n{yaml_content}---\n"

    def _generate_tags_v3(self, commit_info: Dict, work_type: str, flags: Dict[str, bool]) -> List[str]:
        """v3.0 태그 생성"""
        tags = ["commit", work_type]
        files = commit_info.get("files_changed", [])

        # 파일 기반 태그
        if any("test" in f.lower() for f in files):
            tags.append("testing")
        if any("docs" in f.lower() for f in files):
            tags.append("documentation")
        if any("backend" in f.lower() for f in files):
            tags.append("backend")
        if any("frontend" in f.lower() or "web-dashboard" in f.lower() for f in files):
            tags.append("frontend")

        # 플래그 기반 태그
        if flags.get("has_debt"):
            tags.append("tech-debt")
        if flags.get("has_decision"):
            tags.append("decision")

        return list(set(tags))  # 중복 제거

    def _count_today_commits(self, commit_time: datetime) -> int:
        """당일 커밋 수 계산"""
        try:
            today_str = commit_time.strftime("%Y-%m-%d")
            result = subprocess.check_output(
                ["git", "log", "--oneline", f"--since={today_str} 00:00:00", f"--until={today_str} 23:59:59"],
                cwd=self.repo_root,
                encoding="utf-8",
                errors="replace",
            ).strip()
            return len([line for line in result.split("\n") if line])
        except subprocess.CalledProcessError:
            return 1

    def _get_full_diff(self, commit_hash: str) -> str:
        """전체 diff 가져오기"""
        try:
            return subprocess.check_output(
                ["git", "show", "--format=", commit_hash], cwd=self.repo_root, encoding="utf-8", errors="replace"
            ).strip()
        except subprocess.CalledProcessError:
            return ""

    def _load_session_state(self) -> Dict:
        """session_state.json 로드"""
        session_file = self.repo_root / ".udo" / "session_state.json"

        if not session_file.exists():
            return {}

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def generate_dev_log(self, commit_info: Dict) -> str:
        """개발일지 마크다운 생성"""
        work_type = self.categorize_work_type(commit_info)
        frontmatter = self.generate_frontmatter(commit_info, work_type)
        insights = self.generate_ai_insights(commit_info)

        # 커밋 메시지
        message = commit_info.get("message", "")
        message_lines = message.split("\n")
        title = message_lines[0]
        description = "\n".join(message_lines[1:]).strip() if len(message_lines) > 1 else ""

        # 파일 변경 사항
        files = commit_info.get("files_changed", [])
        files_by_category = {
            "Backend": [f for f in files if f.startswith("backend/")],
            "Frontend": [f for f in files if f.startswith("web-dashboard/")],
            "Docs": [f for f in files if f.startswith("docs/")],
            "Scripts": [f for f in files if f.startswith("scripts/")],
            "Tests": [f for f in files if "test" in f.lower()],
            "Other": [],
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

    def sync(self, commit_hash: str, version: int = 2) -> bool:
        """Obsidian 동기화 실행

        Args:
            commit_hash: Git 커밋 해시
            version: 사용할 버전 (2=v2.0, 3=v3.0)
        """
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

            # 3. 개발일지 생성 (버전에 따라 분기)
            if version >= 3:
                dev_log_content = self.generate_dev_log_v3(commit_info)
                version_str = "v3.0"
            else:
                dev_log_content = self.generate_dev_log(commit_info)
                version_str = "v2.0"

            # 4. Obsidian에 저장
            commit_time = datetime.fromisoformat(commit_info["time"].split("+")[0].strip())
            date_folder = commit_time.strftime("%Y-%m-%d")
            topic = commit_info.get("message", "").split("\n")[0].replace(":", "-").replace("/", "-")[:50]
            filename = f"{topic}.md"

            # 날짜 폴더 생성
            date_dir = self.dev_log_dir / date_folder
            date_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            file_path = date_dir / filename
            file_path.write_text(dev_log_content, encoding="utf-8")

            print(f"[OK] Obsidian dev log created ({version_str}): {date_folder}/{filename}")
            return True

        except Exception as e:
            print(f"[ERROR] Sync failed: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return False

    # =========================================================================
    # v3.0: Full Dev Log Generator (9 Daily Sections)
    # =========================================================================

    def generate_dev_log_v3(self, commit_info: Dict) -> str:
        """v3.0 개발일지 마크다운 생성 (9개 Daily 섹션)"""
        # 기본 정보 추출
        work_type = self.categorize_work_type(commit_info)
        commit_hash = commit_info.get("hash", "HEAD")

        # 전체 diff 가져오기
        full_diff = self._get_full_diff(commit_hash)

        # 플래그 감지
        flag_detector = FlagDetector(full_diff, commit_info)
        flags = flag_detector.detect_all()

        # AI 컨텍스트 생성
        ai_context_gen = AIContextGenerator(commit_info, full_diff)
        ai_context = ai_context_gen.generate()

        # v3 Frontmatter 생성
        frontmatter = self.generate_frontmatter_v3(commit_info, work_type, flags, ai_context)

        # 세션 상태 로드
        session_state = self._load_session_state()

        # 섹션 생성기 초기화
        section_gen = SectionGenerator(
            commit_info=commit_info, flags=flags, session_state=session_state, diff=full_diff, repo_root=self.repo_root
        )

        # 전체 콘텐츠 조합
        content = frontmatter
        content += section_gen.generate_all_sections()

        # 푸터
        content += "\n---\n"
        content += f"**커밋 해시**: `{commit_info['hash'][:7]}`  \n"
        content += f"**작성 시각**: {commit_info['time']}  \n"
        content += "**자동 생성**: Obsidian Auto-Sync v3.0  \n"

        return content

    # =========================================================================
    # v3.0: Weekly Sync Method
    # =========================================================================

    def sync_weekly(self, week_offset: int = 0) -> bool:
        """주간 요약 동기화 실행

        Args:
            week_offset: 0=이번 주, -1=지난 주, -2=2주 전 등
        """
        try:
            # 주간 범위 계산
            today = datetime.now()
            # 이번 주 월요일 찾기
            week_start = today - timedelta(days=today.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            # offset 적용
            week_start = week_start + timedelta(weeks=week_offset)
            week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

            print(f"[WEEKLY] Generating summary for {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}")

            # Weekly 생성기 초기화
            weekly_gen = WeeklySummaryGenerator(week_start, week_end)
            weekly_content = weekly_gen.generate_weekly_note()

            # 저장 경로 설정 (개발일지/Weekly/)
            weekly_dir = self.dev_log_dir / "Weekly"
            weekly_dir.mkdir(parents=True, exist_ok=True)

            # 파일명
            week_str = week_start.strftime("%Y-W%W")
            filename = f"{week_str}-weekly-summary.md"
            file_path = weekly_dir / filename

            # 저장
            file_path.write_text(weekly_content, encoding="utf-8")

            print(f"[OK] Weekly summary created: Weekly/{filename}")
            return True

        except Exception as e:
            print(f"[ERROR] Weekly sync failed: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return False


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Obsidian Auto-Sync v3.0 - AI-Enhanced Development Log Generator")
    parser.add_argument("--commit-hash", default="HEAD", help="Commit hash to sync")
    parser.add_argument("--vault", help="Obsidian vault path (optional)")
    parser.add_argument(
        "--version", type=int, default=2, choices=[2, 3], help="Sync version (2=v2.0, 3=v3.0 with extended frontmatter)"
    )
    parser.add_argument("--weekly", action="store_true", help="Generate weekly summary instead of daily log")
    parser.add_argument("--week-offset", type=int, default=0, help="Week offset for weekly summary (0=current, -1=last week)")
    args = parser.parse_args()

    # Repo root 찾기
    repo_root = Path(__file__).resolve().parents[1]

    # Vault 경로
    vault_path = Path(args.vault) if args.vault else None

    # 동기화 실행
    syncer = ObsidianAutoSync(repo_root, vault_path)

    if args.weekly:
        # 주간 요약 생성
        success = syncer.sync_weekly(week_offset=args.week_offset)
    else:
        # 일일 로그 생성
        success = syncer.sync(args.commit_hash, version=args.version)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
