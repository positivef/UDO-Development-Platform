#!/usr/bin/env python3
"""
Tests for SecretsRedactor - Secrets Detection and Redaction

Comprehensive test suite covering:
- All major secret patterns (AWS, GitHub, Google, Stripe, etc.)
- Database connection strings
- JWT tokens
- Private keys
- Redaction strategies (full, partial, preserve_structure)
- Edge cases and false positive handling
- Git diff specific functionality

Author: Security Engineering Team
Date: 2025-12-28
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.secrets_redactor import (  # noqa: E402
    SecretsRedactor,
    SecretFinding,
    SecretSeverity,
    scan_for_secrets,
    redact_secrets,
)


class TestSecretPatterns:
    """Test individual secret pattern detection"""

    @pytest.fixture
    def redactor(self):
        """Create a fresh redactor for each test"""
        return SecretsRedactor(log_findings=False)

    # ========================================================================
    # AWS Patterns
    # ========================================================================

    def test_aws_access_key_detection(self, redactor):
        """Test AWS Access Key ID detection"""
        content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        findings = redactor.scan(content)

        assert len(findings) >= 1
        aws_finding = next((f for f in findings if f.pattern_name == "AWS_ACCESS_KEY"), None)
        assert aws_finding is not None
        assert aws_finding.severity == SecretSeverity.CRITICAL

    def test_aws_secret_key_detection(self, redactor):
        """Test AWS Secret Access Key detection"""
        content = "aws_secret_access_key = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"
        findings = redactor.scan(content)

        assert len(findings) >= 1
        aws_finding = next((f for f in findings if f.pattern_name == "AWS_SECRET_KEY"), None)
        assert aws_finding is not None
        assert aws_finding.severity == SecretSeverity.CRITICAL

    def test_aws_access_key_partial_redaction(self, redactor):
        """Test AWS Access Key uses partial redaction (shows prefix/suffix)"""
        content = "key = AKIAIOSFODNN7EXAMPLE"
        redacted, findings = redactor.redact(content)

        assert "AKIA" in redacted  # Prefix preserved
        assert "MPLE" in redacted  # Suffix preserved
        assert "[REDACTED:AWS_ACCESS_KEY:" in redacted

    # ========================================================================
    # GitHub Patterns
    # ========================================================================

    def test_github_token_new_format(self, redactor):
        """Test new GitHub token format (ghp_, gho_, ghu_, ghs_)"""
        content = "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        findings = redactor.scan(content)

        github_finding = next((f for f in findings if "GITHUB" in f.pattern_name), None)
        assert github_finding is not None
        assert github_finding.severity == SecretSeverity.HIGH

    def test_github_oauth_token(self, redactor):
        """Test GitHub OAuth token detection (matches general GITHUB_TOKEN pattern)"""
        content = "token: gho_abcdefghijklmnopqrstuvwxyz1234567890"
        findings = redactor.scan(content)

        # Note: gho_ tokens match the general GITHUB_TOKEN pattern first
        github_finding = next((f for f in findings if "GITHUB" in f.pattern_name), None)
        assert github_finding is not None
        assert github_finding.severity == SecretSeverity.HIGH

    # ========================================================================
    # Google Patterns
    # ========================================================================

    def test_google_api_key(self, redactor):
        """Test Google API Key detection"""
        content = "GOOGLE_API_KEY=AIzaSyC1234567890abcdefghijklmnopqrstuv"
        findings = redactor.scan(content)

        google_finding = next((f for f in findings if f.pattern_name == "GOOGLE_API_KEY"), None)
        assert google_finding is not None
        assert google_finding.severity == SecretSeverity.HIGH

    # ========================================================================
    # Stripe Patterns
    # ========================================================================

    def test_stripe_live_secret_key(self, redactor):
        """Test Stripe live secret key (CRITICAL severity)"""
        # Split to avoid GitHub secret scanning (concatenated at runtime)
        content = "stripe_key = " + "sk_" + "live_EXAMPLEKEY00000000000000"
        findings = redactor.scan(content)

        stripe_finding = next((f for f in findings if f.pattern_name == "STRIPE_SECRET_KEY"), None)
        assert stripe_finding is not None
        assert stripe_finding.severity == SecretSeverity.CRITICAL

    def test_stripe_test_key_low_severity(self, redactor):
        """Test Stripe test keys have LOW severity"""
        # Split to avoid GitHub secret scanning (concatenated at runtime)
        content = "test_key = " + "sk_" + "test_EXAMPLEKEY00000000000000"
        findings = redactor.scan(content)

        stripe_finding = next((f for f in findings if f.pattern_name == "STRIPE_TEST_KEY"), None)
        assert stripe_finding is not None
        assert stripe_finding.severity == SecretSeverity.LOW

    # ========================================================================
    # Database Connection Strings
    # ========================================================================

    def test_postgres_url_detection(self, redactor):
        """Test PostgreSQL connection string detection"""
        content = "DATABASE_URL=postgresql://admin:supersecret@db.example.com/mydb"
        findings = redactor.scan(content)

        pg_finding = next((f for f in findings if f.pattern_name == "POSTGRES_URL"), None)
        assert pg_finding is not None
        assert pg_finding.severity == SecretSeverity.CRITICAL

    def test_postgres_url_structure_preserved(self, redactor):
        """Test PostgreSQL URL redaction preserves structure"""
        content = "DATABASE_URL=postgresql://admin:supersecret@db.example.com/mydb"
        redacted, findings = redactor.redact(content)

        # Should preserve host but mask credentials
        assert "db.example.com" in redacted
        assert "***:***" in redacted
        assert "supersecret" not in redacted

    def test_mysql_url_detection(self, redactor):
        """Test MySQL connection string detection"""
        content = "MYSQL_URL=mysql://root:password123@localhost/myapp"
        findings = redactor.scan(content)

        mysql_finding = next((f for f in findings if f.pattern_name == "MYSQL_URL"), None)
        assert mysql_finding is not None

    def test_mongodb_url_detection(self, redactor):
        """Test MongoDB connection string detection"""
        content = "MONGO_URI=mongodb+srv://admin:secret@cluster.mongodb.net"
        findings = redactor.scan(content)

        mongo_finding = next((f for f in findings if f.pattern_name == "MONGODB_URL"), None)
        assert mongo_finding is not None

    # ========================================================================
    # JWT Tokens
    # ========================================================================

    def test_jwt_token_detection(self, redactor):
        """Test JWT token detection"""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        content = f"auth_token = '{jwt}'"
        findings = redactor.scan(content)

        jwt_finding = next((f for f in findings if f.pattern_name == "JWT_TOKEN"), None)
        assert jwt_finding is not None
        assert jwt_finding.severity == SecretSeverity.HIGH

    def test_jwt_partial_redaction(self, redactor):
        """Test JWT uses partial redaction"""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        content = f"token = {jwt}"
        redacted, findings = redactor.redact(content)

        assert "eyJh" in redacted  # Prefix preserved
        assert "[REDACTED:JWT_TOKEN:" in redacted

    # ========================================================================
    # Private Keys
    # ========================================================================

    def test_rsa_private_key_detection(self, redactor):
        """Test RSA private key detection"""
        content = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
-----END RSA PRIVATE KEY-----
"""
        findings = redactor.scan(content)

        rsa_finding = next((f for f in findings if f.pattern_name == "RSA_PRIVATE_KEY"), None)
        assert rsa_finding is not None
        assert rsa_finding.severity == SecretSeverity.CRITICAL

    def test_openssh_private_key_detection(self, redactor):
        """Test OpenSSH private key detection"""
        content = """
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAACFwAAAAdz
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
-----END OPENSSH PRIVATE KEY-----
"""
        findings = redactor.scan(content)

        ssh_finding = next((f for f in findings if f.pattern_name == "OPENSSH_PRIVATE_KEY"), None)
        assert ssh_finding is not None
        assert ssh_finding.severity == SecretSeverity.CRITICAL

    # ========================================================================
    # Generic Patterns
    # ========================================================================

    def test_generic_secret_assignment(self, redactor):
        """Test generic secret assignment pattern"""
        content = 'password = "mysupersecretpassword123"'
        findings = redactor.scan(content)

        generic_finding = next((f for f in findings if f.pattern_name == "GENERIC_SECRET"), None)
        assert generic_finding is not None

    def test_bearer_token_detection(self, redactor):
        """Test Bearer token detection"""
        content = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        findings = redactor.scan(content)

        bearer_finding = next((f for f in findings if f.pattern_name == "BEARER_TOKEN"), None)
        assert bearer_finding is not None

    def test_basic_auth_detection(self, redactor):
        """Test Basic auth header detection"""
        content = "Authorization: Basic YWRtaW46cGFzc3dvcmQxMjM="
        findings = redactor.scan(content)

        basic_finding = next((f for f in findings if f.pattern_name == "BASIC_AUTH"), None)
        assert basic_finding is not None


class TestRedactionStrategies:
    """Test different redaction strategies"""

    @pytest.fixture
    def redactor(self):
        return SecretsRedactor(log_findings=False)

    def test_full_redaction(self, redactor):
        """Test full redaction shows only length"""
        content = """
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn
-----END RSA PRIVATE KEY-----
"""
        redacted, findings = redactor.redact(content)

        # Full redaction should show length, not content
        assert "[REDACTED:RSA_PRIVATE_KEY:length:" in redacted
        assert "MIIEpAIBAAK" not in redacted

    def test_partial_redaction_preserves_ends(self, redactor):
        """Test partial redaction preserves first/last 4 chars"""
        content = "token = AKIAIOSFODNN7EXAMPLE"
        redacted, findings = redactor.redact(content)

        # Should preserve AKIA (first 4) and MPLE (last 4)
        assert "AKIA" in redacted
        assert "MPLE" in redacted
        assert "IOSFODNN7EXA" not in redacted  # Middle should be hidden

    def test_structure_preserved_redaction(self, redactor):
        """Test structure-preserving redaction for DB URLs"""
        content = "url = postgresql://admin:supersecret@db.example.com/mydb"
        redacted, findings = redactor.redact(content)

        # Host should be visible, credentials masked
        assert "db.example.com" in redacted
        assert "***:***" in redacted
        assert "supersecret" not in redacted


class TestAllowlist:
    """Test file allowlist functionality"""

    def test_test_files_skipped(self):
        """Test that test files are skipped"""
        redactor = SecretsRedactor(log_findings=False)
        content = "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz"

        # Should find secrets without file path
        findings = redactor.scan(content)
        assert len(findings) > 0

        redactor.reset_fingerprints()

        # Should skip with test file path
        findings = redactor.scan(content, file_path="tests/test_auth.py")
        assert len(findings) == 0

    def test_example_files_skipped(self):
        """Test that example files are skipped"""
        redactor = SecretsRedactor(log_findings=False)
        content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"

        findings = redactor.scan(content, file_path="examples/config.py")
        assert len(findings) == 0

    def test_fixture_files_skipped(self):
        """Test that fixture files are skipped"""
        redactor = SecretsRedactor(log_findings=False)
        content = "password = 'test_password_123'"

        findings = redactor.scan(content, file_path="fixtures/auth_data.json")
        assert len(findings) == 0


class TestSeverityFiltering:
    """Test severity-based filtering"""

    def test_min_severity_high(self):
        """Test filtering with min_severity=HIGH"""
        redactor = SecretsRedactor(min_severity=SecretSeverity.HIGH, log_findings=False)

        # Build content with Stripe key split to avoid GitHub scanning
        stripe_prefix = "sk_"
        content = f"""
        # Critical
        AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE

        # Low (test key)
        stripe_test = {stripe_prefix}test_EXAMPLEKEY00000000000000
        """

        findings = redactor.scan(content)

        # Should find AWS (CRITICAL >= HIGH)
        aws_found = any(f.pattern_name == "AWS_ACCESS_KEY" for f in findings)
        assert aws_found

        # Should NOT find Stripe test key (LOW < HIGH)
        stripe_test_found = any(f.pattern_name == "STRIPE_TEST_KEY" for f in findings)
        assert not stripe_test_found

    def test_min_severity_critical(self):
        """Test filtering with min_severity=CRITICAL"""
        redactor = SecretsRedactor(min_severity=SecretSeverity.CRITICAL, log_findings=False)

        content = """
        # Critical
        db_url = postgresql://admin:secret@localhost/db

        # High
        github_token = ghp_1234567890abcdefghijklmnopqrstuvwxyz
        """

        findings = redactor.scan(content)

        # Should find PostgreSQL (CRITICAL)
        pg_found = any(f.pattern_name == "POSTGRES_URL" for f in findings)
        assert pg_found

        # Should NOT find GitHub token (HIGH < CRITICAL)
        github_found = any("GITHUB" in f.pattern_name for f in findings)
        assert not github_found


class TestGitDiffSpecific:
    """Test git diff specific functionality"""

    @pytest.fixture
    def redactor(self):
        return SecretsRedactor(log_findings=False)

    def test_git_diff_added_lines_only(self, redactor):
        """Test scanning only added lines in git diff"""
        diff = """
diff --git a/config.py b/config.py
index abc123..def456 100644
--- a/config.py
+++ b/config.py
@@ -1,3 +1,5 @@
 # Config file
-old_key = "safe_key"
+AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
+AWS_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
 other_config = "value"
"""

        redacted, findings = redactor.redact_git_diff(diff, only_added_lines=True)

        # Should find secrets in added lines
        assert len(findings) >= 1
        assert any(f.pattern_name == "AWS_ACCESS_KEY" for f in findings)

    def test_git_diff_full_scan(self, redactor):
        """Test scanning entire diff content"""
        # Build diff with Stripe keys split to avoid GitHub scanning
        stripe_prefix = "sk_"
        diff = f"""
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
-old_key = {stripe_prefix}live_EXAMPLEKEY00000000000000
+new_key = {stripe_prefix}live_EXAMPLEKEY11111111111111
"""

        redacted, findings = redactor.redact_git_diff(diff, only_added_lines=False)

        # Should find secrets in both added and removed lines
        assert len(findings) >= 1


class TestDeduplication:
    """Test fingerprint-based deduplication"""

    def test_duplicate_secrets_deduplicated(self):
        """Test that duplicate secrets are only reported once"""
        redactor = SecretsRedactor(log_findings=False)

        content = """
        key1 = AKIAIOSFODNN7EXAMPLE
        key2 = AKIAIOSFODNN7EXAMPLE
        key3 = AKIAIOSFODNN7EXAMPLE
        """

        findings = redactor.scan(content)

        # Should only report once despite 3 occurrences
        aws_findings = [f for f in findings if f.pattern_name == "AWS_ACCESS_KEY"]
        assert len(aws_findings) == 1

    def test_reset_fingerprints(self):
        """Test fingerprint reset allows re-detection"""
        redactor = SecretsRedactor(log_findings=False)
        content = "key = AKIAIOSFODNN7EXAMPLE"

        # First scan
        findings1 = redactor.scan(content)
        assert len(findings1) >= 1

        # Second scan (should be deduplicated)
        findings2 = redactor.scan(content)
        assert len(findings2) == 0

        # Reset and scan again
        redactor.reset_fingerprints()
        findings3 = redactor.scan(content)
        assert len(findings3) >= 1


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_scan_for_secrets(self):
        """Test scan_for_secrets function"""
        content = "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        findings = scan_for_secrets(content)

        assert len(findings) >= 1
        assert any("GITHUB" in f.pattern_name for f in findings)

    def test_redact_secrets(self):
        """Test redact_secrets function"""
        content = "password = 'supersecret123'"
        redacted = redact_secrets(content)

        assert "supersecret123" not in redacted
        assert "[REDACTED:" in redacted


class TestEdgeCases:
    """Test edge cases and potential issues"""

    @pytest.fixture
    def redactor(self):
        return SecretsRedactor(log_findings=False)

    def test_empty_content(self, redactor):
        """Test empty content handling"""
        findings = redactor.scan("")
        assert len(findings) == 0

        redacted, findings = redactor.redact("")
        assert redacted == ""
        assert len(findings) == 0

    def test_no_secrets(self, redactor):
        """Test content with no secrets"""
        content = """
        def hello():
            print("Hello, World!")

        x = 42
        name = "John"
        """

        findings = redactor.scan(content)
        # May have some low-severity false positives, but no HIGH/CRITICAL
        high_findings = [f for f in findings if f.severity in [SecretSeverity.CRITICAL, SecretSeverity.HIGH]]
        assert len(high_findings) == 0

    def test_unicode_content(self, redactor):
        """Test content with unicode characters"""
        content = """
        # Korean comment
        password = "비밀번호123"
        api_key = AKIAIOSFODNN7EXAMPLE
        """

        findings = redactor.scan(content)
        assert any(f.pattern_name == "AWS_ACCESS_KEY" for f in findings)

    def test_multiline_private_key(self, redactor):
        """Test multiline private key detection"""
        content = """
Some text before
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn
ygWyF8Xv0pf7L2Wy3JQq5F7w8xK9mN
2B4C6D8E0F1G3H5I7J9K1L3M5N7O9P
-----END RSA PRIVATE KEY-----
Some text after
"""

        findings = redactor.scan(content)
        assert any(f.pattern_name == "RSA_PRIVATE_KEY" for f in findings)

    def test_line_number_accuracy(self, redactor):
        """Test that line numbers are accurate"""
        content = """line 1
line 2
line 3
AKIAIOSFODNN7EXAMPLE
line 5
"""

        findings = redactor.scan(content)
        aws_finding = next((f for f in findings if f.pattern_name == "AWS_ACCESS_KEY"), None)
        assert aws_finding is not None
        assert aws_finding.line_number == 4

    def test_stats_tracking(self, redactor):
        """Test statistics tracking"""
        content = "AKIAIOSFODNN7EXAMPLE"
        redactor.scan(content)

        stats = redactor.get_stats()
        assert stats["total_patterns"] > 30
        assert "by_severity" in stats
        assert stats["seen_fingerprints"] >= 1


class TestSecretFinding:
    """Test SecretFinding dataclass"""

    def test_to_dict(self):
        """Test SecretFinding.to_dict()"""
        finding = SecretFinding(
            pattern_name="TEST_PATTERN",
            severity=SecretSeverity.HIGH,
            line_number=10,
            original_length=32,
            redacted_placeholder="[REDACTED:TEST]",
            context_hint="...context...",
            fingerprint="abc123",
        )

        d = finding.to_dict()
        assert d["pattern"] == "TEST_PATTERN"
        assert d["severity"] == "HIGH"
        assert d["line"] == 10
        assert d["length"] == 32


class TestIntegration:
    """Integration tests with realistic scenarios"""

    def test_env_file_scan(self):
        """Test scanning a realistic .env file"""
        # Build env content with Stripe key split to avoid GitHub scanning
        stripe_prefix = "sk_"
        env_content = f"""
# Database
DATABASE_URL=postgresql://admin:supersecret123@db.prod.example.com:5432/myapp
REDIS_URL=redis://:redis_password@cache.example.com:6379

# AWS
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# Third Party
GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz
STRIPE_SECRET_KEY={stripe_prefix}live_EXAMPLEKEY00000000000000
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

# App Config
DEBUG=false
LOG_LEVEL=info
"""

        redactor = SecretsRedactor(log_findings=False)
        redacted, findings = redactor.redact(env_content)

        # Should find multiple secrets
        assert len(findings) >= 5

        # Critical secrets should be detected
        critical_patterns = ["AWS_ACCESS_KEY", "AWS_SECRET_KEY", "POSTGRES_URL", "STRIPE_SECRET_KEY"]
        for pattern in critical_patterns:
            assert any(pattern in f.pattern_name for f in findings), f"Missing {pattern}"

        # Secrets should be redacted
        assert "supersecret123" not in redacted
        assert "wJalrXUtnFEMI" not in redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in redacted  # Should be partially redacted

        # Safe values should remain
        assert "us-east-1" in redacted
        assert "DEBUG=false" in redacted

    def test_code_file_scan(self):
        """Test scanning a realistic Python file"""
        # Build code content with Stripe keys split to avoid GitHub scanning
        stripe_prefix = "sk_"
        code_content = f'''
import os
import requests

# Configuration
API_KEY = os.getenv("API_KEY", "{stripe_prefix}live_default_key_1234567890")

def connect_db():
    """Connect to database"""
    url = "postgresql://user:password123@localhost/mydb"
    return create_engine(url)

def call_api():
    """Make API call"""
    headers = {{
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.abc",
        "X-API-Key": "{stripe_prefix}live_another_key_0987654321"
    }}
    return requests.get("https://api.example.com", headers=headers)
'''

        redactor = SecretsRedactor(log_findings=False)
        findings = redactor.scan(code_content)

        # Should detect multiple issues
        assert len(findings) >= 2

        # Should find JWT
        assert any(f.pattern_name == "JWT_TOKEN" for f in findings)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
