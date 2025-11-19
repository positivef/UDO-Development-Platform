"""
Global Error Handler and Recovery System

포괄적인 에러 핸들링과 자동 복구 메커니즘을 제공합니다.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Callable
from datetime import datetime
from enum import Enum
import asyncio
import json

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """에러 심각도 레벨"""
    LOW = "low"          # 경고 수준, 서비스 지속 가능
    MEDIUM = "medium"    # 일부 기능 제한, 복구 시도 필요
    HIGH = "high"        # 주요 기능 영향, 즉시 대응 필요
    CRITICAL = "critical"  # 시스템 중단 위험, 긴급 대응


class ErrorCategory(Enum):
    """에러 카테고리"""
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
    """에러 복구 전략"""

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
        에러 복구 시도

        Args:
            error: 발생한 에러
            category: 에러 카테고리
            context: 복구에 필요한 컨텍스트 정보

        Returns:
            복구 성공 시 결과, 실패 시 None
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
        """데이터베이스 에러 복구"""
        logger.info("Attempting database error recovery...")

        # Mock 서비스로 폴백
        if "service" in context:
            service_name = context["service"]
            logger.info(f"Falling back to mock service for {service_name}")

            # Mock 서비스 활성화
            from app.services.project_context_service import enable_mock_service
            enable_mock_service()

            return {"status": "recovered", "using": "mock_service"}

        return None

    async def _recover_network_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """네트워크 에러 복구"""
        logger.info("Attempting network error recovery...")

        # 재시도 로직
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
        """외부 서비스 에러 복구"""
        logger.info("Attempting external service error recovery...")

        # 캐시된 데이터 사용
        if "cache_key" in context:
            cache_key = context["cache_key"]
            # TODO: 캐시 시스템 구현 후 실제 캐시 조회
            logger.info(f"Looking for cached data with key: {cache_key}")

        return None


class GlobalErrorHandler:
    """전역 에러 핸들러"""

    def __init__(self):
        self.recovery_strategy = ErrorRecoveryStrategy()
        self.error_history: list = []
        self.max_history_size = 100

    def categorize_error(self, error: Exception) -> ErrorCategory:
        """에러를 카테고리로 분류"""
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
        """에러 심각도 평가"""
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
        통합 에러 처리

        Args:
            request: FastAPI 요청 객체
            error: 발생한 에러
            context: 추가 컨텍스트 정보

        Returns:
            JSON 응답
        """
        # 에러 분류
        category = self.categorize_error(error)
        severity = self.assess_severity(error, category)

        # 에러 정보 로깅
        error_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method,
            "category": category.value,
            "severity": severity.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc() if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else None
        }

        # 심각도에 따른 로깅
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {json.dumps(error_info)}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {error_info['error_message']}")
        else:
            logger.info(f"Low severity error: {error_info['error_message']}")

        # 에러 히스토리 저장
        self._record_error(error_info)

        # 복구 시도
        recovery_result = None
        if severity in [ErrorSeverity.MEDIUM, ErrorSeverity.HIGH] and context:
            recovery_result = await self.recovery_strategy.attempt_recovery(
                error, category, context or {}
            )

        # HTTP 상태 코드 결정
        status_code = self._get_status_code(error, category)

        # 응답 생성
        response_data = {
            "error": {
                "message": self._get_user_friendly_message(error, category),
                "category": category.value,
                "severity": severity.value,
                "timestamp": error_info["timestamp"],
                "request_id": getattr(request.state, "request_id", None)
            }
        }

        # 복구 성공 시 정보 추가
        if recovery_result:
            response_data["recovery"] = {
                "status": "success",
                "action_taken": "Automatic recovery applied",
                "result": recovery_result
            }
            status_code = 200  # 복구 성공 시 200 반환

        # 개발 환경에서 상세 정보 추가
        if getattr(request.app.state, "debug", False):
            response_data["debug"] = {
                "error_type": error_info["error_type"],
                "traceback": error_info.get("traceback")
            }

        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

    def _record_error(self, error_info: Dict[str, Any]):
        """에러 히스토리 기록"""
        self.error_history.append(error_info)

        # 최대 크기 유지
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)

    def _get_status_code(self, error: Exception, category: ErrorCategory) -> int:
        """적절한 HTTP 상태 코드 반환"""
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
        """사용자 친화적인 에러 메시지 생성"""
        if isinstance(error, HTTPException) and error.detail:
            return error.detail

        message_map = {
            ErrorCategory.DATABASE: "데이터베이스 연결 문제가 발생했습니다. 잠시 후 다시 시도해주세요.",
            ErrorCategory.NETWORK: "네트워크 연결에 문제가 있습니다. 연결 상태를 확인해주세요.",
            ErrorCategory.VALIDATION: "입력한 데이터가 올바르지 않습니다. 확인 후 다시 시도해주세요.",
            ErrorCategory.AUTHENTICATION: "인증에 실패했습니다. 다시 로그인해주세요.",
            ErrorCategory.AUTHORIZATION: "이 작업을 수행할 권한이 없습니다.",
            ErrorCategory.EXTERNAL_SERVICE: "외부 서비스 연결에 문제가 있습니다.",
            ErrorCategory.BUSINESS_LOGIC: "요청을 처리할 수 없습니다. 입력 데이터를 확인해주세요.",
            ErrorCategory.SYSTEM: "시스템 오류가 발생했습니다. 관리자에게 문의해주세요.",
            ErrorCategory.UNKNOWN: "예기치 않은 오류가 발생했습니다."
        }

        return message_map.get(category, str(error))

    def get_error_statistics(self) -> Dict[str, Any]:
        """에러 통계 반환"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }

        # 카테고리별 집계
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
            "recent_errors": self.error_history[-10:]  # 최근 10개
        }


# 전역 에러 핸들러 인스턴스
error_handler = GlobalErrorHandler()


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI 전역 예외 핸들러"""
    return await error_handler.handle_error(request, exc)


def setup_error_handlers(app):
    """FastAPI 앱에 에러 핸들러 설정"""
    from fastapi import FastAPI

    # 일반 예외 핸들러
    app.add_exception_handler(Exception, global_exception_handler)

    # HTTP 예외 핸들러
    app.add_exception_handler(HTTPException, global_exception_handler)
    app.add_exception_handler(StarletteHTTPException, global_exception_handler)

    logger.info("Global error handlers configured")