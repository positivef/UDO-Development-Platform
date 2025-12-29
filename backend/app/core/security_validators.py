#!/usr/bin/env python3
"""
Security Validators for Knowledge Extraction System

Provides security validation for:
1. Path Traversal Prevention
2. Secrets Detection and Redaction
3. Content Sanitization
4. File Type Validation

These validators integrate with the Knowledge Asset Extractor to ensure
no sensitive data leaks into knowledge assets.
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SecurityViolationType(Enum):
    """Types of security violations."""

    PATH_TRAVERSAL = "path_traversal"
    SECRETS_LEAKED = "secrets_leaked"
    UNSAFE_CONTENT = "unsafe_content"
    INVALID_FILE_TYPE = "invalid_file_type"
    EXTERNAL_PATH = "external_path"


@dataclass
class SecurityViolation:
    """Represents a security violation found during validation."""

    violation_type: SecurityViolationType
    severity: str  # critical, high, medium, low
    message: str
    location: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of security validation."""

    is_valid: bool
    violations: List[SecurityViolation]
    sanitized_content: Optional[str] = None
    redacted_items: int = 0


class PathValidator:
    """
    Validates file paths to prevent path traversal attacks.

    Ensures all paths are:
    - Within allowed project boundaries
    - Not pointing to sensitive system directories
    - Not using path traversal sequences (../)
    """

    # Sensitive directories that should never be accessed
    SENSITIVE_DIRS = {
        "/etc",
        "/root",
        "/var/log",
        "/proc",
        "/sys",
        "C:\\Windows",
        "C:\\Users",
        "C:\\Program Files",
        ".git",
        ".ssh",
        ".aws",
        ".config",
        "__pycache__",
    }

    # Allowed file extensions for knowledge extraction
    ALLOWED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".md",
        ".txt",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".html",
        ".css",
        ".scss",
        ".sql",
    }

    # Files that should never be read
    BLOCKED_FILES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "secrets.yaml",
        "secrets.json",
        "credentials.json",
        "id_rsa",
        "id_ed25519",
        "id_dsa",
        ".htpasswd",
        ".htaccess",
        "config.ini",
        "settings.ini",
    }

    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize path validator.

        Args:
            project_root: Root directory for the project. Paths must be within this.
        """
        self.project_root = Path(project_root).resolve() if project_root else None

    def validate_path(self, path: str) -> ValidationResult:
        """
        Validate a file path for security issues.

        Args:
            path: The path to validate

        Returns:
            ValidationResult with any violations found
        """
        violations = []

        try:
            # Normalize and resolve the path
            normalized = Path(path)

            # Check for path traversal attempts
            if ".." in str(path):
                violations.append(
                    SecurityViolation(
                        violation_type=SecurityViolationType.PATH_TRAVERSAL,
                        severity="critical",
                        message="Path traversal sequence detected",
                        location=path,
                        details={"pattern": ".."},
                    )
                )

            # Resolve to absolute path
            try:
                resolved = normalized.resolve()
            except Exception as e:
                violations.append(
                    SecurityViolation(
                        violation_type=SecurityViolationType.PATH_TRAVERSAL,
                        severity="critical",
                        message=f"Invalid path: {e}",
                        location=path,
                    )
                )
                return ValidationResult(is_valid=False, violations=violations)

            # Check if within project root
            if self.project_root:
                try:
                    resolved.relative_to(self.project_root)
                except ValueError:
                    violations.append(
                        SecurityViolation(
                            violation_type=SecurityViolationType.EXTERNAL_PATH,
                            severity="high",
                            message="Path outside project boundary",
                            location=str(resolved),
                            details={"project_root": str(self.project_root)},
                        )
                    )

            # Check for sensitive directories
            path_str = str(resolved).lower()
            for sensitive in self.SENSITIVE_DIRS:
                if sensitive.lower() in path_str:
                    violations.append(
                        SecurityViolation(
                            violation_type=SecurityViolationType.PATH_TRAVERSAL,
                            severity="critical",
                            message=f"Access to sensitive directory: {sensitive}",
                            location=path,
                        )
                    )

            # Check file extension
            if resolved.suffix and resolved.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                violations.append(
                    SecurityViolation(
                        violation_type=SecurityViolationType.INVALID_FILE_TYPE,
                        severity="medium",
                        message=f"File type not allowed: {resolved.suffix}",
                        location=path,
                        details={"allowed": list(self.ALLOWED_EXTENSIONS)},
                    )
                )

            # Check for blocked files
            filename = resolved.name.lower()
            for blocked in self.BLOCKED_FILES:
                if filename == blocked.lower():
                    violations.append(
                        SecurityViolation(
                            violation_type=SecurityViolationType.SECRETS_LEAKED,
                            severity="critical",
                            message=f"Blocked sensitive file: {blocked}",
                            location=path,
                        )
                    )

        except Exception as e:
            violations.append(
                SecurityViolation(
                    violation_type=SecurityViolationType.PATH_TRAVERSAL,
                    severity="critical",
                    message=f"Path validation error: {e}",
                    location=path,
                )
            )

        is_valid = not any(v.severity == "critical" for v in violations)
        return ValidationResult(is_valid=is_valid, violations=violations)

    def sanitize_path(self, path: str) -> str:
        """
        Sanitize a path by removing dangerous sequences.

        Args:
            path: The path to sanitize

        Returns:
            Sanitized path string
        """
        # Remove null bytes
        sanitized = path.replace("\x00", "")

        # Remove path traversal sequences
        sanitized = re.sub(r"\.\.[\\/]", "", sanitized)
        sanitized = re.sub(r"[\\/]\.\.", "", sanitized)

        # Normalize slashes
        sanitized = sanitized.replace("\\", "/")

        # Remove double slashes
        sanitized = re.sub(r"/+", "/", sanitized)

        return sanitized


class SecretsValidator:
    """
    Validates and redacts secrets from content.

    Detects:
    - API keys (various providers)
    - Passwords and tokens
    - Private keys
    - Database connection strings
    - Cloud provider credentials
    """

    # Pattern definitions with redaction templates
    SECRET_PATTERNS = [
        # API Keys
        (r'(?i)(api[_-]?key\s*[=:]\s*["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', r"\1[REDACTED_API_KEY]\3", "API Key"),
        # Secret Keys
        (r'(?i)(secret[_-]?key\s*[=:]\s*["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', r"\1[REDACTED_SECRET]\3", "Secret Key"),
        # Passwords (various formats)
        (r'(?i)(password\s*[=:]\s*["\']?)([^\s"\']{8,})(["\']?)', r"\1[REDACTED_PASSWORD]\3", "Password"),
        # Generic tokens
        (r'(?i)(token\s*[=:]\s*["\']?)([a-zA-Z0-9_\-]{20,})(["\']?)', r"\1[REDACTED_TOKEN]\3", "Token"),
        # GitHub tokens
        (r"(ghp_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_PAT]", "GitHub PAT"),
        (r"(gho_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_OAUTH]", "GitHub OAuth"),
        (r"(ghs_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_APP]", "GitHub App Token"),
        (r"(ghr_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_REFRESH]", "GitHub Refresh"),
        # OpenAI
        (r"(sk-[a-zA-Z0-9]{48})", "[REDACTED_OPENAI_KEY]", "OpenAI API Key"),
        # AWS
        (r"(AKIA[0-9A-Z]{16})", "[REDACTED_AWS_KEY]", "AWS Access Key"),
        (
            r'(?i)(aws[_-]?secret[_-]?access[_-]?key\s*[=:]\s*["\']?)([a-zA-Z0-9/+]{40})(["\']?)',
            r"\1[REDACTED_AWS_SECRET]\3",
            "AWS Secret",
        ),
        # Bearer tokens
        (r"(?i)(bearer\s+)([a-zA-Z0-9_\-.]{20,})", r"\1[REDACTED_BEARER]", "Bearer Token"),
        # JWT tokens (simple detection)
        (r"(eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})", "[REDACTED_JWT]", "JWT Token"),
        # Database URLs
        (r"(?i)(postgres(?:ql)?://[^:]+:)([^@]+)(@)", r"\1[REDACTED_DB_PASSWORD]\3", "PostgreSQL Password"),
        (r"(?i)(mysql://[^:]+:)([^@]+)(@)", r"\1[REDACTED_DB_PASSWORD]\3", "MySQL Password"),
        (r"(?i)(mongodb(?:\+srv)?://[^:]+:)([^@]+)(@)", r"\1[REDACTED_DB_PASSWORD]\3", "MongoDB Password"),
        # Private keys
        (r"(-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)", "[REDACTED_PRIVATE_KEY_START]", "Private Key"),
        (r"(-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)", "[REDACTED_PRIVATE_KEY_END]", "Private Key End"),
        # Anthropic
        (r"(sk-ant-[a-zA-Z0-9_-]{40,})", "[REDACTED_ANTHROPIC_KEY]", "Anthropic API Key"),
        # Google
        (r"(AIza[a-zA-Z0-9_-]{35})", "[REDACTED_GOOGLE_API_KEY]", "Google API Key"),
        # Stripe
        (r"(sk_live_[a-zA-Z0-9]{24,})", "[REDACTED_STRIPE_SECRET]", "Stripe Secret Key"),
        (r"(rk_live_[a-zA-Z0-9]{24,})", "[REDACTED_STRIPE_RESTRICTED]", "Stripe Restricted Key"),
        # Slack
        (r"(xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24})", "[REDACTED_SLACK_TOKEN]", "Slack Token"),
        # Generic hex secrets (32+ chars)
        (
            r'(?i)(secret|key|token|password|credential)(["\']?\s*[:=]\s*["\']?)([a-f0-9]{32,})(["\']?)',
            r"\1\2[REDACTED_HEX_SECRET]\4",
            "Hex Secret",
        ),
    ]

    def __init__(self, custom_patterns: Optional[List[Tuple[str, str, str]]] = None):
        """
        Initialize secrets validator.

        Args:
            custom_patterns: Additional patterns as (regex, replacement, description) tuples
        """
        self.patterns = list(self.SECRET_PATTERNS)
        if custom_patterns:
            self.patterns.extend(custom_patterns)

    def validate(self, content: str) -> ValidationResult:
        """
        Validate content for secrets.

        Args:
            content: The content to validate

        Returns:
            ValidationResult with violations and sanitized content
        """
        violations = []
        found_secrets: Set[str] = set()

        for pattern, _, description in self.patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    # Get the actual matched secret
                    if isinstance(match, tuple):
                        secret = match[1] if len(match) > 1 else match[0]
                    else:
                        secret = match

                    # Truncate for logging
                    truncated = secret[:10] + "..." if len(secret) > 10 else secret

                    if secret not in found_secrets:
                        found_secrets.add(secret)
                        violations.append(
                            SecurityViolation(
                                violation_type=SecurityViolationType.SECRETS_LEAKED,
                                severity="critical",
                                message=f"Potential {description} detected",
                                details={"preview": truncated, "type": description},
                            )
                        )

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            sanitized_content=self.redact(content) if violations else content,
            redacted_items=len(found_secrets),
        )

    def redact(self, content: str) -> str:
        """
        Redact all secrets from content.

        Args:
            content: The content to redact

        Returns:
            Content with secrets redacted
        """
        redacted = content
        for pattern, replacement, _ in self.patterns:
            redacted = re.sub(pattern, replacement, redacted)
        return redacted

    def has_secrets(self, content: str) -> bool:
        """Quick check if content contains secrets."""
        for pattern, _, _ in self.patterns:
            if re.search(pattern, content):
                return True
        return False


class ContentSanitizer:
    """
    Sanitizes content for safe storage and display.

    Handles:
    - HTML/Script injection
    - Control characters
    - Excessive whitespace
    - Unicode normalization
    """

    # Dangerous HTML/script patterns
    DANGEROUS_PATTERNS = [
        (r"<script[^>]*>.*?</script>", ""),  # Script tags
        (r"javascript:", ""),  # JavaScript URLs
        (r"on\w+\s*=", ""),  # Event handlers
        (r"<iframe[^>]*>", ""),  # Iframes
        (r"<object[^>]*>", ""),  # Objects
        (r"<embed[^>]*>", ""),  # Embeds
        (r"<form[^>]*>", ""),  # Forms
        (r"data:text/html", ""),  # Data URLs
    ]

    def sanitize(self, content: str) -> str:
        """
        Sanitize content for safe storage.

        Args:
            content: The content to sanitize

        Returns:
            Sanitized content
        """
        sanitized = content

        # Remove dangerous patterns
        for pattern, replacement in self.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE | re.DOTALL)

        # Remove control characters (except newlines and tabs)
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)

        # Normalize excessive whitespace
        sanitized = re.sub(r"[ \t]+", " ", sanitized)
        sanitized = re.sub(r"\n{3,}", "\n\n", sanitized)

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        return sanitized

    def validate(self, content: str) -> ValidationResult:
        """
        Validate content for unsafe elements.

        Args:
            content: The content to validate

        Returns:
            ValidationResult with any violations
        """
        violations = []

        for pattern, _ in self.DANGEROUS_PATTERNS:
            matches = re.findall(pattern, content, flags=re.IGNORECASE | re.DOTALL)
            if matches:
                violations.append(
                    SecurityViolation(
                        violation_type=SecurityViolationType.UNSAFE_CONTENT,
                        severity="high",
                        message="Potentially unsafe content detected",
                        details={"pattern": pattern[:30], "count": len(matches)},
                    )
                )

        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            sanitized_content=self.sanitize(content),
        )


class SecurityValidatorService:
    """
    Unified security validation service.

    Combines all validators for comprehensive security checking.
    """

    def __init__(
        self,
        project_root: Optional[str] = None,
        custom_secret_patterns: Optional[List[Tuple[str, str, str]]] = None,
    ):
        """
        Initialize security validator service.

        Args:
            project_root: Root directory for path validation
            custom_secret_patterns: Additional secret patterns to detect
        """
        self.path_validator = PathValidator(project_root)
        self.secrets_validator = SecretsValidator(custom_secret_patterns)
        self.content_sanitizer = ContentSanitizer()

    def validate_path(self, path: str) -> ValidationResult:
        """Validate a file path."""
        return self.path_validator.validate_path(path)

    def validate_content(self, content: str) -> ValidationResult:
        """Validate and sanitize content for secrets and unsafe elements."""
        # Check for secrets first
        secrets_result = self.secrets_validator.validate(content)

        # Then sanitize content
        sanitize_result = self.content_sanitizer.validate(secrets_result.sanitized_content or content)

        # Combine violations
        all_violations = secrets_result.violations + sanitize_result.violations

        return ValidationResult(
            is_valid=len([v for v in all_violations if v.severity == "critical"]) == 0,
            violations=all_violations,
            sanitized_content=sanitize_result.sanitized_content,
            redacted_items=secrets_result.redacted_items,
        )

    def validate_extraction(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate an entire extraction result.

        Args:
            data: The extraction result dictionary

        Returns:
            ValidationResult with all violations found
        """
        all_violations = []
        total_redacted = 0

        # Recursively validate all string content
        def validate_recursive(obj: Any, path: str = "") -> Any:
            nonlocal total_redacted

            if isinstance(obj, str):
                result = self.validate_content(obj)
                for v in result.violations:
                    v.location = path
                all_violations.extend(result.violations)
                total_redacted += result.redacted_items
                return result.sanitized_content

            elif isinstance(obj, dict):
                return {k: validate_recursive(v, f"{path}.{k}" if path else k) for k, v in obj.items()}

            elif isinstance(obj, list):
                return [validate_recursive(item, f"{path}[{i}]") for i, item in enumerate(obj)]

            return obj

        validate_recursive(data)  # noqa: F841 - side effect: populates all_violations

        has_critical = any(v.severity == "critical" for v in all_violations)

        return ValidationResult(
            is_valid=not has_critical,
            violations=all_violations,
            sanitized_content=None,  # Use sanitized_data instead
            redacted_items=total_redacted,
        )

    def redact_secrets(self, content: str) -> str:
        """Redact all secrets from content."""
        return self.secrets_validator.redact(content)

    def sanitize_content(self, content: str) -> str:
        """Sanitize content for safe storage."""
        return self.content_sanitizer.sanitize(content)


# Singleton instance for convenience
_default_service: Optional[SecurityValidatorService] = None


def get_security_service(project_root: Optional[str] = None, reset: bool = False) -> SecurityValidatorService:
    """
    Get the default security validator service.

    Args:
        project_root: Project root for path validation
        reset: Force creation of new instance

    Returns:
        SecurityValidatorService instance
    """
    global _default_service

    if _default_service is None or reset:
        _default_service = SecurityValidatorService(project_root)

    return _default_service


# CLI for testing
def main():
    """CLI entry point for testing security validators."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Security Validators")
    parser.add_argument("--path", "-p", help="Validate a file path")
    parser.add_argument("--content", "-c", help="Validate content string")
    parser.add_argument("--file", "-f", help="Validate content from file")
    parser.add_argument("--redact", "-r", action="store_true", help="Only redact secrets")
    parser.add_argument("--project-root", help="Project root for path validation")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    service = get_security_service(args.project_root)

    if args.path:
        result = service.validate_path(args.path)
        if args.json:
            print(
                json.dumps(
                    {
                        "is_valid": result.is_valid,
                        "violations": [
                            {
                                "type": v.violation_type.value,
                                "severity": v.severity,
                                "message": v.message,
                            }
                            for v in result.violations
                        ],
                    },
                    indent=2,
                )
            )
        else:
            print(f"Path: {args.path}")
            print(f"Valid: {result.is_valid}")
            for v in result.violations:
                print(f"  [{v.severity}] {v.message}")

    elif args.content or args.file:
        content = args.content
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()

        if args.redact:
            print(service.redact_secrets(content))
        else:
            result = service.validate_content(content)
            if args.json:
                print(
                    json.dumps(
                        {
                            "is_valid": result.is_valid,
                            "redacted_items": result.redacted_items,
                            "violations": [
                                {
                                    "type": v.violation_type.value,
                                    "severity": v.severity,
                                    "message": v.message,
                                }
                                for v in result.violations
                            ],
                        },
                        indent=2,
                    )
                )
            else:
                print(f"Valid: {result.is_valid}")
                print(f"Redacted: {result.redacted_items} items")
                for v in result.violations:
                    print(f"  [{v.severity}] {v.message}")
                if result.sanitized_content:
                    print("\nSanitized content:")
                    print(result.sanitized_content[:500])

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
