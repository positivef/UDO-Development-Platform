#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDO Phase 1 Ideation 실행 스크립트
2025-Revenue-App을 위한 아이디어 발굴
"""

import sys
import os
from pathlib import Path

# Windows Unicode 인코딩 문제 근본 해결
if sys.platform == "win32":
    # 환경변수 설정 (재시작 없이 적용)
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # stdout/stderr를 UTF-8 모드로 재구성 (안전하게)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# 경로 추가
ROOT_DIR = Path(__file__).resolve().parent.parent  # repository root
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(SRC_DIR))
sys.path.append(str(ROOT_DIR.parent / "obsidian-vibe-coding-docs" / "scripts"))

from unified_development_orchestrator_v2 import (
    UnifiedDevelopmentOrchestratorV2 as UnifiedDevelopmentOrchestrator,
    ProjectContext,
)


def main():
    print("=" * 80)
    print("[*] UDO Phase 1: Ideation 시작")
    print("=" * 80)
    print()

    # 프로젝트 컨텍스트 생성 (Obsidian README 기반)
    project = ProjectContext(
        project_name="2025-Revenue-App",
        goal="2025년 Q1 상용화 부수익 앱",
        team_size=5,
        timeline_weeks=12,
        budget=50000,
        tech_stack=["Next.js 15", "Flutter", "Supabase"],
        constraints=["3개월 내 출시", "초기 투자 최소화"],
        success_metrics=["DAU 1000+", "MRR $1,000+"],
        current_phase="ideation",
        files=[],
        metadata={
            "ai_tools": ["Claude Code", "v0.dev", "Cursor", "Codex"],
            "target_launch": "2025-02-01",
            "quality_standard": "v0/Lovable 수준 UI + 프로덕션급 백엔드",
        },
    )

    # UDO 초기화
    print("\n[*] UDO 초기화 중...")
    udo = UnifiedDevelopmentOrchestrator(project)

    # Phase 1 요청
    user_request = """
2025년 한국 시장에서 수익 가능한 SaaS/앱 아이디어 발굴

요구사항:
- 타겟: 한국 시장 (개인 또는 소규모 비즈니스)
- 수익 모델: 구독/광고/수수료 등 명확한 수익화 경로
- 기술 스택: Next.js 15, Flutter, Supabase로 구현 가능
- 개발 기간: 3개월 내 MVP 출시 가능
- 차별화: 기존 서비스와 명확한 차별점

산출물:
1. 10개 아이디어 (각각 타겟/수익모델/기술난이도/예상개발시간)
2. 시장성/실현가능성 분석
3. Top 3 추천 및 근거
"""

    # 개발 사이클 시작 (분석 & 계획)
    print("\n[*] 개발 사이클 시작...")
    plan = udo.start_development_cycle(user_request)

    print("\n" + "=" * 80)
    print("[*] 실행 계획")
    print("=" * 80)
    print(f"결정: {plan['decision']}")
    print(f"시스템: {plan['system'].get('system', plan['system'].get('primary', 'N/A'))}")
    print(f"AI 협업: {plan['ai_collaboration'].get('pattern', 'N/A')}")
    print(f"접근 방식: {plan['approach']}")
    print()

    # Go 결정인 경우 실행
    if plan["decision"] in ["GO", "GO_WITH_CHECKPOINTS"]:
        print("[OK] Go 결정 - 실행을 시작합니다")
        print()

        # 실행
        result = udo.execute_plan(plan)

        print("\n" + "=" * 80)
        print("[*] 실행 결과")
        print("=" * 80)
        print(f"상태: {result['status']}")
        if "ai_result" in result:
            print(f"AI 협업 결과: {result['ai_result'].get('status', 'N/A')}")
        print()

        # 결과 기록
        udo.record_outcome(plan, result)

        # 상태 저장
        udo.save_state(Path(__file__).parent / "udo_state_phase1.json")

        print("[OK] Phase 1 Ideation 완료!")

    elif plan["decision"] == "PROTOTYPE_FIRST":
        print("[WARN] 프로토타입 우선 권장 - POC부터 시작하세요")

    else:  # NO_GO
        print("[FAIL] No-Go 결정 - 불확실성 해결 필요")
        print("\n다음 단계:")
        for step in plan["next_steps"]:
            print(f"  {step}")


if __name__ == "__main__":
    main()
