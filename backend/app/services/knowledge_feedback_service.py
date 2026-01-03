"""
Knowledge Feedback Service - PostgreSQL persistence layer

Week 7-8: Database Migration

Responsibilities:
- Store and retrieve user feedback
- Calculate document usefulness scores
- Generate accuracy metrics
- Provide improvement suggestions

Benchmarking:
- Notion AI: Explicit feedback tracking
- Linear: 60%+ accuracy target
- GitHub Copilot: 26-40% acceptance rate
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.db.models.knowledge import (
    KnowledgeDocumentScore,
    KnowledgeFeedback,
    KnowledgeSearchStats,
)


class KnowledgeFeedbackService:
    """Service for knowledge feedback and metrics"""

    def __init__(self, db: Session):
        """
        Initialize service

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # ========================================================================
    # Feedback Operations
    # ========================================================================

    def create_feedback(
        self,
        document_id: str,
        search_query: str,
        is_helpful: bool,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
        implicit_accept: Optional[bool] = None,
        user_id: Optional[str] = None,
    ) -> KnowledgeFeedback:
        """
        Create new feedback entry

        Args:
            document_id: Obsidian document ID
            search_query: User's search query
            is_helpful: Explicit helpful feedback
            reason: Optional reason for negative feedback
            session_id: Session identifier
            implicit_accept: Implicit signal (copy/dismiss)
            user_id: User identifier

        Returns:
            Created feedback entry
        """
        feedback = KnowledgeFeedback(
            id=uuid4(),
            document_id=document_id,
            search_query=search_query,
            is_helpful=is_helpful,
            reason=reason,
            session_id=session_id,
            implicit_accept=implicit_accept,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)

        # Update document score
        self._update_document_score(
            document_id=document_id,
            is_helpful=is_helpful,
            implicit_accept=implicit_accept,
        )

        return feedback

    def get_feedback_by_id(self, feedback_id: str) -> Optional[KnowledgeFeedback]:
        """Get feedback entry by ID"""
        return self.db.query(KnowledgeFeedback).filter(KnowledgeFeedback.id == feedback_id).first()

    def delete_feedback(self, feedback_id: str) -> bool:
        """
        Delete feedback (admin only - spam/test data removal)

        Args:
            feedback_id: Feedback UUID

        Returns:
            True if deleted, False if not found
        """
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            return False

        self.db.delete(feedback)
        self.db.commit()
        return True

    # ========================================================================
    # Document Score Operations
    # ========================================================================

    def get_document_score(self, document_id: str) -> Optional[KnowledgeDocumentScore]:
        """Get document usefulness score"""
        return self.db.query(KnowledgeDocumentScore).filter(KnowledgeDocumentScore.document_id == document_id).first()

    def _update_document_score(self, document_id: str, is_helpful: bool, implicit_accept: Optional[bool]):
        """
        Update document usefulness score

        Scoring (based on GitHub Copilot telemetry):
        - Explicit helpful: +1.0
        - Implicit accept: +0.5
        - Explicit unhelpful: -1.0
        - Implicit reject: -0.3
        """
        doc_score = self.get_document_score(document_id)

        if not doc_score:
            # Create new score entry
            doc_score = KnowledgeDocumentScore(
                document_id=document_id,
                usefulness_score=0.0,
                total_searches=0,
                helpful_count=0,
                unhelpful_count=0,
                acceptance_rate=0.0,
                first_search=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
            )
            self.db.add(doc_score)

        # Increment search count
        doc_score.total_searches += 1

        # Calculate score delta
        score_delta = 0.0

        if is_helpful:
            doc_score.helpful_count += 1
            score_delta += 1.0  # Explicit positive
        else:
            doc_score.unhelpful_count += 1
            score_delta -= 1.0  # Explicit negative

        if implicit_accept is not None:
            if implicit_accept:
                score_delta += 0.5  # Implicit positive (copy/use)
            else:
                score_delta -= 0.3  # Implicit negative (dismiss)

        # Update running average score
        doc_score.usefulness_score = (
            doc_score.usefulness_score * (doc_score.total_searches - 1) + score_delta
        ) / doc_score.total_searches

        # Update acceptance rate
        doc_score.acceptance_rate = (
            (doc_score.helpful_count / doc_score.total_searches * 100) if doc_score.total_searches > 0 else 0.0
        )

        doc_score.last_updated = datetime.now(timezone.utc)

        self.db.commit()

    # ========================================================================
    # Metrics Operations
    # ========================================================================

    def get_knowledge_metrics(self, days: int = 7) -> Dict:
        """
        Get knowledge reuse accuracy metrics

        Metrics:
        1. Search Accuracy: % of helpful searches (Target: 70%+)
        2. Acceptance Rate: % of accepted solutions (Target: 40%+)
        3. False Positive Rate: % of unhelpful searches (Target: <15%)

        Benchmarking:
        - Linear: 60%+ accuracy
        - GitHub Copilot: 26-40% acceptance
        - Notion AI: <10% false positive

        Args:
            days: Number of days to include (default: 7)

        Returns:
            Dictionary with metrics
        """
        # Time period
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=days)

        # Get feedback within period
        feedback_query = self.db.query(KnowledgeFeedback).filter(KnowledgeFeedback.created_at >= period_start)

        total_feedback = feedback_query.count()

        if total_feedback == 0:
            # No data yet
            return {
                "search_accuracy": 0.0,
                "acceptance_rate": 0.0,
                "false_positive_rate": 0.0,
                "total_searches": 0,
                "total_feedback_count": 0,
                "top_documents": [],
                "low_quality_documents": [],
                "period_start": period_start,
                "period_end": period_end,
            }

        # Calculate metrics
        helpful_count = feedback_query.filter(KnowledgeFeedback.is_helpful.is_(True)).count()

        unhelpful_count = total_feedback - helpful_count

        # Acceptance rate (implicit + explicit positive)
        accept_count = feedback_query.filter(
            (KnowledgeFeedback.is_helpful.is_(True)) | (KnowledgeFeedback.implicit_accept.is_(True))
        ).count()

        search_accuracy = (helpful_count / total_feedback * 100) if total_feedback > 0 else 0.0
        acceptance_rate = (accept_count / total_feedback * 100) if total_feedback > 0 else 0.0
        false_positive_rate = (unhelpful_count / total_feedback * 100) if total_feedback > 0 else 0.0

        # Top documents (usefulness score >= 3.0)
        top_docs = (
            self.db.query(KnowledgeDocumentScore)
            .filter(KnowledgeDocumentScore.usefulness_score >= 3.0)
            .order_by(desc(KnowledgeDocumentScore.usefulness_score))
            .limit(10)
            .all()
        )

        # Low quality documents (usefulness score < 2.0, searches >= 3)
        low_quality = (
            self.db.query(KnowledgeDocumentScore.document_id)
            .filter(
                KnowledgeDocumentScore.usefulness_score < 2.0,
                KnowledgeDocumentScore.total_searches >= 3,
            )
            .all()
        )

        low_quality_ids = [doc[0] for doc in low_quality]

        return {
            "search_accuracy": round(search_accuracy, 1),
            "acceptance_rate": round(acceptance_rate, 1),
            "false_positive_rate": round(false_positive_rate, 1),
            "total_searches": total_feedback,
            "total_feedback_count": total_feedback,
            "top_documents": top_docs,
            "low_quality_documents": low_quality_ids,
            "period_start": period_start,
            "period_end": period_end,
        }

    def get_improvement_suggestions(self) -> List[Dict]:
        """
        Auto-generated improvement suggestions

        Rules:
        1. Usefulness < 2.0 + searches >= 3 -> "Consider rewriting or archiving"
        2. False positive rate > 20% -> "Review search keywords"
        3. No feedback for 30+ days -> "Document may be outdated"

        Benchmarking:
        - Linear: Weekly accuracy reports
        - GitHub Copilot: Model fine-tuning based on telemetry

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Low quality documents
        low_quality_docs = (
            self.db.query(KnowledgeDocumentScore)
            .filter(
                KnowledgeDocumentScore.usefulness_score < 2.0,
                KnowledgeDocumentScore.total_searches >= 3,
            )
            .all()
        )

        for doc_score in low_quality_docs:
            suggestions.append(
                {
                    "type": "low_quality",
                    "document_id": doc_score.document_id,
                    "score": doc_score.usefulness_score,
                    "recommendation": "Consider rewriting or archiving this document",
                    "priority": ("high" if doc_score.usefulness_score < 1.0 else "medium"),
                }
            )

        # Overall false positive check
        total_feedback = self.db.query(KnowledgeFeedback).count()
        if total_feedback > 0:
            unhelpful_count = self.db.query(KnowledgeFeedback).filter(KnowledgeFeedback.is_helpful.is_(False)).count()

            fp_rate = unhelpful_count / total_feedback

            if fp_rate > 0.20:  # >20%
                suggestions.append(
                    {
                        "type": "high_false_positive",
                        "false_positive_rate": round(fp_rate * 100, 1),
                        "recommendation": "Review search keywords and frontmatter tags",
                        "priority": "high",
                    }
                )

        return suggestions

    # ========================================================================
    # Search Stats Operations
    # ========================================================================

    def create_search_stats(
        self,
        search_query: str,
        search_time_ms: float,
        tier1_hits: int,
        tier2_hits: int,
        tier3_hits: int,
        total_results: int,
        session_id: Optional[str] = None,
    ) -> KnowledgeSearchStats:
        """
        Create search statistics entry

        Args:
            search_query: Search query text
            search_time_ms: Total search time in milliseconds
            tier1_hits: Filename pattern matches
            tier2_hits: Frontmatter YAML matches
            tier3_hits: Full-text content matches
            total_results: Total results returned
            session_id: Session identifier

        Returns:
            Created search stats entry
        """
        stats = KnowledgeSearchStats(
            id=uuid4(),
            search_query=search_query,
            search_time_ms=search_time_ms,
            tier1_hits=tier1_hits,
            tier2_hits=tier2_hits,
            tier3_hits=tier3_hits,
            total_results=total_results,
            session_id=session_id,
            created_at=datetime.now(timezone.utc),
        )

        self.db.add(stats)
        self.db.commit()
        self.db.refresh(stats)

        return stats

    def get_search_statistics(self, days: int = 7) -> Dict:
        """
        Get aggregated search statistics

        Args:
            days: Number of days to include

        Returns:
            Dictionary with search stats
        """
        period_end = datetime.now(timezone.utc)
        period_start = period_end - timedelta(days=days)

        stats_query = self.db.query(KnowledgeSearchStats).filter(KnowledgeSearchStats.created_at >= period_start)

        total_searches = stats_query.count()

        if total_searches == 0:
            return {
                "total_searches": 0,
                "avg_search_time_ms": 0.0,
                "tier1_hit_rate": 0.0,
                "tier2_hit_rate": 0.0,
                "tier3_hit_rate": 0.0,
                "avg_results_per_search": 0.0,
            }

        # Aggregate metrics
        avg_time = (
            self.db.query(func.avg(KnowledgeSearchStats.search_time_ms))
            .filter(KnowledgeSearchStats.created_at >= period_start)
            .scalar()
            or 0.0
        )

        tier1_hits = stats_query.filter(KnowledgeSearchStats.tier1_hits > 0).count()

        tier2_hits = stats_query.filter(KnowledgeSearchStats.tier2_hits > 0).count()

        tier3_hits = stats_query.filter(KnowledgeSearchStats.tier3_hits > 0).count()

        avg_results = (
            self.db.query(func.avg(KnowledgeSearchStats.total_results))
            .filter(KnowledgeSearchStats.created_at >= period_start)
            .scalar()
            or 0.0
        )

        return {
            "total_searches": total_searches,
            "avg_search_time_ms": round(avg_time, 2),
            "tier1_hit_rate": round(tier1_hits / total_searches * 100, 1),
            "tier2_hit_rate": round(tier2_hits / total_searches * 100, 1),
            "tier3_hit_rate": round(tier3_hits / total_searches * 100, 1),
            "avg_results_per_search": round(avg_results, 1),
        }


# ============================================================================
# Export
# ============================================================================

__all__ = ["KnowledgeFeedbackService"]
