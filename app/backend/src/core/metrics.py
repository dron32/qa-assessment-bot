"""Prometheus метрики для FastAPI и Celery."""

import time
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


# Реестр метрик
REGISTRY = CollectorRegistry()

# HTTP метрики
HTTP_REQUESTS_TOTAL = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# LLM метрики
LLM_REQUESTS_TOTAL = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'operation', 'status'],
    registry=REGISTRY
)

LLM_TOKENS_TOTAL = Counter(
    'llm_tokens_total',
    'Total LLM tokens',
    ['model', 'type'],  # type: input/output
    registry=REGISTRY
)

LLM_REQUEST_DURATION = Histogram(
    'llm_request_duration_seconds',
    'LLM request duration in seconds',
    ['model', 'operation'],
    registry=REGISTRY
)

# Celery метрики
CELERY_TASKS_TOTAL = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status'],
    registry=REGISTRY
)

CELERY_TASK_DURATION = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    registry=REGISTRY
)

# Бизнес метрики
REVIEWS_TOTAL = Counter(
    'reviews_total',
    'Total reviews created',
    ['type', 'platform'],  # type: self/peer, platform: slack/telegram/web
    registry=REGISTRY
)

SUMMARIES_GENERATED = Counter(
    'summaries_generated_total',
    'Total summaries generated',
    ['status'],
    registry=REGISTRY
)

# Системные метрики
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Active database connections',
    registry=REGISTRY
)

REDIS_CONNECTIONS = Gauge(
    'redis_connections',
    'Active Redis connections',
    registry=REGISTRY
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора HTTP метрик."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Извлекаем endpoint без параметров
        endpoint = request.url.path
        if endpoint.startswith('/api/'):
            # Группируем API endpoints
            parts = endpoint.split('/')
            if len(parts) >= 4:
                endpoint = f"/api/{parts[2]}/{'*' if parts[3].isdigit() else parts[3]}"
        
        response = await call_next(request)
        
        # Записываем метрики
        duration = time.time() - start_time
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).inc()
        
        HTTP_REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        return response


class LLMMetrics:
    """Класс для сбора LLM метрик."""
    
    @staticmethod
    def record_request(
        model: str,
        operation: str,
        status: str,
        duration: float,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None
    ):
        """Записывает метрики LLM запроса."""
        LLM_REQUESTS_TOTAL.labels(
            model=model,
            operation=operation,
            status=status
        ).inc()
        
        LLM_REQUEST_DURATION.labels(
            model=model,
            operation=operation
        ).observe(duration)
        
        if tokens_in:
            LLM_TOKENS_TOTAL.labels(
                model=model,
                type='input'
            ).inc(tokens_in)
            
        if tokens_out:
            LLM_TOKENS_TOTAL.labels(
                model=model,
                type='output'
            ).inc(tokens_out)


class CeleryMetrics:
    """Класс для сбора Celery метрик."""
    
    @staticmethod
    def record_task(
        task_name: str,
        status: str,
        duration: float
    ):
        """Записывает метрики Celery задачи."""
        CELERY_TASKS_TOTAL.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        CELERY_TASK_DURATION.labels(
            task_name=task_name
        ).observe(duration)


class BusinessMetrics:
    """Класс для сбора бизнес метрик."""
    
    @staticmethod
    def record_review(review_type: str, platform: str):
        """Записывает создание ревью."""
        REVIEWS_TOTAL.labels(
            type=review_type,
            platform=platform
        ).inc()
    
    @staticmethod
    def record_summary(status: str):
        """Записывает генерацию сводки."""
        SUMMARIES_GENERATED.labels(status=status).inc()


def get_metrics() -> str:
    """Возвращает метрики в формате Prometheus."""
    return generate_latest(REGISTRY).decode('utf-8')


def update_system_metrics():
    """Обновляет системные метрики."""
    # Здесь можно добавить логику для получения реальных метрик
    # Например, количество активных соединений к БД
    ACTIVE_CONNECTIONS.set(0)  # Заглушка
    REDIS_CONNECTIONS.set(0)   # Заглушка
