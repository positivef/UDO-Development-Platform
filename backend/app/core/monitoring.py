"""
Performance Monitoring System

Prometheus 기반 메트릭 수집 및 모니터링 시스템입니다.
"""

import time
import psutil
import logging
from typing import Dict, Any, Callable
from functools import wraps
from datetime import datetime, UTC
import asyncio
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client import CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# =====================
# Prometheus Metrics
# =====================

# Request metrics
request_count = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])

request_duration = Histogram("http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"])

# System metrics
cpu_usage_gauge = Gauge("system_cpu_usage_percent", "CPU usage percentage")
memory_usage_gauge = Gauge("system_memory_usage_percent", "Memory usage percentage")
disk_usage_gauge = Gauge("system_disk_usage_percent", "Disk usage percentage")

# Application metrics
active_connections = Gauge("app_active_connections", "Number of active connections")
task_queue_size = Gauge("app_task_queue_size", "Size of task queue")
error_rate = Counter("app_errors_total", "Total application errors", ["error_type"])

# UDO specific metrics
udo_execution_count = Counter("udo_executions_total", "Total UDO executions", ["phase", "decision"])

udo_confidence_histogram = Histogram("udo_confidence_score", "UDO confidence scores distribution", ["phase"])

uncertainty_level_gauge = Gauge("udo_uncertainty_level", "Current uncertainty level", ["phase"])

# Database metrics
db_connection_pool_size = Gauge("db_connection_pool_size", "Database connection pool size")
db_query_duration = Histogram("db_query_duration_seconds", "Database query duration", ["operation"])

# Cache metrics
cache_hits = Counter("cache_hits_total", "Total cache hits")
cache_misses = Counter("cache_misses_total", "Total cache misses")
cache_size = Gauge("cache_size_bytes", "Current cache size in bytes")


class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self):
        """PerformanceMonitor 초기화"""
        self.start_time = time.time()
        self.request_times = []
        self.error_counts = {}
        self.is_collecting = False

        # 시스템 메트릭 수집 시작
        self._start_system_monitoring()

    def _start_system_monitoring(self):
        """시스템 메트릭 수집 시작"""
        self.is_collecting = True
        logger.info("System monitoring started")

    def collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_usage_gauge.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_gauge.set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage_gauge.set(disk.percent)

            return {"cpu_percent": cpu_percent, "memory_percent": memory.percent, "disk_percent": disk.percent}
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    @contextmanager
    def measure_request(self, method: str, endpoint: str):
        """
        HTTP 요청 측정 컨텍스트 매니저

        Args:
            method: HTTP 메소드
            endpoint: 엔드포인트 경로
        """
        start_time = time.time()
        status_code = 200  # Default

        try:
            yield
        except Exception as e:
            status_code = 500
            error_rate.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time
            request_count.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
            request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            # Store for internal analytics
            self.request_times.append(duration)
            if len(self.request_times) > 1000:
                self.request_times = self.request_times[-1000:]

    def track_udo_execution(self, phase: str, decision: str, confidence: float, uncertainty: float):
        """
        UDO 실행 메트릭 추적

        Args:
            phase: 개발 단계
            decision: 의사결정 (GO/NO_GO/GO_WITH_CHECKPOINTS)
            confidence: 신뢰도 점수
            uncertainty: 불확실성 수준
        """
        udo_execution_count.labels(phase=phase, decision=decision).inc()
        udo_confidence_histogram.labels(phase=phase).observe(confidence)
        uncertainty_level_gauge.labels(phase=phase).set(uncertainty)

    def track_database_query(self, operation: str, duration: float):
        """
        데이터베이스 쿼리 메트릭 추적

        Args:
            operation: 작업 유형 (select/insert/update/delete)
            duration: 쿼리 실행 시간
        """
        db_query_duration.labels(operation=operation).observe(duration)

    def track_cache_access(self, hit: bool):
        """
        캐시 접근 메트릭 추적

        Args:
            hit: 캐시 적중 여부
        """
        if hit:
            cache_hits.inc()
        else:
            cache_misses.inc()

    def update_connection_count(self, count: int):
        """활성 연결 수 업데이트"""
        active_connections.set(count)

    def update_task_queue_size(self, size: int):
        """태스크 큐 크기 업데이트"""
        task_queue_size.set(size)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        메트릭 요약 정보 반환

        Returns:
            메트릭 요약 딕셔너리
        """
        uptime = time.time() - self.start_time

        # Calculate average request time
        avg_request_time = 0
        if self.request_times:
            avg_request_time = sum(self.request_times) / len(self.request_times)

        # Get system metrics
        system_metrics = self.collect_system_metrics()

        # Calculate cache hit rate
        total_cache_access = cache_hits._value.get() + cache_misses._value.get()
        cache_hit_rate = 0
        if total_cache_access > 0:
            cache_hit_rate = cache_hits._value.get() / total_cache_access * 100

        return {
            "uptime_seconds": uptime,
            "average_request_time": avg_request_time,
            "total_requests": len(self.request_times),
            "system_metrics": system_metrics,
            "cache_hit_rate": cache_hit_rate,
            "active_connections": active_connections._value.get(),
            "task_queue_size": task_queue_size._value.get(),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_prometheus_metrics(self) -> bytes:
        """
        Prometheus 형식의 메트릭 반환

        Returns:
            메트릭 데이터 (bytes)
        """
        # Collect current system metrics
        self.collect_system_metrics()

        # Generate Prometheus format
        return generate_latest(REGISTRY)


def monitor_performance(func: Callable) -> Callable:
    """
    함수 성능 모니터링 데코레이터

    Args:
        func: 모니터링할 함수

    Returns:
        래핑된 함수
    """

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} took {duration:.4f} seconds")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} took {duration:.4f} seconds")

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


class RequestTracker:
    """요청 추적 클래스 (미들웨어용)"""

    def __init__(self, monitor: PerformanceMonitor):
        """
        RequestTracker 초기화

        Args:
            monitor: PerformanceMonitor 인스턴스
        """
        self.monitor = monitor

    async def __call__(self, request, call_next):
        """
        미들웨어 실행

        Args:
            request: FastAPI 요청 객체
            call_next: 다음 미들웨어/핸들러

        Returns:
            응답 객체
        """
        method = request.method
        path = request.url.path

        start_time = time.time()
        status_code = 200

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            error_rate.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start_time

            # Track metrics
            request_count.labels(method=method, endpoint=path, status=str(status_code)).inc()

            request_duration.labels(method=method, endpoint=path).observe(duration)

            # Log slow requests
            if duration > 1.0:
                logger.warning(f"Slow request: {method} {path} took {duration:.2f}s")


# Create singleton instance
performance_monitor = PerformanceMonitor()


def setup_monitoring(app):
    """
    FastAPI 앱에 모니터링 설정

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from fastapi.responses import Response

    # Add request tracking middleware
    tracker = RequestTracker(performance_monitor)
    app.add_middleware(BaseHTTPMiddleware, dispatch=tracker)

    # Add metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def get_metrics():
        """Prometheus 메트릭 엔드포인트"""
        metrics = performance_monitor.get_prometheus_metrics()
        return Response(content=metrics, media_type=CONTENT_TYPE_LATEST)

    logger.info("Performance monitoring configured")


# Export key components
__all__ = ["performance_monitor", "monitor_performance", "setup_monitoring", "PerformanceMonitor", "RequestTracker"]
