"""
Задачи для сравнения self vs peer reviews (несоответствия/дубликаты).
"""

import asyncio
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.exceptions import Retry

from ..llm.client import LlmClient, FAST_PROFILE
from ..core.logging import get_logger
from .celery_app import celery_app

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30},
    retry_backoff=True,
    queue='comparison'
)
def compare_reviews_task(self, review_id: int) -> Dict[str, Any]:
    """
    Сравнение self и peer reviews для выявления несоответствий и дубликатов.
    
    Args:
        review_id: ID review для анализа
        
    Returns:
        Dict с результатами сравнения
    """
    try:
        task_id = getattr(self.request, 'id', None) or 'test-task-id'
        logger.info(
            "Starting review comparison",
            extra={
                'task_id': task_id,
                'review_id': review_id,
            }
        )
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 0, 'total': 100, 'status': 'Loading review data...'}
            )
        
        # Получаем данные review
        review_data = _get_review_data(review_id)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Analyzing conflicts...'}
            )
        
        # Анализируем конфликты через LLM
        llm_client = LlmClient()
        conflicts = llm_client.detect_conflicts(
            self_review=review_data['self_review'],
            peer_reviews=review_data['peer_reviews'],
            profile=FAST_PROFILE
        )
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 60, 'total': 100, 'status': 'Detecting duplicates...'}
            )
        
        # Ищем дубликаты
        duplicates = _detect_duplicates(review_data)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Saving results...'}
            )
        
        # Сохраняем результаты
        result_id = _save_comparison_results(review_id, conflicts, duplicates)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Completed'}
            )
        
        result = {
            'review_id': review_id,
            'conflicts': conflicts,
            'duplicates': duplicates,
            'result_id': result_id,
            'status': 'completed'
        }
        
        logger.info(
            "Review comparison completed",
            extra={
                'task_id': self.request.id,
                'review_id': review_id,
                'conflicts_count': len(conflicts.get('conflicts', [])),
                'duplicates_count': len(duplicates),
            }
        )
        
        return result
        
    except Exception as exc:
        logger.error(
            "Review comparison failed",
            extra={
                'task_id': self.request.id,
                'review_id': review_id,
                'error': str(exc),
            }
        )
        
        raise self.retry(exc=exc)

def _get_review_data(review_id: int) -> Dict[str, Any]:
    """Получение данных review из БД."""
    # Заглушка - в реальности здесь будет запрос к БД
    return {
        'review_id': review_id,
        'self_review': {
            'user_id': 1,
            'competencies': [
                {
                    'competency': 'analytical_thinking',
                    'answer': 'Хорошо анализирую проблемы',
                    'score': 4
                },
                {
                    'competency': 'bug_reports',
                    'answer': 'Пишу подробные баг-репорты',
                    'score': 5
                }
            ]
        },
        'peer_reviews': [
            {
                'reviewer_id': 2,
                'competencies': [
                    {
                        'competency': 'analytical_thinking',
                        'answer': 'Отличные аналитические навыки',
                        'score': 5
                    },
                    {
                        'competency': 'bug_reports',
                        'answer': 'Качественные баг-репорты',
                        'score': 4
                    }
                ]
            }
        ]
    }

def _detect_duplicates(review_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Поиск дубликатов в ответах."""
    duplicates = []
    
    # Простой алгоритм поиска дубликатов по схожести текста
    self_answers = review_data['self_review']['competencies']
    peer_answers = []
    
    for peer_review in review_data['peer_reviews']:
        peer_answers.extend(peer_review['competencies'])
    
    # Сравниваем ответы на одинаковые компетенции
    for self_comp in self_answers:
        for peer_comp in peer_answers:
            if (self_comp['competency'] == peer_comp['competency'] and
                _calculate_similarity(self_comp['answer'], peer_comp['answer']) > 0.8):
                
                duplicates.append({
                    'competency': self_comp['competency'],
                    'self_answer': self_comp['answer'],
                    'peer_answer': peer_comp['answer'],
                    'similarity': _calculate_similarity(self_comp['answer'], peer_comp['answer']),
                    'self_score': self_comp['score'],
                    'peer_score': peer_comp['score']
                })
    
    return duplicates

def _calculate_similarity(text1: str, text2: str) -> float:
    """Простой расчет схожести текстов."""
    # Упрощенный алгоритм - в реальности можно использовать более сложные методы
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def _save_comparison_results(review_id: int, conflicts: Dict[str, Any], duplicates: List[Dict[str, Any]]) -> int:
    """Сохранение результатов сравнения в БД."""
    # Заглушка - в реальности здесь будет сохранение в БД
    import time
    result_id = int(time.time() * 1000)
    
    logger.info(
        "Comparison results saved",
        extra={
            'result_id': result_id,
            'review_id': review_id,
            'conflicts_count': len(conflicts.get('conflicts', [])),
            'duplicates_count': len(duplicates),
        }
    )
    
    return result_id

@celery_app.task(queue='comparison')
def batch_compare_reviews_task(review_ids: List[int]) -> Dict[str, Any]:
    """
    Массовое сравнение reviews.
    
    Args:
        review_ids: Список ID reviews для анализа
        
    Returns:
        Dict с результатами
    """
    results = []
    errors = []
    
    for review_id in review_ids:
        try:
            task_result = compare_reviews_task.delay(review_id)
            results.append({
                'review_id': review_id,
                'task_id': task_result.id,
                'status': 'started'
            })
        except Exception as exc:
            errors.append({
                'review_id': review_id,
                'error': str(exc)
            })
    
    return {
        'total_reviews': len(review_ids),
        'started_tasks': len(results),
        'errors': len(errors),
        'results': results,
        'error_details': errors
    }

@celery_app.task(queue='comparison')
def cleanup_old_comparisons_task(days_old: int = 30) -> Dict[str, Any]:
    """
    Очистка старых результатов сравнения.
    
    Args:
        days_old: Возраст записей для удаления в днях
        
    Returns:
        Dict с результатами очистки
    """
    try:
        # Заглушка - в реальности здесь будет удаление из БД
        deleted_count = 0  # Симуляция удаления
        
        logger.info(
            "Old comparisons cleaned up",
            extra={
                'days_old': days_old,
                'deleted_count': deleted_count,
            }
        )
        
        return {
            'deleted_count': deleted_count,
            'days_old': days_old,
            'status': 'completed'
        }
        
    except Exception as exc:
        logger.error(
            "Cleanup failed",
            extra={
                'days_old': days_old,
                'error': str(exc),
            }
        )
        raise
