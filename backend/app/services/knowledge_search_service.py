"""
Knowledge Search Service - 3-Tier Search System

Week 6 Day 4 PM: 3-Tier Search Implementation

Architecture:
- Tier 1: Filename Pattern Matching (Debug-{Error}-{Component}-*.md)
  - Speed: <1ms
  - Accuracy: 95%+
  - Use Case: Recurring errors with known patterns

- Tier 2: Frontmatter YAML Search
  - Speed: <50ms
  - Accuracy: 80%+
  - Use Case: Metadata-based filtering (error_type, tags, category)

- Tier 3: Full-Text Content Search
  - Speed: <500ms
  - Accuracy: 60%+
  - Use Case: Fuzzy matching, semantic search

Scoring Formula:
final_score = (
    tier1_match * 10 +
    tier2_match * 5 +
    tier3_match * 1 +
    freshness_bonus * 2 +
    usefulness_score * 3
)

Benchmarking:
- Obsidian: Backlinks + Freshness
- Notion AI: CTR + Helpful rate
- Linear: Confidence score + Accuracy tracking
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SearchResult:
    """Search result with relevance score"""

    def __init__(
        self,
        document_id: str,
        document_path: str,
        relevance_score: float,
        tier1_score: float = 0.0,
        tier2_score: float = 0.0,
        tier3_score: float = 0.0,
        freshness_bonus: float = 0.0,
        usefulness_score: float = 0.0,
        matched_query: str = "",
        snippet: str = "",
    ):
        self.document_id = document_id
        self.document_path = document_path
        self.relevance_score = relevance_score
        self.tier1_score = tier1_score
        self.tier2_score = tier2_score
        self.tier3_score = tier3_score
        self.freshness_bonus = freshness_bonus
        self.usefulness_score = usefulness_score
        self.matched_query = matched_query
        self.snippet = snippet

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "document_path": self.document_path,
            "relevance_score": round(self.relevance_score, 2),
            "tier1_score": round(self.tier1_score, 2),
            "tier2_score": round(self.tier2_score, 2),
            "tier3_score": round(self.tier3_score, 2),
            "freshness_bonus": round(self.freshness_bonus, 2),
            "usefulness_score": round(self.usefulness_score, 2),
            "matched_query": self.matched_query,
            "snippet": self.snippet,
        }


class KnowledgeSearchService:
    """
    3-Tier Knowledge Search Service

    Integrates with Obsidian MCP for actual file operations.
    """

    def __init__(self, obsidian_vault_path: str):
        """
        Initialize Knowledge Search Service

        Args:
            obsidian_vault_path: Path to Obsidian vault
        """
        self.obsidian_vault_path = Path(obsidian_vault_path)

    # =========================================================================
    # Tier 1: Filename Pattern Matching (Fast, High Accuracy)
    # =========================================================================

    def tier1_filename_search(
        self,
        query: str,
        error_type: Optional[str] = None,
        obsidian_files: Optional[List[str]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Tier 1: Fast filename pattern matching

        Pattern: Debug-{Error}-{Component}-*.md

        Examples:
        - Debug-ModuleNotFound-pandas-2025-11-02.md
        - Debug-401-Auth-Service-2025-10-15.md
        - Debug-Permission-Scripts-Deploy-2025-11-01.md

        Args:
            query: Search query (e.g., "ModuleNotFoundError pandas")
            error_type: Optional specific error type
            obsidian_files: Optional pre-fetched file list from Obsidian MCP

        Returns:
            List of (document_path, score) tuples

        Speed: <1ms (regex pattern matching)
        """
        results = []

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Score calculation
        score_weight = 10.0  # Tier 1 weight

        # If files provided from MCP, use them; otherwise use mock data
        if obsidian_files:
            # Match files against patterns
            for keyword in keywords:
                # Normalize keyword (remove "Error" suffix if present)
                normalized_keyword = keyword.replace("Error", "").replace("error", "")

                if len(normalized_keyword) < 3:  # Skip short keywords
                    continue

                # Pattern: Debug-{normalized_keyword}-*.md (case-insensitive)
                pattern = re.compile(rf"Debug-{re.escape(normalized_keyword)}-.*\.md$", re.IGNORECASE)

                # Find matching files
                for file_path in obsidian_files:
                    # Extract filename from path
                    filename = Path(file_path).name if isinstance(file_path, str) else file_path

                    if pattern.search(str(filename)):
                        results.append((file_path, score_weight))
        else:
            # MVP fallback: Mock results
            for keyword in keywords:
                normalized_keyword = keyword.replace("Error", "").replace("error", "")
                if len(normalized_keyword) >= 3:
                    results.append(
                        (
                            f"Debug-{normalized_keyword}-Component-YYYY-MM-DD.md",
                            score_weight,
                        )
                    )

        return results

    # =========================================================================
    # Tier 2: Frontmatter YAML Search (Medium Speed, Good Accuracy)
    # =========================================================================

    def tier2_frontmatter_search(
        self,
        query: str,
        error_type: Optional[str] = None,
        complex_search_results: Optional[List[Dict]] = None,
    ) -> List[Tuple[str, float]]:
        """
        Tier 2: Frontmatter YAML metadata search

        Frontmatter fields:
        - error_type: "ModuleNotFoundError", "PermissionError", "401"
        - error_category: "permission", "auth", "import", "file-not-found"
        - tags: ["python", "pandas", "pytest"]
        - resolution_status: "resolved", "workaround", "permanent"
        - confidence: 0.0-1.0 (solution quality)

        Args:
            query: Search query
            error_type: Optional specific error type
            complex_search_results: Optional results from Obsidian MCP complex_search

        Returns:
            List of (document_path, score) tuples

        Speed: <50ms (YAML parsing + keyword matching)
        """
        results = []

        # Extract keywords from query
        keywords = self._extract_keywords(query)

        # Score calculation
        score_weight = 5.0  # Tier 2 weight

        # If complex search results provided, process them
        if complex_search_results:
            # Process results from obsidian_complex_search
            # Expected format: List of documents matching JsonLogic query
            for doc in complex_search_results:
                # Extract path from document
                if isinstance(doc, dict):
                    doc_path = doc.get("path") or doc.get("file") or str(doc)
                else:
                    doc_path = str(doc)

                results.append((doc_path, score_weight))
        else:
            # MVP fallback: Mock results based on keywords
            for keyword in keywords:
                results.append((f"Frontmatter-Match-{keyword}.md", score_weight))

        return results

    def _build_frontmatter_query(self, keywords: List[str], error_type: Optional[str] = None) -> Dict:
        """
        Build JsonLogic query for frontmatter search

        Example output:
        {
          "and": [
            {"in": ["ModuleNotFoundError", {"var": "frontmatter.error_type"}]},
            {"in": ["pandas", {"var": "frontmatter.tags"}]}
          ]
        }

        Args:
            keywords: Extracted search keywords
            error_type: Optional specific error type

        Returns:
            JsonLogic query dictionary
        """
        conditions = []

        # Add error_type condition if provided
        if error_type:
            conditions.append({"in": [error_type, {"var": "frontmatter.error_type"}]})

        # Add keyword conditions (search in tags and error_category)
        for keyword in keywords:
            # Search in tags array
            conditions.append({"in": [keyword, {"var": "frontmatter.tags"}]})

        # Combine with OR logic (any keyword match)
        if len(conditions) == 1:
            return conditions[0]
        elif len(conditions) > 1:
            return {"or": conditions}
        else:
            # No conditions - match all
            return {"==": [1, 1]}

    # =========================================================================
    # Tier 3: Full-Text Content Search (Slower, Semantic Matching)
    # =========================================================================

    def tier3_content_search(
        self, query: str, simple_search_results: Optional[List[Dict]] = None
    ) -> List[Tuple[str, float, str]]:
        """
        Tier 3: Full-text content search

        Uses Obsidian MCP obsidian_simple_search for content matching.

        Args:
            query: Search query
            simple_search_results: Optional results from Obsidian MCP simple_search

        Returns:
            List of (document_path, score, snippet) tuples

        Speed: <500ms (full-text search with context)
        """
        results = []

        # Score calculation
        score_weight = 1.0  # Tier 3 weight

        # If simple search results provided, process them
        if simple_search_results:
            # Process results from obsidian_simple_search
            # Expected format: List of {file, matches, context}
            for result in simple_search_results:
                if isinstance(result, dict):
                    doc_path = result.get("file") or result.get("path")
                    snippet = result.get("context", "")[:200]  # Limit to 200 chars

                    if doc_path:
                        # Calculate score based on match count
                        match_count = len(result.get("matches", []))
                        adjusted_score = score_weight * (1 + match_count * 0.1)

                        results.append((doc_path, adjusted_score, snippet))
                else:
                    # Fallback: treat as path string
                    results.append((str(result), score_weight, ""))
        else:
            # MVP fallback: Mock result
            results.append(
                (
                    f"Content-Match-{query[:20]}.md",
                    score_weight,
                    f"Found content matching '{query[:50]}...'",
                )
            )

        return results

    # =========================================================================
    # Scoring & Ranking
    # =========================================================================

    def calculate_relevance_score(
        self,
        tier1_score: float,
        tier2_score: float,
        tier3_score: float,
        freshness_days: int,
        usefulness_score: float = 0.0,
    ) -> float:
        """
        Calculate final relevance score

        Formula:
        final_score = (
            tier1_score * 10 +
            tier2_score * 5 +
            tier3_score * 1 +
            freshness_bonus * 2 +
            usefulness_score * 3
        )

        Freshness Bonus:
        - <7 days: +5.0
        - <30 days: +3.0
        - <90 days: +1.0
        - >90 days: 0.0

        Args:
            tier1_score: Filename match score (0-10)
            tier2_score: Frontmatter match score (0-5)
            tier3_score: Content match score (0-1)
            freshness_days: Days since last update
            usefulness_score: User feedback score (-5.0 to +5.0)

        Returns:
            Final relevance score (0-100+)
        """
        # Freshness bonus (decay over time)
        if freshness_days < 7:
            freshness_bonus = 5.0
        elif freshness_days < 30:
            freshness_bonus = 3.0
        elif freshness_days < 90:
            freshness_bonus = 1.0
        else:
            freshness_bonus = 0.0

        # Final score calculation
        final_score = tier1_score * 10 + tier2_score * 5 + tier3_score * 1 + freshness_bonus * 2 + usefulness_score * 3

        return final_score

    # =========================================================================
    # Main Search Interface
    # =========================================================================

    def search(
        self,
        query: str,
        error_type: Optional[str] = None,
        max_results: int = 10,
        min_score: float = 5.0,
    ) -> List[SearchResult]:
        """
        Unified 3-tier search

        Execution:
        1. Tier 1: Filename pattern (fastest, highest weight)
        2. Tier 2: Frontmatter YAML (medium speed, good accuracy)
        3. Tier 3: Full-text content (slower, fuzzy matching)
        4. Merge results with scoring
        5. Sort by relevance score
        6. Return top N results

        Args:
            query: Search query (e.g., "authentication 401 error")
            error_type: Optional specific error type
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold

        Returns:
            List of SearchResult objects, sorted by relevance

        Performance Target: <500ms (p95)
        """
        all_results = {}  # document_path -> SearchResult

        # Tier 1: Filename search
        tier1_results = self.tier1_filename_search(query, error_type)
        for doc_path, score in tier1_results:
            if doc_path not in all_results:
                all_results[doc_path] = SearchResult(
                    document_id=doc_path,
                    document_path=doc_path,
                    relevance_score=0.0,
                    tier1_score=score,
                )
            else:
                all_results[doc_path].tier1_score += score

        # Tier 2: Frontmatter search
        tier2_results = self.tier2_frontmatter_search(query, error_type)
        for doc_path, score in tier2_results:
            if doc_path not in all_results:
                all_results[doc_path] = SearchResult(
                    document_id=doc_path,
                    document_path=doc_path,
                    relevance_score=0.0,
                    tier2_score=score,
                )
            else:
                all_results[doc_path].tier2_score += score

        # Tier 3: Content search
        tier3_results = self.tier3_content_search(query)
        for result_tuple in tier3_results:
            # Handle both (path, score) and (path, score, snippet) formats
            if len(result_tuple) == 3:
                doc_path, score, snippet = result_tuple
            else:
                doc_path, score = result_tuple
                snippet = ""

            if doc_path not in all_results:
                all_results[doc_path] = SearchResult(
                    document_id=doc_path,
                    document_path=doc_path,
                    relevance_score=0.0,
                    tier3_score=score,
                    snippet=snippet,
                )
            else:
                all_results[doc_path].tier3_score += score
                if snippet:
                    all_results[doc_path].snippet = snippet

        # Calculate final scores
        for doc_path, result in all_results.items():
            # TODO: Get freshness from file modification time (Obsidian MCP)
            freshness_days = 15  # Mock value for MVP

            # TODO: Get usefulness score from feedback storage
            usefulness_score = 0.0  # Mock value for MVP

            result.relevance_score = self.calculate_relevance_score(
                tier1_score=result.tier1_score,
                tier2_score=result.tier2_score,
                tier3_score=result.tier3_score,
                freshness_days=freshness_days,
                usefulness_score=usefulness_score,
            )

            result.freshness_bonus = (
                5.0 if freshness_days < 7 else 3.0 if freshness_days < 30 else 1.0 if freshness_days < 90 else 0.0
            )
            result.usefulness_score = usefulness_score

        # Filter by minimum score
        filtered_results = [result for result in all_results.values() if result.relevance_score >= min_score]

        # Sort by relevance score (descending)
        filtered_results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Return top N results
        return filtered_results[:max_results]

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from search query

        Rules:
        - Split by whitespace
        - Remove stop words (a, an, the, is, are, etc.)
        - Normalize case
        - Remove special characters

        Args:
            query: Search query string

        Returns:
            List of extracted keywords
        """
        # Stop words (common words to ignore)
        stop_words = {
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "how",
            "what",
            "when",
            "where",
            "why",
            "which",
        }

        # Split and normalize
        words = query.lower().split()

        # Filter stop words and short words
        keywords = [
            word.strip(".,;:!?\"'()[]{}").strip() for word in words if word.lower() not in stop_words and len(word) >= 3
        ]

        return keywords


# =============================================================================
# Export
# =============================================================================

__all__ = ["KnowledgeSearchService", "SearchResult"]
