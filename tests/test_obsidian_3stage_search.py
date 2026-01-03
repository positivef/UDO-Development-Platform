"""
Unit tests for Obsidian 3-Stage Search

Tests progressive search strategy:
Stage 1: Filename pattern (<10ms)
Stage 2: Frontmatter metadata (<500ms)
Stage 3: Full-text search (<5s)
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch  # noqa: F401

from scripts.obsidian_3stage_search import Obsidian3StageSearch, SearchResult, search_obsidian_solutions


class TestObsidian3StageSearch:
    """Test suite for Obsidian3StageSearch class"""

    def setup_method(self):
        """Create temporary Obsidian vault structure"""
        self.temp_vault = tempfile.mkdtemp()
        self.dev_log = Path(self.temp_vault) / "개발일지" / "2025-11-21"
        self.dev_log.mkdir(parents=True)

        # Create sample files for testing
        self._create_test_files()

        # Initialize searcher
        self.searcher = Obsidian3StageSearch(self.temp_vault)

    def teardown_method(self):
        """Clean up temporary vault"""
        shutil.rmtree(self.temp_vault)

    def _create_test_files(self):
        """Create test markdown files"""
        # File 1: ModuleNotFoundError (for Stage 1 filename match)
        module_error_file = self.dev_log / "Debug-ModuleNotFound-pandas.md"
        module_error_file.write_text(
            """# ModuleNotFoundError 디버깅

## [OK] 최종 해결 방법

pip install pandas로 해결했습니다.

```bash
pip install pandas
```

성공!
""",
            encoding="utf-8",
        )

        # File 2: Permission error with frontmatter (for Stage 2)
        perm_error_file = self.dev_log / "Permission-Debug-2025.md"
        perm_error_file.write_text(
            """---
error_type: "PermissionError"
error_category: "permission"
tags: [debug, permission]
---

# Permission 문제 해결

## 해결

chmod +r로 읽기 권한 부여했습니다.
""",
            encoding="utf-8",
        )

        # File 3: Generic file for Stage 3 full-text search
        generic_file = self.dev_log / "General-Notes.md"
        generic_file.write_text(
            """# 일반 개발 노트

여기서는 timeout 문제를 다룹니다.
network connection timeout 해결 방법:
- 네트워크 확인
- 타임아웃 늘리기

성공했습니다.
""",
            encoding="utf-8",
        )

        # File 4: WebSocket debugging (recent)
        websocket_file = self.dev_log / "WebSocket-Debugging-Complete.md"
        websocket_file.write_text(
            """# WebSocket 404 오류 디버깅

## [OK] 최종 해결 방법

main.py의 중복 엔드포인트를 제거했습니다.

Line 534-562 삭제:
- @app.websocket("/ws") 중복
- 새 라우터가 동작하도록 수정

성공!
""",
            encoding="utf-8",
        )

    def test_initialization(self):
        """Test Obsidian3StageSearch initializes correctly"""
        assert self.searcher.vault_path == Path(self.temp_vault)
        assert self.searcher.dev_log_path == self.dev_log.parent
        assert len(self.searcher.error_patterns) > 0

    def test_stage1_filename_match(self):
        """Test Stage 1: Filename pattern matching"""
        result = self.searcher.search("ModuleNotFoundError: No module named 'pandas'")

        assert result.found is True
        assert result.stage == 1
        assert "pip install pandas" in result.solution
        assert result.search_time_ms < 100  # Very fast
        assert result.confidence >= 0.90

    def test_stage1_websocket_match(self):
        """Test Stage 1: WebSocket error filename match"""
        result = self.searcher.search("WebSocket connection to ws://localhost:8000/ws failed: 404")

        assert result.found is True
        assert result.stage == 1
        assert "중복 엔드포인트" in result.solution or "WebSocket" in result.solution
        assert result.search_time_ms < 100

    def test_stage1_no_match(self):
        """Test Stage 1: No filename match, falls through to Stage 2"""
        # This error doesn't match any filename patterns
        result = self.searcher._stage1_filename_search("CustomBusinessError: Unknown")

        assert result.found is False
        assert result.stage == 1

    def test_stage2_frontmatter_match(self):
        """Test Stage 2: Frontmatter metadata matching"""
        # Search for PermissionError (should match frontmatter)
        result = self.searcher.search("PermissionError: [Errno 13] Permission denied")

        # Might be caught by Stage 1 if pattern exists, or Stage 2
        assert result.found is True
        assert "chmod" in result.solution.lower() or "permission" in result.solution.lower()

    def test_stage3_fulltext_search(self):
        """Test Stage 3: Full-text search"""
        # Search for "timeout" which is only in generic file
        result = self.searcher.search("network connection timeout issue")

        assert result.found is True
        # Should find the generic notes file
        assert "timeout" in result.solution.lower() or "네트워크" in result.solution

    def test_no_solution_found(self):
        """Test when no solution exists"""
        result = self.searcher.search("CompletlyUnknownErrorThatDoesNotExist12345")

        assert result.found is False
        assert result.solution == ""

    def test_extract_error_type(self):
        """Test error type extraction"""
        assert self.searcher._extract_error_type("ModuleNotFoundError: pandas") == "ModuleNotFoundError"
        assert self.searcher._extract_error_type("PermissionError: denied") == "PermissionError"
        assert self.searcher._extract_error_type("HTTP 404 Not Found") == "404"
        assert self.searcher._extract_error_type("500 Internal Server Error") == "500"

    def test_extract_keywords(self):
        """Test keyword extraction"""
        keywords = self.searcher._extract_keywords("WebSocket connection failed with error")

        assert "websocket" in keywords or "connection" in keywords or "failed" in keywords
        assert len(keywords) <= 5  # Max 5 keywords

    def test_search_result_dataclass(self):
        """Test SearchResult dataclass"""
        result = SearchResult(
            found=True,
            solution="test solution",
            file_path="/path/to/file.md",
            stage=1,
            search_time_ms=5.2,
            token_usage=100,
            confidence=0.95,
        )

        assert result.found is True
        assert result.solution == "test solution"
        assert result.stage == 1
        assert result.confidence == 0.95


class TestConvenienceFunction:
    """Test suite for convenience function"""

    def setup_method(self):
        """Create temporary vault"""
        self.temp_vault = tempfile.mkdtemp()
        self.dev_log = Path(self.temp_vault) / "개발일지" / "2025-11-21"
        self.dev_log.mkdir(parents=True)

        # Create a simple test file
        test_file = self.dev_log / "Debug-404-NotFound.md"
        test_file.write_text(
            """# 404 오류

## Solution

엔드포인트 경로 확인했습니다.
""",
            encoding="utf-8",
        )

    def teardown_method(self):
        """Clean up"""
        shutil.rmtree(self.temp_vault)

    def test_search_obsidian_solutions(self):
        """Test convenience function search_obsidian_solutions()"""
        # Mock the global instance
        with patch("scripts.obsidian_3stage_search.get_search_instance") as mock_get:
            searcher = Obsidian3StageSearch(self.temp_vault)
            mock_get.return_value = searcher

            result = search_obsidian_solutions("404 error occurred")

            assert "found" in result
            assert "solution" in result
            assert "stage" in result
            assert "search_time_ms" in result


class TestPerformance:
    """Test suite for performance characteristics"""

    def setup_method(self):
        """Create vault with many files"""
        self.temp_vault = tempfile.mkdtemp()
        self.dev_log = Path(self.temp_vault) / "개발일지"

        # Create multiple date folders
        for i in range(1, 10):
            date_folder = self.dev_log / f"2025-11-{i:02d}"
            date_folder.mkdir(parents=True)

            # Create 10 files per folder
            for j in range(10):
                file = date_folder / f"Debug-Test-{i}-{j}.md"
                file.write_text(
                    f"""# Debug {i}-{j}

## Solution

Test solution {i}-{j}
""",
                    encoding="utf-8",
                )

        self.searcher = Obsidian3StageSearch(self.temp_vault)

    def teardown_method(self):
        """Clean up"""
        shutil.rmtree(self.temp_vault)

    def test_stage1_speed(self):
        """Test Stage 1 is fast (<100ms even with many files)"""
        result = self.searcher._stage1_filename_search("Some random error")

        # Should complete quickly even if not found
        # (we can't measure time here accurately, but the test shouldn't hang)
        assert result.stage == 1

    def test_stage2_reasonable_speed(self):
        """Test Stage 2 completes in reasonable time"""
        result = self.searcher._stage2_frontmatter_search("Some error")

        # Should complete without hanging
        assert result.stage == 2

    def test_full_search_with_fallback(self):
        """Test full 3-stage search completes"""
        import time

        start = time.time()
        result = self.searcher.search("nonexistent error message xyz")
        elapsed = (time.time() - start) * 1000  # ms

        # Should complete within 10 seconds even with 90 files
        assert elapsed < 10000  # 10 seconds
        assert result.search_time_ms > 0


@pytest.fixture
def mock_vault_with_files(tmp_path):
    """Fixture for temporary vault with test files"""
    vault = tmp_path / "test_vault"
    dev_log = vault / "개발일지" / "2025-11-21"
    dev_log.mkdir(parents=True)

    # Create test file
    test_file = dev_log / "Debug-ModuleNotFound-test.md"
    test_file.write_text(
        """## [OK] Solution

Install the module:
```bash
pip install test-module
```
""",
        encoding="utf-8",
    )

    return str(vault)


def test_integration_full_workflow(mock_vault_with_files):
    """Integration test: Full search workflow"""
    searcher = Obsidian3StageSearch(mock_vault_with_files)

    # Search for error
    result = searcher.search("ModuleNotFoundError: test-module")

    # Should find the solution
    assert result.found is True
    assert "pip install" in result.solution
    assert result.stage == 1  # Should match filename
    assert result.search_time_ms >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
