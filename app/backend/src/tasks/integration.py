"""
Интеграция фоновых задач с API и ботами.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException

from .celery_app import celery_app
from .summary import generate_summary_task, generate_batch_summaries_task
from .comparison import compare_reviews_task, batch_compare_reviews_task
from .embeddings import generate_embeddings_task, cache_templates_task, warm_up_embeddings_cache_task
from ..core.logging import get_logger

logger = get_logger(__name__)

class TaskManager:
    """Менеджер для управления фоновыми задачами."""
    
    @staticmethod
    def start_summary_generation(user_id: int, cycle_id: Optional[int] = None) -> Dict[str, Any]:
        """Запуск генерации summary для пользователя."""
        try:
            task = generate_summary_task.delay(user_id, cycle_id)
            
            logger.info(
                "Summary generation task started",
                extra={
                    'user_id': user_id,
                    'cycle_id': cycle_id,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'user_id': user_id,
                'cycle_id': cycle_id,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start summary generation",
                extra={
                    'user_id': user_id,
                    'cycle_id': cycle_id,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start summary generation")
    
    @staticmethod
    def start_batch_summary_generation(user_ids: list, cycle_id: Optional[int] = None) -> Dict[str, Any]:
        """Запуск массовой генерации summary."""
        try:
            task = generate_batch_summaries_task.delay(user_ids, cycle_id)
            
            logger.info(
                "Batch summary generation task started",
                extra={
                    'user_ids': user_ids,
                    'cycle_id': cycle_id,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'user_ids': user_ids,
                'cycle_id': cycle_id,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start batch summary generation",
                extra={
                    'user_ids': user_ids,
                    'cycle_id': cycle_id,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start batch summary generation")
    
    @staticmethod
    def start_review_comparison(review_id: int) -> Dict[str, Any]:
        """Запуск сравнения review."""
        try:
            task = compare_reviews_task.delay(review_id)
            
            logger.info(
                "Review comparison task started",
                extra={
                    'review_id': review_id,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'review_id': review_id,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start review comparison",
                extra={
                    'review_id': review_id,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start review comparison")
    
    @staticmethod
    def start_batch_review_comparison(review_ids: list) -> Dict[str, Any]:
        """Запуск массового сравнения reviews."""
        try:
            task = batch_compare_reviews_task.delay(review_ids)
            
            logger.info(
                "Batch review comparison task started",
                extra={
                    'review_ids': review_ids,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'review_ids': review_ids,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start batch review comparison",
                extra={
                    'review_ids': review_ids,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start batch review comparison")
    
    @staticmethod
    def start_embeddings_generation(text: str, model: str = 'text-embedding-3-small') -> Dict[str, Any]:
        """Запуск генерации эмбеддингов."""
        try:
            task = generate_embeddings_task.delay(text, model)
            
            logger.info(
                "Embeddings generation task started",
                extra={
                    'text_length': len(text),
                    'model': model,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'text_length': len(text),
                'model': model,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start embeddings generation",
                extra={
                    'text': text[:100] + '...' if len(text) > 100 else text,
                    'model': model,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start embeddings generation")
    
    @staticmethod
    def start_templates_caching(template_ids: Optional[list] = None) -> Dict[str, Any]:
        """Запуск кэширования шаблонов."""
        try:
            task = cache_templates_task.delay(template_ids)
            
            logger.info(
                "Templates caching task started",
                extra={
                    'template_ids': template_ids,
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'template_ids': template_ids,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start templates caching",
                extra={
                    'template_ids': template_ids,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start templates caching")
    
    @staticmethod
    def start_embeddings_cache_warmup() -> Dict[str, Any]:
        """Запуск прогрева кэша эмбеддингов."""
        try:
            task = warm_up_embeddings_cache_task.delay()
            
            logger.info(
                "Embeddings cache warmup task started",
                extra={
                    'task_id': task.id,
                }
            )
            
            return {
                'task_id': task.id,
                'status': 'started'
            }
            
        except Exception as exc:
            logger.error(
                "Failed to start embeddings cache warmup",
                extra={
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to start embeddings cache warmup")
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Получение статуса задачи."""
        try:
            task_result = celery_app.AsyncResult(task_id)
            
            if task_result.state == 'PENDING':
                return {
                    'task_id': task_id,
                    'status': 'pending',
                    'progress': 0
                }
            elif task_result.state == 'PROGRESS':
                return {
                    'task_id': task_id,
                    'status': 'progress',
                    'progress': task_result.info.get('current', 0),
                    'total': task_result.info.get('total', 100),
                    'message': task_result.info.get('status', '')
                }
            elif task_result.state == 'SUCCESS':
                return {
                    'task_id': task_id,
                    'status': 'completed',
                    'result': task_result.result
                }
            elif task_result.state == 'FAILURE':
                return {
                    'task_id': task_id,
                    'status': 'failed',
                    'error': str(task_result.info)
                }
            else:
                return {
                    'task_id': task_id,
                    'status': task_result.state.lower(),
                    'result': task_result.result if task_result.result else None
                }
                
        except Exception as exc:
            logger.error(
                "Failed to get task status",
                extra={
                    'task_id': task_id,
                    'error': str(exc),
                }
            )
            raise HTTPException(status_code=500, detail="Failed to get task status")
    
    @staticmethod
    def get_task_metrics() -> Dict[str, Any]:
        """Получение метрик выполнения задач."""
        try:
            from .celery_app import get_task_metrics
            return get_task_metrics()
            
        except Exception as exc:
            logger.error(
                "Failed to get task metrics",
                extra={'error': str(exc)}
            )
            raise HTTPException(status_code=500, detail="Failed to get task metrics")

# Глобальный экземпляр менеджера задач
task_manager = TaskManager()
