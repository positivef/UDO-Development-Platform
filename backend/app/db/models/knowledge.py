"""
SQLAlchemy Models for Knowledge Reuse System

Week 7-8: PostgreSQL Migration

Tables:
- knowledge_feedback: User feedback on search results
- knowledge_document_scores: Aggregate quality scores per document
- knowledge_search_stats: Search performance metrics
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (Boolean, Column, DateTime, Float, Index, Integer,
                        String, Text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class KnowledgeFeedback(Base):
    """
    User feedback on knowledge search results

    Tracks explicit and implicit feedback to calculate accuracy metrics.

    Benchmarking:
    - Notion AI: Explicit [EMOJI]/[EMOJI] feedback
    - Linear: Confidence-based accuracy tracking
    - GitHub Copilot: Acceptance rate metrics (tab/esc)
    """

    __tablename__ = "knowledge_feedback"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document reference
    document_id = Column(
        String(500),
        nullable=False,
        index=True,
        comment="Obsidian document ID or filename",
    )

    # Search context
    search_query = Column(Text, nullable=False, comment="User's original search query")
    session_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Session identifier for tracking",
    )

    # Feedback signals
    is_helpful = Column(
        Boolean, nullable=False, comment="Explicit feedback: helpful or not"
    )
    implicit_accept = Column(
        Boolean, nullable=True, comment="Implicit signal (copy/dismiss)"
    )
    reason = Column(
        Text, nullable=True, comment="Optional reason for negative feedback"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Feedback submission timestamp",
    )
    user_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="User identifier (for future multi-user support)",
    )

    # Indexes for performance
    __table_args__ = (
        Index("ix_feedback_document_created", "document_id", "created_at"),
        Index("ix_feedback_helpful_created", "is_helpful", "created_at"),
        Index("ix_feedback_session_created", "session_id", "created_at"),
    )


class KnowledgeDocumentScore(Base):
    """
    Aggregate quality scores for documents

    Maintains running statistics per document for quick metrics retrieval.

    Score calculation:
    - Explicit helpful: +1.0
    - Implicit accept: +0.5
    - Explicit unhelpful: -1.0
    - Implicit reject: -0.3

    Benchmarking:
    - Obsidian: Backlinks count
    - Notion AI: CTR + helpful rate
    """

    __tablename__ = "knowledge_document_scores"

    # Primary key
    document_id = Column(
        String(500), primary_key=True, comment="Obsidian document ID or filename"
    )

    # Aggregate metrics
    usefulness_score = Column(
        Float, nullable=False, default=0.0, comment="Weighted score: -5.0 to +5.0"
    )
    total_searches = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total search count for this document",
    )
    helpful_count = Column(
        Integer, nullable=False, default=0, comment="Explicit helpful feedback count"
    )
    unhelpful_count = Column(
        Integer, nullable=False, default=0, comment="Explicit unhelpful feedback count"
    )
    acceptance_rate = Column(
        Float, nullable=False, default=0.0, comment="Percentage: 0-100"
    )

    # Metadata
    last_updated = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last score update timestamp",
    )
    first_search = Column(
        DateTime(timezone=True), nullable=True, comment="First search timestamp"
    )

    # Indexes
    __table_args__ = (
        Index("ix_doc_score_usefulness", "usefulness_score"),
        Index("ix_doc_score_acceptance", "acceptance_rate"),
        Index("ix_doc_score_updated", "last_updated"),
    )


class KnowledgeSearchStats(Base):
    """
    Search performance and tier breakdown statistics

    Tracks search speed and tier hit rates for performance monitoring.

    Performance targets:
    - Tier 1 (filename): <1ms, 95% accuracy
    - Tier 2 (frontmatter): <50ms, 80% accuracy
    - Tier 3 (content): <500ms, 60% accuracy
    """

    __tablename__ = "knowledge_search_stats"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Search metadata
    search_query = Column(Text, nullable=False, comment="Search query text")
    session_id = Column(
        String(100), nullable=True, index=True, comment="Session identifier"
    )

    # Performance metrics
    search_time_ms = Column(
        Float, nullable=False, comment="Total search time in milliseconds"
    )
    tier1_hits = Column(
        Integer, nullable=False, default=0, comment="Filename pattern matches"
    )
    tier2_hits = Column(
        Integer, nullable=False, default=0, comment="Frontmatter YAML matches"
    )
    tier3_hits = Column(
        Integer, nullable=False, default=0, comment="Full-text content matches"
    )
    total_results = Column(
        Integer, nullable=False, default=0, comment="Total results returned"
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Search execution timestamp",
    )

    # Indexes for analytics
    __table_args__ = (
        Index("ix_search_stats_created", "created_at"),
        Index("ix_search_stats_time", "search_time_ms"),
        Index("ix_search_stats_session_created", "session_id", "created_at"),
    )


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "KnowledgeFeedback",
    "KnowledgeDocumentScore",
    "KnowledgeSearchStats",
]
