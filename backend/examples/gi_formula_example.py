"""
GI Formula Service Usage Example

Demonstrates how to use the Genius Insight Formula service for problem-solving.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.gi_formula_service import GIFormulaService
from app.models.gi_formula import GIFormulaRequest


async def main():
    """Example usage of GI Formula service"""

    # Initialize service
    service = GIFormulaService()

    # Example 1: API Performance Problem
    print("=" * 60)
    print("Example 1: API Performance Optimization")
    print("=" * 60)

    request1 = GIFormulaRequest(
        problem="How can we reduce API response time from 200ms to 100ms?",
        context={
            "current_latency": "200ms",
            "target_latency": "100ms",
            "bottleneck": "database queries",
            "tech_stack": "FastAPI + PostgreSQL"
        },
        project="UDO-Development-Platform"
    )

    result1 = await service.generate_insight(request1)

    print(f"\n[OK] Insight ID: {result1.id}")
    print(f"⏱  Duration: {result1.total_duration_ms}ms ({result1.total_duration_ms / 1000:.1f}s)")
    print(f"[EMOJI] Confidence: {result1.bias_check.confidence_score:.2%}")
    print(f"\n[EMOJI] Final Insight:")
    print(f"{result1.final_insight[:200]}...")

    # Show stage breakdown
    print(f"\n[EMOJI] Stage Breakdown:")
    for stage_name, stage_result in result1.stages.items():
        print(f"  {stage_name:15s}: {stage_result.duration_ms:>6}ms - {stage_result.content[:50]}...")

    # Show bias check results
    if result1.bias_check.biases_detected:
        print(f"\n[WARN]  Biases Detected: {', '.join(result1.bias_check.biases_detected)}")
        print(f"[EMOJI]  Mitigation: {', '.join(result1.bias_check.mitigation_strategies)}")
    else:
        print(f"\n[OK] No biases detected")

    if result1.obsidian_path:
        print(f"\n[EMOJI] Saved to Obsidian: {result1.obsidian_path}")

    # Example 2: Architecture Decision
    print("\n" + "=" * 60)
    print("Example 2: Architecture Decision")
    print("=" * 60)

    request2 = GIFormulaRequest(
        problem="Should we use microservices or monolithic architecture for our new feature?",
        context={
            "team_size": 5,
            "timeline": "3 months",
            "scalability_needs": "medium",
            "current_architecture": "monolithic"
        },
        project="UDO-Development-Platform"
    )

    result2 = await service.generate_insight(request2)

    print(f"\n[OK] Insight ID: {result2.id}")
    print(f"⏱  Duration: {result2.total_duration_ms}ms")
    print(f"\n[EMOJI] Final Insight:")
    print(f"{result2.final_insight[:200]}...")

    # Example 3: List recent insights
    print("\n" + "=" * 60)
    print("Example 3: List Recent Insights")
    print("=" * 60)

    summaries = await service.list_insights(limit=5)

    print(f"\nRecent Insights ({len(summaries)}):")
    for summary in summaries:
        print(f"\n  ID: {summary.id}")
        print(f"  Problem: {summary.problem[:60]}...")
        print(f"  Confidence: {summary.confidence_score:.2%}")
        print(f"  Duration: {summary.total_duration_ms}ms")

    # Example 4: Retrieve specific insight
    print("\n" + "=" * 60)
    print("Example 4: Retrieve Specific Insight")
    print("=" * 60)

    retrieved = await service.get_insight(result1.id)

    if retrieved:
        print(f"\n[OK] Successfully retrieved insight: {retrieved.id}")
        print(f"   Problem: {retrieved.problem}")
        print(f"   Stages: {', '.join(retrieved.stages.keys())}")
    else:
        print(f"\n[FAIL] Insight not found: {result1.id}")


if __name__ == "__main__":
    asyncio.run(main())
