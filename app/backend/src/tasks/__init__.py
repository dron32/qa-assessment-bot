"""
Фоновые задачи Celery для QA Assessment Bot.

Задачи:
- Генерация summary с LLM
- Сравнение self vs peer (несоответствия/дубликаты)
- Эмбеддинги и кэш шаблонов
- Метрики и мониторинг
"""

from .celery_app import celery_app
from .summary import generate_summary_task
from .comparison import compare_reviews_task
from .embeddings import generate_embeddings_task, cache_templates_task

__all__ = [
    'celery_app',
    'generate_summary_task',
    'compare_reviews_task', 
    'generate_embeddings_task',
    'cache_templates_task',
]
