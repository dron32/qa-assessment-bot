"""
Celery приложение с конфигурацией, метриками и мониторингом.
"""

import os
import time
from typing import Any, Dict
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from celery.utils.log import get_task_logger
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)

# Настройка Sentry для Celery
if os.getenv('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[CeleryIntegration()],
        traces_sample_rate=0.1,
    )

# Создание Celery приложения
settings = get_settings()

celery_app = Celery(
    'qa_assessment',
    broker=settings.redis_url,
    backend=settings.redis_url.replace('/0', '/1'),
    include=[
        'app.backend.src.tasks.summary',
        'app.backend.src.tasks.comparison', 
        'app.backend.src.tasks.embeddings',
    ]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 минут максимум
    task_soft_time_limit=240,  # 4 минуты мягкий лимит
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    result_expires=3600,  # 1 час
    task_routes={
        'app.backend.src.tasks.summary.*': {'queue': 'summary'},
        'app.backend.src.tasks.comparison.*': {'queue': 'comparison'},
        'app.backend.src.tasks.embeddings.*': {'queue': 'embeddings'},
    },
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'summary': {
            'exchange': 'summary',
            'routing_key': 'summary',
        },
        'comparison': {
            'exchange': 'comparison', 
            'routing_key': 'comparison',
        },
        'embeddings': {
            'exchange': 'embeddings',
            'routing_key': 'embeddings',
        },
    },
)

# Метрики времени выполнения задач
task_metrics: Dict[str, list] = {}

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Обработчик перед запуском задачи."""
    logger.info(
        "Task started",
        extra={
            'task_id': task_id,
            'task_name': task.name,
            'args': args,
            'kwargs': kwargs,
        }
    )
    
    # Инициализация метрик для задачи
    if task.name not in task_metrics:
        task_metrics[task.name] = []
    
    # Сохранение времени начала
    task_metrics[task.name].append({
        'task_id': task_id,
        'start_time': time.time(),
        'status': 'started'
    })

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Обработчик после завершения задачи."""
    end_time = time.time()
    
    # Находим соответствующую запись в метриках
    task_record = None
    for record in task_metrics.get(task.name, []):
        if record.get('task_id') == task_id and record.get('status') == 'started':
            task_record = record
            break
    
    if task_record:
        duration = end_time - task_record['start_time']
        task_record.update({
            'end_time': end_time,
            'duration': duration,
            'status': 'completed',
            'result': retval
        })
        
        logger.info(
            "Task completed",
            extra={
                'task_id': task_id,
                'task_name': task.name,
                'duration': duration,
                'state': state,
            }
        )
        
        # Отправка метрик в Sentry (если настроено)
        if os.getenv('SENTRY_DSN'):
            with sentry_sdk.push_scope() as scope:
                scope.set_tag('task_name', task.name)
                scope.set_tag('task_id', task_id)
                scope.set_extra('duration', duration)
                scope.set_extra('args', args)
                scope.set_extra('kwargs', kwargs)

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """Обработчик ошибок задач."""
    logger.error(
        "Task failed",
        extra={
            'task_id': task_id,
            'task_name': sender.name if sender else 'unknown',
            'exception': str(exception),
            'traceback': traceback,
        }
    )
    
    # Отправка ошибки в Sentry
    if os.getenv('SENTRY_DSN'):
        sentry_sdk.capture_exception(exception)

def get_task_metrics(task_name: str = None) -> Dict[str, Any]:
    """Получение метрик выполнения задач."""
    if task_name:
        metrics = task_metrics.get(task_name, [])
    else:
        metrics = task_metrics
    
    if not metrics:
        return {}
    
    if task_name and isinstance(metrics, list):
        # Метрики для конкретной задачи
        durations = [m.get('duration', 0) for m in metrics if m.get('duration')]
        if not durations:
            return {}
        
        durations.sort()
        n = len(durations)
        
        return {
            'task_name': task_name,
            'total_tasks': n,
            'avg_duration': sum(durations) / n,
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50_duration': durations[n // 2],
            'p95_duration': durations[int(n * 0.95)],
            'p99_duration': durations[int(n * 0.99)],
            'failed_tasks': len([m for m in metrics if m.get('status') == 'failed']),
        }
    
    # Общие метрики по всем задачам
    result = {}
    for name, task_metrics_list in metrics.items():
        if isinstance(task_metrics_list, list):
            result[name] = get_task_metrics(name)
    
    return result

def cleanup_old_metrics(max_records: int = 1000):
    """Очистка старых метрик для экономии памяти."""
    for task_name in task_metrics:
        if len(task_metrics[task_name]) > max_records:
            # Оставляем только последние записи
            task_metrics[task_name] = task_metrics[task_name][-max_records:]
