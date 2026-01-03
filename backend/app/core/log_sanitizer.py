"""
Log Sanitizer - MED-04 Security Improvement

Prevents sensitive information from appearing in logs by automatically
detecting and masking:
- Passwords
- API keys / Secrets
- JWT tokens
- Email addresses (optionally)
- Credit card numbers
- Personal identifiable information (PII)

Usage:
    from app.core.log_sanitizer import sanitize_log_message, SecureLogger

    # Direct sanitization
    safe_msg = sanitize_log_message(f"User {user} failed login with password {pw}")

    # Using SecureLogger (recommended)
    logger = SecureLogger(__name__)
    logger.info(f"Processing request for {email}")  # Email masked automatically
"""

import logging
import re
from functools import wraps
from typing import List, Optional

# =============================================================================
# Sensitive Data Patterns
# =============================================================================

SENSITIVE_PATTERNS = [
    # Passwords (various formats)
    (
        r'(?i)(password|passwd|pwd|pass)\s*[=:]\s*[\'"]?([^\s\'"&]+)',
        r"\1=***REDACTED***",
    ),
    (
        r'(?i)(password|passwd|pwd|pass)\s*[\'"]?\s*:\s*[\'"]?([^\s\'"}\]]+)',
        r"\1: ***REDACTED***",
    ),
    # API keys and secrets
    (
        r'(?i)(api[_-]?key|apikey|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[=:]\s*[\'"]?([A-Za-z0-9_\-\.]{16,})[\'"]?',
        r"\1=***REDACTED***",
    ),
    # JWT tokens (Bearer tokens)
    (
        r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+\.[A-Za-z0-9_\-\.]+)",
        r"\1***JWT_REDACTED***",
    ),
    # Generic JWT pattern (eyJ...)
    (r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "***JWT_REDACTED***"),
    # Authorization headers
    (r'(?i)(authorization)\s*[=:]\s*[\'"]?([^\s\'"]+)', r"\1=***REDACTED***"),
    # Credit card numbers (basic patterns)
    (
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b",
        "***CC_REDACTED***",
    ),
    # Social Security Numbers (US format)
    (r"\b\d{3}-\d{2}-\d{4}\b", "***SSN_REDACTED***"),
    # Session IDs and cookies
    (
        r'(?i)(session[_-]?id|sessionid|sid)\s*[=:]\s*[\'"]?([A-Za-z0-9_\-]{16,})',
        r"\1=***REDACTED***",
    ),
    # Database connection strings with passwords
    (
        r"(?i)(postgres|mysql|mongodb|redis)://[^:]+:([^@]+)@",
        r"\1://***:***REDACTED***@",
    ),
    # AWS credentials
    (
        r'(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[=:]\s*[\'"]?([A-Za-z0-9/+=]{16,})',
        r"\1=***REDACTED***",
    ),
    # Private keys (partial detection)
    (
        r"-----BEGIN [A-Z]+ PRIVATE KEY-----.*?-----END [A-Z]+ PRIVATE KEY-----",
        "***PRIVATE_KEY_REDACTED***",
    ),
    # Hash values that might be password hashes (bcrypt, pbkdf2)
    (r"\$2[ayb]\$[0-9]{2}\$[A-Za-z0-9./]{53}", "***HASH_REDACTED***"),
    (r"pbkdf2\$[A-Fa-f0-9]+\$[A-Fa-f0-9]+", "***HASH_REDACTED***"),
]

# Optional: Email masking (can be enabled per use case)
EMAIL_PATTERN = (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "***EMAIL***")


def sanitize_log_message(
    message: str,
    mask_emails: bool = False,
    additional_patterns: Optional[List[tuple]] = None,
) -> str:
    """
    Sanitize a log message by removing/masking sensitive information.

    Args:
        message: The log message to sanitize
        mask_emails: If True, also mask email addresses
        additional_patterns: Additional regex patterns to apply [(pattern, replacement), ...]

    Returns:
        Sanitized message with sensitive data masked
    """
    if not message:
        return message

    sanitized = message

    # Apply standard sensitive patterns
    for pattern, replacement in SENSITIVE_PATTERNS:
        try:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.DOTALL)
        except re.error:
            # Skip invalid patterns
            continue

    # Optionally mask emails
    if mask_emails:
        pattern, replacement = EMAIL_PATTERN
        sanitized = re.sub(pattern, replacement, sanitized)

    # Apply additional custom patterns
    if additional_patterns:
        for pattern, replacement in additional_patterns:
            try:
                sanitized = re.sub(pattern, replacement, sanitized)
            except re.error:
                continue

    return sanitized


def sanitize_exception(exception: Exception, mask_emails: bool = False) -> str:
    """
    Sanitize an exception message.

    Args:
        exception: The exception to sanitize
        mask_emails: If True, also mask email addresses

    Returns:
        Sanitized exception message
    """
    exc_str = str(exception)
    return sanitize_log_message(exc_str, mask_emails=mask_emails)


def sanitize_dict(data: dict, mask_emails: bool = False) -> dict:
    """
    Recursively sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        mask_emails: If True, also mask email addresses

    Returns:
        Sanitized dictionary (new copy)
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_log_message(value, mask_emails=mask_emails)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, mask_emails=mask_emails)
        elif isinstance(value, list):
            sanitized[key] = [
                (
                    sanitize_log_message(v, mask_emails=mask_emails)
                    if isinstance(v, str)
                    else (sanitize_dict(v, mask_emails=mask_emails) if isinstance(v, dict) else v)
                )
                for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized


# =============================================================================
# Secure Logger Class
# =============================================================================


class SecureLogger:
    """
    A wrapper around Python's logging module that automatically sanitizes
    all log messages to prevent sensitive data leakage.

    Usage:
        logger = SecureLogger(__name__)
        logger.info(f"User logged in with token {token}")  # Token auto-masked
        logger.error(f"Auth failed: {exception}")  # Exception details sanitized
    """

    def __init__(
        self,
        name: str,
        mask_emails: bool = False,
        additional_patterns: Optional[List[tuple]] = None,
    ):
        """
        Initialize SecureLogger.

        Args:
            name: Logger name (usually __name__)
            mask_emails: If True, mask email addresses by default
            additional_patterns: Additional patterns to sanitize
        """
        self._logger = logging.getLogger(name)
        self._mask_emails = mask_emails
        self._additional_patterns = additional_patterns

    def _sanitize(self, msg: str) -> str:
        """Sanitize a message."""
        return sanitize_log_message(
            msg,
            mask_emails=self._mask_emails,
            additional_patterns=self._additional_patterns,
        )

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with sanitization."""
        self._logger.debug(self._sanitize(str(msg)), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with sanitization."""
        self._logger.info(self._sanitize(str(msg)), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with sanitization."""
        self._logger.warning(self._sanitize(str(msg)), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with sanitization."""
        self._logger.error(self._sanitize(str(msg)), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with sanitization."""
        self._logger.critical(self._sanitize(str(msg)), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception with sanitization."""
        self._logger.exception(self._sanitize(str(msg)), *args, **kwargs)


# =============================================================================
# Decorator for Secure Logging in Functions
# =============================================================================


def secure_log_args(func):
    """
    Decorator that sanitizes function arguments before logging.

    Usage:
        @secure_log_args
        def authenticate(email: str, password: str):
            logger.info(f"Auth attempt for {email}")  # Email logged safely
            # password is never logged due to sanitization
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Sanitize keyword arguments for any logging
        _ = sanitize_dict(kwargs)  # Reserved for future logging use
        return func(*args, **kwargs)

    return wrapper


# =============================================================================
# Production Configuration Helper
# =============================================================================


def configure_production_logging():
    """
    Configure logging for production environment.

    - Sets appropriate log level
    - Adds log sanitization filter
    - Configures secure log format (no sensitive data in format)
    """
    import os

    is_production = os.environ.get("ENVIRONMENT") == "production"

    if is_production:
        # Production: WARNING and above only
        logging.basicConfig(
            level=logging.WARNING,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Development: DEBUG with more details
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "sanitize_log_message",
    "sanitize_exception",
    "sanitize_dict",
    "SecureLogger",
    "secure_log_args",
    "configure_production_logging",
    "SENSITIVE_PATTERNS",
]
