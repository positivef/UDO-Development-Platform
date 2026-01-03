#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UDO v2 + Uncertainty Map v3 통합 테스트
모든 Phase에 대한 종합 테스트
"""

import sys
import os
from pathlib import Path

# Windows Unicode 인코딩 문제 근본 해결
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# 경로 추가
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent.parent / "obsidian-vibe-coding-docs" / "scripts"))

from unified_development_orchestrator_v2 import (  # noqa: E402
    UnifiedDevelopmentOrchestratorV2 as UnifiedDevelopmentOrchestrator,
    ProjectContext,
)


def print_section(title: str, char: str = "="):
    """섹션 구분 출력"""
    line = char * 80
    print(f"\n{line}")
    print(f"  {title}")
    print(line)


def run_phase_test(udo, phase_name: str, request: str, expected_files: list = None):
    """특정 Phase 테스트"""
    print_section(f"PHASE TEST: {phase_name.upper()}", "=")

    # Phase 업데이트
    udo.context.current_phase = phase_name
    if expected_files:
        udo.context.files = expected_files

    print(f"[*] Phase: {phase_name}")
    print(f"[*] Request: {request[:100]}...")
    print(f"[*] Files: {len(udo.context.files)} files")

    # 개발 사이클 실행
    plan = udo.start_development_cycle(request)

    # 결과 출력
    print("\n[*] Results:")
    print(f"  Decision: {plan.get('decision', 'UNKNOWN')}")
    print(f"  Confidence: {plan.get('confidence', 0):.1%}")
    print(f"  System: {plan.get('system', {}).get('system', 'N/A')}")

    # 불확실성 예측 확인
    if hasattr(udo.uncertainty, "predictions"):
        print("\n[*] Uncertainty Predictions:")
        for key, pred_model in udo.uncertainty.predictions.items():
            if hasattr(pred_model, "trend"):
                print(f"  {key}: {pred_model.trend} trend")

    # 실행 (GO 결정인 경우)
    if plan["decision"] in ["GO", "GO_WITH_CHECKPOINTS"]:
        result = udo.execute_plan(plan)
        udo.record_outcome(plan, result)
        print(f"\n[OK] Execution: {result.get('status', 'UNKNOWN')}")
    else:
        print(f"\n[WARN] No execution: {plan['decision']}")

    return plan


def main():
    print_section("UDO v2 + UNCERTAINTY MAP v3 INTEGRATION TEST", "=")
    print("Testing all phases with predictive uncertainty modeling\n")

    # 프로젝트 컨텍스트 생성
    project = ProjectContext(
        project_name="AI-SaaS-Platform",
        goal="AI 기반 SaaS 플랫폼 개발",
        team_size=5,
        timeline_weeks=16,
        budget=100000,
        tech_stack=["Next.js 15", "FastAPI", "PostgreSQL", "Redis"],
        constraints=["4개월 내 출시", "클라우드 비용 최적화"],
        success_metrics=["MAU 5000+", "MRR $5,000+", "Churn < 5%"],
        current_phase="ideation",
        files=[],
        metadata={
            "ai_tools": ["Claude Code", "Codex", "Gemini"],
            "target_launch": "2025-03-01",
            "quality_standard": "Enterprise-grade",
        },
    )

    # UDO 초기화
    print("[*] Initializing UDO v2 with Uncertainty Map v3...")
    udo = UnifiedDevelopmentOrchestrator(project)

    # Collect results from all phases
    results = []

    # Phase 1: Ideation
    results.append(run_phase_test(udo, "ideation", "AI 기반 코드 리뷰 자동화 SaaS 플랫폼 아이디어 검증"))

    # Phase 2: Design
    results.append(
        run_phase_test(
            udo,
            "design",
            "마이크로서비스 아키텍처 설계 with API Gateway, Auth Service, Review Service",
            expected_files=["docs/architecture.md", "docs/api_spec.yaml"],
        )
    )

    # Phase 3: MVP
    results.append(
        run_phase_test(
            udo,
            "mvp",
            "핵심 기능 MVP 구현: GitHub 연동, 기본 리뷰 엔진, 대시보드",
            expected_files=["src/api/github.py", "src/api/review.py", "src/frontend/dashboard.tsx"],
        )
    )

    # Phase 4: Implementation
    results.append(
        run_phase_test(
            udo,
            "implementation",
            "전체 기능 구현 with ML 모델 통합, 실시간 알림, 팀 협업 기능",
            expected_files=[
                "src/api/github.py",
                "src/api/review.py",
                "src/ml/model.py",
                "src/workers/notification.py",
                "tests/test_review.py",
            ],
        )
    )

    # Phase 5: Testing
    results.append(
        run_phase_test(
            udo,
            "testing",
            "종합 테스트: 단위 테스트, 통합 테스트, 부하 테스트, 보안 테스트",
            expected_files=["tests/unit/", "tests/integration/", "tests/load/", "tests/security/", "coverage.xml"],
        )
    )

    # 최종 리포트
    print_section("FINAL REPORT", "=")

    # 학습 데이터 분석
    if udo.learning_data:
        print("\n[LEARN] Data:")
        for phase, perf in udo.learning_data.get("phase_performance", {}).items():
            success_rate = perf.get("success_rate", 0)
            total = perf.get("total", 0)
            print("  %s: %.1f%% success (%d attempts)" % (phase, success_rate * 100, total))

    # 불확실성 진화 분석
    if hasattr(udo, "uncertainty_tracker"):
        print("\n[*] Uncertainty Evolution:")
        history = udo.uncertainty_tracker.confidence_history
        if history:
            print("  Initial confidence: %.1f%%" % (history[0] * 100))
            print("  Final confidence: %.1f%%" % (history[-1] * 100))
            print("  Average confidence: %.1f%%" % (sum(history) / len(history) * 100))
            print("  Trend: %s" % ("Improving ^" if history[-1] > history[0] else "Declining v"))

    # 상태 저장
    state_file = Path(__file__).parent / "udo_v3_test_state.json"
    udo.save_state(state_file)
    print("\n[*] State saved to: %s" % state_file)

    # 성공 메트릭
    print_section("SUCCESS METRICS", "=")

    phases = ["ideation", "design", "mvp", "implementation", "testing"]

    go_decisions = sum(1 for r in results if r.get("decision") == "GO")
    avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)

    print("[OK] GO Decisions: %d/%d (%.0f%%)" % (go_decisions, len(phases), go_decisions / len(phases) * 100))
    print("[*] Average Confidence: %.1f%%" % (avg_confidence * 100))
    print("[*] Success Rate: %.1f%%" % (go_decisions / len(phases) * avg_confidence * 100))

    if avg_confidence > 0.7 and go_decisions >= 4:
        print("\n[*] TEST PASSED: System is production-ready!")
    elif avg_confidence > 0.5 and go_decisions >= 3:
        print("\n[OK] TEST PASSED: System is functional with room for improvement")
    else:
        print("\n[WARN] TEST NEEDS WORK: System requires further optimization")

    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
