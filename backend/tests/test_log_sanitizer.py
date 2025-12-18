"""
Tests for Log Sanitizer - MED-04 Security

Tests the log sanitization functionality to ensure sensitive data
is properly masked before being logged.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from backend.app.core.log_sanitizer import (
    sanitize_log_message,
    sanitize_exception,
    sanitize_dict,
    SecureLogger,
)


class TestSanitizeLogMessage:
    """Tests for sanitize_log_message function"""

    def test_password_in_key_value_format(self):
        """Test that passwords in key=value format are masked"""
        msg = "User login failed with password=secret123"
        result = sanitize_log_message(msg)
        assert "secret123" not in result
        assert "***REDACTED***" in result

    def test_password_in_json_format(self):
        """Test that passwords in JSON-like format are masked"""
        msg = "Request body: {'password': 'mysecretpass'}"
        result = sanitize_log_message(msg)
        assert "mysecretpass" not in result
        assert "***REDACTED***" in result

    def test_jwt_token_bearer(self):
        """Test that Bearer JWT tokens are masked"""
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        result = sanitize_log_message(msg)
        assert "eyJ" not in result
        assert "***JWT_REDACTED***" in result

    def test_jwt_token_standalone(self):
        """Test that standalone JWT tokens are masked"""
        msg = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.abc123xyz"
        result = sanitize_log_message(msg)
        assert "eyJhbGciOi" not in result
        assert "***JWT_REDACTED***" in result

    def test_api_key(self):
        """Test that API keys are masked"""
        msg = "Using api_key=AKIAIOSFODNN7EXAMPLE"
        result = sanitize_log_message(msg)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "***REDACTED***" in result

    def test_secret_key(self):
        """Test that secret keys are masked"""
        msg = "Config: secret_key: my-super-secret-key-12345"
        result = sanitize_log_message(msg)
        assert "my-super-secret-key-12345" not in result
        assert "***REDACTED***" in result

    def test_credit_card_visa(self):
        """Test that Visa credit card numbers are masked"""
        msg = "Payment with card 4111111111111111"
        result = sanitize_log_message(msg)
        assert "4111111111111111" not in result
        assert "***CC_REDACTED***" in result

    def test_credit_card_mastercard(self):
        """Test that MasterCard numbers are masked"""
        msg = "Card: 5500000000000004"
        result = sanitize_log_message(msg)
        assert "5500000000000004" not in result
        assert "***CC_REDACTED***" in result

    def test_ssn(self):
        """Test that Social Security Numbers are masked"""
        msg = "User SSN: 123-45-6789"
        result = sanitize_log_message(msg)
        assert "123-45-6789" not in result
        assert "***SSN_REDACTED***" in result

    def test_database_connection_string(self):
        """Test that database passwords in connection strings are masked"""
        msg = "Connecting to postgres://admin:supersecret@localhost:5432/db"
        result = sanitize_log_message(msg)
        assert "supersecret" not in result
        assert "***REDACTED***" in result

    def test_session_id(self):
        """Test that session IDs are masked"""
        msg = "Session: session_id=abc123def456ghi789jkl012"
        result = sanitize_log_message(msg)
        assert "abc123def456ghi789jkl012" not in result
        assert "***REDACTED***" in result

    def test_bcrypt_hash(self):
        """Test that bcrypt hashes are masked"""
        msg = "Hash: $2b$12$K3ik3K4x5FhGXLMNQLJKhOKYwG.7bVTtL3YGOUDkU.lbIlvVxJq8."
        result = sanitize_log_message(msg)
        assert "$2b$12$" not in result
        assert "***HASH_REDACTED***" in result

    def test_email_not_masked_by_default(self):
        """Test that emails are NOT masked by default"""
        msg = "User email: test@example.com"
        result = sanitize_log_message(msg)
        assert "test@example.com" in result

    def test_email_masked_when_enabled(self):
        """Test that emails are masked when mask_emails=True"""
        msg = "User email: test@example.com"
        result = sanitize_log_message(msg, mask_emails=True)
        assert "test@example.com" not in result
        assert "***EMAIL***" in result

    def test_multiple_sensitive_items(self):
        """Test that multiple sensitive items in one message are all masked"""
        msg = "Login: email=admin@test.com, password=secret123, token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc"
        result = sanitize_log_message(msg, mask_emails=True)
        assert "admin@test.com" not in result
        assert "secret123" not in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_empty_string(self):
        """Test that empty strings are handled"""
        result = sanitize_log_message("")
        assert result == ""

    def test_none_handling(self):
        """Test that None is handled"""
        result = sanitize_log_message(None)
        assert result is None

    def test_safe_message_unchanged(self):
        """Test that safe messages are not altered"""
        msg = "User logged in successfully from IP 192.168.1.1"
        result = sanitize_log_message(msg)
        assert result == msg


class TestSanitizeException:
    """Tests for sanitize_exception function"""

    def test_exception_with_password(self):
        """Test that exceptions containing passwords are sanitized"""
        try:
            raise ValueError("Invalid credentials: password=wrongpass")
        except ValueError as e:
            result = sanitize_exception(e)
            assert "wrongpass" not in result
            assert "***REDACTED***" in result

    def test_exception_with_token(self):
        """Test that exceptions containing tokens are sanitized"""
        try:
            raise RuntimeError("Token expired: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.xyz")
        except RuntimeError as e:
            result = sanitize_exception(e)
            assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result


class TestSanitizeDict:
    """Tests for sanitize_dict function"""

    def test_dict_with_password(self):
        """Test that dictionary values containing passwords are sanitized"""
        data = {"message": "password=secret123", "status": "failed"}
        result = sanitize_dict(data)
        assert "secret123" not in result["message"]
        assert result["status"] == "failed"

    def test_nested_dict(self):
        """Test that nested dictionaries are sanitized"""
        data = {
            "user": {
                "credentials": "api_key=SUPERSECRETKEY123456"
            }
        }
        result = sanitize_dict(data)
        assert "SUPERSECRETKEY123456" not in result["user"]["credentials"]

    def test_dict_with_list(self):
        """Test that lists in dictionaries are sanitized"""
        data = {
            "messages": [
                "password=pass1",
                "password=pass2"
            ]
        }
        result = sanitize_dict(data)
        assert "pass1" not in result["messages"][0]
        assert "pass2" not in result["messages"][1]


class TestSecureLogger:
    """Tests for SecureLogger class"""

    def test_secure_logger_sanitizes_info(self, caplog):
        """Test that SecureLogger sanitizes info messages"""
        logger = SecureLogger("test_logger")
        with caplog.at_level("INFO"):
            logger.info("User password=secret123 logged in")

        # Check that the sanitized message was logged
        assert "secret123" not in caplog.text
        assert "***REDACTED***" in caplog.text

    def test_secure_logger_sanitizes_warning(self, caplog):
        """Test that SecureLogger sanitizes warning messages"""
        logger = SecureLogger("test_logger")
        with caplog.at_level("WARNING"):
            logger.warning("Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIn0.abc")

        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in caplog.text
        assert "***JWT_REDACTED***" in caplog.text

    def test_secure_logger_sanitizes_error(self, caplog):
        """Test that SecureLogger sanitizes error messages"""
        logger = SecureLogger("test_logger")
        with caplog.at_level("ERROR"):
            logger.error("Database postgres://user:password123@host:5432/db failed")

        assert "password123" not in caplog.text
        assert "***REDACTED***" in caplog.text

    def test_secure_logger_with_email_masking(self, caplog):
        """Test SecureLogger with email masking enabled"""
        logger = SecureLogger("test_logger", mask_emails=True)
        with caplog.at_level("INFO"):
            logger.info("User admin@company.com logged in")

        assert "admin@company.com" not in caplog.text
        assert "***EMAIL***" in caplog.text


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_partial_password_pattern(self):
        """Test that partial password patterns don't cause issues"""
        msg = "Processing passwordless authentication"
        result = sanitize_log_message(msg)
        # Should not crash or incorrectly mask
        assert "passwordless" in result

    def test_unicode_characters(self):
        """Test that unicode characters don't cause issues"""
        msg = "User [EMOJI] with password=[EMOJI]123"
        result = sanitize_log_message(msg)
        assert "[EMOJI]123" not in result
        assert "[EMOJI]" in result

    def test_very_long_message(self):
        """Test that very long messages are handled"""
        msg = "password=secret123 " * 1000
        result = sanitize_log_message(msg)
        assert "secret123" not in result

    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        msg = "password=p@$$w0rd!#%&*"
        result = sanitize_log_message(msg)
        assert "p@$$w0rd" not in result
