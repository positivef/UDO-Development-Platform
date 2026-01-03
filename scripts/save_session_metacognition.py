#!/usr/bin/env python
"""
AI 세션 메타인지 저장 스크립트

커밋 전에 실행하여 AI 세션의 메타인지 정보를 저장합니다.
이 정보는 obsidian_auto_sync.py에서 개발일지에 자동 포함됩니다.

사용법:
    1. 직접 실행: python scripts/save_session_metacognition.py
    2. 인자로 전달: python scripts/save_session_metacognition.py --confidence 70 --area "에러 핸들링"
    3. Claude Code에서 호출: from scripts.save_session_metacognition import save_current_session

데이터 구조:
    - least_confident: 가장 덜 자신있는 부분 (신뢰도 %)
    - simplifications: 단순화한 가정 (유효확률 %)
    - opinion_changers: 의견 변경 가능 질문 (변경확률 %)
    - areas_to_improve: 보완 필요 영역 (완성도 + 긴급도)
    - blockers: 현재 차단 요소
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    # Git 루트 찾기
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()


def load_session_state() -> Dict[str, Any]:
    """현재 세션 상태 로드"""
    session_file = get_project_root() / ".udo" / "session_state.json"
    if not session_file.exists():
        return {}
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_session_state(data: Dict[str, Any]) -> bool:
    """세션 상태 저장"""
    session_file = get_project_root() / ".udo" / "session_state.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError:
        return False


def analyze_git_diff(use_last_commit: bool = False) -> Dict[str, Any]:
    """Git diff를 분석하여 자동으로 메타인지 추출

    Args:
        use_last_commit: True면 마지막 커밋의 diff 사용, False면 staged diff 사용
    """
    try:
        # diff 명령어 결정
        if use_last_commit:
            # 마지막 커밋의 diff (post-commit에서 사용)
            diff_cmd = ["git", "diff", "HEAD~1", "HEAD", "--stat"]
            files_cmd = ["git", "diff", "HEAD~1", "HEAD", "--name-only"]
        else:
            # 스테이징된 변경사항 (pre-commit에서 사용)
            diff_cmd = ["git", "diff", "--cached", "--stat"]
            files_cmd = ["git", "diff", "--cached", "--name-only"]

        result = subprocess.run(diff_cmd, capture_output=True, text=True)
        diff_stat = result.stdout

        # 변경된 파일 수
        files_changed = len([line for line in diff_stat.split("\n") if "|" in line])

        # 변경된 파일 목록
        result = subprocess.run(files_cmd, capture_output=True, text=True)
        changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # 카테고리별 분류
        categories = {
            "backend": [],
            "frontend": [],
            "tests": [],
            "docs": [],
            "scripts": [],
            "config": [],
        }
        for f in changed_files:
            if f.startswith("backend/") or f.startswith("src/"):
                categories["backend"].append(f)
            elif f.startswith("web-dashboard/"):
                categories["frontend"].append(f)
            elif "test" in f.lower():
                categories["tests"].append(f)
            elif f.startswith("docs/") or f.endswith(".md"):
                categories["docs"].append(f)
            elif f.startswith("scripts/"):
                categories["scripts"].append(f)
            else:
                categories["config"].append(f)

        return {
            "files_changed": files_changed,
            "changed_files": changed_files,
            "categories": categories,
        }
    except subprocess.CalledProcessError:
        return {"files_changed": 0, "changed_files": [], "categories": {}}


def generate_auto_metacognition(diff_info: Dict[str, Any]) -> Dict[str, Any]:
    """Git diff 정보를 기반으로 자동 메타인지 생성"""
    metacognition = {
        "least_confident": [],
        "simplifications": [],
        "opinion_changers": [],
        "areas_to_improve": [],
        "blockers": [],
        "auto_generated": True,
        "generated_at": datetime.now().isoformat(),
    }

    categories = diff_info.get("categories", {})
    files_changed = diff_info.get("files_changed", 0)

    # 대규모 변경 시 불확실성 추가
    if files_changed > 10:
        metacognition["least_confident"].append(
            {
                "item": f"대규모 변경 ({files_changed}개 파일)",
                "confidence": max(40, 80 - files_changed),
                "expected_effect": "전체 통합 테스트로 안정성 확보",
            }
        )

    # 백엔드 변경 시
    if categories.get("backend"):
        backend_count = len(categories["backend"])
        metacognition["areas_to_improve"].append(
            {
                "item": f"백엔드 변경 ({backend_count}개)",
                "completeness": 75,
                "urgency": "high" if backend_count > 5 else "medium",
                "expected_effect": "API 안정성 검증",
            }
        )

    # 프론트엔드 변경 시
    if categories.get("frontend"):
        frontend_count = len(categories["frontend"])
        metacognition["areas_to_improve"].append(
            {
                "item": f"프론트엔드 변경 ({frontend_count}개)",
                "completeness": 70,
                "urgency": "medium",
                "expected_effect": "UI/UX 일관성 확인",
            }
        )

    # 테스트 파일 변경 시
    if categories.get("tests"):
        metacognition["simplifications"].append(
            {
                "item": "테스트 커버리지 충분",
                "validity": 65,
                "expected_effect": "엣지 케이스 검증 필요",
            }
        )

    # 설정 파일 변경 시
    if categories.get("config"):
        metacognition["opinion_changers"].append(
            {
                "item": "설정 변경이 다른 환경에 영향?",
                "change_prob": 45,
                "expected_effect": "환경별 테스트로 검증",
            }
        )

    # 스크립트 변경 시
    if categories.get("scripts"):
        scripts_count = len(categories["scripts"])
        metacognition["areas_to_improve"].append(
            {
                "item": f"스크립트 변경 ({scripts_count}개)",
                "completeness": 70,
                "urgency": "high" if scripts_count > 3 else "medium",
                "expected_effect": "자동화 스크립트 동작 검증",
            }
        )
        # 스크립트 변경은 다른 시스템에 영향 가능
        metacognition["opinion_changers"].append(
            {
                "item": "스크립트 변경이 CI/CD 또는 자동화에 영향?",
                "change_prob": 40,
                "expected_effect": "파이프라인 테스트로 검증",
            }
        )

    return metacognition


def save_current_session(
    least_confident: Optional[List[Dict]] = None,
    simplifications: Optional[List[Dict]] = None,
    opinion_changers: Optional[List[Dict]] = None,
    areas_to_improve: Optional[List[Dict]] = None,
    blockers: Optional[List[str]] = None,
    auto_analyze: bool = True,
    use_last_commit: bool = False,
) -> bool:
    """현재 세션의 메타인지 정보 저장

    Args:
        least_confident: 가장 덜 자신있는 부분 리스트
        simplifications: 단순화한 가정 리스트
        opinion_changers: 의견 변경 가능 질문 리스트
        areas_to_improve: 보완 필요 영역 리스트
        blockers: 현재 차단 요소 리스트
        auto_analyze: Git diff 기반 자동 분석 여부
        use_last_commit: True면 마지막 커밋의 diff 분석 (post-commit용)

    Returns:
        성공 여부
    """
    # 자동 분석
    if auto_analyze:
        diff_info = analyze_git_diff(use_last_commit=use_last_commit)
        auto_meta = generate_auto_metacognition(diff_info)
    else:
        auto_meta = {
            "least_confident": [],
            "simplifications": [],
            "opinion_changers": [],
            "areas_to_improve": [],
            "blockers": [],
        }

    # 수동 입력과 자동 분석 병합
    metacognition = {
        "least_confident": (least_confident or []) + auto_meta.get("least_confident", []),
        "simplifications": (simplifications or []) + auto_meta.get("simplifications", []),
        "opinion_changers": (opinion_changers or []) + auto_meta.get("opinion_changers", []),
        "areas_to_improve": (areas_to_improve or []) + auto_meta.get("areas_to_improve", []),
        "blockers": blockers or auto_meta.get("blockers", []),
        "updated_at": datetime.now().isoformat(),
        "auto_generated": auto_analyze
        and not any([least_confident, simplifications, opinion_changers, areas_to_improve, blockers]),
    }

    # 세션 상태 업데이트
    data = load_session_state()
    data["ai_metacognition"] = metacognition
    data["ai_metacognition_updated"] = datetime.now().isoformat()

    return save_session_state(data)


def quick_save(
    confidence: int = 70,
    area: str = "",
    uncertainty: str = "",
    blocker: str = "",
) -> bool:
    """간편 저장 - 단일 항목 빠르게 저장

    Args:
        confidence: 전체 신뢰도 (0-100)
        area: 보완 필요 영역
        uncertainty: 불확실한 부분
        blocker: 차단 요소

    Returns:
        성공 여부
    """
    least_confident = []
    areas_to_improve = []
    blockers = []

    if confidence < 80:
        least_confident.append(
            {
                "item": "전체 구현 신뢰도",
                "confidence": confidence,
                "expected_effect": "추가 검증으로 안정성 확보",
            }
        )

    if area:
        areas_to_improve.append(
            {
                "item": area,
                "completeness": confidence,
                "urgency": "high" if confidence < 60 else "medium",
                "expected_effect": "품질 향상",
            }
        )

    if uncertainty:
        least_confident.append(
            {
                "item": uncertainty,
                "confidence": max(30, confidence - 20),
                "expected_effect": "검증 필요",
            }
        )

    if blocker:
        blockers.append(blocker)

    return save_current_session(
        least_confident=least_confident,
        areas_to_improve=areas_to_improve,
        blockers=blockers,
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI 세션 메타인지 저장",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 자동 분석만
  python scripts/save_session_metacognition.py

  # 신뢰도와 영역 지정
  python scripts/save_session_metacognition.py --confidence 70 --area "WebSocket 안정성"

  # 불확실성 추가
  python scripts/save_session_metacognition.py --uncertainty "동시 연결 1000+ 미검증"

  # 차단 요소 추가
  python scripts/save_session_metacognition.py --blocker "DB 마이그레이션 필요"
        """,
    )

    parser.add_argument(
        "--confidence",
        "-c",
        type=int,
        default=75,
        help="전체 신뢰도 (0-100, 기본값: 75)",
    )
    parser.add_argument(
        "--area",
        "-a",
        type=str,
        default="",
        help="보완 필요 영역",
    )
    parser.add_argument(
        "--uncertainty",
        "-u",
        type=str,
        default="",
        help="불확실한 부분",
    )
    parser.add_argument(
        "--blocker",
        "-b",
        type=str,
        default="",
        help="차단 요소",
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help="자동 분석만 수행 (수동 입력 무시)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="상세 출력",
    )

    args = parser.parse_args()

    if args.auto_only:
        success = save_current_session(auto_analyze=True)
    else:
        success = quick_save(
            confidence=args.confidence,
            area=args.area,
            uncertainty=args.uncertainty,
            blocker=args.blocker,
        )

    if success:
        # pre-commit hook에서는 출력 최소화 (verbose 플래그일 때만 출력)
        if args.verbose:
            print("[OK] AI 메타인지 저장 완료")
            data = load_session_state()
            meta = data.get("ai_metacognition", {})
            print(f"  - 신뢰도 낮은 항목: {len(meta.get('least_confident', []))}개")
            print(f"  - 단순화 가정: {len(meta.get('simplifications', []))}개")
            print(f"  - 보완 필요 영역: {len(meta.get('areas_to_improve', []))}개")
            print(f"  - 차단 요소: {len(meta.get('blockers', []))}개")
        sys.exit(0)
    else:
        # 실패 시에만 stderr로 출력
        print("[ERROR] AI 메타인지 저장 실패", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
