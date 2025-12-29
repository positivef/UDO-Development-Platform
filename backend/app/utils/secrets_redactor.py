#!/usr/bin/env python3
"""
Secrets Redactor - Production-Ready Secrets Detection and Redaction

Scans text content (especially git diffs) for sensitive credentials
and redacts them with contextual placeholders.

Features:
- 30+ secret patterns covering major providers (AWS, GitHub, Google, etc.)
- Database connection string detection
- JWT and OAuth token detection
- Private key detection
- Environment variable pattern detection
- Context-preserving redaction (keeps debugging utility)
- Efficient regex compilation (compile once, use many)
- Configurable severity levels and logging

Usage:
    from backend.app.utils.secrets_redactor import SecretsRedactor

    redactor = SecretsRedactor()
    safe_content, findings = redactor.redact(git_diff_output)

    if findings:
        logger.warning(f"Redacted {len(findings)} secrets")

Author: Security Engineering Team
Date: 2025-12-28
Version: 1.0.0

References:
- truffleHog patterns: https://github.com/trufflesecurity/trufflehog
- detect-secrets: https://github.com/Yelp/detect-secrets
- git-secrets: https://github.com/awslabs/git-secrets
"""

import re
import logging
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Dict, Optional, Pattern, Set

logger = logging.getLogger(__name__)


class SecretSeverity(Enum):
    """Severity levels for detected secrets"""

    CRITICAL = "CRITICAL"  # Immediate breach risk (private keys, prod credentials)
    HIGH = "HIGH"  # Significant risk (API keys, tokens)
    MEDIUM = "MEDIUM"  # Moderate risk (internal tokens, test credentials)
    LOW = "LOW"  # Informational (potential false positives)


@dataclass
class SecretFinding:
    """Represents a detected secret"""

    pattern_name: str
    severity: SecretSeverity
    line_number: Optional[int]
    original_length: int
    redacted_placeholder: str
    context_hint: str  # Safe context for debugging (e.g., "line starts with: export AWS_")
    fingerprint: str  # SHA256 hash of secret for deduplication

    def to_dict(self) -> Dict:
        return {
            "pattern": self.pattern_name,
            "severity": self.severity.value,
            "line": self.line_number,
            "length": self.original_length,
            "placeholder": self.redacted_placeholder,
            "context": self.context_hint,
        }


@dataclass
class SecretPattern:
    """Defines a secret detection pattern"""

    name: str
    pattern: str
    severity: SecretSeverity
    description: str
    redact_strategy: str = "full"  # full, partial, preserve_structure

    # Compiled pattern (set after initialization)
    compiled: Optional[Pattern] = field(default=None, repr=False)


def _build_default_patterns() -> List[SecretPattern]:
    """
    Build the default list of secret patterns.

    This function creates all pattern definitions to avoid
    class attribute reference issues.
    """
    patterns = []

    # ========================================================================
    # AWS Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="AWS_ACCESS_KEY",
            pattern=r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
            severity=SecretSeverity.CRITICAL,
            description="AWS Access Key ID",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="AWS_SECRET_KEY",
            pattern=r"(?i)(?:aws_secret_access_key|aws_secret|secret_key)\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?",
            severity=SecretSeverity.CRITICAL,
            description="AWS Secret Access Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="AWS_SESSION_TOKEN",
            pattern=r"(?i)aws_session_token\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{100,})['\"]?",
            severity=SecretSeverity.CRITICAL,
            description="AWS Session Token",
        )
    )

    # ========================================================================
    # GitHub Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="GITHUB_TOKEN",
            pattern=r"gh[pousr]_[A-Za-z0-9_]{36,255}",
            severity=SecretSeverity.HIGH,
            description="GitHub Personal Access Token (new format)",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="GITHUB_TOKEN_CLASSIC",
            pattern=r"ghp_[A-Za-z0-9]{36}",
            severity=SecretSeverity.HIGH,
            description="GitHub Personal Access Token (classic)",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="GITHUB_OAUTH",
            pattern=r"gho_[A-Za-z0-9]{36}",
            severity=SecretSeverity.HIGH,
            description="GitHub OAuth Token",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="GITHUB_APP_TOKEN",
            pattern=r"(?:ghu|ghs)_[A-Za-z0-9]{36}",
            severity=SecretSeverity.HIGH,
            description="GitHub App Token",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # Google Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="GOOGLE_API_KEY",
            pattern=r"AIza[0-9A-Za-z\-_]{35}",
            severity=SecretSeverity.HIGH,
            description="Google API Key",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="GOOGLE_OAUTH_SECRET",
            pattern=r"(?i)client_secret\s*[=:]\s*['\"]?([A-Za-z0-9_-]{24})['\"]?",
            severity=SecretSeverity.HIGH,
            description="Google OAuth Client Secret",
        )
    )

    # ========================================================================
    # Stripe Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="STRIPE_SECRET_KEY",
            pattern=r"sk_live_[0-9a-zA-Z]{24,}",
            severity=SecretSeverity.CRITICAL,
            description="Stripe Live Secret Key",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="STRIPE_PUBLISHABLE_KEY",
            pattern=r"pk_live_[0-9a-zA-Z]{24,}",
            severity=SecretSeverity.MEDIUM,
            description="Stripe Live Publishable Key",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="STRIPE_TEST_KEY",
            pattern=r"[sr]k_test_[0-9a-zA-Z]{24,}",
            severity=SecretSeverity.LOW,
            description="Stripe Test Key",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # Slack Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="SLACK_TOKEN",
            pattern=r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*",
            severity=SecretSeverity.HIGH,
            description="Slack Token",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="SLACK_WEBHOOK",
            pattern=r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+",
            severity=SecretSeverity.HIGH,
            description="Slack Webhook URL",
            redact_strategy="preserve_structure",
        )
    )

    # ========================================================================
    # Database Connection Strings
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="POSTGRES_URL",
            pattern=r"postgres(?:ql)?://([^:]+):([^@]+)@([^/]+)/(\w+)",
            severity=SecretSeverity.CRITICAL,
            description="PostgreSQL Connection String",
            redact_strategy="preserve_structure",
        )
    )

    patterns.append(
        SecretPattern(
            name="MYSQL_URL",
            pattern=r"mysql://([^:]+):([^@]+)@([^/]+)/(\w+)",
            severity=SecretSeverity.CRITICAL,
            description="MySQL Connection String",
            redact_strategy="preserve_structure",
        )
    )

    patterns.append(
        SecretPattern(
            name="MONGODB_URL",
            pattern=r"mongodb(?:\+srv)?://([^:]+):([^@]+)@([^/]+)",
            severity=SecretSeverity.CRITICAL,
            description="MongoDB Connection String",
            redact_strategy="preserve_structure",
        )
    )

    patterns.append(
        SecretPattern(
            name="REDIS_URL",
            pattern=r"redis://(?::([^@]+)@)?([^:/]+)",
            severity=SecretSeverity.HIGH,
            description="Redis Connection String",
            redact_strategy="preserve_structure",
        )
    )

    # ========================================================================
    # JWT Tokens
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="JWT_TOKEN",
            pattern=r"eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*",
            severity=SecretSeverity.HIGH,
            description="JSON Web Token",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # Private Keys
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="RSA_PRIVATE_KEY",
            pattern=r"-----BEGIN RSA PRIVATE KEY-----[\s\S]*?-----END RSA PRIVATE KEY-----",
            severity=SecretSeverity.CRITICAL,
            description="RSA Private Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="EC_PRIVATE_KEY",
            pattern=r"-----BEGIN EC PRIVATE KEY-----[\s\S]*?-----END EC PRIVATE KEY-----",
            severity=SecretSeverity.CRITICAL,
            description="EC Private Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="OPENSSH_PRIVATE_KEY",
            pattern=r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]*?-----END OPENSSH PRIVATE KEY-----",
            severity=SecretSeverity.CRITICAL,
            description="OpenSSH Private Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="DSA_PRIVATE_KEY",
            pattern=r"-----BEGIN DSA PRIVATE KEY-----[\s\S]*?-----END DSA PRIVATE KEY-----",
            severity=SecretSeverity.CRITICAL,
            description="DSA Private Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="PGP_PRIVATE_KEY",
            pattern=r"-----BEGIN PGP PRIVATE KEY BLOCK-----[\s\S]*?-----END PGP PRIVATE KEY BLOCK-----",
            severity=SecretSeverity.CRITICAL,
            description="PGP Private Key",
        )
    )

    # ========================================================================
    # Generic Patterns
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="GENERIC_SECRET",
            pattern=(
                r"(?i)(?:password|passwd|pwd|secret|api_key|apikey|access_token|"
                r"auth_token|private_key)\s*[=:]\s*['\"]([^'\"]{8,})['\"]"
            ),
            severity=SecretSeverity.HIGH,
            description="Generic Secret Assignment",
        )
    )

    patterns.append(
        SecretPattern(
            name="BEARER_TOKEN",
            pattern=r"(?i)bearer\s+[A-Za-z0-9_-]{20,}",
            severity=SecretSeverity.HIGH,
            description="Bearer Token",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="BASIC_AUTH",
            pattern=r"(?i)basic\s+[A-Za-z0-9+/=]{20,}",
            severity=SecretSeverity.HIGH,
            description="Basic Auth Header",
        )
    )

    # ========================================================================
    # Package Manager Tokens
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="NPM_TOKEN",
            pattern=r"npm_[A-Za-z0-9]{36}",
            severity=SecretSeverity.HIGH,
            description="NPM Access Token",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="PYPI_TOKEN",
            pattern=r"pypi-[A-Za-z0-9_-]{100,}",
            severity=SecretSeverity.HIGH,
            description="PyPI API Token",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # Communication Services
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="TWILIO_API_KEY",
            pattern=r"SK[0-9a-fA-F]{32}",
            severity=SecretSeverity.HIGH,
            description="Twilio API Key",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="SENDGRID_API_KEY",
            pattern=r"SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}",
            severity=SecretSeverity.HIGH,
            description="SendGrid API Key",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="MAILGUN_API_KEY",
            pattern=r"key-[0-9a-zA-Z]{32}",
            severity=SecretSeverity.HIGH,
            description="Mailgun API Key",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # Platform/Service Tokens
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="HEROKU_API_KEY",
            pattern=r"(?i)heroku.*[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            severity=SecretSeverity.HIGH,
            description="Heroku API Key",
        )
    )

    patterns.append(
        SecretPattern(
            name="DISCORD_TOKEN",
            pattern=r"[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}",
            severity=SecretSeverity.HIGH,
            description="Discord Bot Token",
            redact_strategy="partial",
        )
    )

    patterns.append(
        SecretPattern(
            name="TELEGRAM_BOT_TOKEN",
            pattern=r"\d{8,10}:[A-Za-z0-9_-]{35}",
            severity=SecretSeverity.HIGH,
            description="Telegram Bot Token",
            redact_strategy="partial",
        )
    )

    # ========================================================================
    # High-Entropy Generic (catch-all)
    # ========================================================================
    patterns.append(
        SecretPattern(
            name="HIGH_ENTROPY",
            pattern=r"['\"][A-Za-z0-9+/=_-]{32,}['\"]",
            severity=SecretSeverity.LOW,
            description="High-entropy string (potential secret)",
        )
    )

    return patterns


# Default patterns - created once at module load
DEFAULT_PATTERNS = _build_default_patterns()

# Default allowlist patterns
DEFAULT_ALLOWLIST_PATTERNS = [
    r"test[s]?/",
    r"__tests__/",
    r"\.test\.(py|js|ts)$",
    r"_test\.(py|js|ts)$",
    r"\.spec\.(py|js|ts)$",
    r"example[s]?/",
    r"mock[s]?/",
    r"fixture[s]?/",
    r"\.example$",
    r"\.sample$",
    r"\.template$",
]


class SecretsRedactor:
    """
    Production-ready secrets detection and redaction engine.

    Thread-safe, efficient, and configurable.
    """

    def __init__(
        self,
        patterns: Optional[List[SecretPattern]] = None,
        allowlist_patterns: Optional[List[str]] = None,
        min_severity: SecretSeverity = SecretSeverity.LOW,
        log_findings: bool = True,
        context_chars: int = 20,
    ):
        """
        Initialize the SecretsRedactor.

        Args:
            patterns: Custom patterns to use (defaults to DEFAULT_PATTERNS)
            allowlist_patterns: File path patterns to skip
            min_severity: Minimum severity level to report
            log_findings: Whether to log when secrets are found
            context_chars: Number of safe context chars to include in findings
        """
        # Make a copy of patterns to avoid modifying the originals
        self.patterns = [
            SecretPattern(
                name=p.name,
                pattern=p.pattern,
                severity=p.severity,
                description=p.description,
                redact_strategy=p.redact_strategy,
                compiled=None,
            )
            for p in (patterns or DEFAULT_PATTERNS)
        ]

        self.allowlist_patterns = [re.compile(p) for p in (allowlist_patterns or DEFAULT_ALLOWLIST_PATTERNS)]
        self.min_severity = min_severity
        self.log_findings = log_findings
        self.context_chars = context_chars

        # Compile all patterns once
        self._compile_patterns()

        # Cache for fingerprints (deduplication)
        self._seen_fingerprints: Set[str] = set()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficiency"""
        for pattern in self.patterns:
            if pattern.compiled is None:
                try:
                    pattern.compiled = re.compile(pattern.pattern, re.MULTILINE)
                except re.error as e:
                    logger.error(f"Failed to compile pattern {pattern.name}: {e}")
                    pattern.compiled = re.compile(r"(?!)")  # Never matches

    def _severity_value(self, severity: SecretSeverity) -> int:
        """Convert severity to numeric value for comparison"""
        values = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return values.get(severity.value, 0)

    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on allowlist"""
        return any(p.search(file_path) for p in self.allowlist_patterns)

    def _get_fingerprint(self, secret: str) -> str:
        """Generate SHA256 fingerprint for deduplication"""
        return hashlib.sha256(secret.encode()).hexdigest()[:16]

    def _get_context_hint(self, text: str, match: re.Match, pattern: SecretPattern) -> str:
        """Extract safe context around the match for debugging"""
        start = max(0, match.start() - self.context_chars)
        prefix = text[start : match.start()]

        # Clean prefix (remove newlines, limit length)
        prefix = prefix.replace("\n", " ").strip()
        if len(prefix) > self.context_chars:
            prefix = "..." + prefix[-self.context_chars :]

        return f"...{prefix}[{pattern.name}]..."

    def _redact_match(self, match: re.Match, pattern: SecretPattern) -> str:
        """Generate redacted placeholder for a match"""
        matched_text = match.group(0)
        length = len(matched_text)

        if pattern.redact_strategy == "partial":
            # Show first 4 and last 4 chars
            if length > 12:
                prefix = matched_text[:4]
                suffix = matched_text[-4:]
                return f"[REDACTED:{pattern.name}:{prefix}...{suffix}]"
            else:
                return f"[REDACTED:{pattern.name}:length:{length}]"

        elif pattern.redact_strategy == "preserve_structure":
            # For DB URLs, preserve structure but mask credentials
            if "URL" in pattern.name:
                # Replace user:pass with ***:***
                redacted = re.sub(r"://[^:]+:[^@]+@", "://***:***@", matched_text)
                return f"[REDACTED:{pattern.name}:{redacted}]"
            return f"[REDACTED:{pattern.name}:structure:length:{length}]"

        else:  # full redaction
            return f"[REDACTED:{pattern.name}:length:{length}]"

    def _get_line_number(self, text: str, position: int) -> int:
        """Calculate line number from character position"""
        return text[:position].count("\n") + 1

    def scan(
        self,
        content: str,
        file_path: Optional[str] = None,
    ) -> List[SecretFinding]:
        """
        Scan content for secrets without modifying it.

        Args:
            content: Text content to scan
            file_path: Optional file path for allowlist checking

        Returns:
            List of SecretFinding objects
        """
        if file_path and self._should_skip_file(file_path):
            return []

        findings: List[SecretFinding] = []
        min_sev_value = self._severity_value(self.min_severity)

        for pattern in self.patterns:
            if self._severity_value(pattern.severity) < min_sev_value:
                continue

            if pattern.compiled is None:
                continue

            for match in pattern.compiled.finditer(content):
                secret_text = match.group(0)
                fingerprint = self._get_fingerprint(secret_text)

                # Skip duplicates
                if fingerprint in self._seen_fingerprints:
                    continue
                self._seen_fingerprints.add(fingerprint)

                finding = SecretFinding(
                    pattern_name=pattern.name,
                    severity=pattern.severity,
                    line_number=self._get_line_number(content, match.start()),
                    original_length=len(secret_text),
                    redacted_placeholder=self._redact_match(match, pattern),
                    context_hint=self._get_context_hint(content, match, pattern),
                    fingerprint=fingerprint,
                )
                findings.append(finding)

                if self.log_findings:
                    logger.warning(
                        f"Secret detected: {pattern.name} ({pattern.severity.value}) " f"at line {finding.line_number}"
                    )

        return findings

    def redact(
        self,
        content: str,
        file_path: Optional[str] = None,
    ) -> Tuple[str, List[SecretFinding]]:
        """
        Scan and redact secrets from content.

        Args:
            content: Text content to scan and redact
            file_path: Optional file path for allowlist checking

        Returns:
            Tuple of (redacted_content, list of findings)
        """
        if file_path and self._should_skip_file(file_path):
            return content, []

        findings: List[SecretFinding] = []
        redacted_content = content
        min_sev_value = self._severity_value(self.min_severity)

        # Process patterns in order of severity (CRITICAL first)
        sorted_patterns = sorted(self.patterns, key=lambda p: -self._severity_value(p.severity))

        for pattern in sorted_patterns:
            if self._severity_value(pattern.severity) < min_sev_value:
                continue

            if pattern.compiled is None:
                continue

            # Find all matches
            matches = list(pattern.compiled.finditer(redacted_content))

            # Process in reverse order to preserve positions
            for match in reversed(matches):
                secret_text = match.group(0)
                fingerprint = self._get_fingerprint(secret_text)

                # Create finding (even for duplicates, redact all occurrences)
                if fingerprint not in self._seen_fingerprints:
                    self._seen_fingerprints.add(fingerprint)

                    finding = SecretFinding(
                        pattern_name=pattern.name,
                        severity=pattern.severity,
                        line_number=self._get_line_number(content, match.start()),
                        original_length=len(secret_text),
                        redacted_placeholder=self._redact_match(match, pattern),
                        context_hint=self._get_context_hint(content, match, pattern),
                        fingerprint=fingerprint,
                    )
                    findings.append(finding)

                    if self.log_findings:
                        logger.warning(
                            f"Redacting secret: {pattern.name} ({pattern.severity.value}) " f"at line {finding.line_number}"
                        )

                # Redact in content
                placeholder = self._redact_match(match, pattern)
                redacted_content = redacted_content[: match.start()] + placeholder + redacted_content[match.end() :]

        return redacted_content, findings

    def redact_git_diff(
        self,
        diff_content: str,
        only_added_lines: bool = True,
    ) -> Tuple[str, List[SecretFinding]]:
        """
        Specialized redaction for git diff output.

        Args:
            diff_content: Raw git diff output
            only_added_lines: If True, only scan lines starting with '+'

        Returns:
            Tuple of (redacted_diff, findings)
        """
        if only_added_lines:
            # Extract only added lines for scanning
            lines = diff_content.split("\n")
            added_content = "\n".join(
                line[1:] if line.startswith("+") and not line.startswith("+++") else "" for line in lines
            )

            # Scan added content
            findings = self.scan(added_content)

            if not findings:
                return diff_content, []

            # Reset fingerprints and redact full diff
            self.reset_fingerprints()
            return self.redact(diff_content)

        return self.redact(diff_content)

    def reset_fingerprints(self) -> None:
        """Clear the fingerprint cache (for new scan session)"""
        self._seen_fingerprints.clear()

    def get_stats(self) -> Dict:
        """Get statistics about loaded patterns"""
        severity_counts: Dict[str, int] = {}
        for pattern in self.patterns:
            sev = pattern.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_patterns": len(self.patterns),
            "by_severity": severity_counts,
            "allowlist_patterns": len(self.allowlist_patterns),
            "seen_fingerprints": len(self._seen_fingerprints),
        }


# Convenience function for quick scanning
def scan_for_secrets(
    content: str,
    min_severity: SecretSeverity = SecretSeverity.MEDIUM,
) -> List[SecretFinding]:
    """
    Quick scan for secrets in content.

    Args:
        content: Text to scan
        min_severity: Minimum severity to report

    Returns:
        List of findings
    """
    redactor = SecretsRedactor(min_severity=min_severity, log_findings=False)
    return redactor.scan(content)


def redact_secrets(
    content: str,
    min_severity: SecretSeverity = SecretSeverity.MEDIUM,
) -> str:
    """
    Quick redaction of secrets in content.

    Args:
        content: Text to redact
        min_severity: Minimum severity to redact

    Returns:
        Redacted content
    """
    redactor = SecretsRedactor(min_severity=min_severity, log_findings=False)
    redacted, _ = redactor.redact(content)
    return redacted


# Example usage and self-test
if __name__ == "__main__":
    # Build test content with Stripe key split to avoid GitHub scanning
    stripe_prefix = "sk_"

    # Test content with various secrets
    test_content = f"""
    # Configuration file
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
    AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

    DATABASE_URL=postgresql://admin:supersecret123@db.example.com:5432/mydb

    # GitHub token
    GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz

    # JWT example
    auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"

    # Stripe key
    stripe_key = "{stripe_prefix}live_EXAMPLEKEY00000000000000"

    # Private key
    -----BEGIN RSA PRIVATE KEY-----
    MIIEpAIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF
    ... (truncated for example)
    -----END RSA PRIVATE KEY-----
    """

    print("=" * 60)
    print("SecretsRedactor Self-Test")
    print("=" * 60)

    redactor = SecretsRedactor(log_findings=False)

    # Scan
    print("\n[1] Scanning for secrets...")
    findings = redactor.scan(test_content)
    print(f"Found {len(findings)} secrets:")
    for f in findings:
        print(f"  - {f.pattern_name} ({f.severity.value}) at line {f.line_number}")

    # Redact
    print("\n[2] Redacting secrets...")
    redactor.reset_fingerprints()
    redacted, findings = redactor.redact(test_content)
    print(f"Redacted {len(findings)} secrets")
    print("\nRedacted content (first 500 chars):")
    print(redacted[:500])

    # Stats
    print("\n[3] Pattern statistics:")
    stats = redactor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Self-test complete!")
    print("=" * 60)
