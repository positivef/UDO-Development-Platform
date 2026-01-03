"""
C-K Theory Service Usage Example

Demonstrates how to use the C-K Theory service for design alternative generation.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.ck_theory import CKTheoryRequest, DesignFeedback  # noqa: E402
from app.services.ck_theory_service import CKTheoryService  # noqa: E402


async def main():
    """Example usage of C-K Theory service"""

    # Initialize service
    service = CKTheoryService()

    # Example 1: Authentication System Design
    print("=" * 60)
    print("Example 1: Authentication System Design")
    print("=" * 60)

    request1 = CKTheoryRequest(
        challenge="Design an authentication system that supports multiple providers",
        constraints={
            "budget": "2 weeks",
            "team_size": 2,
            "security_requirement": "high",
            "complexity": "medium",
        },
        project="UDO-Development-Platform",
    )

    result1 = await service.generate_design(request1)

    print(f"\n[OK] Design ID: {result1.id}")
    print(f"[*]  Duration: {result1.total_duration_ms}ms ({result1.total_duration_ms / 1000:.1f}s)")

    # Show alternatives
    print("\n[DESIGN] Alternatives:")
    for alt in result1.alternatives:
        print(f"\n  Alternative {alt.id}: {alt.title}")
        print(
            f"  RICE Score: {alt.rice.score:.2f} (R:{alt.rice.reach} I:{alt.rice.impact} C:{alt.rice.confidence} E:{alt.rice.effort})"
        )
        print(f"  Description: {alt.description[:100]}...")
        print(f"  Timeline: {alt.estimated_timeline}")
        print(f"  Pros: {', '.join(alt.pros[:2])}...")
        print(f"  Cons: {', '.join(alt.cons[:2])}...")

    # Show trade-off analysis
    print("\n[*]  Trade-off Analysis:")
    print(f"  Summary: {result1.tradeoff_analysis.summary[:150]}...")
    print(f"  Recommendation: {result1.tradeoff_analysis.recommendation[:150]}...")

    # Show decision tree
    print("\n[DECISION] Tree:")
    for i, criterion in enumerate(result1.tradeoff_analysis.decision_tree[:3], 1):
        print(f"  {i}. {criterion}")

    if result1.obsidian_path:
        print(f"\n[SAVED] to Obsidian: {result1.obsidian_path}")

    # Example 2: Performance Optimization Design
    print("\n" + "=" * 60)
    print("Example 2: Performance Optimization Strategy")
    print("=" * 60)

    request2 = CKTheoryRequest(
        challenge="Design a caching strategy to improve API performance",
        constraints={
            "timeline": "1 week",
            "performance_requirement": "high",
            "complexity": "low",
        },
        project="UDO-Development-Platform",
    )

    result2 = await service.generate_design(request2)

    print(f"\n[OK] Design ID: {result2.id}")
    print(f"[*]  Duration: {result2.total_duration_ms}ms")

    # Show RICE scores
    print("\n[RICE] Score Comparison:")
    for alt in result2.alternatives:
        print(f"  {alt.id}: {alt.rice.score:>5.2f} - {alt.title}")

    # Show recommended alternative
    print("\n[*] Recommendation:")
    print(f"{result2.tradeoff_analysis.recommendation[:200]}...")

    # Example 3: Add feedback
    print("\n" + "=" * 60)
    print("Example 3: Add Feedback for Design")
    print("=" * 60)

    feedback = DesignFeedback(
        design_id=result1.id,
        alternative_id="A",
        rating=5,
        comments="Excellent balance of security and flexibility. Easy to implement.",
        selected_alternative="A",
        outcome="success",
    )

    success = await service.add_feedback(result1.id, feedback)

    if success:
        print("\n[OK] Feedback added successfully")
        print(f"   Design: {result1.id}")
        print(f"   Selected: Alternative {feedback.selected_alternative}")
        print(f"   Rating: {feedback.rating}/5")
        print(f"   Outcome: {feedback.outcome}")
    else:
        print("\n[FAIL] Failed to add feedback")

    # Example 4: Retrieve feedback
    print("\n" + "=" * 60)
    print("Example 4: Retrieve Feedback")
    print("=" * 60)

    feedback_list = await service.get_feedback(result1.id)

    print(f"\nFeedback for design {result1.id} ({len(feedback_list)} entries):")
    for fb in feedback_list:
        print(f"\n  Alternative: {fb.alternative_id or 'N/A'}")
        print(f"  Rating: {fb.rating}/5")
        print(f"  Selected: {fb.selected_alternative or 'N/A'}")
        print(f"  Outcome: {fb.outcome or 'N/A'}")
        if fb.comments:
            print(f"  Comments: {fb.comments[:80]}...")

    # Example 5: List recent designs
    print("\n" + "=" * 60)
    print("Example 5: List Recent Designs")
    print("=" * 60)

    summaries = await service.list_designs(limit=5)

    print(f"\nRecent Designs ({len(summaries)}):")
    for summary in summaries:
        print(f"\n  ID: {summary.id}")
        print(f"  Challenge: {summary.challenge[:60]}...")
        print(f"  Recommended: Alternative {summary.recommended_alternative}")
        print(f"  Avg RICE Score: {summary.avg_rice_score:.2f}")
        print(f"  Duration: {summary.total_duration_ms}ms")

    # Example 6: Retrieve specific design
    print("\n" + "=" * 60)
    print("Example 6: Retrieve Specific Design")
    print("=" * 60)

    retrieved = await service.get_design(result1.id)

    if retrieved:
        print(f"\n[OK] Successfully retrieved design: {retrieved.id}")
        print(f"   Challenge: {retrieved.challenge}")
        print(f"   Alternatives: {', '.join(a.id for a in retrieved.alternatives)}")
        print(f"   Created: {retrieved.created_at}")
    else:
        print(f"\n[FAIL] Design not found: {result1.id}")


if __name__ == "__main__":
    asyncio.run(main())
