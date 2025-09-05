"""
Задачи для генерации эмбеддингов и кэширования шаблонов.
"""

import asyncio
import hashlib
from typing import Dict, Any, List, Optional
from celery import current_task
from celery.exceptions import Retry

from ..llm.client import LlmClient
from ..core.logging import get_logger
from .celery_app import celery_app

logger = get_logger(__name__)

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 30},
    retry_backoff=True,
    queue='embeddings'
)
def generate_embeddings_task(self, text: str, model: str = 'text-embedding-3-small') -> Dict[str, Any]:
    """
    Генерация эмбеддингов для текста.
    
    Args:
        text: Текст для генерации эмбеддингов
        model: Модель для генерации эмбеддингов
        
    Returns:
        Dict с эмбеддингами и метаданными
    """
    try:
        task_id = getattr(self.request, 'id', None) or 'test-task-id'
        logger.info(
            "Starting embeddings generation",
            extra={
                'task_id': task_id,
                'text_length': len(text),
                'model': model,
            }
        )
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 0, 'total': 100, 'status': 'Generating embeddings...'}
            )
        
        # Генерируем хэш текста для кэширования
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Проверяем кэш
        cached_embeddings = _get_cached_embeddings(text_hash)
        if cached_embeddings:
            logger.info(
                "Using cached embeddings",
                extra={
                    'task_id': task_id,
                    'text_hash': text_hash,
                }
            )
            return cached_embeddings
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 50, 'total': 100, 'status': 'Calling OpenAI API...'}
            )
        
        # Генерируем эмбеддинги через OpenAI
        llm_client = LlmClient()
        embeddings = llm_client.generate_embeddings(text, model)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 80, 'total': 100, 'status': 'Caching embeddings...'}
            )
        
        # Кэшируем результат
        result = {
            'text_hash': text_hash,
            'embeddings': embeddings,
            'model': model,
            'text_length': len(text),
            'cached': False
        }
        
        _cache_embeddings(text_hash, result)
        
        if task_id != 'test-task-id':
            current_task.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Completed'}
            )
        
        logger.info(
            "Embeddings generation completed",
            extra={
                'task_id': self.request.id,
                'text_hash': text_hash,
                'embeddings_dimension': len(embeddings) if embeddings else 0,
            }
        )
        
        return result
        
    except Exception as exc:
        logger.error(
            "Embeddings generation failed",
            extra={
                'task_id': self.request.id,
                'text': text[:100] + '...' if len(text) > 100 else text,
                'model': model,
                'error': str(exc),
            }
        )
        
        raise self.retry(exc=exc)

@celery_app.task(queue='embeddings')
def cache_templates_task(template_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Кэширование шаблонов с предварительной генерацией эмбеддингов.
    
    Args:
        template_ids: Список ID шаблонов для кэширования (если None - все)
        
    Returns:
        Dict с результатами кэширования
    """
    try:
        logger.info(
            "Starting templates caching",
            extra={
                'template_ids': template_ids,
            }
        )
        
        # Получаем шаблоны для кэширования
        templates = _get_templates_for_caching(template_ids)
        
        results = []
        errors = []
        
        for template in templates:
            try:
                # Генерируем эмбеддинги для контента шаблона
                embeddings_task = generate_embeddings_task.delay(
                    template['content'],
                    'text-embedding-3-small'
                )
                
                # Сохраняем кэш
                cache_key = f"template:{template['id']}"
                _save_template_cache(cache_key, {
                    'template_id': template['id'],
                    'competency_id': template['competency_id'],
                    'language': template['language'],
                    'content': template['content'],
                    'version': template['version'],
                    'embeddings_task_id': embeddings_task.id,
                    'cached_at': _get_current_timestamp()
                })
                
                results.append({
                    'template_id': template['id'],
                    'embeddings_task_id': embeddings_task.id,
                    'status': 'cached'
                })
                
            except Exception as exc:
                errors.append({
                    'template_id': template['id'],
                    'error': str(exc)
                })
        
        logger.info(
            "Templates caching completed",
            extra={
                'total_templates': len(templates),
                'cached': len(results),
                'errors': len(errors),
            }
        )
        
        return {
            'total_templates': len(templates),
            'cached': len(results),
            'errors': len(errors),
            'results': results,
            'error_details': errors
        }
        
    except Exception as exc:
        logger.error(
            "Templates caching failed",
            extra={
                'template_ids': template_ids,
                'error': str(exc),
            }
        )
        raise

def _get_templates_for_caching(template_ids: Optional[List[int]]) -> List[Dict[str, Any]]:
    """Получение шаблонов для кэширования."""
    # Заглушка - в реальности здесь будет запрос к БД
    return [
        {
            'id': 1,
            'competency_id': 1,
            'language': 'ru',
            'content': 'Опишите ваш опыт в анализе проблем и поиске решений',
            'version': 1
        },
        {
            'id': 2,
            'competency_id': 2,
            'language': 'ru',
            'content': 'Расскажите о качестве ваших баг-репортов',
            'version': 1
        }
    ]

def _get_cached_embeddings(text_hash: str) -> Optional[Dict[str, Any]]:
    """Получение кэшированных эмбеддингов."""
    # Заглушка - в реальности здесь будет запрос к Redis/БД
    return None

def _cache_embeddings(text_hash: str, embeddings_data: Dict[str, Any]):
    """Кэширование эмбеддингов."""
    # Заглушка - в реальности здесь будет сохранение в Redis
    logger.info(
        "Embeddings cached",
        extra={
            'text_hash': text_hash,
            'model': embeddings_data.get('model'),
        }
    )

def _save_template_cache(cache_key: str, template_data: Dict[str, Any]):
    """Сохранение кэша шаблона."""
    # Заглушка - в реальности здесь будет сохранение в Redis
    logger.info(
        "Template cache saved",
        extra={
            'cache_key': cache_key,
            'template_id': template_data.get('template_id'),
        }
    )

def _get_current_timestamp() -> int:
    """Получение текущего timestamp."""
    import time
    return int(time.time())

@celery_app.task(queue='embeddings')
def cleanup_old_embeddings_cache_task(days_old: int = 7) -> Dict[str, Any]:
    """
    Очистка старого кэша эмбеддингов.
    
    Args:
        days_old: Возраст записей для удаления в днях
        
    Returns:
        Dict с результатами очистки
    """
    try:
        # Заглушка - в реальности здесь будет очистка Redis
        deleted_count = 0
        
        logger.info(
            "Old embeddings cache cleaned up",
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
            "Embeddings cache cleanup failed",
            extra={
                'days_old': days_old,
                'error': str(exc),
            }
        )
        raise

@celery_app.task(queue='embeddings')
def warm_up_embeddings_cache_task() -> Dict[str, Any]:
    """
    Прогрев кэша эмбеддингов для популярных шаблонов.
    """
    try:
        logger.info("Starting embeddings cache warm-up")
        
        # Получаем популярные шаблоны
        popular_templates = _get_popular_templates()
        
        results = []
        for template in popular_templates:
            try:
                # Генерируем эмбеддинги для популярных шаблонов
                task_result = generate_embeddings_task.delay(
                    template['content'],
                    'text-embedding-3-small'
                )
                
                results.append({
                    'template_id': template['id'],
                    'task_id': task_result.id,
                    'status': 'started'
                })
                
            except Exception as exc:
                logger.error(
                    "Failed to warm up template",
                    extra={
                        'template_id': template['id'],
                        'error': str(exc),
                    }
                )
        
        logger.info(
            "Embeddings cache warm-up completed",
            extra={
                'total_templates': len(popular_templates),
                'started_tasks': len(results),
            }
        )
        
        return {
            'total_templates': len(popular_templates),
            'started_tasks': len(results),
            'results': results
        }
        
    except Exception as exc:
        logger.error(
            "Embeddings cache warm-up failed",
            extra={'error': str(exc)}
        )
        raise

def _get_popular_templates() -> List[Dict[str, Any]]:
    """Получение популярных шаблонов для прогрева кэша."""
    # Заглушка - в реальности здесь будет запрос к БД
    return [
        {
            'id': 1,
            'content': 'Опишите ваш опыт в анализе проблем'
        },
        {
            'id': 2,
            'content': 'Расскажите о качестве ваших баг-репортов'
        }
    ]
