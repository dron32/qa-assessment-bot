"""
Задачи для генерации summary с LLM.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from celery import current_task
from celery.exceptions import Retry

from ..llm.client import LlmClient, SUMMARY_PROFILE
from ..core.logging import get_logger
from ..core.metrics import CeleryMetrics
from .celery_app import celery_app

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_jitter=True,
    queue='summary'
)
def generate_summary_task(self, user_id: int, cycle_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Генерация summary для пользователя за цикл.
    
    Args:
        user_id: ID пользователя
        cycle_id: ID цикла (опционально)
        
    Returns:
        Dict с результатом генерации summary
    """
    start_time = time.time()
    task_name = "generate_summary"
    
    try:
        task_id = getattr(self.request, 'id', None) or 'test-task-id'
        logger.info(
            "summary_generation_started",
            action="celery_task",
            task_id=task_id,
            user_id=user_id,
            cycle_id=cycle_id,
        )
        
        # Обновляем прогресс задачи только если task_id существует
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 0, 'total': 100, 'status': 'Initializing...'}
            )
        
        # Получаем данные для summary
        summary_data = _collect_summary_data(user_id, cycle_id)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 30, 'total': 100, 'status': 'Data collected, generating summary...'}
            )
        
        # Генерируем summary через LLM
        llm_client = LlmClient()
        summary_result = llm_client.generate_summary(
            user_id=user_id,
            cycle_id=cycle_id,
            data=summary_data,
            profile=SUMMARY_PROFILE
        )
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Saving summary...'}
            )
        
        # Сохраняем результат в БД
        summary_id = _save_summary_to_db(user_id, cycle_id, summary_result)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Completed'}
            )
        
        result = {
            'summary_id': summary_id,
            'user_id': user_id,
            'cycle_id': cycle_id,
            'summary': summary_result,
            'status': 'completed'
        }
        
        duration = time.time() - start_time
        
        # Записываем метрики успеха
        CeleryMetrics.record_task(task_name, "success", duration)
        
        logger.info(
            "summary_generation_completed",
            action="celery_task",
            task_id=self.request.id,
            user_id=user_id,
            cycle_id=cycle_id,
            summary_id=summary_id,
            latency_ms=round(duration * 1000, 2)
        )
        
        return result
        
    except Exception as exc:
        duration = time.time() - start_time
        
        # Записываем метрики ошибки
        CeleryMetrics.record_task(task_name, "error", duration)
        
        logger.error(
            "summary_generation_failed",
            action="celery_task",
            task_id=self.request.id,
            user_id=user_id,
            cycle_id=cycle_id,
            error=str(exc),
            latency_ms=round(duration * 1000, 2)
        )
        
        # Если это последняя попытка, сохраняем ошибку
        if self.request.retries >= self.max_retries:
            _save_summary_error(user_id, cycle_id, str(exc))
        
        raise self.retry(exc=exc)

def _collect_summary_data(user_id: int, cycle_id: Optional[int]) -> Dict[str, Any]:
    """Сбор данных для генерации summary."""
    # Заглушка - в реальности здесь будет запрос к БД
    return {
        'user_id': user_id,
        'cycle_id': cycle_id,
        'self_reviews': [
            {
                'competency': 'analytical_thinking',
                'answer': 'Хорошо анализирую проблемы и нахожу решения',
                'score': 4
            },
            {
                'competency': 'bug_reports',
                'answer': 'Пишу подробные баг-репорты с шагами воспроизведения',
                'score': 5
            }
        ],
        'peer_reviews': [
            {
                'reviewer_id': 2,
                'competency': 'analytical_thinking',
                'answer': 'Отличные аналитические навыки',
                'score': 5
            }
        ],
        'conflicts': [],
        'duplicates': []
    }

def _save_summary_to_db(user_id: int, cycle_id: Optional[int], summary_data: Dict[str, Any]) -> int:
    """Сохранение summary в БД."""
    # Заглушка - в реальности здесь будет сохранение в БД
    import time
    summary_id = int(time.time() * 1000)  # Простой ID
    
    logger.info(
        "Summary saved to database",
        extra={
            'summary_id': summary_id,
            'user_id': user_id,
            'cycle_id': cycle_id,
        }
    )
    
    return summary_id

def _save_summary_error(user_id: int, cycle_id: Optional[int], error: str):
    """Сохранение ошибки генерации summary."""
    logger.error(
        "Summary generation error saved",
        extra={
            'user_id': user_id,
            'cycle_id': cycle_id,
            'error': error,
        }
    )

@celery_app.task(queue='summary')
def generate_batch_summaries_task(user_ids: list, cycle_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Генерация summary для нескольких пользователей.
    
    Args:
        user_ids: Список ID пользователей
        cycle_id: ID цикла (опционально)
        
    Returns:
        Dict с результатами генерации
    """
    results = []
    errors = []
    
    for user_id in user_ids:
        try:
            # Запускаем задачу для каждого пользователя
            task_result = generate_summary_task.delay(user_id, cycle_id)
            results.append({
                'user_id': user_id,
                'task_id': task_result.id,
                'status': 'started'
            })
        except Exception as exc:
            errors.append({
                'user_id': user_id,
                'error': str(exc)
            })
    
    return {
        'total_users': len(user_ids),
        'started_tasks': len(results),
        'errors': len(errors),
        'results': results,
        'error_details': errors
    }
