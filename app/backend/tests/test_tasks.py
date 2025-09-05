"""
Тесты для фоновых задач Celery.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.backend.src.main import create_app
from app.backend.src.tasks.celery_app import celery_app, get_task_metrics
from app.backend.src.tasks.summary import generate_summary_task
from app.backend.src.tasks.comparison import compare_reviews_task
from app.backend.src.tasks.embeddings import generate_embeddings_task
from app.backend.src.tasks.integration import task_manager


class TestCeleryApp:
    """Тесты Celery приложения."""
    
    def test_celery_app_initialization(self):
        """Тест инициализации Celery приложения."""
        assert celery_app is not None
        assert celery_app.main == 'qa_assessment'
    
    def test_task_metrics_empty(self):
        """Тест метрик для пустого состояния."""
        metrics = get_task_metrics()
        assert metrics == {}
    
    def test_task_metrics_with_data(self):
        """Тест метрик с данными."""
        # Симулируем выполнение задач
        from app.backend.src.tasks.celery_app import task_metrics
        
        task_metrics['test_task'] = [
            {
                'task_id': 'test-1',
                'start_time': 1000,
                'end_time': 1005,
                'duration': 5,
                'status': 'completed'
            },
            {
                'task_id': 'test-2', 
                'start_time': 1010,
                'end_time': 1018,
                'duration': 8,
                'status': 'completed'
            }
        ]
        
        metrics = get_task_metrics('test_task')
        
        assert metrics['task_name'] == 'test_task'
        assert metrics['total_tasks'] == 2
        assert metrics['avg_duration'] == 6.5
        assert metrics['min_duration'] == 5
        assert metrics['max_duration'] == 8
        assert metrics['p95_duration'] == 8
        assert metrics['failed_tasks'] == 0


class TestSummaryTasks:
    """Тесты задач генерации summary."""
    
    @patch('app.backend.src.tasks.summary._collect_summary_data')
    @patch('app.backend.src.tasks.summary._save_summary_to_db')
    def test_generate_summary_task_success(self, mock_save, mock_collect):
        """Тест успешной генерации summary."""
        # Настройка моков
        mock_collect.return_value = {'user_id': 1, 'self_reviews': []}
        mock_save.return_value = 123
        
        # Мокаем LLM клиент
        with patch('app.backend.src.tasks.summary.LlmClient') as mock_llm:
            mock_client = Mock()
            mock_client.generate_summary.return_value = {'summary': 'Test summary'}
            mock_llm.return_value = mock_client
            
            # Выполняем задачу
            result = generate_summary_task(1, 1)
            
            # Проверяем результат
            assert result['user_id'] == 1
            assert result['cycle_id'] == 1
            assert result['summary_id'] == 123
            assert result['status'] == 'completed'
    
    def test_generate_summary_task_retry(self):
        """Тест повторных попыток при ошибке."""
        with patch('app.backend.src.tasks.summary._collect_summary_data') as mock_collect:
            mock_collect.side_effect = Exception("Test error")
            
            # Создаем mock задачу с retry
            mock_task = Mock()
            mock_task.request.retries = 0
            mock_task.max_retries = 3
            mock_task.retry = Mock()
            
            # Мокаем self для задачи
            with patch.object(generate_summary_task, 'retry') as mock_retry:
                try:
                    generate_summary_task(mock_task, 1, 1)
                except Exception:
                    pass
                
                # Проверяем, что retry был вызван
                assert mock_retry.called


class TestComparisonTasks:
    """Тесты задач сравнения reviews."""
    
    @patch('app.backend.src.tasks.comparison._get_review_data')
    @patch('app.backend.src.tasks.comparison._save_comparison_results')
    def test_compare_reviews_task_success(self, mock_save, mock_get_data):
        """Тест успешного сравнения reviews."""
        # Настройка моков
        mock_get_data.return_value = {
            'review_id': 1,
            'self_review': {'competencies': []},
            'peer_reviews': []
        }
        mock_save.return_value = 456
        
        # Мокаем LLM клиент
        with patch('app.backend.src.tasks.comparison.LlmClient') as mock_llm:
            mock_client = Mock()
            mock_client.detect_conflicts.return_value = {'conflicts': []}
            mock_llm.return_value = mock_client
            
            # Выполняем задачу
            result = compare_reviews_task(1)
            
            # Проверяем результат
            assert result['review_id'] == 1
            assert result['result_id'] == 456
            assert result['status'] == 'completed'
    
    def test_detect_duplicates(self):
        """Тест поиска дубликатов."""
        from app.backend.src.tasks.comparison import _detect_duplicates, _calculate_similarity
        
        # Тест расчета схожести
        similarity = _calculate_similarity("Hello world", "Hello world")
        assert similarity == 1.0
        
        similarity = _calculate_similarity("Hello world", "Goodbye world")
        assert 0 < similarity < 1
        
        similarity = _calculate_similarity("Hello", "Goodbye")
        assert similarity == 0.0


class TestEmbeddingsTasks:
    """Тесты задач генерации эмбеддингов."""
    
    @patch('app.backend.src.tasks.embeddings._get_cached_embeddings')
    @patch('app.backend.src.tasks.embeddings._cache_embeddings')
    def test_generate_embeddings_task_success(self, mock_cache, mock_get_cached):
        """Тест успешной генерации эмбеддингов."""
        # Настройка моков
        mock_get_cached.return_value = None  # Нет в кэше
        
        # Мокаем LLM клиент
        with patch('app.backend.src.tasks.embeddings.LlmClient') as mock_llm:
            mock_client = Mock()
            mock_client.generate_embeddings.return_value = [0.1, 0.2, 0.3]
            mock_llm.return_value = mock_client
            
            # Выполняем задачу
            result = generate_embeddings_task("Test text")
            
            # Проверяем результат
            assert result['embeddings'] == [0.1, 0.2, 0.3]
            assert result['model'] == 'text-embedding-3-small'
            assert result['cached'] == False
            assert 'text_hash' in result
    
    @patch('app.backend.src.tasks.embeddings._get_cached_embeddings')
    def test_generate_embeddings_task_cached(self, mock_get_cached):
        """Тест использования кэшированных эмбеддингов."""
        # Настройка моков
        cached_result = {
            'text_hash': 'test-hash',
            'embeddings': [0.1, 0.2, 0.3],
            'model': 'text-embedding-3-small',
            'cached': True
        }
        mock_get_cached.return_value = cached_result
        
        # Выполняем задачу
        result = generate_embeddings_task("Test text")
        
        # Проверяем, что вернулся кэшированный результат
        assert result == cached_result


class TestTaskIntegration:
    """Тесты интеграции задач с API."""
    
    def test_task_manager_summary_generation(self):
        """Тест менеджера задач для генерации summary."""
        with patch('app.backend.src.tasks.integration.generate_summary_task') as mock_task:
            mock_task.delay.return_value = Mock(id='test-task-id')
            
            result = task_manager.start_summary_generation(1, 1)
            
            assert result['task_id'] == 'test-task-id'
            assert result['user_id'] == 1
            assert result['cycle_id'] == 1
            assert result['status'] == 'started'
    
    def test_task_manager_review_comparison(self):
        """Тест менеджера задач для сравнения reviews."""
        with patch('app.backend.src.tasks.integration.compare_reviews_task') as mock_task:
            mock_task.delay.return_value = Mock(id='test-task-id')
            
            result = task_manager.start_review_comparison(1)
            
            assert result['task_id'] == 'test-task-id'
            assert result['review_id'] == 1
            assert result['status'] == 'started'
    
    def test_task_manager_embeddings_generation(self):
        """Тест менеджера задач для генерации эмбеддингов."""
        with patch('app.backend.src.tasks.integration.generate_embeddings_task') as mock_task:
            mock_task.delay.return_value = Mock(id='test-task-id')
            
            result = task_manager.start_embeddings_generation("Test text")
            
            assert result['task_id'] == 'test-task-id'
            assert result['text_length'] == 9
            assert result['model'] == 'text-embedding-3-small'
            assert result['status'] == 'started'


class TestTaskAPI:
    """Тесты API эндпоинтов для задач."""
    
    def test_get_task_status(self):
        """Тест получения статуса задачи."""
        app = create_app()
        client = TestClient(app)
        
        with patch('app.backend.src.tasks.integration.task_manager') as mock_manager:
            mock_manager.get_task_status.return_value = {
                'task_id': 'test-id',
                'status': 'completed',
                'result': {'summary': 'Test'}
            }
            
            response = client.get(
                "/api/tasks/test-id/status",
                headers={"X-User-Id": "1", "X-User-Role": "admin"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['task_id'] == 'test-id'
            assert data['status'] == 'completed'
    
    def test_get_task_metrics(self):
        """Тест получения метрик задач."""
        app = create_app()
        client = TestClient(app)
        
        with patch('app.backend.src.tasks.integration.task_manager') as mock_manager:
            mock_manager.get_task_metrics.return_value = {
                'summary_task': {
                    'total_tasks': 10,
                    'avg_duration': 5.5,
                    'p95_duration': 8.0
                }
            }
            
            response = client.get(
                "/api/tasks/metrics",
                headers={"X-User-Id": "1", "X-User-Role": "admin"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'summary_task' in data
            assert data['summary_task']['total_tasks'] == 10
