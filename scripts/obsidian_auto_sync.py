#!/usr/bin/env python
"""
Obsidian Auto-Sync v3.6 - AI-Enhanced Development Log Generator

자동으로 Git commit 정보를 분석하여 Obsidian 개발일지를 생성합니다.

Features (v3.6):
- 체크포인트 자동 감지 (커밋 메시지 + diff 패턴 분석)
- 완료된 체크포인트 자동 체크 및 저장

Features (v3.5):
- 학습 진행 상황 추적 (Learning Progress Tracking)
- 고려사항(Considerations) + 주의점(Warnings) 표시
- Bridge Review/Preview (월간 전환 시)

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
Version: 3.6.0 (Checkpoint Auto-Detection)
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
# v3.0: Diff Utilities (Git diff 분석 헬퍼)
# =============================================================================


def extract_added_lines(diff: str) -> str:
    """Git diff에서 추가된 줄만 추출 (+ 로 시작하는 줄)

    이 함수는 diff 전체가 아닌 실제 '추가된 코드'만 분석하도록 합니다.
    문자열 리터럴 내 주석 오탐지를 방지합니다.
    """
    lines = []
    for line in diff.split("\n"):
        # +로 시작하지만 +++ (파일 헤더)는 제외
        if line.startswith("+") and not line.startswith("+++"):
            # 앞의 + 제거
            lines.append(line[1:])
    return "\n".join(lines)


# =============================================================================
# v3.1: AI Metacognition Support (AI 메타인지 연동)
# =============================================================================


def load_ai_metacognition() -> Dict[str, Any]:
    """AI 세션에서 저장한 메타인지 정보 로드

    Returns:
        AI 메타인지 딕셔너리:
        - least_confident: 가장 덜 자신있는 부분 리스트
        - simplifications: 단순화 가정 리스트
        - opinion_changers: 의견 변경 가능 질문 리스트
        - areas_to_improve: 보완 필요 영역 리스트
        - blockers: 현재 차단 요소 리스트
    """
    session_file = Path(".udo/session_state.json")
    if not session_file.exists():
        return {}

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("ai_metacognition", {})
    except (json.JSONDecodeError, IOError):
        return {}


def save_ai_metacognition(metacognition: Dict[str, Any]) -> bool:
    """AI 메타인지 정보를 session_state.json에 저장

    Args:
        metacognition: AI 메타인지 딕셔너리

    Returns:
        성공 여부
    """
    session_file = Path(".udo/session_state.json")
    session_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 기존 데이터 로드
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # 메타인지 정보 업데이트
        data["ai_metacognition"] = metacognition
        data["ai_metacognition_updated"] = datetime.now().isoformat()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (json.JSONDecodeError, IOError):
        return False


# =============================================================================
# v3.5: Learning Progress Tracking (학습 진행 상황 추적)
# =============================================================================

# 3개월 커리큘럼 정의 (Month, Week, 설명, 필수 체크포인트, 고려사항, 주의점)
LEARNING_CURRICULUM = {
    (0, 0): {
        "title": "환경 설정 및 사전 준비",
        "focus": "학습 환경 구성 및 기초 점검",
        "checkpoints": [
            "Python 3.11+ 설치 확인",
            "Node.js 18+ 설치 확인",
            "Git 설정 완료 (user.name, user.email)",
            "Obsidian Vault 생성 및 경로 설정",
            "Claude Pro 구독 및 API 접근 확인",
        ],
        "considerations": [
            "환경 설정은 한 번만 정확히 하면 이후 수정 불필요",
            "버전 호환성 확인 (Python/Node.js 최소 버전)",
        ],
        "warnings": [
            "환경 변수 설정 주의 (OBSIDIAN_VAULT_PATH, API keys)",
            "PATH 설정 확인 (python, node, git 명령어 실행 가능 여부)",
        ],
        "guide": "VibeCoding-Growth-Guide",
    },
    (1, 1): {
        "title": "기초 다지기 - Claude Code 기본",
        "focus": "Claude Code 기본 명령어 익히기",
        "checkpoints": [
            "/sc:analyze 3회 이상 사용",
            "간단한 함수 구현 1회",
        ],
        "considerations": [
            "AI 응답을 그대로 복붙하지 말고 이해한 후 사용",
            "작은 단위로 요청하여 결과 확인",
        ],
        "warnings": [
            "AI가 생성한 코드도 반드시 검토 필요",
            "민감 정보(API키, 비밀번호)를 프롬프트에 포함하지 않기",
        ],
        "guide": "Claude-Skills-Curriculum",
    },
    (1, 2): {
        "title": "기초 다지기 - 코드 분석",
        "focus": "/sc:analyze로 코드 분석 학습",
        "checkpoints": [
            "/sc:analyze --focus quality 1회",
            "/sc:analyze --focus security 1회",
        ],
        "considerations": [
            "분석 결과의 우선순위(severity)를 먼저 확인",
            "모든 경고를 한번에 수정하려 하지 말고 중요한 것부터",
        ],
        "warnings": [
            "보안 취약점은 즉시 수정 (나중에로 미루지 않기)",
            "false positive도 있을 수 있으니 맹신 금지",
        ],
        "guide": "Claude-Skills-Curriculum",
    },
    (1, 3): {
        "title": "기초 다지기 - Context7 MCP",
        "focus": "공식 문서 검색으로 라이브러리 학습",
        "checkpoints": [
            "Context7로 라이브러리 문서 검색 3회",
            "공식 문서 기반 구현 1회",
        ],
        "considerations": [
            "공식 문서 버전과 프로젝트 버전 일치 확인",
            "deprecated 메서드 사용 주의",
        ],
        "warnings": [
            "Stack Overflow보다 공식 문서 우선",
            "오래된 예제 코드는 현재 버전과 다를 수 있음",
        ],
        "guide": "MCP-Combination-Patterns",
    },
    (1, 4): {
        "title": "기초 다지기 - 테스트 작성",
        "focus": "/sc:test로 단위 테스트 작성",
        "checkpoints": [
            "단위 테스트 5개 작성",
            "테스트 커버리지 확인 1회",
        ],
        "considerations": [
            "Happy path뿐 아니라 edge case도 테스트",
            "테스트 이름은 무엇을 테스트하는지 명확하게",
        ],
        "warnings": [
            "테스트가 통과한다고 버그가 없는 게 아님",
            "테스트 건너뛰기(skip) 남발 금지",
        ],
        "guide": "Claude-Skills-Curriculum",
        "bridge_preview": {
            "next_month": "Month 2: 실전 적용",
            "preview": "MCP 서버 조합으로 복잡한 문제 해결",
            "preparation": [
                "Context7 MCP 설치 확인",
                "Sequential MCP 개념 학습",
                "복잡한 디버깅 케이스 1개 준비",
            ],
        },
    },
    (2, 1): {
        "title": "실전 적용 - MCP 조합",
        "focus": "Sequential + Context7 조합 디버깅",
        "checkpoints": [
            "MCP 조합으로 복잡한 버그 해결 1회",
            "Obsidian -> Context7 체인 사용 1회",
        ],
        "considerations": [
            "MCP 서버 간 의존성 순서 중요",
            "먼저 Obsidian(과거 솔루션) 확인 후 Context7",
        ],
        "warnings": [
            "너무 많은 MCP 동시 사용 시 혼란 가능",
            "각 MCP 응답을 검증 후 다음 단계 진행",
        ],
        "guide": "MCP-Combination-Patterns",
        "bridge_review": {
            "previous_month": "Month 1: 기초 다지기",
            "key_concepts": [
                "Claude Code 기본 명령어",
                "/sc:analyze 코드 분석",
                "Context7 공식 문서 검색",
            ],
            "self_check": [
                "간단한 함수를 AI로 구현할 수 있는가?",
                "에러 메시지를 해석하고 해결할 수 있는가?",
            ],
        },
    },
    (2, 2): {
        "title": "실전 적용 - UI 개발",
        "focus": "Magic MCP로 UI 컴포넌트 생성",
        "checkpoints": [
            "Magic MCP로 컴포넌트 생성 2회",
            "Context7 -> Magic 체인 사용 1회",
        ],
        "considerations": [
            "생성된 UI의 접근성(a11y) 확인",
            "반응형 디자인 검증 필수",
        ],
        "warnings": [
            "UI 라이브러리 버전 호환성 확인",
            "생성된 스타일이 기존 디자인 시스템과 충돌하지 않는지 확인",
        ],
        "guide": "MCP-Combination-Patterns",
    },
    (2, 3): {
        "title": "실전 적용 - E2E 테스트",
        "focus": "Playwright로 자동화 테스트",
        "checkpoints": [
            "E2E 테스트 3개 작성",
            "Magic -> Playwright 체인 사용 1회",
        ],
        "considerations": [
            "selector는 data-testid 사용 권장",
            "네트워크 지연 고려한 적절한 timeout 설정",
        ],
        "warnings": [
            "flaky test(가끔 실패하는 테스트) 방치 금지",
            "실제 API 호출 대신 mock 사용 고려",
        ],
        "guide": "MCP-Combination-Patterns",
    },
    (2, 4): {
        "title": "실전 적용 - 워크플로우",
        "focus": "/sc:workflow로 PRD 기반 구현",
        "checkpoints": [
            "/sc:workflow로 구현 계획 1개 생성",
            "계획 기반 구현 완료 1회",
        ],
        "considerations": [
            "워크플로우 각 단계별 완료 기준 명확히",
            "의존성 있는 작업은 순서대로 진행",
        ],
        "warnings": [
            "계획만 세우고 실행 안 하면 무의미",
            "계획 변경 시 문서 업데이트 필수",
        ],
        "guide": "Claude-Skills-Curriculum",
        "bridge_preview": {
            "next_month": "Month 3: 고급 활용",
            "preview": "멀티에이전트 오케스트레이션과 대규모 코드베이스 관리",
            "preparation": [
                "Task 에이전트 개념 이해",
                "Morphllm 대량 편집 학습",
                "Serena 프로젝트 메모리 설정",
            ],
        },
    },
    (3, 1): {
        "title": "고급 활용 - 멀티에이전트",
        "focus": "Task 에이전트 병렬 실행",
        "checkpoints": [
            "2개 이상 에이전트 병렬 실행 1회",
            "Explore 에이전트 사용 2회",
        ],
        "considerations": [
            "에이전트 결과를 종합하여 최종 판단은 본인이",
            "각 에이전트의 전문 영역 파악 후 적절히 활용",
        ],
        "warnings": [
            "에이전트 간 상충되는 의견 발생 가능 - 맥락에 맞게 판단",
            "병렬 실행 시 토큰 소비량 증가에 주의",
        ],
        "guide": "Multi-Agent-Workflows",
        "bridge_review": {
            "previous_month": "Month 2: 실전 적용",
            "key_concepts": [
                "Sequential + Context7 조합",
                "Magic MCP UI 컴포넌트",
                "Playwright E2E 테스트",
            ],
            "self_check": [
                "MCP 서버 2개 이상 조합하여 문제를 해결할 수 있는가?",
                "PRD 기반으로 워크플로우를 설계할 수 있는가?",
            ],
        },
    },
    (3, 2): {
        "title": "고급 활용 - 페르소나 리뷰",
        "focus": "security-engineer 등 페르소나 활용",
        "checkpoints": [
            "security-engineer 리뷰 1회",
            "performance-engineer 리뷰 1회",
        ],
        "considerations": [
            "페르소나별 관점 차이 이해하고 활용",
            "모든 제안을 수용할 필요 없음 - 프로젝트 맥락 고려",
        ],
        "warnings": [
            "보안 리뷰 결과는 반드시 검토 후 적용",
            "성능 최적화는 측정 먼저, 최적화 나중에",
        ],
        "guide": "Multi-Agent-Workflows",
    },
    (3, 3): {
        "title": "고급 활용 - 대량 리팩토링",
        "focus": "Morphllm으로 코드 일괄 수정",
        "checkpoints": [
            "Morphllm 패턴 변환 1회",
            "Sequential -> Morphllm 체인 1회",
        ],
        "considerations": [
            "리팩토링 전 반드시 테스트 스위트 확보",
            "작은 범위부터 시작하여 점진적 확대",
        ],
        "warnings": [
            "대량 수정 전 git commit으로 롤백 포인트 확보 필수",
            "자동 변환 후 반드시 diff 검토",
        ],
        "guide": "MCP-Combination-Patterns",
    },
    (3, 4): {
        "title": "고급 활용 - 프로젝트 메모리",
        "focus": "Serena로 세션 지속성 관리",
        "checkpoints": [
            "/sc:load, /sc:save 사용 1회",
            "프로젝트 심볼 검색 2회",
        ],
        "considerations": [
            "세션 종료 전 중요 컨텍스트 저장 습관화",
            "프로젝트 메모리는 주기적으로 정리",
        ],
        "warnings": [
            "오래된 컨텍스트가 현재 코드와 불일치할 수 있음",
            "민감 정보가 메모리에 저장되지 않도록 주의",
        ],
        "guide": "VibeCoding-Growth-Guide",
    },
}


def load_learning_progress() -> Dict[str, Any]:
    """학습 진행 상황 로드

    Returns:
        learning_progress: {month, week, started_at, checkpoints_done}
    """
    session_file = Path(".udo/session_state.json")
    if not session_file.exists():
        return {"month": 1, "week": 1, "started_at": None, "checkpoints_done": []}

    try:
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        progress = data.get("learning_progress", {})
        if not progress:
            return {"month": 1, "week": 1, "started_at": None, "checkpoints_done": []}
        return progress
    except (json.JSONDecodeError, IOError):
        return {"month": 1, "week": 1, "started_at": None, "checkpoints_done": []}


def save_learning_progress(progress: Dict[str, Any]) -> bool:
    """학습 진행 상황 저장"""
    session_file = Path(".udo/session_state.json")
    session_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}

        # 시작일 자동 설정
        if not progress.get("started_at"):
            progress["started_at"] = datetime.now().isoformat()

        data["learning_progress"] = progress
        data["learning_progress_updated"] = datetime.now().isoformat()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except (json.JSONDecodeError, IOError):
        return False


def get_current_curriculum() -> Dict[str, Any]:
    """현재 학습 단계의 커리큘럼 정보 반환"""
    progress = load_learning_progress()
    month = progress.get("month", 1)
    week = progress.get("week", 1)

    # 범위 체크 (month=0은 사전 준비 주간으로 허용)
    if month < 0:
        month = 0
    if month > 3:
        month = 3
    if month == 0:
        week = 0  # month=0일 때는 week도 0으로 고정
    elif week < 1:
        week = 1
    elif week > 4:
        week = 4

    key = (month, week)
    curriculum = LEARNING_CURRICULUM.get(key, LEARNING_CURRICULUM[(1, 1)])

    return {
        "month": month,
        "week": week,
        "title": curriculum["title"],
        "focus": curriculum["focus"],
        "checkpoints": curriculum["checkpoints"],
        "considerations": curriculum.get("considerations", []),
        "warnings": curriculum.get("warnings", []),
        "guide": curriculum["guide"],
        "checkpoints_done": progress.get("checkpoints_done", []),
    }


# =============================================================================
# v3.6: Checkpoint Auto-Detection (체크포인트 자동 감지)
# =============================================================================

# 체크포인트별 감지 패턴 정의
# 각 키는 체크포인트 설명의 일부이며, 값은 해당 체크포인트 완료를 감지하는 정규식 패턴 리스트
CHECKPOINT_PATTERNS: Dict[str, List[str]] = {
    # Week 0 (환경 설정) patterns
    "Python": [r"python.*3\.\d+", r"pip\s+install", r"requirements\.txt"],
    "Node.js": [r"node.*\d+\.", r"npm\s+install", r"package\.json"],
    "Git 설정": [r"git\s+config", r"user\.name", r"user\.email"],
    "Obsidian": [r"obsidian", r"vault", r"\.md\s+생성"],
    "Claude": [r"claude", r"anthropic", r"api.*key"],
    # Week 1 (기초 다지기 - Claude Code 기본) patterns
    "/sc:analyze": [
        r"sc:analyze",
        r"분석\s*완료",
        r"analyze.*quality",
        r"analyze.*security",
        r"quality.*check",
        r"코드\s*분석",
    ],
    "함수 구현": [
        r"def\s+\w+\s*\(",
        r"function\s+\w+\s*\(",
        r"const\s+\w+\s*=\s*\(",
        r"async\s+def\s+\w+",
        r"impl.*function",
        r"구현\s*완료",
    ],
    # Week 2 (기초 다지기 - 코드 분석) patterns
    "코드 분석": [
        r"sc:analyze",
        r"quality.*check",
        r"lint.*pass",
        r"pylint",
        r"flake8",
        r"eslint",
    ],
    "--focus quality": [r"--focus\s+quality", r"quality\s+분석", r"코드\s*품질"],
    "--focus security": [r"--focus\s+security", r"security\s+분석", r"보안\s*점검"],
    # Week 3 (기초 다지기 - Context7 MCP) patterns
    "Context7": [
        r"context7",
        r"mcp.*context",
        r"공식.*문서",
        r"라이브러리.*문서",
        r"documentation",
    ],
    "공식 문서": [r"official.*doc", r"공식.*문서", r"문서.*기반"],
    # Week 4 (기초 다지기 - 테스트 작성) patterns
    "테스트 작성": [
        r"test_\w+",
        r"\.test\.",
        r"pytest",
        r"jest",
        r"spec\.",
        r"unittest",
        r"테스트.*작성",
    ],
    "단위 테스트": [r"unit.*test", r"단위.*테스트", r"test_\w+\.py"],
    "테스트 커버리지": [r"coverage", r"--cov", r"커버리지", r"\d+%\s*coverage"],
    # Month 2 Week 1 (실전 적용 - MCP 조합) patterns
    "MCP 조합": [
        r"mcp.*조합",
        r"sequential.*context7",
        r"체인.*사용",
        r"mcp.*chain",
    ],
    "Obsidian -> Context7": [r"obsidian.*context7", r"지식.*문서", r"3tier"],
    # Month 2 Week 2 (실전 적용 - UI 개발) patterns
    "Magic MCP": [r"magic.*mcp", r"21st\.dev", r"ui.*컴포넌트", r"component.*생성"],
    "Context7 -> Magic": [r"context7.*magic", r"문서.*ui", r"pattern.*component"],
    # Month 2 Week 3 (실전 적용 - E2E 테스트) patterns
    "E2E 테스트": [
        r"e2e",
        r"playwright",
        r"cypress",
        r"end.to.end",
        r"integration.*test",
    ],
    "Magic -> Playwright": [r"magic.*playwright", r"ui.*e2e", r"component.*test"],
    # Month 2 Week 4 (실전 적용 - 워크플로우) patterns
    "/sc:workflow": [r"sc:workflow", r"workflow.*생성", r"계획.*생성"],
    "계획 기반": [r"prd.*기반", r"계획.*구현", r"workflow.*impl"],
    # Month 3 Week 1 (고급 활용 - 멀티에이전트) patterns
    "에이전트 병렬": [r"parallel.*agent", r"병렬.*실행", r"multi.*agent"],
    "Explore 에이전트": [r"explore.*agent", r"탐색.*에이전트", r"exploration"],
    # Month 3 Week 2 (고급 활용 - 페르소나 리뷰) patterns
    "security-engineer": [r"security.engineer", r"보안.*리뷰", r"security.*review"],
    "performance-engineer": [r"performance.engineer", r"성능.*리뷰", r"perf.*review"],
    # Month 3 Week 3 (고급 활용 - 대량 리팩토링) patterns
    "리팩토링": [
        r"refactor",
        r"리팩토링",
        r"cleanup",
        r"개선",
        r"restructure",
    ],
    "Morphllm": [r"morphllm", r"morph.*transform", r"패턴.*변환"],
    "Sequential -> Morphllm": [r"sequential.*morph", r"분석.*변환"],
    # Month 3 Week 4 (고급 활용 - 프로젝트 메모리) patterns
    "/sc:load": [r"sc:load", r"세션.*로드", r"context.*load"],
    "/sc:save": [r"sc:save", r"세션.*저장", r"context.*save"],
    "심볼 검색": [r"symbol.*search", r"심볼.*검색", r"find.*symbol"],
    # General patterns (공통)
    "버그 수정": [r"fix", r"bug", r"버그", r"수정", r"resolve", r"해결"],
}


def detect_checkpoint_completion(commit_message: str, diff: str, current_curriculum: Dict[str, Any]) -> List[str]:
    """커밋 메시지와 diff를 분석하여 완료된 체크포인트 감지

    Args:
        commit_message: Git 커밋 메시지
        diff: Git diff 내용
        current_curriculum: 현재 학습 단계 커리큘럼 정보

    Returns:
        완료된 체크포인트 설명 리스트 (새로 감지된 것만)
    """
    newly_completed = []
    checkpoints = current_curriculum.get("checkpoints", [])
    already_done = set(current_curriculum.get("checkpoints_done", []))

    # 분석 대상 텍스트 결합 (커밋 메시지 + 추가된 줄만)
    added_lines = extract_added_lines(diff)
    combined_text = f"{commit_message}\n{added_lines}".lower()

    for checkpoint in checkpoints:
        # 이미 완료된 체크포인트는 스킵
        if checkpoint in already_done:
            continue

        # 체크포인트와 매칭되는 패턴 찾기
        checkpoint_matched = False
        for pattern_key, patterns in CHECKPOINT_PATTERNS.items():
            # 패턴 키가 체크포인트 설명에 포함되어 있는지 확인
            if pattern_key.lower() in checkpoint.lower():
                # 해당 패턴들 중 하나라도 매칭되면 완료로 판정
                for pattern in patterns:
                    if re.search(pattern, combined_text, re.IGNORECASE):
                        newly_completed.append(checkpoint)
                        checkpoint_matched = True
                        break
                if checkpoint_matched:
                    break

    return newly_completed


def update_checkpoints_done(newly_completed: List[str]) -> bool:
    """완료된 체크포인트를 learning_progress에 저장

    Args:
        newly_completed: 새로 완료된 체크포인트 리스트

    Returns:
        저장 성공 여부
    """
    if not newly_completed:
        return True

    progress = load_learning_progress()
    existing = set(progress.get("checkpoints_done", []))
    updated = existing.union(set(newly_completed))

    if updated != existing:
        progress["checkpoints_done"] = list(updated)
        return save_learning_progress(progress)
    return True


def is_real_comment(line: str, pattern: str) -> bool:
    """실제 주석인지 문자열 리터럴인지 구분

    Args:
        line: 검사할 라인
        pattern: 찾는 패턴 (예: "# TODO:")

    Returns:
        True if 실제 주석, False if 문자열 리터럴
    """
    # 문자열 리터럴 내부인지 확인
    # 패턴 앞에 따옴표가 있으면 문자열 내부일 가능성
    pattern_pos = line.find(pattern)
    if pattern_pos == -1:
        return False

    before = line[:pattern_pos]

    # 열린 따옴표 개수 확인 (홀수면 문자열 내부)
    single_quotes = before.count("'") - before.count("\\'")
    double_quotes = before.count('"') - before.count('\\"')

    # 홀수면 문자열 내부로 판단
    if single_quotes % 2 == 1 or double_quotes % 2 == 1:
        return False

    return True


def clean_extracted_text(text: str) -> str:
    """추출된 텍스트에서 노이즈 제거

    - 이스케이프 문자 제거
    - 짧은 무의미 문자열 제거
    - 따옴표 제거
    - 코드 설명 주석 필터링
    """
    if not text:
        return ""

    # 이스케이프 문자 포함 시 무효
    if "\\n" in text or "\\r" in text or "\\t" in text:
        return ""

    # 따옴표로 시작/끝나면 문자열 리터럴
    text = text.strip()
    if text.startswith('"') or text.startswith("'"):
        return ""
    if text.endswith('",') or text.endswith("',"):
        return ""

    # 너무 짧거나 무의미한 패턴
    if len(text) < 5:
        return ""

    # 코드 조각 필터링
    noise_patterns = [
        r"^\s*\(",
        r"^\s*\)",
        r"^\s*\[",
        r"^\s*\]",
        r"^\s*\{",
        r"^\s*\}",
        r"^\s*#\s*$",
        r"^[,;:\"\']",
    ]
    for pattern in noise_patterns:
        if re.match(pattern, text):
            return ""

    # 코드 설명 주석 필터링 (코드 동작 설명은 제외)
    # "추출", "반환", "생성", "검사" 등으로만 구성된 짧은 설명은 제외
    code_desc_patterns = [
        r"^(추출|반환|생성|검사|확인|변환|처리|호출|설정|초기화|로드|저장)\s*$",
        r"^(에서|에게|으로|로|를|을|이|가)\s",  # 조사로 시작하면 불완전한 문장
        r"^\w{1,3}\s+(추출|반환|생성|검사)$",  # 짧은 명사 + 동작
    ]
    for pattern in code_desc_patterns:
        if re.match(pattern, text, re.I):
            return ""

    return text


def extract_real_comments(diff: str, prefix: str, require_colon: bool = None) -> List[str]:
    """diff에서 실제 주석만 추출 (문자열 리터럴 제외)

    Args:
        diff: Git diff 전체 텍스트
        prefix: 찾을 주석 접두사 (예: "TODO", "FIXME", "TIL")
        require_colon: 콜론 필수 여부 (None=자동 결정)
            - TODO, FIXME, HACK, XXX, RISK: 콜론 필수 (액션 아이템)
            - TIL, Solution, Pattern, Decision, Why, Rollback: 콜론 선택

    Returns:
        추출된 주석 내용 리스트
    """
    added_lines = extract_added_lines(diff)
    results = []

    # 액션 아이템 접두사는 콜론 필수 (코드 설명 주석과 구분)
    action_prefixes = ["TODO", "FIXME", "HACK", "XXX", "RISK"]

    if require_colon is None:
        require_colon = prefix.upper() in action_prefixes

    # 패턴 구성: 콜론 필수 여부에 따라 다름
    if require_colon:
        # 콜론 필수: # TODO: 내용 (공백 허용)
        pattern = rf"^\s*#\s*{prefix}\s*:\s*(.+)"
    else:
        # 콜론 선택: # TIL 내용 또는 # TIL: 내용
        pattern = rf"^\s*#\s*{prefix}:?\s+(.+)"

    for line in added_lines.split("\n"):
        match = re.search(pattern, line, re.I)
        if match:
            content = match.group(1).strip()
            # 문자열 리터럴 내부인지 확인
            if is_real_comment(line, f"# {prefix}"):
                cleaned = clean_extracted_text(content)
                if cleaned:
                    results.append(cleaned)

    return results


# =============================================================================
# v3.0: Flag Detection System
# =============================================================================


class FlagDetector:
    """Git diff와 커밋 정보에서 플래그 자동 감지

    v3.0.1: 추가된 줄만 분석하여 오탐지 방지
    """

    def __init__(self, diff: str, commit_info: Dict):
        self.diff = diff
        # 추가된 줄만 추출하여 분석 (삭제된 줄, 컨텍스트 제외)
        self.added_lines = extract_added_lines(diff)
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
            r"learned|학습|배움",  # 키워드
            r"refactor",  # 리팩토링 (학습 포함)
        ]
        # 파일 기반 감지
        if any("test" in f.lower() for f in self.files):
            return True
        # 추가된 줄 기반 감지
        if any(re.search(p, self.added_lines, re.I) for p in patterns):
            return True
        # 명시적 TIL 주석 (실제 주석만)
        return len(extract_real_comments(self.diff, "TIL")) > 0

    def detect_solution(self) -> bool:
        """해결책 감지: 버그 수정, 문제 해결"""
        patterns = [
            r"해결|수정|고침",  # 한글 키워드
            r"fixed|resolved",  # 영어 키워드
        ]
        if any(p in self.message for p in ["fix", "bug", "resolve", "해결"]):
            return True
        # 추가된 줄에서 키워드 검색
        if any(re.search(p, self.added_lines, re.I) for p in patterns):
            return True
        # 명시적 Solution 주석 (실제 주석만)
        return len(extract_real_comments(self.diff, "Solution")) > 0

    def detect_pattern(self) -> bool:
        """패턴 감지: 디자인 패턴, 아키텍처 패턴"""
        # 디자인 패턴 클래스/함수 정의 감지 (추가된 줄에서만)
        pattern_keywords = [
            r"class\s+\w*(singleton|factory|observer|strategy|decorator|adapter|facade)",
            r"def\s+\w*(factory|observer|strategy)",
        ]
        if any(re.search(p, self.added_lines, re.I) for p in pattern_keywords):
            return True
        # 명시적 Pattern 주석 (실제 주석만)
        return len(extract_real_comments(self.diff, "Pattern")) > 0

    def detect_uncertainty(self) -> bool:
        """불확실성 감지: 미확정 사항, 리스크"""
        # 실제 TODO/FIXME 주석 확인
        if extract_real_comments(self.diff, "TODO"):
            return True
        if extract_real_comments(self.diff, "FIXME"):
            return True
        if extract_real_comments(self.diff, "RISK"):
            return True
        # 추가된 줄에서 불확실성 키워드 검색
        uncertainty_patterns = [
            r"불확실|uncertain",  # 키워드
            r"\?\?\?|XXX",  # 의문 마커
            r"maybe|perhaps|아마",  # 불확실 표현
        ]
        return any(re.search(p, self.added_lines, re.I) for p in uncertainty_patterns)

    def detect_rollback(self) -> bool:
        """롤백 계획 감지: 롤백 전략, 복구 계획"""
        # 마이그레이션 파일이 있으면 롤백 계획 필요
        if any("migration" in f.lower() for f in self.files):
            return True
        # 명시적 Rollback 주석
        if extract_real_comments(self.diff, "Rollback"):
            return True
        # 추가된 줄에서 롤백 관련 키워드 검색
        rollback_patterns = [
            r"rollback|롤백",  # 키워드
            r"revert|복구|되돌리",  # 복구 키워드
            r"backup|백업",  # 백업 키워드
            r"feature.?flag",  # 피처 플래그
        ]
        return any(re.search(p, self.added_lines, re.I) for p in rollback_patterns)

    def detect_debt(self) -> bool:
        """기술부채 감지: TODO, FIXME, 임시 해결책"""
        # 실제 주석 확인 (문자열 리터럴 제외)
        if extract_real_comments(self.diff, "TODO"):
            return True
        if extract_real_comments(self.diff, "FIXME"):
            return True
        if extract_real_comments(self.diff, "HACK"):
            return True
        if extract_real_comments(self.diff, "XXX"):
            return True
        # 추가된 줄에서 기술부채 패턴 검색
        debt_patterns = [
            r"temporary|임시",  # 임시 키워드
            r"workaround",  # 우회 해결책
            r"@pytest\.mark\.skip",  # 스킵된 테스트
            r"#\s*type:\s*ignore",  # 타입 무시 (주석 형태만)
        ]
        return any(re.search(p, self.added_lines, re.I) for p in debt_patterns)

    def detect_decision(self) -> bool:
        """의사결정 감지: 아키텍처 변경, 라이브러리 추가"""
        # requirements.txt 또는 package.json 변경
        if any(f in ["requirements.txt", "package.json", "pyproject.toml"] for f in self.files):
            return True
        # 명시적 Decision/Why 주석
        if extract_real_comments(self.diff, "Decision"):
            return True
        if extract_real_comments(self.diff, "Why"):
            return True
        # 추가된 줄에서 의사결정 키워드 검색
        decision_patterns = [
            r"선택|결정|채택",  # 한글 키워드
            r"chose|decided|selected",  # 영어 키워드
        ]
        return any(re.search(p, self.added_lines, re.I) for p in decision_patterns)


# =============================================================================
# v3.0: AI Context Generator
# =============================================================================


class AIContextGenerator:
    """AI 컨텍스트 자동 생성

    v3.0.1: 실제 주석만 추출하여 오탐지 방지
    """

    def __init__(self, commit_info: Dict, diff: str):
        self.commit_info = commit_info
        self.diff = diff
        self.added_lines = extract_added_lines(diff)
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

        # 실제 TODO 주석에서 추출 (문자열 리터럴 제외)
        real_todos = extract_real_comments(self.diff, "TODO")
        for todo in real_todos[:3]:
            actions.append(f"TODO: {todo[:50]}")

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

        # 실제 FIXME 주석에서 추출 (문자열 리터럴 제외)
        real_fixmes = extract_real_comments(self.diff, "FIXME")
        for fixme in real_fixmes[:3]:
            warnings.append(f"FIXME: {fixme[:50]}")

        # 추가된 줄에서 위험 패턴 감지
        if re.search(r"rm\s+-rf|DROP\s+TABLE|DELETE\s+FROM", self.added_lines, re.I):
            warnings.append("위험한 명령어 감지 - 주의 필요")

        if re.search(r"password|secret|api.?key", self.added_lines, re.I):
            warnings.append("민감 정보 노출 가능성 - 확인 필요")

        if len(self.files) > 20:
            warnings.append(f"대규모 변경 ({len(self.files)}개 파일) - 신중한 리뷰 필요")

        return warnings[:5]  # 최대 5개


# =============================================================================
# v3.0: Section Generator (9 Daily Sections + Conditional Rendering)
# =============================================================================


class SectionGenerator:
    """9개 Daily 섹션 생성기 (조건부 렌더링 지원)

    v3.0.1: 실제 주석만 추출하여 오탐지 방지
    """

    def __init__(self, commit_info: Dict, flags: Dict[str, bool], session_state: Dict, diff: str, repo_root: Path):
        self.commit_info = commit_info
        self.flags = flags
        self.session_state = session_state
        self.diff = diff
        self.added_lines = extract_added_lines(diff)
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
        """TIL 섹션 - 배운 점 자동 추출 (구체적 인사이트 + 초보자 학습 포인트)

        v3.2: 초보자가 배워야 할 점과 적용 방법 추가
        v3.4: 전문가 검증된 메트릭 추가 (카테고리 + 적용 가능성)
              - 제거: difficulty, utility, acquisition_time (측정 불가)
              - 추가: category (Pattern/Tool/Concept/Debug/Performance)
              - 추가: applicability (Immediate/Future/General)
        """
        content = "## Today I Learned (TIL)\n\n"

        # v3.4: 구조화된 TIL 항목 (카테고리 + 적용 가능성)
        til_items: List[Dict[str, str]] = []
        beginner_tips = []  # 초보자 학습 포인트

        # 테스트 추가 감지 - 구체적인 파일명 포함
        test_files = [f for f in self.files if "test" in f.lower()]
        if test_files:
            test_names = [Path(f).stem for f in test_files[:2]]
            til_items.append(
                {
                    "item": f"테스트 작성: `{', '.join(test_names)}`",
                    "category": "Tool",
                    "applicability": "Immediate",
                }
            )
            beginner_tips.append(
                "**[초보자 팁]** 테스트를 먼저 작성하면 요구사항이 명확해지고, "
                "나중에 코드를 수정해도 기존 기능이 깨지지 않았는지 바로 확인할 수 있어요."
            )

        # 리팩토링 감지 - 무엇을 리팩토링했는지 추출
        if "refactor" in self.message.lower():
            # 리팩토링 대상 추출
            refactor_target = re.search(r"refactor[:\s]+(.+?)(?:\n|$)", self.message, re.I)
            if refactor_target:
                target = refactor_target.group(1).strip()[:40]
                til_items.append(
                    {
                        "item": f"리팩토링: {target}",
                        "category": "Pattern",
                        "applicability": "Immediate",
                    }
                )
            else:
                til_items.append(
                    {
                        "item": "리팩토링으로 코드 구조 개선",
                        "category": "Pattern",
                        "applicability": "Immediate",
                    }
                )
            beginner_tips.append(
                "**[초보자 팁]** 리팩토링은 기능은 그대로 두고 코드 구조만 개선하는 것이에요. "
                "항상 테스트가 통과하는 상태에서 조금씩 변경하세요."
            )

        # 새 패턴/클래스 감지 - 구체적인 클래스명 포함
        new_classes = re.findall(r"class\s+(\w+)", self.added_lines)
        if new_classes:
            class_names = list(set(new_classes))[:3]
            til_items.append(
                {
                    "item": f"새 클래스 설계: `{', '.join(class_names)}`",
                    "category": "Concept",
                    "applicability": "Future",
                }
            )
            beginner_tips.append(
                "**[초보자 팁]** 클래스는 관련된 데이터와 기능을 묶는 설계 도구예요. "
                "하나의 클래스는 하나의 책임만 갖도록(SRP) 설계하세요."
            )

        # 새 함수 감지 - 구체적인 함수명 포함
        new_funcs = re.findall(r"def\s+(\w+)\s*\(", self.added_lines)
        if new_funcs and not new_classes:  # 클래스 없이 함수만 있는 경우
            func_names = [f for f in set(new_funcs) if not f.startswith("_")][:3]
            if func_names:
                til_items.append(
                    {
                        "item": f"새 함수 구현: `{', '.join(func_names)}`",
                        "category": "Concept",
                        "applicability": "Future",
                    }
                )
                beginner_tips.append(
                    "**[초보자 팁]** 함수 이름은 동사로 시작하고, 무엇을 하는지 명확히 드러내세요. "
                    "한 함수는 한 가지 일만 하도록(Single Responsibility) 작성하세요."
                )

        # 성능 최적화 - 구체적인 기법 추출
        perf_patterns = {
            "cache": ("캐싱 적용으로 반복 연산 최소화", "같은 계산을 여러 번 하지 않도록 결과를 저장해두는 기법"),
            "memoiz": ("메모이제이션으로 함수 결과 재사용", "함수의 입력값에 대한 결과를 기억해서 재계산 방지"),
            "async": ("비동기 처리로 응답성 향상", "I/O 작업 중 다른 작업을 할 수 있게 해주는 패턴"),
            "parallel": ("병렬 처리로 성능 개선", "여러 작업을 동시에 실행해 전체 시간 단축"),
            "batch": ("배치 처리로 I/O 최적화", "여러 요청을 모아서 한 번에 처리하는 기법"),
            "lazy": ("지연 로딩으로 초기화 시간 단축", "필요할 때까지 로딩을 미루는 최적화 기법"),
        }
        for pattern, (desc, tip) in perf_patterns.items():
            if pattern in self.added_lines.lower():
                til_items.append(
                    {
                        "item": f"성능 최적화: {desc}",
                        "category": "Performance",
                        "applicability": "General",
                    }
                )
                beginner_tips.append(f"**[초보자 팁]** {tip}. 먼저 측정하고, 병목 지점을 찾은 후 최적화하세요.")
                break

        # 에러 처리 개선
        if "try:" in self.added_lines or "except" in self.added_lines:
            til_items.append(
                {
                    "item": "에러 처리 강화: 예외 상황에 대한 안정성 확보",
                    "category": "Debug",
                    "applicability": "General",
                }
            )
            beginner_tips.append(
                "**[초보자 팁]** try-except는 예상 가능한 에러만 잡으세요. "
                "`except Exception:`처럼 너무 광범위하게 잡으면 버그를 숨길 수 있어요."
            )

        # 타입 힌팅 추가
        if ": str" in self.added_lines or ": int" in self.added_lines or "-> " in self.added_lines:
            til_items.append(
                {
                    "item": "타입 힌팅 적용: 코드 문서화 및 IDE 지원 향상",
                    "category": "Tool",
                    "applicability": "General",
                }
            )
            beginner_tips.append(
                "**[초보자 팁]** 타입 힌팅은 함수가 어떤 값을 받고 반환하는지 명시해요. "
                "IDE 자동완성과 버그 조기 발견에 큰 도움이 됩니다."
            )

        # 명시적 TIL 주석 추출 (실제 주석만)
        til_comments = extract_real_comments(self.diff, "TIL")
        for comment in til_comments[:3]:
            til_items.append(
                {
                    "item": comment[:80],
                    "category": self._estimate_til_category(comment),
                    "applicability": "Immediate",
                }
            )

        # v3.4: 테이블 형식으로 렌더링
        if til_items:
            content += "| 학습 항목 | 카테고리 | 적용 가능성 |\n"
            content += "|----------|---------|-------------|\n"
            for item in til_items[:6]:
                cat_emoji = {
                    "Pattern": "🔄",
                    "Tool": "🔧",
                    "Concept": "💡",
                    "Debug": "🐛",
                    "Performance": "⚡",
                }.get(item["category"], "📝")
                appl_emoji = {
                    "Immediate": "🎯 이번 프로젝트",
                    "Future": "🔮 다른 프로젝트",
                    "General": "🌐 범용",
                }.get(item["applicability"], item["applicability"])
                content += f"| {item['item']} | {cat_emoji} {item['category']} | {appl_emoji} |\n"
            content += "\n"

            # 초보자 학습 포인트 추가
            if beginner_tips:
                content += "### 💡 초보자 학습 포인트\n\n"
                for tip in beginner_tips[:3]:
                    content += f"{tip}\n\n"
        else:
            content += "- (자동 감지된 학습 항목 없음 - 수동 작성 권장)\n\n"

        return content

    def _estimate_til_category(self, item: str) -> str:
        """TIL 항목의 카테고리 추정 (v3.4)

        Categories: Pattern, Tool, Concept, Debug, Performance
        """
        item_lower = item.lower()

        # Performance 키워드
        if any(k in item_lower for k in ["성능", "최적화", "cache", "async", "parallel", "lazy"]):
            return "Performance"

        # Debug 키워드
        if any(k in item_lower for k in ["에러", "버그", "디버그", "fix", "debug", "exception"]):
            return "Debug"

        # Pattern 키워드
        if any(k in item_lower for k in ["패턴", "리팩토링", "factory", "singleton", "observer"]):
            return "Pattern"

        # Tool 키워드
        if any(k in item_lower for k in ["테스트", "도구", "설정", "config", "pytest", "lint"]):
            return "Tool"

        # Default: Concept
        return "Concept"

    def _estimate_debt_severity(self, debt_type: str, desc: str) -> int:
        """기술부채 심각도 추정 (0-100) (v3.4)

        Args:
            debt_type: 부채 유형 (TODO, FIXME, HACK)
            desc: 부채 설명 텍스트

        Returns:
            0-100 범위의 심각도 점수
        """
        # 유형별 기본 심각도
        base_severity = {
            "FIXME": 80,  # 버그/문제 → 높은 심각도
            "HACK": 70,  # 임시 해결책 → 중상 심각도
            "TODO": 50,  # 구현 예정 → 중간 심각도
            "SKIP": 60,  # 스킵 테스트 → 중간 심각도
            "TYPE": 40,  # 타입 무시 → 낮은 심각도
        }.get(debt_type, 50)

        desc_lower = desc.lower()

        # 심각도 증가 키워드
        if any(k in desc_lower for k in ["security", "보안", "auth", "인증"]):
            base_severity = min(100, base_severity + 20)
        elif any(k in desc_lower for k in ["critical", "긴급", "urgent", "asap"]):
            base_severity = min(100, base_severity + 15)
        elif any(k in desc_lower for k in ["production", "프로덕션", "배포"]):
            base_severity = min(100, base_severity + 10)

        # 심각도 감소 키워드
        if any(k in desc_lower for k in ["later", "나중에", "eventually", "maybe"]):
            base_severity = max(20, base_severity - 10)
        elif any(k in desc_lower for k in ["minor", "사소한", "cosmetic"]):
            base_severity = max(20, base_severity - 15)

        return base_severity

    def _estimate_debt_effort(self, desc: str) -> str:
        """기술부채 수정 노력 추정 (T-shirt sizing) (v3.4)

        Args:
            desc: 부채 설명 텍스트

        Returns:
            S (< 1시간), M (1-4시간), L (1-3일), XL (> 3일)
        """
        desc_lower = desc.lower()

        # XL 키워드 (대규모 리팩토링, 아키텍처 변경)
        if any(k in desc_lower for k in ["refactor entire", "전체 리팩토링", "architecture", "아키텍처"]):
            return "XL"

        # L 키워드 (복잡한 구현)
        if any(k in desc_lower for k in ["implement", "구현", "migration", "마이그레이션", "redesign"]):
            return "L"

        # S 키워드 (간단한 수정)
        if any(k in desc_lower for k in ["typo", "오타", "rename", "이름 변경", "comment", "주석"]):
            return "S"

        # Default: M
        return "M"

    def _estimate_debt_impact(self, desc: str) -> str:
        """기술부채 누적 리스크 유형 추정 (v3.4)

        Args:
            desc: 부채 설명 텍스트

        Returns:
            Security, Performance, Maintenance, Reliability 중 하나
        """
        desc_lower = desc.lower()

        # Security 키워드
        if any(k in desc_lower for k in ["security", "보안", "auth", "인증", "xss", "injection", "권한"]):
            return "Security"

        # Performance 키워드
        if any(k in desc_lower for k in ["performance", "성능", "slow", "느림", "optimize", "최적화", "cache"]):
            return "Performance"

        # Reliability 키워드
        if any(k in desc_lower for k in ["test", "테스트", "error", "에러", "exception", "crash", "fail"]):
            return "Reliability"

        # Default: Maintenance
        return "Maintenance"

    def _estimate_decision_scope(self, desc: str) -> str:
        """의사결정 범위 추정 (v3.4)

        Args:
            desc: 결정 설명 텍스트

        Returns:
            Local (단일 파일), Module (모듈), System (시스템 전체)
        """
        desc_lower = desc.lower()

        # System 키워드
        if any(k in desc_lower for k in ["architecture", "아키텍처", "전체", "system", "global", "all"]):
            return "System"

        # Local 키워드
        if any(k in desc_lower for k in ["local", "함수", "function", "method", "변수", "variable"]):
            return "Local"

        # Default: Module
        return "Module"

    # -------------------------------------------------------------------------
    # Section 4: Solutions & Patterns (has_solution OR has_pattern)
    # -------------------------------------------------------------------------
    def _section_solutions_patterns(self) -> str:
        """Solutions & Patterns 섹션

        v3.2: 초보자를 위한 패턴 설명 및 언제 사용하는지 가이드 추가
        """
        content = "## Solutions & Patterns\n\n"

        # 디자인 패턴 설명 사전 (초보자용)
        pattern_explanations = {
            "Singleton": (
                "애플리케이션 전체에서 인스턴스가 하나만 존재해야 할 때 사용",
                "예: 설정 관리자, 로거, DB 연결 풀",
            ),
            "Factory": (
                "객체 생성 로직을 분리해서 유연성을 높일 때 사용",
                "예: 다양한 타입의 객체를 조건에 따라 생성할 때",
            ),
            "Observer": (
                "한 객체의 상태 변화를 여러 객체에게 알릴 때 사용",
                "예: 이벤트 시스템, 구독/발행 패턴",
            ),
            "Strategy": (
                "알고리즘을 런타임에 교체할 수 있게 할 때 사용",
                "예: 정렬 방식, 결제 방식 선택",
            ),
            "Decorator": (
                "기존 클래스를 수정하지 않고 기능을 추가할 때 사용",
                "예: 로깅, 캐싱, 권한 체크 래퍼",
            ),
            "Adapter": (
                "호환되지 않는 인터페이스를 연결할 때 사용",
                "예: 외부 라이브러리를 내부 인터페이스에 맞출 때",
            ),
            "Facade": (
                "복잡한 서브시스템을 단순한 인터페이스로 감쌀 때 사용",
                "예: 여러 API를 하나의 간단한 함수로 묶을 때",
            ),
            "Proxy": (
                "객체에 대한 접근을 제어하거나 추가 동작을 넣을 때 사용",
                "예: 지연 로딩, 접근 권한 체크, 로깅",
            ),
            "Mixin": (
                "다중 상속 없이 여러 클래스에 기능을 추가할 때 사용",
                "예: 공통 유틸리티 메서드 공유",
            ),
        }

        # 해결책 추출 (v3.5: 자동 추출 로직 강화)
        if self.flags.get("has_solution"):
            content += "### Solutions\n\n"
            extracted_solutions = []

            # 1. 실제 Solution 주석 추출
            solutions = extract_real_comments(self.diff, "Solution")
            if solutions:
                for sol in solutions[:5]:
                    extracted_solutions.append(sol[:80])

            # 2. 커밋 메시지에서 해결책 패턴 자동 추출 (v3.5)
            fix_patterns = {
                r"fix(?:ed|es)?[:\s]+(.+?)(?:\n|$)": "버그 수정",
                r"resolve[ds]?[:\s]+(.+?)(?:\n|$)": "이슈 해결",
                r"(?:수정|고침|해결)[:\s]+(.+?)(?:\n|$)": "문제 해결",
                r"by[:\s]+(.+?)(?:\n|$)": "해결 방법",
            }
            for pattern, prefix in fix_patterns.items():
                matches = re.findall(pattern, self.message, re.I)
                for match in matches[:2]:
                    if len(match) > 5:
                        extracted_solutions.append(f"{prefix}: {match[:60]}")

            # 3. diff에서 수정 패턴 자동 분석 (v3.5)
            code_fix_patterns = {
                r"[-]\s*.*(?:bug|error|issue).*\n[+]\s*(.+)": "코드 수정",
                r"[-]\s*#.*(?:TODO|FIXME).*\n[+]\s*(.+)": "기술부채 해결",
                r"[+]\s*try:.*\n[+]\s*(.+?)\n[+]\s*except": "예외 처리 추가",
            }
            for pattern, prefix in code_fix_patterns.items():
                matches = re.findall(pattern, self.diff, re.I | re.MULTILINE)
                for match in matches[:2]:
                    if len(match) > 10:
                        extracted_solutions.append(f"{prefix}: {match[:50]}...")

            # 결과 렌더링
            if extracted_solutions:
                for sol in extracted_solutions[:5]:
                    content += f"- {sol}\n"
            elif "fix" in self.message.lower():
                content += f"- {self.message.split(chr(10))[0]}\n"
            else:
                content += "- (Solution 주석을 추가하여 해결책 기록 권장)\n"
            content += "\n"

            # 바이브코딩 학습 가이드 (v3.5 추가)
            content += "### 🎯 바이브코딩 성장 가이드 (초보자용)\n\n"
            content += "**[프롬프트 팁]** AI에게 명확한 컨텍스트를 제공하세요:\n"
            content += "- 현재 상황 → 원하는 결과 → 제약 조건 순으로 설명\n"
            content += '- 예: "FastAPI에서 401 에러 발생. JWT 토큰 검증 로직 수정 필요. Python 3.11 사용 중"\n\n'

            content += "**[SW 설계 원칙]** 검증된 이론 학습 추천:\n"
            content += "- **SOLID 원칙**: 단일 책임(S), 개방-폐쇄(O), 리스코프 치환(L), 인터페이스 분리(I), 의존성 역전(D)\n"
            content += "- **DRY/KISS/YAGNI**: 반복 금지, 단순하게, 필요할 때만 구현\n"
            content += '- 📚 추천: "Clean Code" (Robert C. Martin), "Refactoring" (Martin Fowler)\n\n'

            content += "**[오류 정정 프로세스]** 체계적 디버깅 5단계:\n"
            content += "1. 에러 메시지 정확히 읽기 (스택 트레이스 분석)\n"
            content += "2. 최소 재현 케이스 만들기\n"
            content += "3. 가설 수립 → 검증 → 반복\n"
            content += "4. 수정 후 회귀 테스트\n"
            content += "5. 해결책 문서화 (다음에 재사용)\n\n"

            content += "**[테스트 전략]** TDD/BDD 접근법:\n"
            content += "- 테스트 먼저 작성 → 실패 확인 → 코드 작성 → 통과 확인 → 리팩토링\n"
            content += "- 경계값, 엣지 케이스, 예외 상황 우선 테스트\n"
            content += '- 📚 추천: "Test-Driven Development" (Kent Beck)\n\n'

        # 패턴 추출
        if self.flags.get("has_pattern"):
            content += "### Patterns Applied\n\n"
            # 클래스/함수 정의에서 패턴명 추출
            pattern_defs = re.findall(
                r"class\s+(\w*(?:Singleton|Factory|Observer|Strategy|Decorator|Adapter|Facade|Mixin|Proxy))",
                self.added_lines,
                re.I,
            )
            # 실제 Pattern 주석만 추출
            pattern_comments = extract_real_comments(self.diff, "Pattern")

            detected_patterns = []
            if pattern_defs:
                for p in set(pattern_defs):
                    content += f"- **{p}** 클래스\n"
                    # 패턴명에서 패턴 타입 추출
                    for pattern_type in pattern_explanations:
                        if pattern_type.lower() in p.lower():
                            detected_patterns.append(pattern_type)
                            break
            if pattern_comments:
                for pc in pattern_comments[:3]:
                    content += f"- {pc[:80]}\n"
            if not pattern_defs and not pattern_comments:
                content += "- (Pattern 주석을 추가하여 패턴 기록 권장)\n"
            content += "\n"

            # 초보자를 위한 패턴 설명 추가
            if detected_patterns:
                content += "### 💡 패턴 이해하기 (초보자 가이드)\n\n"
                for pattern_type in set(detected_patterns):
                    if pattern_type in pattern_explanations:
                        when_to_use, example = pattern_explanations[pattern_type]
                        content += f"**{pattern_type} 패턴**\n"
                        content += f"- **언제 사용?** {when_to_use}\n"
                        content += f"- **실제 예시:** {example}\n"
                        content += "- **주의점:** 패턴을 위한 패턴은 피하세요. " "문제가 명확할 때만 적용하세요.\n\n"

        return content

    # -------------------------------------------------------------------------
    # Section 5: Uncertainty Map (has_uncertainty)
    # v3.1: A + B 조합 - 기술적 불확실성 + AI 메타인지 + Blockers
    # -------------------------------------------------------------------------
    def _section_uncertainty(self) -> str:
        """Uncertainty Map 섹션 - 다층 불확실성 분석

        구성:
        1. 🔍 기술적 불확실성 (Option A): Git diff 자동 분석
        2. 🤔 AI 메타인지 (Option B): 세션 기반 자기 성찰
        3. 🚧 Blockers: 작업 차단 요소
        """
        content = "## Uncertainty Map\n\n"

        # =====================================================================
        # Part 1: 🔍 기술적 불확실성 (Option A - Git diff 기반 자동 분석)
        # =====================================================================
        content += "### 🔍 기술적 불확실성 (자동 분석)\n\n"

        tech_uncertainties = []

        # 1-1. 주석 기반 명시적 불확실성
        todos = extract_real_comments(self.diff, "TODO")
        tech_uncertainties.extend([f"**TODO**: {t[:60]}" for t in todos[:3]])

        fixmes = extract_real_comments(self.diff, "FIXME")
        tech_uncertainties.extend([f"**FIXME**: {f[:60]}" for f in fixmes[:2]])

        risks = extract_real_comments(self.diff, "RISK")
        tech_uncertainties.extend([f"**RISK**: {r[:60]}" for r in risks[:2]])

        # 1-2. 복잡도 기반 추론 (Option A 강화)
        complexity_indicators = {
            r"if.*if.*if": "⚠️ 중첩 조건문 3단계 - 로직 단순화 검토 필요",
            r"for.*for": "⚠️ 중첩 루프 - O(n²) 성능 영향 확인 필요",
            r"try.*try": "⚠️ 중첩 예외 처리 - 에러 흐름 정리 필요",
            r"except\s*:": "⚠️ 광범위 예외 처리 - 구체적 예외 타입 권장",
        }
        for pattern, msg in complexity_indicators.items():
            if re.search(pattern, self.added_lines, re.DOTALL):
                tech_uncertainties.append(msg)

        # 1-3. 변경 규모 기반 추론 (Option A 강화)
        lines_added = len(self.added_lines.split("\n"))
        files_changed = len(self.files)

        if lines_added > 200:
            tech_uncertainties.append(f"📊 대규모 변경 ({lines_added}줄) - 모든 엣지 케이스 고려했는지 검토 필요")
        if files_changed > 5:
            tech_uncertainties.append(f"📁 다중 파일 변경 ({files_changed}개) - 파일 간 일관성 확인 필요")

        # 1-4. 외부 의존성 추가 감지
        new_imports = re.findall(r"(?:import|from)\s+(\w+)", self.added_lines)
        new_deps = re.findall(r'"([^"]+)":\s*"[\^~]?\d', self.added_lines)  # package.json
        if new_imports or new_deps:
            dep_names = list(set(new_imports[:3] + new_deps[:2]))
            if dep_names:
                tech_uncertainties.append(f"📦 외부 의존성 추가: `{', '.join(dep_names)}` - 호환성 확인 필요")

        # 1-5. 테스트 미작성 신규 코드
        new_funcs = re.findall(r"def\s+(\w+)\s*\(", self.added_lines)
        new_classes = re.findall(r"class\s+(\w+)", self.added_lines)
        test_files = [f for f in self.files if "test" in f.lower()]

        if (new_funcs or new_classes) and not test_files:
            items = [f for f in set(new_funcs) if not f.startswith("_")][:2]
            items += [c for c in set(new_classes)][:1]
            if items:
                tech_uncertainties.append(f"🧪 테스트 미작성: `{', '.join(items)}` - 테스트 추가 권장")

        # 1-6. 불확실성 키워드 (코드 내 maybe, 아마 등)
        uncertainty_keywords = []
        for line in self.added_lines.split("\n"):
            if re.search(r"maybe|perhaps|아마|possibly|\?\?\?|임시|temp", line, re.I):
                cleaned = line.strip()[:40]
                if cleaned and not cleaned.startswith("#"):
                    uncertainty_keywords.append(cleaned)

        if uncertainty_keywords:
            tech_uncertainties.append(f"❓ 불확실한 구현 감지: `{uncertainty_keywords[0][:30]}...`")

        # 기술적 불확실성 출력
        if tech_uncertainties:
            for item in tech_uncertainties[:6]:
                content += f"- {item}\n"
        else:
            content += "> ✅ 코드 분석에서 주요 불확실성이 감지되지 않았습니다.\n"

        content += "\n"

        # =====================================================================
        # Part 2: 🤔 AI 메타인지 v3.3 (정량적 지표 + 우선순위 매트릭스)
        # =====================================================================
        content += "### 🤔 AI 메타인지 (신뢰도 기반)\n\n"

        ai_meta = load_ai_metacognition()
        all_priority_items = []  # 우선순위 정렬용

        if ai_meta:
            # 2-1. 가장 덜 자신있는 부분 (신뢰도 %)
            least_confident = ai_meta.get("least_confident", [])
            if least_confident:
                content += "**1. 🔴 덜 자신있는 부분** (신뢰도: 구현 정확성 확신 수준)\n\n"
                content += "| 항목 | 신뢰도 | 보완 시 기대효과 |\n"
                content += "|------|--------|------------------|\n"
                for item in least_confident[:4]:
                    if isinstance(item, dict):
                        name = item.get("item", str(item))
                        conf = item.get("confidence", 40)
                        effect = item.get("expected_effect", "정확도 향상")
                    else:
                        name = str(item)[:40]
                        conf = self._estimate_confidence(name)
                        effect = self._estimate_effect("confidence", name)
                    content += f"| {name} | **{conf}%** | {effect} |\n"
                    all_priority_items.append(
                        {
                            "category": "신뢰도",
                            "item": name,
                            "score": conf,
                            "urgency": "high" if conf < 40 else "medium" if conf < 60 else "low",
                            "effect": effect,
                        }
                    )
                content += "\n"

            # 2-2. 단순화한 가정 (유효확률 %)
            simplifications = ai_meta.get("simplifications", [])
            if simplifications:
                content += "**2. 🟡 단순화한 가정** (유효확률: 가정이 현실에서 성립할 확률)\n\n"
                content += "| 가정 | 유효확률 | 검증 시 기대효과 |\n"
                content += "|------|----------|------------------|\n"
                for item in simplifications[:4]:
                    if isinstance(item, dict):
                        name = item.get("item", str(item))
                        validity = item.get("validity", 55)
                        effect = item.get("expected_effect", "설계 안정성 확보")
                    else:
                        name = str(item)[:40]
                        validity = self._estimate_validity(name)
                        effect = self._estimate_effect("validity", name)
                    content += f"| {name} | **{validity}%** | {effect} |\n"
                    all_priority_items.append(
                        {
                            "category": "유효확률",
                            "item": name,
                            "score": validity,
                            "urgency": "high" if validity < 40 else "medium" if validity < 60 else "low",
                            "effect": effect,
                        }
                    )
                content += "\n"

            # 2-3. 의견 변경 가능 질문 (변경확률 %)
            opinion_changers = ai_meta.get("opinion_changers", [])
            if opinion_changers:
                content += "**3. 🟠 의견 변경 가능 질문** (변경확률: 검증 시 설계가 바뀔 확률)\n\n"
                content += "| 질문 | 변경확률 | 조기 검증 효과 |\n"
                content += "|------|----------|----------------|\n"
                for item in opinion_changers[:4]:
                    if isinstance(item, dict):
                        name = item.get("item", str(item))
                        change_prob = item.get("change_prob", 65)
                        effect = item.get("expected_effect", "재작업 방지")
                    else:
                        name = str(item)[:40]
                        change_prob = self._estimate_change_prob(name)
                        effect = self._estimate_effect("change", name)
                    content += f"| {name} | **{change_prob}%** | {effect} |\n"
                    all_priority_items.append(
                        {
                            "category": "변경확률",
                            "item": name,
                            "score": 100 - change_prob,  # 높은 변경확률 = 낮은 안정성
                            "urgency": "high" if change_prob > 70 else "medium" if change_prob > 50 else "low",
                            "effect": effect,
                        }
                    )
                content += "\n"

            # 2-4. 보완 필요 영역 (완성도 + 긴급도 2차원)
            areas_to_improve = ai_meta.get("areas_to_improve", [])
            if areas_to_improve:
                content += "**4. 🔵 보완 필요 영역** (완성도 × 긴급도 2차원 분석)\n\n"
                content += "| 영역 | 완성도 | 긴급도 | 우선순위 | 보완 시 기대효과 |\n"
                content += "|------|--------|--------|----------|------------------|\n"
                for item in areas_to_improve[:5]:
                    if isinstance(item, dict):
                        name = item.get("item", str(item))
                        completeness = item.get("completeness", 45)
                        urgency = item.get("urgency", "medium")
                        remaining = 100 - completeness
                        effect = item.get("expected_effect", f"+{remaining}% 기능 완성")
                    else:
                        name = str(item)[:35]
                        completeness = self._estimate_completeness(name)
                        urgency = self._estimate_urgency(name, completeness)
                        effect = self._estimate_effect("completeness", name)

                    # 우선순위 계산: 완성도 낮고 긴급도 높으면 최우선
                    urgency_score = {"high": 3, "medium": 2, "low": 1}.get(urgency.lower(), 2)
                    priority_score = (100 - completeness) * urgency_score
                    priority_label = "🚨 즉시" if priority_score > 150 else "⚡ 우선" if priority_score > 100 else "📋 계획"

                    urgency_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency.lower(), "🟡")
                    content += (
                        f"| {name} | {completeness}% | {urgency_icon} {urgency.capitalize()} | {priority_label} | {effect} |\n"
                    )

                    all_priority_items.append(
                        {
                            "category": "완성도",
                            "item": name,
                            "score": completeness,
                            "urgency": urgency.lower(),
                            "priority_score": priority_score,
                            "effect": effect,
                        }
                    )
                content += "\n"

                # 2차원 해석 가이드 (초보자용)
                content += "**💡 우선순위 판단 기준:**\n"
                content += "```\n"
                content += "              긴급도\n"
                content += "         Low    Medium    High\n"
                content += "완성도  ┌────────┬────────┬────────┐\n"
                content += " High   │ 관찰   │ 계획   │ 즉시   │\n"
                content += " (>70%) │        │        │ 마무리 │\n"
                content += "        ├────────┼────────┼────────┤\n"
                content += " Medium │ 백로그 │ 다음   │ 우선   │\n"
                content += " (40-70)│ 등록   │ 스프린트│ 처리   │\n"
                content += "        ├────────┼────────┼────────┤\n"
                content += " Low    │ 장기   │ 단기   │ 🚨     │\n"
                content += " (<40%) │ 로드맵 │ 계획   │ 크리티컬│\n"
                content += "        └────────┴────────┴────────┘\n"
                content += "```\n\n"

            # 전체 우선순위 정렬 요약
            if all_priority_items:
                content += "**📊 전체 메타인지 우선순위 (점수 기준 정렬)**\n\n"
                # 점수가 낮을수록 (불확실할수록) 우선순위 높음
                sorted_items = sorted(
                    all_priority_items,
                    key=lambda x: ({"high": 0, "medium": 1, "low": 2}.get(x.get("urgency", "medium"), 1), x.get("score", 50)),
                )

                content += "| 순위 | 카테고리 | 항목 | 점수 | 긴급도 | 조치 |\n"
                content += "|------|----------|------|------|--------|------|\n"
                for idx, item in enumerate(sorted_items[:8], 1):
                    urgency = item.get("urgency", "medium")
                    urgency_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(urgency, "🟡")
                    action = "즉시 검증" if urgency == "high" else "모니터링" if urgency == "medium" else "관찰"
                    cat = item["category"]
                    name = item["item"][:25]
                    score = item["score"]
                    content += f"| {idx} | {cat} | {name} | {score}% | {urgency_icon} | {action} |\n"
                content += "\n"

            if not any([least_confident, simplifications, opinion_changers, areas_to_improve]):
                content += "> AI 세션 메타인지가 로드되었으나 내용이 비어있습니다.\n\n"
        else:
            content += "> 💡 AI 세션 메타인지 정보가 없습니다.\n"
            content += "> `save_ai_metacognition()` 함수로 AI 작업 중 메타인지를 저장하면 자동 포함됩니다.\n\n"
            content += self._generate_default_metacognition()

        # =====================================================================
        # Part 3: 🚧 Blockers (작업 차단 요소)
        # =====================================================================
        content += "### 🚧 Blockers\n\n"

        blockers = []

        # 3-1. 주석 기반 Blockers
        blocked_comments = extract_real_comments(self.diff, "BLOCKED")
        blockers.extend([f"🔴 {b[:60]}" for b in blocked_comments[:2]])

        decision_comments = extract_real_comments(self.diff, "DECISION")
        blockers.extend([f"🟡 결정 대기: {d[:50]}" for d in decision_comments[:2]])

        waiting_comments = extract_real_comments(self.diff, "WAITING")
        blockers.extend([f"🟠 대기 중: {w[:50]}" for w in waiting_comments[:2]])

        # 3-2. AI 세션 Blockers
        ai_blockers = ai_meta.get("blockers", [])
        for b in ai_blockers[:3]:
            blockers.append(f"🔵 {b}")

        # 3-3. 외부 의존성 대기
        if re.search(r"#.*외부.*대기|#.*external.*wait", self.added_lines, re.I):
            blockers.append("🟣 외부 시스템 응답 대기 중")

        # Blockers 출력
        if blockers:
            for item in blockers[:5]:
                content += f"- {item}\n"
        else:
            content += "> ✅ 현재 차단 요소가 없습니다.\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # v3.3 Metacognition Helper Methods
    # -------------------------------------------------------------------------
    def _estimate_confidence(self, item: str) -> int:
        """항목명에서 신뢰도 추정 (휴리스틱)"""
        item_lower = item.lower()
        # 키워드 기반 신뢰도 추정
        if any(k in item_lower for k in ["regex", "정규", "패턴", "edge", "엣지"]):
            return 35
        elif any(k in item_lower for k in ["성능", "performance", "최적화"]):
            return 45
        elif any(k in item_lower for k in ["api", "인터페이스", "연동"]):
            return 50
        elif any(k in item_lower for k in ["테스트", "test", "검증"]):
            return 55
        else:
            return 40  # 기본값

    def _estimate_validity(self, item: str) -> int:
        """가정의 유효확률 추정"""
        item_lower = item.lower()
        if any(k in item_lower for k in ["충분", "enough", "만으로"]):
            return 55
        elif any(k in item_lower for k in ["항상", "always", "모든"]):
            return 40  # 절대적 가정은 낮은 확률
        elif any(k in item_lower for k in ["대부분", "most", "일반적"]):
            return 65
        else:
            return 55

    def _estimate_change_prob(self, item: str) -> int:
        """의견 변경 확률 추정"""
        item_lower = item.lower()
        if any(k in item_lower for k in ["사용자", "user", "피드백", "feedback"]):
            return 75  # 사용자 의견에 따라 변경 가능성 높음
        elif any(k in item_lower for k in ["성능", "performance", "속도"]):
            return 65
        elif any(k in item_lower for k in ["구조", "architecture", "설계"]):
            return 70
        else:
            return 60

    def _estimate_completeness(self, item: str) -> int:
        """완성도 추정"""
        item_lower = item.lower()
        if any(k in item_lower for k in ["미구현", "todo", "not implemented"]):
            return 20
        elif any(k in item_lower for k in ["부분", "partial", "일부"]):
            return 45
        elif any(k in item_lower for k in ["개선", "improve", "보완"]):
            return 60
        elif any(k in item_lower for k in ["조정", "adjust", "튜닝"]):
            return 70
        else:
            return 45

    def _estimate_urgency(self, item: str, completeness: int) -> str:
        """긴급도 추정 (완성도와 항목명 기반)"""
        item_lower = item.lower()
        # 키워드 기반
        if any(k in item_lower for k in ["보안", "security", "인증", "auth"]):
            return "high"
        elif any(k in item_lower for k in ["버그", "bug", "에러", "error", "crash"]):
            return "high"
        elif any(k in item_lower for k in ["성능", "performance", "느림", "slow"]):
            return "medium"
        # 완성도 기반
        elif completeness < 30:
            return "high"
        elif completeness < 50:
            return "medium"
        else:
            return "low"

    def _estimate_effect(self, effect_type: str, item: str) -> str:
        """기대효과 추정"""
        item_lower = item.lower()

        if effect_type == "confidence":
            if "regex" in item_lower or "정규" in item_lower:
                return "+40% 정확도, 엣지케이스 90% 해결"
            elif "성능" in item_lower:
                return "+30% 응답속도, 리소스 최적화"
            else:
                return "+25% 정확도 향상"

        elif effect_type == "validity":
            if "충분" in item_lower:
                return "검증 시 설계 안정성 확보"
            else:
                return "가정 검증으로 리스크 감소"

        elif effect_type == "change":
            if "사용자" in item_lower or "user" in item_lower:
                return "사용자 피드백 반영으로 만족도 +20%"
            else:
                return "조기 검증으로 재작업 -50%"

        elif effect_type == "completeness":
            if "자동" in item_lower or "auto" in item_lower:
                return "자동화로 수작업 -70%"
            elif "저장" in item_lower or "save" in item_lower:
                return "데이터 연속성 확보"
            else:
                return "기능 완성도 향상"

        return "개선 효과 기대"

    def _generate_default_metacognition(self) -> str:
        """Diff 분석 기반 기본 메타인지 생성 (세션 데이터 없을 때)"""
        content = "\n**📝 자동 분석 기반 메타인지:**\n\n"

        items = []

        # 복잡도 기반 추정
        nested_count = len(re.findall(r"if.*:\s*\n\s+if", self.added_lines))
        if nested_count > 0:
            items.append(
                {
                    "category": "신뢰도",
                    "item": f"중첩 조건문 {nested_count}개",
                    "score": max(30, 60 - nested_count * 10),
                    "urgency": "high" if nested_count > 2 else "medium",
                    "effect": "로직 단순화로 버그 감소",
                }
            )

        # 테스트 커버리지 기반
        has_tests = any("test" in f.lower() for f in self.files)
        if not has_tests and len(self.files) > 2:
            items.append(
                {
                    "category": "완성도",
                    "item": "테스트 코드 미작성",
                    "score": 30,
                    "urgency": "medium",
                    "effect": "테스트 추가로 안정성 +50%",
                }
            )

        # TODO 주석 기반
        todos = re.findall(r"#\s*TODO[:\s](.{10,40})", self.added_lines, re.I)
        if todos:
            items.append(
                {
                    "category": "완성도",
                    "item": f"TODO 항목 {len(todos)}개",
                    "score": 40,
                    "urgency": "low",
                    "effect": "기술부채 해소",
                }
            )

        if items:
            content += "| 카테고리 | 항목 | 점수 | 긴급도 | 기대효과 |\n"
            content += "|----------|------|------|--------|----------|\n"
            for item in items[:5]:
                urgency_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item["urgency"], "🟡")
                content += f"| {item['category']} | {item['item']} | {item['score']}% | {urgency_icon} | {item['effect']} |\n"
            content += "\n"
        else:
            content += "> 자동 분석에서 주요 메타인지 항목이 감지되지 않았습니다.\n\n"

        return content

    # -------------------------------------------------------------------------
    # Section 6: Rollback Plans (has_rollback)
    # -------------------------------------------------------------------------
    def _section_rollback(self) -> str:
        """Rollback Plans 섹션

        v3.2: 실전 명령어 + 초보자 가이드 추가
        v3.4: 전문가 검증된 메트릭 추가 (영향 범위 + 복잡도)
              - 제거: success_rate (측정 불가, 오탐률 70%+)
              - 추가: impact_scope (Code/Config/DB/Full)
              - 추가: complexity (Low/Medium/High)
        """
        content = "## Rollback Plans\n\n"

        # v3.4: 구조화된 롤백 전략 (영향 범위 + 복잡도)
        rollbacks: List[Dict[str, str]] = []
        commit_hash = self.commit_info.get("hash", "HEAD")[:7]

        # 실제 Rollback 주석 추출 (문자열 리터럴 제외)
        rollback_comments = extract_real_comments(self.diff, "Rollback")
        rollbacks.extend(
            [
                {
                    "strategy": r[:60],
                    "cmd": "",
                    "time": "",
                    "impact": "Code-only",
                    "complexity": "Low",
                }
                for r in rollback_comments[:2]
            ]
        )

        # 마이그레이션 파일 감지 (v3.4: 영향 범위 = Code+DB)
        migrations = [f for f in self.files if "migration" in f.lower()]
        if migrations:
            rollbacks.append(
                {
                    "strategy": f"DB 마이그레이션 롤백 ({len(migrations)}개)",
                    "cmd": "python manage.py migrate <app> <previous_migration>",
                    "time": "~5분",
                    "impact": "Code+DB",
                    "complexity": "High",
                }
            )

        # Feature flag 감지 (v3.4: 영향 범위 = Code+Config)
        if re.search(r"feature.?flag", self.added_lines, re.I):
            rollbacks.append(
                {
                    "strategy": "Feature Flag 비활성화",
                    "cmd": "config에서 플래그 OFF 또는 환경변수 변경",
                    "time": "<10초",
                    "impact": "Code+Config",
                    "complexity": "Low",
                }
            )

        # 백업 전략 (v3.4: 영향 범위 = Full-system)
        if re.search(r"backup|백업", self.added_lines, re.I):
            rollbacks.append(
                {
                    "strategy": "백업 복원",
                    "cmd": "백업 파일에서 복원 (위치 확인 필요)",
                    "time": "~10분",
                    "impact": "Full-system",
                    "complexity": "High",
                }
            )

        # 기본 롤백 가이드 (항상 추가)
        rollbacks.append(
            {
                "strategy": "Git Revert (커밋 되돌리기)",
                "cmd": f"git revert {commit_hash}",
                "time": "~1분",
                "impact": "Code-only",
                "complexity": "Low",
            }
        )
        rollbacks.append(
            {
                "strategy": "Git Reset (히스토리 삭제)",
                "cmd": f"git reset --hard {commit_hash}~1",
                "time": "<30초 (주의: 푸시 전에만!)",
                "impact": "Code-only",
                "complexity": "Medium",
            }
        )

        # v3.4: 5열 테이블 (전략, 영향 범위, 복잡도, 명령어, 예상 시간)
        content += "| 전략 | 영향 범위 | 복잡도 | 명령어/방법 | 예상 시간 |\n"
        content += "|------|----------|--------|------------|----------|\n"
        for idx, item in enumerate(rollbacks[:5], 1):
            if isinstance(item, dict):
                strategy = item.get("strategy", "-")
                impact = item.get("impact", "Code-only")
                complexity = item.get("complexity", "Low")
                complexity_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(complexity, "🟡")
                cmd = f"`{item['cmd']}`" if item.get("cmd") else "-"
                time = item.get("time", "-")
                content += f"| Tier {idx}: {strategy} | {impact} | {complexity_emoji} {complexity} | {cmd} | {time} |\n"
            else:
                content += f"| Tier {idx} | {item} | - | - | - |\n"

        content += "\n"

        # 초보자를 위한 롤백 가이드
        content += "### 💡 롤백 가이드 (초보자용)\n\n"
        content += "**상황별 롤백 선택:**\n"
        content += "1. **코드만 문제** → `git revert` (안전, 히스토리 유지)\n"
        content += "2. **DB도 변경됨** → DB 롤백 먼저 → 코드 롤백\n"
        content += "3. **설정만 변경** → Feature Flag OFF 또는 환경변수 복원\n"
        content += "4. **긴급 상황** → `git reset --hard` (히스토리 삭제됨, 신중히!)\n\n"

        content += "**롤백 전 체크리스트:**\n"
        content += "- [ ] 다른 팀원에게 알림\n"
        content += "- [ ] 현재 상태 백업/스냅샷\n"
        content += "- [ ] 롤백 후 테스트 계획 준비\n\n"

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

        # v3.5: 학습 가이드 + 현재 단계 표시
        curriculum = get_current_curriculum()
        month = curriculum["month"]
        week = curriculum["week"]
        title = curriculum["title"]
        focus = curriculum["focus"]
        checkpoints = curriculum["checkpoints"]
        considerations = curriculum["considerations"]
        warnings = curriculum["warnings"]
        guide = curriculum["guide"]

        # v3.6: Bridge content for smooth month transitions
        key = (month, week)
        raw_curriculum = LEARNING_CURRICULUM.get(key, {})
        bridge_preview = raw_curriculum.get("bridge_preview")
        bridge_review = raw_curriculum.get("bridge_review")

        content += "\n### 📚 Learning Progress (VibeCoding)\n\n"

        # Progress bar visualization
        # Week 0 = week 1 of 13, Month 1 Week 1 = week 2 of 13, etc.
        # Formula: ((month-1)*4 + week) gives 0-based week index
        # For Week 0 (month=0, week=0): total_weeks = 1
        # For Month 1-3: total_weeks = month*4 + week
        if month == 0:
            total_weeks_completed = week  # Week 0 = 0 weeks completed initially
        else:
            total_weeks_completed = (month - 1) * 4 + week

        # Calculate progress percentage (13 weeks total: Week 0 + 3 months * 4 weeks)
        progress_percent = min(100, int((total_weeks_completed / 13) * 100))

        # Create ASCII progress bar (10 characters wide)
        filled_chars = int(progress_percent / 10)
        empty_chars = 10 - filled_chars
        progress_bar = "█" * filled_chars + "░" * empty_chars

        # Calculate current week number (1-indexed for display)
        if month == 0:
            current_week_num = 1  # Week 0 is displayed as Week 1/13
        else:
            current_week_num = 1 + (month - 1) * 4 + week  # +1 for Week 0

        content += f"**진행률**: {progress_bar} {progress_percent}% (Week {current_week_num}/13)\n\n"
        content += f"**현재 단계**: Month {month} Week {week} - {title}\n"
        content += f"**이번 주 포커스**: {focus}\n\n"

        # v3.6: 체크포인트 자동 감지
        newly_detected = detect_checkpoint_completion(self.message, self.diff, curriculum)
        already_done = set(curriculum.get("checkpoints_done", []))
        all_completed = already_done.union(set(newly_detected))

        # 새로 감지된 체크포인트를 session_state에 저장
        if newly_detected:
            update_checkpoints_done(newly_detected)

        # 필수 체크포인트 (완료 여부 + 자동 감지 표시)
        content += "**필수 체크포인트**:\n"
        for cp in checkpoints:
            if cp in all_completed:
                if cp in newly_detected:
                    # 이번 커밋에서 새로 감지됨
                    content += f"- [x] {cp} (자동 감지됨)\n"
                else:
                    # 이전에 이미 완료됨
                    content += f"- [x] {cp}\n"
            else:
                content += f"- [ ] {cp}\n"
        content += "\n"

        # 고려사항
        if considerations:
            content += "**💡 고려사항**:\n"
            for c in considerations:
                content += f"- {c}\n"
            content += "\n"

        # 주의점
        if warnings:
            content += "**⚠️ 주의점**:\n"
            for w in warnings:
                content += f"- {w}\n"
            content += "\n"

        # v3.6: Bridge Review (Week 1 of Months 2 and 3 - start of new month)
        if bridge_review:
            content += "**🔄 지난 달 복습 (Bridge Review)**:\n\n"
            content += f"*이전 단계*: {bridge_review['previous_month']}\n\n"
            content += "핵심 개념 확인:\n"
            for concept in bridge_review["key_concepts"]:
                content += f"- {concept}\n"
            content += "\n자가 점검:\n"
            for check in bridge_review["self_check"]:
                content += f"- [ ] {check}\n"
            content += "\n"

        # v3.6: Bridge Preview (Week 4 of Months 1 and 2 - end of month)
        if bridge_preview:
            content += "**🚀 다음 달 미리보기 (Bridge Preview)**:\n\n"
            content += f"*다음 단계*: {bridge_preview['next_month']}\n\n"
            content += f"미리보기: {bridge_preview['preview']}\n\n"
            content += "사전 준비 사항:\n"
            for prep in bridge_preview["preparation"]:
                content += f"- [ ] {prep}\n"
            content += "\n"

        # 참고 가이드 링크
        content += f"**참고**: [[{guide}]]\n\n"

        # 전체 가이드 링크 (접힌 상태)
        content += "<details>\n<summary>📖 전체 가이드 목록</summary>\n\n"
        content += "- [[VibeCoding-Growth-Guide]] - 3개월 성장 로드맵\n"
        content += "- [[MCP-Combination-Patterns]] - MCP 서버 조합 패턴\n"
        content += "- [[Claude-Skills-Curriculum]] - 클로드 스킬 4주 커리큘럼\n"
        content += "- [[Prompt-Pattern-Library]] - 효과적인 프롬프트 패턴\n"
        content += "- [[Multi-Agent-Workflows]] - 멀티에이전트 워크플로우\n"
        content += "</details>\n"

        content += "\n"
        return content

    # -------------------------------------------------------------------------
    # Section 8: Technical Debt Daily (has_debt)
    # -------------------------------------------------------------------------
    def _section_tech_debt(self) -> str:
        """Technical Debt Daily 섹션

        v3.2: 초보자 학습 가이드 + 기술부채 관리 방법 추가
        v3.4: 전문가 검증된 메트릭 추가 (심각도 + 노력 + 누적 리스크)
              - 추가: severity_score (0-100, 자동 계산)
              - 추가: effort (T-shirt: S/M/L/XL)
              - 추가: impact_type (security/performance/maintenance/reliability)
        """
        content = "## Technical Debt (Daily)\n\n"

        # v3.4: 구조화된 기술부채 (심각도 + 노력 + 누적 리스크)
        debts: List[Dict[str, Any]] = []

        # TODO 추출 (실제 주석만)
        todos = extract_real_comments(self.diff, "TODO")
        for t in todos[:5]:
            debts.append(
                {
                    "type": "TODO",
                    "desc": t[:60],
                    "severity": self._estimate_debt_severity("TODO", t),
                    "effort": self._estimate_debt_effort(t),
                    "impact": self._estimate_debt_impact(t),
                }
            )

        # FIXME 추출 (실제 주석만)
        fixmes = extract_real_comments(self.diff, "FIXME")
        for f in fixmes[:3]:
            debts.append(
                {
                    "type": "FIXME",
                    "desc": f[:60],
                    "severity": self._estimate_debt_severity("FIXME", f),
                    "effort": self._estimate_debt_effort(f),
                    "impact": self._estimate_debt_impact(f),
                }
            )

        # HACK 추출 (실제 주석만)
        hacks = extract_real_comments(self.diff, "HACK")
        for h in hacks[:2]:
            debts.append(
                {
                    "type": "HACK",
                    "desc": h[:60],
                    "severity": self._estimate_debt_severity("HACK", h),
                    "effort": self._estimate_debt_effort(h),
                    "impact": self._estimate_debt_impact(h),
                }
            )

        # 스킵된 테스트 (추가된 줄에서만)
        skips = re.findall(r"@pytest\.mark\.skip\(reason=[\"'](.+?)[\"']\)", self.added_lines)
        for s in skips[:2]:
            debts.append(
                {
                    "type": "SKIP",
                    "desc": s[:60],
                    "severity": 60,  # 스킵 테스트는 중간 심각도
                    "effort": "S",
                    "impact": "Reliability",
                }
            )

        # 타입 무시 (추가된 줄에서만)
        ignores = len(re.findall(r"#\s*type:\s*ignore", self.added_lines))
        if ignores > 0:
            debts.append(
                {
                    "type": "TYPE",
                    "desc": f"type: ignore 주석 {ignores}개",
                    "severity": 40 + (ignores * 5),  # 개수에 따라 심각도 증가
                    "effort": "S" if ignores <= 3 else "M",
                    "impact": "Maintenance",
                }
            )

        if debts:
            # v3.4: 심각도 기준 정렬 후 테이블 렌더링
            debts.sort(key=lambda x: x.get("severity", 0), reverse=True)

            content += "| 유형 | 설명 | 심각도 | 노력 | 누적 리스크 |\n"
            content += "|------|------|--------|------|------------|\n"
            for debt in debts[:8]:
                severity = debt.get("severity", 50)
                severity_emoji = "🔴" if severity >= 80 else "🟠" if severity >= 60 else "🟡" if severity >= 40 else "🟢"
                effort = debt.get("effort", "M")
                impact = debt.get("impact", "Maintenance")
                content += f"| {debt['type']} | {debt['desc']} | {severity_emoji} {severity}% | {effort} | {impact} |\n"

            content += "\n"

            # 초보자를 위한 기술부채 가이드
            content += "### 💡 기술부채 이해하기 (초보자용)\n\n"
            content += "**기술부채 유형별 의미:**\n"
            content += "| 유형 | 의미 | 조치 시점 |\n"
            content += "|------|------|----------|\n"
            content += "| TODO | 나중에 구현할 기능 | 시간 여유 있을 때 |\n"
            content += "| FIXME | 알려진 버그/문제 | **가능한 빨리!** |\n"
            content += "| HACK | 임시 해결책 | 다음 리팩토링 시 |\n"
            content += "| SKIP | 스킵된 테스트 | 테스트 안정화 후 |\n"
            content += "| TYPE | 타입 무시 | 타입 정의 완료 후 |\n\n"

            content += "**기술부채 관리 원칙:**\n"
            content += "1. **의도적 부채** (마감에 맞추기 위해) → 반드시 기록하고 상환 계획 세우기\n"
            content += "2. **무의식적 부채** (나중에 발견) → 발견 즉시 기록, 우선순위 판단\n"
            content += "3. **20% 규칙** - 매 스프린트 시간의 20%는 부채 상환에 할당\n\n"

        else:
            # 기술부채 플래그가 감지되었지만 구체적 항목이 없는 경우
            possible_reasons = []
            if any("test" in f.lower() and "skip" in self.added_lines.lower() for f in self.files):
                possible_reasons.append("스킵된 테스트가 있을 수 있음")
            if "# type: ignore" in self.added_lines:
                possible_reasons.append("타입 무시 주석이 있음")

            if possible_reasons:
                content += f"> 감지된 패턴: {', '.join(possible_reasons)}\n\n"
            else:
                content += "> 기술부채 플래그가 감지되었지만 구체적 항목이 없습니다.\n\n"

            content += "### 💡 기술부채 기록 방법 (초보자용)\n\n"
            content += "코드에 다음 주석을 추가하면 자동으로 추출됩니다:\n"
            content += "```python\n"
            content += "# TODO: 나중에 구현할 기능 설명\n"
            content += "# FIXME: 알려진 버그 설명 (빨리 고쳐야 함)\n"
            content += "# HACK: 임시 해결책 설명 (나중에 제대로 고쳐야 함)\n"
            content += "```\n\n"

        return content

    # -------------------------------------------------------------------------
    # Section 9: Decisions Made (has_decision)
    # -------------------------------------------------------------------------
    def _section_decisions(self) -> str:
        """Decisions Made 섹션 - 구체적 의사결정 분석

        v3.2: 초보자를 위한 결정 배경 및 트레이드오프 설명 추가
        v3.4: 전문가 검증된 메트릭 추가 (유형 + 되돌림 가능성 + 결정 범위)
              - 추가: type (Architecture/Dependency/Config/Process)
              - 추가: reversibility (Easy/Medium/Hard) - AI 신뢰도와 구분
              - 추가: scope (Local/Module/System)
        """
        content = "## Decisions Made (Daily)\n\n"

        # v3.4: 구조화된 의사결정 (유형 + 되돌림 + 범위)
        decisions: List[Dict[str, Any]] = []
        decision_contexts = []  # 결정 배경/트레이드오프

        # 명시적 Decision 주석 (실제 주석만)
        decision_comments = extract_real_comments(self.diff, "Decision")
        for d in decision_comments[:5]:
            decisions.append(
                {
                    "desc": d[:70],
                    "type": "Process",
                    "reversibility": "Medium",
                    "scope": self._estimate_decision_scope(d),
                }
            )

        # Why 주석 (실제 주석만) - 배경 컨텍스트용
        why_comments = extract_real_comments(self.diff, "Why")
        for w in why_comments[:3]:
            decision_contexts.append(f"**이유**: {w[:80]}")

        # 의존성 변경 감지 (v3.4: Dependency 유형)
        if "requirements.txt" in self.files:
            added_deps = re.findall(r"^\+([a-zA-Z0-9_-]+)==([0-9.]+)", self.added_lines, re.M)
            for name, version in added_deps[:3]:
                decisions.append(
                    {
                        "desc": f"의존성 추가: {name}=={version}",
                        "type": "Dependency",
                        "reversibility": "Easy",  # pip uninstall 가능
                        "scope": "Module",
                    }
                )
            if added_deps:
                decision_contexts.append("**의존성 추가 주의**: 라이선스 호환성, 보안 취약점, 유지보수 상태 확인")

        if "package.json" in self.files:
            added_npm = re.findall(r'"([^"]+)":\s*"[\^~]?([0-9.]+)"', self.added_lines)
            for name, version in added_npm[:3]:
                if not name.startswith("@types"):
                    decisions.append(
                        {
                            "desc": f"NPM 패키지: {name}@{version}",
                            "type": "Dependency",
                            "reversibility": "Easy",
                            "scope": "Module",
                        }
                    )

        # 아키텍처 결정 감지 (v3.4: Architecture 유형)
        arch_patterns = {
            r"class\s+(\w+Factory)": ("Factory 패턴", "Hard", "System"),
            r"class\s+(\w+Singleton)": ("Singleton 패턴", "Hard", "System"),
            r"class\s+(\w+Service)": ("Service 계층", "Medium", "Module"),
            r"class\s+(\w+Repository)": ("Repository 패턴", "Medium", "Module"),
            r"class\s+(\w+Controller)": ("Controller 계층", "Medium", "Module"),
        }
        for pattern, (desc, rev, scope) in arch_patterns.items():
            matches = re.findall(pattern, self.added_lines)
            if matches:
                decisions.append(
                    {
                        "desc": f"{desc}: {matches[0]}",
                        "type": "Architecture",
                        "reversibility": rev,
                        "scope": scope,
                    }
                )
                break

        # 설정 파일 변경 감지 (v3.4: Config 유형)
        config_files = [f for f in self.files if f.endswith((".yaml", ".yml", ".json", ".toml", ".env"))]
        if config_files:
            config_names = [Path(f).name for f in config_files[:2]]
            decisions.append(
                {
                    "desc": f"설정 변경: {', '.join(config_names)}",
                    "type": "Config",
                    "reversibility": "Easy",
                    "scope": "System" if any("prod" in f.lower() for f in config_files) else "Local",
                }
            )
            decision_contexts.append("**설정 변경 주의**: 환경별(dev/staging/prod) 차이, 민감정보 노출 확인 필요")

        # 커밋 메시지에서 결정사항 추출 (v3.4: Process 유형)
        commit_decision_patterns = [
            (r"대신|instead of|rather than", "대안 선택", "Medium", "Module"),
            (r"전환|migrate|switch", "기술 전환", "Hard", "System"),
            (r"도입|introduce|adopt", "새 기술 도입", "Medium", "Module"),
            (r"제거|remove|deprecate", "기능 제거", "Hard", "System"),
        ]
        for pattern, desc, rev, scope in commit_decision_patterns:
            if re.search(pattern, self.message, re.I):
                decisions.append(
                    {
                        "desc": f"{desc}: {self.message.split(chr(10))[0][:40]}",
                        "type": "Process",
                        "reversibility": rev,
                        "scope": scope,
                    }
                )
                break

        if decisions:
            # v3.4: 테이블 형식으로 렌더링 (되돌림 가능성 기준 정렬)
            reversibility_order = {"Hard": 0, "Medium": 1, "Easy": 2}
            decisions.sort(key=lambda x: reversibility_order.get(x.get("reversibility", "Medium"), 1))

            content += "| 결정 내용 | 유형 | 되돌림 | 범위 |\n"
            content += "|----------|------|--------|------|\n"
            for dec in decisions[:8]:
                rev = dec.get("reversibility", "Medium")
                rev_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(rev, "🟡")
                scope = dec.get("scope", "Module")
                scope_emoji = {"Local": "📄", "Module": "📦", "System": "🌐"}.get(scope, "📦")
                content += f"| {dec['desc']} | {dec['type']} | {rev_emoji} {rev} | {scope_emoji} {scope} |\n"
            content += "\n"

            # 초보자를 위한 메트릭 설명
            content += "### 💡 의사결정 메트릭 이해하기 (초보자용)\n\n"
            content += "**되돌림 가능성 (Reversibility)**:\n"
            content += "- 🟢 Easy: 쉽게 되돌릴 수 있음 (의존성 제거, 설정 변경)\n"
            content += "- 🟡 Medium: 약간의 작업 필요 (코드 리팩토링, DB 마이그레이션)\n"
            content += "- 🔴 Hard: 되돌리기 어려움 (아키텍처 변경, 데이터 스키마 변경)\n\n"

            content += "**결정 범위 (Scope)**:\n"
            content += "- 📄 Local: 단일 파일/함수 수준\n"
            content += "- 📦 Module: 모듈/패키지 수준\n"
            content += "- 🌐 System: 시스템 전체 영향\n\n"

            # 결정 배경 설명
            if decision_contexts:
                content += "### 📝 결정의 배경\n\n"
                for ctx in decision_contexts[:3]:
                    content += f"{ctx}\n\n"

        else:
            # 구체적인 폴백 메시지
            content += "> 의사결정 플래그가 감지되었지만 구체적 내용이 없습니다.\n\n"

            content += "### 💡 의사결정 기록의 중요성 (초보자용)\n\n"
            content += "코드는 **무엇**을 하는지 보여주지만, **왜** 그렇게 했는지는 보여주지 않습니다.\n"
            content += "6개월 후의 자신(또는 동료)이 이해할 수 있도록 결정 이유를 남기세요:\n\n"
            content += "```python\n"
            content += "# Decision: 여기에 결정 내용\n"
            content += "# Why: 여기에 이유\n"
            content += "```\n\n"

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
        content += "**자동 생성**: Obsidian Auto-Sync v3.0 Weekly  \n"
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
        content += "**자동 생성**: Obsidian Auto-Sync v2.0  \n"

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
