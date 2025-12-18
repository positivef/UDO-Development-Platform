"""
Global Error Handler and Recovery System

[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].

Security improvements (MED-01):
- Production environment hides detailed error messages
- Stack traces only logged, never returned to client in production
- Generic error messages for unknown errors
"""

import logging
import traceback
import os
from typing import Any, Dict, Optional, Callable
from datetime import datetime, UTC
from enum import Enum
import asyncio
import json

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

# MED-01: Environment-aware error detail level
IS_PRODUCTION = os.environ.get("ENVIRONMENT") == "production"
DEBUG_MODE = os.environ.get("DEBUG", "false").lower() == "true" and not IS_PRODUCTION


class ErrorSeverity(Enum):
    """[EMOJI] [EMOJI] [EMOJI]"""
    LOW = "low"          # [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI]
    MEDIUM = "medium"    # [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI]
    HIGH = "high"        # [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI] [EMOJI]
    CRITICAL = "critical"  # [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI]


class ErrorCategory(Enum):
    """[EMOJI] [EMOJI]"""
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class ErrorRecoveryStrategy:
    """[EMOJI] [EMOJI] [EMOJI]"""

    def __init__(self):
        self.strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.DATABASE: self._recover_database_error,
            ErrorCategory.NETWORK: self._recover_network_error,
            ErrorCategory.EXTERNAL_SERVICE: self._recover_external_service_error,
        }
        self.retry_counts: Dict[str, int] = {}
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

    async def attempt_recovery(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            error: [EMOJI] [EMOJI]
            category: [EMOJI] [EMOJI]
            context: [EMOJI] [EMOJI] [EMOJI] [EMOJI]

        Returns:
            [EMOJI] [EMOJI] [EMOJI] [EMOJI], [EMOJI] [EMOJI] None
        """
        if category not in self.strategies:
            logger.warning(f"No recovery strategy for category: {category}")
            return None

        error_id = f"{category.value}:{str(error)[:50]}"
        retry_count = self.retry_counts.get(error_id, 0)

        if retry_count >= self.max_retries:
            logger.error(f"Max retries exceeded for error: {error_id}")
            return None

        self.retry_counts[error_id] = retry_count + 1

        try:
            # Exponential backoff
            await asyncio.sleep(self.retry_delay * (2 ** retry_count))

            strategy = self.strategies[category]
            result = await strategy(error, context)

            # Reset retry count on success
            if result is not None:
                self.retry_counts[error_id] = 0
                logger.info(f"Successfully recovered from error: {error_id}")

            return result

        except Exception as recovery_error:
            logger.error(f"Recovery failed for {error_id}: {recovery_error}")
            return None

    async def _recover_database_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """[EMOJI] [EMOJI] [EMOJI]"""
        logger.info("Attempting database error recovery...")

        # Mock [EMOJI] [EMOJI]
        if "service" in context:
            service_name = context["service"]
            logger.info(f"Falling back to mock service for {service_name}")

            # Mock [EMOJI] [EMOJI]
            from app.services.project_context_service import enable_mock_service
            enable_mock_service()

            return {"status": "recovered", "using": "mock_service"}

        return None

    async def _recover_network_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """[EMOJI] [EMOJI] [EMOJI]"""
        logger.info("Attempting network error recovery...")

        # [EMOJI] [EMOJI]
        if "request_func" in context:
            request_func = context["request_func"]
            try:
                result = await request_func()
                return result
            except Exception:
                pass

        return None

    async def _recover_external_service_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        logger.info("Attempting external service error recovery...")

        # [EMOJI] [EMOJI] [EMOJI]
        if "cache_key" in context:
            cache_key = context["cache_key"]
            # TODO: [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            logger.info(f"Looking for cached data with key: {cache_key}")

        return None


class GlobalErrorHandler:
    """[EMOJI] [EMOJI] [EMOJI]"""

    def __init__(self):
        self.recovery_strategy = ErrorRecoveryStrategy()
        self.error_history: list = []
        self.max_history_size = 100

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """[EMOJI] [EMOJI] [EMOJI]"""
        error_message = str(error).lower()

        if any(word in error_message for word in ["database", "connection", "postgres", "redis"]):
            return ErrorCategory.DATABASE
        elif any(word in error_message for word in ["network", "timeout", "refused"]):
            return ErrorCategory.NETWORK
        elif any(word in error_message for word in ["validation", "invalid", "required"]):
            return ErrorCategory.VALIDATION
        elif any(word in error_message for word in ["authentication", "auth", "token"]):
            return ErrorCategory.AUTHENTICATION
        elif any(word in error_message for word in ["permission", "forbidden", "unauthorized"]):
            return ErrorCategory.AUTHORIZATION
        elif any(word in error_message for word in ["external", "api", "third-party"]):
            return ErrorCategory.EXTERNAL_SERVICE
        else:
            return ErrorCategory.UNKNOWN

    def assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """[EMOJI] [EMOJI] [EMOJI]"""
        # Critical errors
        if isinstance(error, SystemError) or isinstance(error, MemoryError):
            return ErrorSeverity.CRITICAL

        # High severity categories
        if category in [ErrorCategory.DATABASE, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_SERVICE]:
            return ErrorSeverity.MEDIUM

        # Low severity
        if category in [ErrorCategory.VALIDATION]:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM

    async def handle_error(
        self,
        request: Request,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        [EMOJI] [EMOJI] [EMOJI]

        Args:
            request: FastAPI [EMOJI] [EMOJI]
            error: [EMOJI] [EMOJI]
            context: [EMOJI] [EMOJI] [EMOJI]

        Returns:
            JSON [EMOJI]
        """
        # [EMOJI] [EMOJI]
        category = self.categorize_error(error)
        severity = self.assess_severity(error, category)

        # [EMOJI] [EMOJI] [EMOJI]
        error_info = {
            "timestamp": datetime.now(UTC).isoformat(),
            "path": str(request.url),
            "method": request.method,
            "category": category.value,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }

        # [EMOJI] [EMOJI] [EMOJI]
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error_info['error_message']}")
        else:
            logger.info(f"Low severity error: {error_info['error_message']}")

        # [EMOJI] [EMOJI] [EMOJI]
        self._record_error(error_info)

        # [EMOJI] [EMOJI]
        recovery_result = None
        if severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH] and context:
            recovery_result = await self.recovery_strategy.attempt_recovery(
                error, category, context or {}
            )

        # HTTP [EMOJI] [EMOJI] [EMOJI]
        status_code = self._get_status_code(error, category)

        # MED-01: Production-safe response generation
        # In production, hide all detailed error information
        if IS_PRODUCTION:
            response_data = {
                "error": {
                    "message": self._get_user_friendly_message(error, category),
                    "code": self._get_error_code(category),
                    "timestamp": error_info["timestamp"],
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        else:
            # Development: include more details for debugging
            response_data = {
                "error": {
                    "message": self._get_user_friendly_message(error, category),
                    "category": category.value,
                    "severity": severity.value,
                    "timestamp": error_info["timestamp"],
                    "request_id": getattr(request.state, "request_id", None)
                }
            }

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        if recovery_result:
            response_data["recovery"] = {
                "status": "success",
                "action_taken": "Automatic recovery applied"
            }
            # Don't expose recovery result details in production
            if not IS_PRODUCTION:
                response_data["recovery"]["result"] = recovery_result
            status_code = 200  # [EMOJI] [EMOJI] [EMOJI] 200 [EMOJI]

        # Debug information only in development with DEBUG flag
        if DEBUG_MODE and not IS_PRODUCTION:
            response_data["debug"] = {
                "error_type": error_info["error_type"],
                "traceback": error_info.get("traceback")
            }

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

    def _record_error(self, error_info: Dict[str, Any]):
        """[EMOJI] [EMOJI] [EMOJI]"""
        self.error_history.append(error_info)

        # [EMOJI] [EMOJI] [EMOJI]
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)

    def _get_status_code(self, error: Exception, category: ErrorCategory) -> int:
        """[EMOJI] HTTP [EMOJI] [EMOJI] [EMOJI]"""
        if isinstance(error, HTTPException):
            return error.status_code
        elif isinstance(error, StarletteHTTPException):
            return error.status_code

        status_map = {
            ErrorCategory.VALIDATION: 400,
            ErrorCategory.AUTHENTICATION: 401,
            ErrorCategory.AUTHORIZATION: 403,
            ErrorCategory.DATABASE: 503,
            ErrorCategory.NETWORK: 503,
            ErrorCategory.EXTERNAL_SERVICE: 502,
            ErrorCategory.BUSINESS_LOGIC: 422,
            ErrorCategory.SYSTEM: 500,
            ErrorCategory.UNKNOWN: 500
        }

        return status_map.get(category, 500)

    def _get_user_friendly_message(self, error: Exception, category: ErrorCategory) -> str:
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        # In production, never expose raw error messages for unknown errors
        if IS_PRODUCTION and category == ErrorCategory.UNKNOWN:
            return "An unexpected error occurred. Please try again later."

        if isinstance(error, HTTPException) and error.detail:
            # In production, sanitize HTTPException details
            if IS_PRODUCTION:
                detail = str(error.detail)
                # Don't expose internal paths, stack traces, or technical details
                if any(x in detail.lower() for x in ['traceback', 'line ', 'file ', '/app/', '\\app\\']):
                    return "An error occurred while processing your request."
            return error.detail

        message_map = {
            ErrorCategory.DATABASE: "[EMOJI] [EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.NETWORK: "[EMOJI] [EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.VALIDATION: "[EMOJI] [EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.AUTHENTICATION: "[EMOJI] [EMOJI]. [EMOJI] [EMOJI].",
            ErrorCategory.AUTHORIZATION: "[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.EXTERNAL_SERVICE: "[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.BUSINESS_LOGIC: "[EMOJI] [EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI] [EMOJI].",
            ErrorCategory.SYSTEM: "[EMOJI] [EMOJI] [EMOJI]. [EMOJI] [EMOJI].",
            ErrorCategory.UNKNOWN: "[EMOJI] [EMOJI] [EMOJI] [EMOJI]."
        }

        return message_map.get(category, "An error occurred." if IS_PRODUCTION else str(error))

    def _get_error_code(self, category: ErrorCategory) -> str:
        """MED-01: Return generic error code for production (no internal details)"""
        code_map = {
            ErrorCategory.DATABASE: "ERR_DB",
            ErrorCategory.NETWORK: "ERR_NET",
            ErrorCategory.VALIDATION: "ERR_VAL",
            ErrorCategory.AUTHENTICATION: "ERR_AUTH",
            ErrorCategory.AUTHORIZATION: "ERR_PERM",
            ErrorCategory.EXTERNAL_SERVICE: "ERR_EXT",
            ErrorCategory.BUSINESS_LOGIC: "ERR_BIZ",
            ErrorCategory.SYSTEM: "ERR_SYS",
            ErrorCategory.UNKNOWN: "ERR_UNK"
        }
        return code_map.get(category, "ERR_UNK")

    def get_error_statistics(self) -> Dict[str, Any]:
        """[EMOJI] [EMOJI] [EMOJI]"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }

        # [EMOJI] [EMOJI]
        by_category = {}
        by_severity = {}

        for error in self.error_history:
            category = error.get("category", "unknown")
            severity = error.get("severity", "unknown")

            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": self.error_history[-10:]  # [EMOJI] 10[EMOJI]
        }


# [EMOJI] [EMOJI] [EMOJI] [EMOJI]
error_handler = GlobalErrorHandler()


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI [EMOJI] [EMOJI] [EMOJI]"""
    return await error_handler.handle_error(request, exc)


def setup_error_handlers(app):
    """FastAPI [EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
    from fastapi import FastAPI

    # [EMOJI] [EMOJI] [EMOJI]
    app.add_exception_handler(Exception, global_exception_handler)

    # HTTP [EMOJI] [EMOJI]
    app.add_exception_handler(HTTPException, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, global_exception_handler)

    logger.info("Global error handlers configured")