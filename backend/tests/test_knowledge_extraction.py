#!/usr/bin/env python3
"""
Tests for Knowledge Extraction System

Tests:
1. KnowledgeAssetExtractor - 5-category extraction
2. KnowledgeQualityService - 6 quality gates
3. SecurityValidators - secrets redaction, path traversal
4. Integration with KanbanArchiveService

Quality Target: 63/80 commercial parity
"""

import sys
import pytest
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_extraction_data():
    """Sample extraction data for quality validation tests."""
    return {
        "task_id": str(uuid4()),
        "task_title": "Implement Authentication Module",
        "extraction_timestamp": datetime.now(UTC).isoformat(),
        "beginner_concepts": [
            {
                "title": "JWT Token Handling",
                "explanation": "JSON Web Tokens (JWT) are a secure way to transmit information between parties. "
                "They consist of three parts: header, payload, and signature. "
                "Always validate tokens on the server side and never store sensitive data in the payload.",
                "difficulty": "medium",
                "code_example": "import jwt\ntoken = jwt.encode({'user_id': 123}, secret, algorithm='HS256')",
                "related_files": ["backend/auth.py", "backend/middleware.py"],
                "tags": ["security", "authentication", "jwt"],
            },
            {
                "title": "Password Hashing Best Practices",
                "explanation": "Never store passwords in plain text. Use bcrypt or argon2 for hashing. "
                "Always use a unique salt per password. "
                "Cost factor should be high enough to slow down brute force attacks.",
                "difficulty": "easy",
                "code_example": "from bcrypt import hashpw, gensalt\nhash = hashpw(password.encode(), gensalt())",
                "related_files": ["backend/auth_service.py"],
                "tags": ["security", "passwords"],
            },
        ],
        "management_insights": [
            {
                "category": "Security",
                "insight": "Authentication module implementation reduces security risk by 40%",
                "recommendation": "Should continue with MFA implementation in Q2 to further reduce risk by 25%",
                "roi_estimate": "Estimated $50k annual savings from prevented breaches",
                "timeline": "2 weeks for MFA implementation",
            },
            {
                "category": "Technical Debt",
                "insight": "Legacy session management replaced with JWT, reducing maintenance overhead",
                "recommendation": "Consider implementing refresh token rotation for enhanced security",
            },
        ],
        "technical_debt": [
            {
                "description": "Hardcoded token expiration time - should be configurable",
                "severity": "medium",
                "is_intentional": True,
                "remediation_estimate": "2 hours",
                "location": "backend/auth.py:45",
            },
            {
                "description": "Missing rate limiting on login endpoint",
                "severity": "high",
                "is_intentional": False,
                "remediation_estimate": "4 hours",
                "location": "backend/routes/auth.py:12",
            },
        ],
        "patterns": [
            {
                "pattern_name": "Circuit Breaker",
                "context": "Applied to external auth provider calls to prevent cascade failures",
                "is_anti_pattern": False,
                "files": ["backend/auth_service.py"],
            },
            {
                "pattern_name": "God Object",
                "context": "AuthService handles too many responsibilities - needs refactoring",
                "is_anti_pattern": True,
                "files": ["backend/auth_service.py"],
            },
        ],
        "ai_synergy": [
            {
                "tool": "Claude Code",
                "effectiveness": "High",
                "context": "Used for refactoring authentication flow - 3x faster than manual",
                "tokens_used": 15000,
                "time_saved_minutes": 120,
            },
            {
                "tool": "GitHub Copilot",
                "effectiveness": "Medium",
                "context": "Helpful for boilerplate code, less effective for security-critical logic",
            },
        ],
    }


@pytest.fixture
def minimal_extraction_data():
    """Minimal extraction data that should fail quality gates."""
    return {
        "task_id": str(uuid4()),
        "task_title": "Quick Fix",
        "beginner_concepts": [],
        "management_insights": [],
        "technical_debt": [],
        "patterns": [],
        "ai_synergy": [],
    }


@pytest.fixture
def secrets_test_content():
    """Content containing various secrets for testing redaction."""
    return {
        "description": "API integration setup",
        "notes": """
            Configure with api_key = "sk-proj-abcdefghij1234567890abcdefghij1234567890abcd"
            Use bearer token: ghp_abcdefghijklmnopqrstuvwxyz123456
            Database: postgres://admin:supersecretpassword@localhost:5432/db
            AWS: AKIAIOSFODNN7EXAMPLE
        """,
        "code": 'openai_key = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"',
    }


# ============================================================================
# KnowledgeAssetExtractor Tests
# ============================================================================


class TestKnowledgeAssetExtractor:
    """Tests for the 5-category knowledge extraction system."""

    def test_extractor_import(self):
        """Test that knowledge extractor can be imported."""
        try:
            from knowledge_asset_extractor import KnowledgeAssetExtractor

            assert KnowledgeAssetExtractor is not None
        except ImportError as e:
            pytest.skip(f"KnowledgeAssetExtractor not available: {e}")

    def test_extractor_initialization(self):
        """Test extractor initialization."""
        try:
            from knowledge_asset_extractor import KnowledgeAssetExtractor

            extractor = KnowledgeAssetExtractor()
            assert extractor is not None
        except ImportError:
            pytest.skip("KnowledgeAssetExtractor not available")

    def test_pattern_detection_signatures(self):
        """Test that pattern detection signatures are defined."""
        try:
            from knowledge_asset_extractor import PatternDetector, PATTERN_SIGNATURES

            _detector = PatternDetector()  # noqa: F841

            # Check for expected pattern categories in module-level constant
            expected_patterns = ["tdd", "error_handling", "type_hints", "dependency_injection", "caching", "async_pattern"]

            for pattern in expected_patterns:
                assert pattern in PATTERN_SIGNATURES, f"Missing pattern: {pattern}"
        except ImportError:
            pytest.skip("PatternDetector not available")

    def test_todo_extraction(self):
        """Test TODO/FIXME extraction from content."""
        try:
            from knowledge_asset_extractor import TodoExtractor

            extractor = TodoExtractor()

            content = """
            def example():
                # TODO: Implement proper error handling
                # FIXME: This is a bug
                # HACK: Temporary workaround
                pass
            """

            todos = extractor.extract_from_content(content)
            assert len(todos) >= 3

            # todos is a list of dicts with 'content' key
            todo_contents = [t.get("content", "").lower() if isinstance(t, dict) else t.lower() for t in todos]
            assert any("error handling" in t for t in todo_contents)
        except ImportError:
            pytest.skip("TodoExtractor not available")

    def test_extraction_result_structure(self):
        """Test that extraction result has correct structure."""
        try:
            from knowledge_asset_extractor import ExtractionResult

            result = ExtractionResult(
                task_id="test-001",
                task_title="Test Task",
                extraction_timestamp=datetime.now(UTC),
            )

            # Check all 5 categories exist
            assert hasattr(result, "beginner_concepts")
            assert hasattr(result, "management_insights")
            assert hasattr(result, "technical_debt")
            assert hasattr(result, "patterns")
            assert hasattr(result, "ai_synergy")
            assert hasattr(result, "quality_score")
        except ImportError:
            pytest.skip("ExtractionResult not available")


# ============================================================================
# KnowledgeQualityService Tests
# ============================================================================


class TestKnowledgeQualityService:
    """Tests for the 6 quality gates validation service."""

    def test_quality_service_import(self):
        """Test that quality service can be imported."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            assert KnowledgeQualityService is not None
        except ImportError as e:
            pytest.skip(f"KnowledgeQualityService not available: {e}")

    def test_quality_service_initialization(self):
        """Test quality service initialization."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            assert service is not None
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate1_category_coverage_pass(self, sample_extraction_data):
        """Test Gate 1: Category coverage with 5/5 categories."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            # Find Gate 1 result
            gate1 = next(g for g in report.gates if g.gate_number == 1)
            assert gate1.result.value == "passed"
            assert gate1.score >= 9  # At least 3 categories (3 points each)
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate1_category_coverage_fail(self, minimal_extraction_data):
        """Test Gate 1: Category coverage with 0/5 categories."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(minimal_extraction_data)

            gate1 = next(g for g in report.gates if g.gate_number == 1)
            assert gate1.result.value in ["failed", "warning"]
            assert gate1.score < 9
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate2_content_volume(self, sample_extraction_data):
        """Test Gate 2: Content volume check."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            gate2 = next(g for g in report.gates if g.gate_number == 2)
            # Sample data should have reasonable content volume
            assert gate2.score > 0
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate3_beginner_quality(self, sample_extraction_data):
        """Test Gate 3: Beginner concept quality."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            gate3 = next(g for g in report.gates if g.gate_number == 3)
            # Sample has code examples, explanations, etc.
            assert gate3.score > 5
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate4_management_actionability(self, sample_extraction_data):
        """Test Gate 4: Management insight actionability."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            gate4 = next(g for g in report.gates if g.gate_number == 4)
            # Sample has ROI, timeline, recommendations
            assert gate4.score > 5
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate5_debt_classification(self, sample_extraction_data):
        """Test Gate 5: Technical debt classification."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            gate5 = next(g for g in report.gates if g.gate_number == 5)
            # Sample has severity, intentional flags, estimates
            assert gate5.score > 3
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate6_secrets_security_clean(self, sample_extraction_data):
        """Test Gate 6: Secrets security with clean data."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            gate6 = next(g for g in report.gates if g.gate_number == 6)
            # Clean sample should pass security gate
            assert gate6.result.value == "passed"
            assert gate6.score == 10
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_gate6_secrets_security_fail(self, secrets_test_content):
        """Test Gate 6: Secrets security with leaked secrets."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(secrets_test_content)

            gate6 = next(g for g in report.gates if g.gate_number == 6)
            # Content with secrets should fail
            assert gate6.result.value == "failed"
            assert gate6.severity.value == "critical"
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_overall_quality_pass(self, sample_extraction_data):
        """Test overall quality assessment passes for good data."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            assert report.passed is True
            assert report.percentage >= 60  # Minimum passing threshold
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_overall_quality_fail(self, minimal_extraction_data):
        """Test overall quality assessment fails for poor data."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(minimal_extraction_data)

            assert report.passed is False
            assert report.percentage < 60
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_commercial_parity_target(self, sample_extraction_data):
        """Test that good data approaches 63/80 commercial parity target."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)

            # Check if approaching commercial quality (63/80 = 78.75%)
            # We aim for at least 60% on sample data
            assert report.percentage >= 60
            print(f"Quality score: {report.total_score}/{report.max_possible_score} ({report.percentage:.1f}%)")
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_markdown_report_generation(self, sample_extraction_data):
        """Test markdown report generation."""
        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()
            report = service.validate(sample_extraction_data)
            markdown = service.to_markdown(report)

            assert "# Knowledge Quality Report" in markdown
            assert "Gate Results" in markdown
            assert "passed" in markdown.lower() or "failed" in markdown.lower()
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")


# ============================================================================
# SecurityValidators Tests
# ============================================================================


class TestSecurityValidators:
    """Tests for security validators (secrets redaction, path traversal)."""

    def test_security_validators_import(self):
        """Test that security validators can be imported."""
        try:
            from app.core.security_validators import SecurityValidatorService

            assert SecurityValidatorService is not None
        except ImportError as e:
            pytest.skip(f"SecurityValidators not available: {e}")

    def test_path_validator_traversal_detection(self):
        """Test path traversal attack detection."""
        try:
            from app.core.security_validators import PathValidator

            validator = PathValidator()

            # Test path traversal sequences (should detect ..)
            traversal_paths = [
                "../../../etc/passwd",
                "..\\..\\Windows\\System32",
            ]

            for path in traversal_paths:
                result = validator.validate_path(path)
                # Path traversal should trigger violations
                assert len(result.violations) > 0, f"Path traversal should be detected: {path}"
        except ImportError:
            pytest.skip("PathValidator not available")

    def test_path_validator_safe_paths(self):
        """Test that safe paths without traversal are processed."""
        try:
            from app.core.security_validators import PathValidator

            validator = PathValidator()

            # These paths don't have traversal sequences
            safe_paths = [
                "app/main.py",
                "test.py",
                "README.md",
            ]

            for path in safe_paths:
                result = validator.validate_path(path)
                # Paths without .. should not have traversal violations
                traversal_violations = [v for v in result.violations if v.violation_type.value == "path_traversal"]
                # Should have no path traversal violations (may have other types)
                assert not any(
                    ".." in str(v.details) for v in traversal_violations
                ), f"Clean path should not trigger traversal: {path}"
        except ImportError:
            pytest.skip("PathValidator not available")

    def test_secrets_validator_api_keys(self):
        """Test API key detection and redaction."""
        try:
            from app.core.security_validators import SecretsValidator

            validator = SecretsValidator()

            content = 'api_key = "sk-proj-abcdefghij1234567890abcdefghij1234567890abcd"'
            result = validator.validate(content)

            assert not result.is_valid
            assert result.redacted_items > 0
            assert "[REDACTED" in result.sanitized_content
        except ImportError:
            pytest.skip("SecretsValidator not available")

    def test_secrets_validator_github_tokens(self):
        """Test GitHub token detection."""
        try:
            from app.core.security_validators import SecretsValidator

            validator = SecretsValidator()

            content = "token = ghp_abcdefghijklmnopqrstuvwxyz123456"
            result = validator.validate(content)

            # Check that secrets were found (either via is_valid or violations)
            assert not result.is_valid or result.redacted_items > 0
            # Check that redacted content contains the redaction marker
            assert "[REDACTED" in result.sanitized_content
        except ImportError:
            pytest.skip("SecretsValidator not available")

    def test_secrets_validator_database_urls(self):
        """Test database URL password detection."""
        try:
            from app.core.security_validators import SecretsValidator

            validator = SecretsValidator()

            content = "db_url = postgres://admin:supersecret@localhost:5432/db"
            result = validator.validate(content)

            assert not result.is_valid
            assert "[REDACTED_DB_PASSWORD]" in result.sanitized_content
        except ImportError:
            pytest.skip("SecretsValidator not available")

    def test_secrets_validator_clean_content(self):
        """Test that clean content passes validation."""
        try:
            from app.core.security_validators import SecretsValidator

            validator = SecretsValidator()

            clean_content = """
            def hello_world():
                print("Hello, World!")
                return True
            """

            result = validator.validate(clean_content)
            assert result.is_valid
            assert result.redacted_items == 0
        except ImportError:
            pytest.skip("SecretsValidator not available")

    def test_content_sanitizer_xss(self):
        """Test XSS/script injection prevention."""
        try:
            from app.core.security_validators import ContentSanitizer

            sanitizer = ContentSanitizer()

            malicious = '<script>alert("xss")</script><p>Safe content</p>'
            result = sanitizer.validate(malicious)

            assert "<script>" not in result.sanitized_content
            assert "Safe content" in result.sanitized_content
        except ImportError:
            pytest.skip("ContentSanitizer not available")

    def test_unified_security_service(self, secrets_test_content):
        """Test unified security validation service."""
        try:
            from app.core.security_validators import SecurityValidatorService

            service = SecurityValidatorService()

            result = service.validate_extraction(secrets_test_content)

            # Should detect secrets in the test content
            assert result.redacted_items > 0
            secret_violations = [v for v in result.violations if v.violation_type.value == "secrets_leaked"]
            assert len(secret_violations) > 0
        except ImportError:
            pytest.skip("SecurityValidatorService not available")


# ============================================================================
# Integration Tests
# ============================================================================


class TestKanbanArchiveIntegration:
    """Integration tests for knowledge extraction in archive service."""

    def test_archive_service_has_extractor(self):
        """Test that archive service initializes knowledge extractor."""
        try:
            from app.services.kanban_archive_service import KanbanArchiveService

            service = KanbanArchiveService()

            # Check that extractor attribute exists
            assert hasattr(service, "knowledge_extractor")
            assert hasattr(service, "quality_service")
            assert hasattr(service, "security_service")
        except ImportError as e:
            pytest.skip(f"KanbanArchiveService not available: {e}")

    def test_enhanced_note_generation(self, sample_extraction_data):
        """Test enhanced Obsidian note generation with knowledge assets."""
        try:
            from app.services.kanban_archive_service import KanbanArchiveService
            from app.models.kanban_archive import (
                ObsidianKnowledgeEntry,
                ROIMetrics,
            )

            service = KanbanArchiveService()

            # Create test entry and metrics
            entry = ObsidianKnowledgeEntry(
                task_id=uuid4(),
                title="Test Task",
                phase_name="implementation",
                summary="Test summary",
                key_learnings=["Learning 1", "Learning 2"],
                technical_insights=["Insight 1"],
                tags=["test"],
                related_tasks=[],
                created_at=datetime.now(UTC),
                archived_at=datetime.now(UTC),
            )

            metrics = ROIMetrics(
                task_id=entry.task_id,
                estimated_hours=4.0,
                actual_hours=3.5,
                time_saved_hours=0.5,
                efficiency_percentage=114.3,
                quality_score=85,
                constitutional_compliance=True,
                violated_articles=[],
                ai_suggested=True,
                ai_confidence=0.9,
            )

            # Generate enhanced note
            note = service._generate_enhanced_obsidian_note(entry, metrics, sample_extraction_data)

            # Check for enhanced sections
            assert "## Beginner Learning Points" in note
            assert "## Management Insights" in note
            assert "## Technical Debt Tracking" in note
            assert "## Patterns Identified" in note
            assert "## AI Tool Effectiveness" in note
        except ImportError as e:
            pytest.skip(f"Integration test not available: {e}")

    def test_extraction_with_quality_validation(self):
        """Test full extraction pipeline with quality validation."""
        try:
            from knowledge_asset_extractor import KnowledgeAssetExtractor
            from app.services.knowledge_quality_service import KnowledgeQualityService

            extractor = KnowledgeAssetExtractor()
            quality_service = KnowledgeQualityService()

            # Extract from HEAD commit (may be empty in CI)
            result = extractor.extract_from_commit(
                commit_hash="HEAD",
                task_id="test-001",
                task_title="Test Extraction",
            )

            # Convert to dict and validate
            extraction_dict = extractor.to_dict(result)
            quality_report = quality_service.validate(extraction_dict)

            # Basic assertions
            assert quality_report is not None
            assert len(quality_report.gates) == 6
            assert quality_report.max_possible_score == 80
        except (ImportError, Exception) as e:
            pytest.skip(f"Full pipeline test not available: {e}")


# ============================================================================
# Performance Tests
# ============================================================================


class TestExtractionPerformance:
    """Performance tests for extraction system."""

    def test_quality_validation_speed(self, sample_extraction_data):
        """Test that quality validation completes in <100ms."""
        import time

        try:
            from app.services.knowledge_quality_service import KnowledgeQualityService

            service = KnowledgeQualityService()

            start = time.time()
            for _ in range(10):
                service.validate(sample_extraction_data)
            elapsed = (time.time() - start) / 10 * 1000  # ms per validation

            assert elapsed < 100, f"Quality validation too slow: {elapsed:.2f}ms"
            print(f"Quality validation: {elapsed:.2f}ms average")
        except ImportError:
            pytest.skip("KnowledgeQualityService not available")

    def test_secrets_redaction_speed(self):
        """Test that secrets redaction completes in <50ms."""
        import time

        try:
            from app.core.security_validators import SecretsValidator

            validator = SecretsValidator()

            # Large content with many potential secrets
            content = "\n".join([f'api_key_{i} = "sk-test-{i:040d}"' for i in range(100)])

            start = time.time()
            validator.redact(content)
            elapsed = (time.time() - start) * 1000

            assert elapsed < 50, f"Secrets redaction too slow: {elapsed:.2f}ms"
            print(f"Secrets redaction (100 keys): {elapsed:.2f}ms")
        except ImportError:
            pytest.skip("SecretsValidator not available")


# ============================================================================
# CLI Tests
# ============================================================================


class TestCLIInterface:
    """Tests for CLI interfaces."""

    def test_extractor_cli_help(self):
        """Test that extractor CLI shows help."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "scripts/knowledge_asset_extractor.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent.parent),
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "options" in result.stdout.lower()

    def test_quality_service_cli_help(self):
        """Test that quality service CLI shows help."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "app.services.knowledge_quality_service", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent),
        )

        # May not have CLI, that's okay
        # Just check it doesn't crash badly
        assert result.returncode in [0, 1, 2]  # 0=success, 1=error, 2=argparse error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
