"""
Performance monitoring with uncertainty tracking
Implements measurement methods from PRD_UNIFIED_ENHANCED
"""

from functools import wraps
import time
from typing import Callable, Any, Optional, Dict
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog
from fastapi import Request, Response
import asyncio

logger = structlog.get_logger()

# Define Prometheus metrics
api_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

api_requests = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

uncertainty_score = Gauge(
    'system_uncertainty_score',
    'Current system uncertainty level (0-1)',
    ['component']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table']
)

ai_response_time = Histogram(
    'ai_response_duration_seconds',
    'AI model response time',
    ['model', 'operation']
)

error_rate = Counter(
    'errors_total',
    'Total number of errors',
    ['error_type', 'component']
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)


def measure_latency(endpoint: str = None):
    """
    Decorator to measure API endpoint latency.
    Implements measurement method from PRD Section 5.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"

            # Extract request if available
            request = kwargs.get('request')
            method = "UNKNOWN"
            if request and isinstance(request, Request):
                method = request.method

            try:
                # Execute the actual function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result

            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                error_rate.labels(
                    error_type=error_type,
                    component="api"
                ).inc()
                logger.error(
                    f"API error in {endpoint}",
                    error=str(e),
                    error_type=error_type
                )
                raise

            finally:
                duration = time.time() - start_time

                # Record metrics
                api_latency.labels(
                    method=method,
                    endpoint=endpoint or func.__name__,
                    status=status
                ).observe(duration)

                api_requests.labels(
                    method=method,
                    endpoint=endpoint or func.__name__,
                    status=status
                ).inc()

                # Log slow requests (P95 threshold from PRD)
                if duration > 0.2:  # 200ms threshold
                    logger.warning(
                        "Slow API call detected",
                        endpoint=endpoint,
                        duration=duration,
                        method=method
                    )

                # Update circuit breaker if needed
                if duration > 1.0:  # 1 second extreme threshold
                    CircuitBreakerManager.instance().record_slow_call(endpoint)

        return wrapper
    return decorator


def measure_db_query(query_type: str, table: str = "unknown"):
    """
    Decorator to measure database query performance.
    Implements SQL measurement from PRD Section 5.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()

            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return result

            except Exception as e:
                error_rate.labels(
                    error_type=type(e).__name__,
                    component="database"
                ).inc()
                raise

            finally:
                duration = time.time() - start_time
                db_query_duration.labels(
                    query_type=query_type,
                    table=table
                ).observe(duration)

                # Alert on slow queries (30ms threshold from PRD)
                if duration > 0.03:
                    logger.warning(
                        "Slow database query",
                        query_type=query_type,
                        table=table,
                        duration=duration
                    )

        return wrapper
    return decorator


def track_uncertainty(component: str, score: float):
    """
    Update uncertainty score for a component.
    Maps to 5 quantum states from PRD.
    """
    # Clamp score between 0 and 1
    score = max(0.0, min(1.0, score))

    # Update Prometheus metric
    uncertainty_score.labels(component=component).set(score)

    # Map to quantum state
    if score < 0.1:
        state = "DETERMINISTIC"
        emoji = "🟢"
    elif score < 0.3:
        state = "PROBABILISTIC"
        emoji = "🟡"
    elif score < 0.5:
        state = "QUANTUM"
        emoji = "🟠"
    elif score < 0.7:
        state = "CHAOTIC"
        emoji = "🔴"
    else:
        state = "VOID"
        emoji = "⚫"

    logger.info(
        f"{emoji} Uncertainty update",
        component=component,
        score=score,
        state=state
    )

    # Trigger alerts for high uncertainty
    if score > 0.5:
        logger.warning(
            f"High uncertainty detected - activating fallback strategies",
            component=component,
            score=score,
            state=state
        )
        # TODO: Trigger fallback strategy based on component


class CircuitBreakerManager:
    """
    Implements circuit breaker pattern for service protection.
    Based on uncertainty-aware architecture from PRD.
    """

    _instance: Optional['CircuitBreakerManager'] = None

    def __init__(self):
        self.breakers: Dict[str, 'CircuitBreaker'] = {}

    @classmethod
    def instance(cls) -> 'CircuitBreakerManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_breaker(self, service: str) -> 'CircuitBreaker':
        if service not in self.breakers:
            self.breakers[service] = CircuitBreaker(service)
        return self.breakers[service]

    def record_slow_call(self, service: str):
        breaker = self.get_breaker(service)
        breaker.record_failure()


class CircuitBreaker:
    """Individual circuit breaker for a service"""

    def __init__(self, service: str, threshold: int = 5, timeout: float = 60.0):
        self.service = service
        self.failure_count = 0
        self.threshold = threshold
        self.timeout = timeout
        self.state = "closed"  # closed, open, half-open
        self.last_failure_time: Optional[float] = None

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.threshold:
            self.open()

    def record_success(self):
        if self.state == "half-open":
            self.close()

    def open(self):
        """Open the circuit breaker"""
        self.state = "open"
        circuit_breaker_state.labels(service=self.service).set(1)
        logger.critical(
            f"Circuit breaker OPENED",
            service=self.service,
            failure_count=self.failure_count
        )

    def close(self):
        """Close the circuit breaker"""
        self.state = "closed"
        self.failure_count = 0
        circuit_breaker_state.labels(service=self.service).set(0)
        logger.info(f"Circuit breaker CLOSED", service=self.service)

    def is_available(self) -> bool:
        """Check if service is available"""
        if self.state == "closed":
            return True

        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) > self.timeout:
                self.state = "half-open"
                circuit_breaker_state.labels(service=self.service).set(2)
                return True
            return False

        return True  # half-open state allows one try


class PerformanceMonitor:
    """
    Central performance monitoring with adaptive thresholds.
    Implements performance tracking from PRD Section 5.
    """

    def __init__(self):
        self.latency_buffer = []
        self.error_count = 0
        self.degraded_mode = False
        self.alert_threshold_p95 = 0.2  # 200ms from PRD
        self.alert_threshold_p50 = 0.05  # 50ms from PRD

    def record_latency(self, latency: float):
        """Record latency and check for degradation"""
        self.latency_buffer.append(latency)

        # Keep only last 1000 measurements
        if len(self.latency_buffer) > 1000:
            self.latency_buffer.pop(0)

        # Need at least 20 samples for percentile calculation
        if len(self.latency_buffer) >= 20:
            sorted_latencies = sorted(self.latency_buffer)

            # Calculate percentiles
            p50_index = int(len(sorted_latencies) * 0.50)
            p95_index = int(len(sorted_latencies) * 0.95)

            p50_latency = sorted_latencies[p50_index]
            p95_latency = sorted_latencies[p95_index]

            # Check against thresholds
            if p95_latency > self.alert_threshold_p95:
                logger.warning(
                    f"P95 latency exceeds threshold",
                    p95=p95_latency,
                    threshold=self.alert_threshold_p95
                )
                self._activate_degraded_mode()

            if p50_latency > self.alert_threshold_p50:
                logger.info(
                    f"P50 latency approaching threshold",
                    p50=p50_latency,
                    threshold=self.alert_threshold_p50
                )

    def _activate_degraded_mode(self):
        """Activate degraded mode to protect system"""
        if not self.degraded_mode:
            self.degraded_mode = True
            logger.critical("Activating DEGRADED MODE - switching to cache-first strategy")
            track_uncertainty("system", 0.7)  # High uncertainty
            # TODO: Implement cache-first strategy
            # TODO: Notify team via Slack webhook

    def _deactivate_degraded_mode(self):
        """Return to normal mode"""
        if self.degraded_mode:
            self.degraded_mode = False
            logger.info("Returning to NORMAL MODE")
            track_uncertainty("system", 0.2)  # Lower uncertainty


# Global monitor instance
monitor = PerformanceMonitor()


async def metrics_endpoint(request: Request) -> Response:
    """
    Expose metrics for Prometheus scraping.
    Endpoint to be added to FastAPI router.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )