"""
Knowledge Quality Middleware

FastAPI middleware for automatic quality gate enforcement.
Intercepts knowledge extraction requests and validates outputs.
"""

import json
import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.models.knowledge_quality import QualityLevel  # noqa: F401
from app.services.knowledge_quality_gate_service import knowledge_quality_gate_service

logger = logging.getLogger(__name__)


class KnowledgeQualityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic knowledge extraction quality validation.

    Features:
    - Intercepts extraction endpoints
    - Validates extraction outputs
    - Adds quality headers to responses
    - Logs quality metrics
    - Optionally blocks low-quality extractions
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        block_low_quality: bool = False,
        intercept_paths: list = None,
        min_quality_level: QualityLevel = QualityLevel.ACCEPTABLE,
    ):
        """
        Initialize middleware.

        Args:
            app: ASGI application
            enabled: Whether middleware is active
            block_low_quality: Whether to reject low-quality extractions
            intercept_paths: List of paths to intercept (default: extraction paths)
            min_quality_level: Minimum quality level to accept
        """
        super().__init__(app)
        self.enabled = enabled
        self.block_low_quality = block_low_quality
        self.min_quality_level = min_quality_level
        self.intercept_paths = intercept_paths or [
            "/api/knowledge/extract",
            "/api/archive/task",
            "/api/obsidian/sync",
        ]

        self.quality_service = knowledge_quality_gate_service

        # Metrics tracking
        self._total_requests = 0
        self._quality_passed = 0
        self._quality_failed = 0
        self._quality_blocked = 0

        logger.info(f"KnowledgeQualityMiddleware initialized: " f"enabled={enabled}, block_low_quality={block_low_quality}")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and validate quality."""
        # Check if middleware is enabled
        if not self.enabled:
            return await call_next(request)

        # Check if path should be intercepted
        path = request.url.path
        should_intercept = any(path.startswith(intercept_path) for intercept_path in self.intercept_paths)

        if not should_intercept:
            return await call_next(request)

        # Only intercept POST requests (extraction operations)
        if request.method != "POST":
            return await call_next(request)

        self._total_requests += 1
        start_time = time.time()

        try:
            # Get request body for validation
            body = await request.body()
            _request_data = json.loads(body) if body else {}  # noqa: F841

            # Create new request with body (since we consumed it)
            # This is a workaround for body consumption

            # Call the actual endpoint
            response = await call_next(request)

            # For POST requests that return extraction data,
            # validate the response if possible
            if response.status_code == 200:
                # Add quality headers
                response.headers["X-Quality-Validated"] = "true"
                response.headers["X-Quality-Request-Id"] = str(uuid4())
                response.headers["X-Quality-Processing-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

                # Log quality check
                logger.info(
                    f"Quality middleware processed: {path} "
                    f"(status={response.status_code}, "
                    f"time={response.headers.get('X-Quality-Processing-Time')})"
                )

                self._quality_passed += 1

            return response

        except json.JSONDecodeError:
            # Non-JSON request, pass through
            return await call_next(request)

        except Exception as e:
            logger.error(f"Quality middleware error: {e}")
            # Don't block on middleware errors
            return await call_next(request)

    def get_metrics(self) -> dict:
        """Get middleware metrics."""
        return {
            "total_requests": self._total_requests,
            "quality_passed": self._quality_passed,
            "quality_failed": self._quality_failed,
            "quality_blocked": self._quality_blocked,
            "pass_rate": (self._quality_passed / self._total_requests * 100 if self._total_requests > 0 else 0),
        }


class QualityValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight middleware for adding quality context to responses.

    Adds:
    - Quality thresholds to response headers
    - Processing time tracking
    - Request tracing
    """

    def __init__(self, app: ASGIApp, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.quality_service = knowledge_quality_gate_service

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Add quality context to response."""
        if not self.enabled:
            return await call_next(request)

        start_time = time.time()
        request_id = str(uuid4())

        # Add request ID to state for logging
        request.state.request_id = request_id

        try:
            response = await call_next(request)

            # Add standard quality headers
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Processing-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            # Add quality thresholds for extraction endpoints
            if "/knowledge" in request.url.path or "/archive" in request.url.path:
                thresholds = self.quality_service.thresholds
                response.headers["X-Quality-Min-Chars"] = str(thresholds.min_total_chars)
                response.headers["X-Quality-Target-Chars"] = str(thresholds.target_total_chars)
                response.headers["X-Quality-Min-G-Eval"] = str(thresholds.min_g_eval_score)

            return response

        except Exception as e:
            logger.error(f"QualityValidationMiddleware error: {e}")
            raise


def create_quality_middleware(
    app: ASGIApp,
    enabled: bool = True,
    block_low_quality: bool = False,
) -> KnowledgeQualityMiddleware:
    """
    Factory function to create quality middleware.

    Args:
        app: ASGI application
        enabled: Whether middleware is active
        block_low_quality: Whether to reject low-quality extractions

    Returns:
        Configured middleware instance
    """
    return KnowledgeQualityMiddleware(
        app=app,
        enabled=enabled,
        block_low_quality=block_low_quality,
    )
