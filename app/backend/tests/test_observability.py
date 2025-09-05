"""Тесты для observability модулей."""

import json
import pytest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from app.backend.src.main import create_app
from app.backend.src.core.logging import PIIMasker, ObservabilityLogger
from app.backend.src.core.metrics import get_metrics, LLMMetrics, CeleryMetrics
from app.backend.src.core.encryption import TextEncryption, generate_encryption_key


class TestPIIMasker:
    """Тесты маскирования PII."""
    
    def test_mask_email(self):
        """Тест маскирования email."""
        text = "Мой email: user@example.com для связи"
        masked = PIIMasker.mask_pii(text)
        assert "[EMAIL_MASKED]" in masked
        assert "user@example.com" not in masked
    
    def test_mask_phone(self):
        """Тест маскирования телефона."""
        text = "Позвоните по номеру +7 (999) 123-45-67"
        masked = PIIMasker.mask_pii(text)
        assert "[PHONE_MASKED]" in masked
        assert "+7 (999) 123-45-67" not in masked
    
    def test_mask_credit_card(self):
        """Тест маскирования кредитной карты."""
        text = "Карта 1234-5678-9012-3456"
        masked = PIIMasker.mask_pii(text)
        assert "[CARD_MASKED]" in masked
        assert "1234-5678-9012-3456" not in masked
    
    def test_mask_dict(self):
        """Тест маскирования словаря."""
        data = {
            "user": "test@example.com",
            "phone": "+7 999 123 45 67",
            "nested": {
                "email": "nested@test.com"
            }
        }
        masked = PIIMasker.mask_dict(data)
        assert masked["user"] == "[EMAIL_MASKED]"
        assert masked["phone"] == "[PHONE_MASKED]"
        assert masked["nested"]["email"] == "[EMAIL_MASKED]"


class TestObservabilityLogger:
    """Тесты observability логгера."""
    
    def test_logger_with_metrics(self):
        """Тест логгера с метриками."""
        logger = ObservabilityLogger("test")
        
        with patch.object(logger.logger, 'log') as mock_log:
            logger.info("test message", user_id=123, action="test")
            
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][0] == 20  # INFO level
            assert call_args[0][1] == "test message"
            
            # Проверяем extra поля
            extra = call_args[1]['extra']
            assert extra['user_id'] == 123
            assert extra['action'] == "test"
            assert 'trace_id' in extra
    
    def test_logger_timer(self):
        """Тест измерения времени."""
        logger = ObservabilityLogger("test")
        
        with patch.object(logger.logger, 'log') as mock_log:
            logger.start_timer()
            # Имитируем задержку
            import time
            time.sleep(0.01)
            logger.info("test message")
            
            call_args = mock_log.call_args
            extra = call_args[1]['extra']
            assert 'latency_ms' in extra
            assert extra['latency_ms'] > 0


class TestMetrics:
    """Тесты метрик."""
    
    def test_get_metrics(self):
        """Тест получения метрик."""
        metrics = get_metrics()
        assert isinstance(metrics, str)
        assert "http_requests_total" in metrics
    
    def test_llm_metrics(self):
        """Тест LLM метрик."""
        with patch('app.backend.src.core.metrics.LLM_REQUESTS_TOTAL') as mock_counter:
            LLMMetrics.record_request(
                model="gpt-4o",
                operation="test",
                status="success",
                duration=1.0,
                tokens_in=100,
                tokens_out=50
            )
            mock_counter.labels.assert_called_once_with(
                model="gpt-4o",
                operation="test",
                status="success"
            )
    
    def test_celery_metrics(self):
        """Тест Celery метрик."""
        with patch('app.backend.src.core.metrics.CELERY_TASKS_TOTAL') as mock_counter:
            CeleryMetrics.record_task("test_task", "success", 2.0)
            mock_counter.labels.assert_called_once_with(
                task_name="test_task",
                status="success"
            )


class TestEncryption:
    """Тесты шифрования."""
    
    def test_generate_key(self):
        """Тест генерации ключа."""
        key = generate_encryption_key()
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_encryption_without_key(self):
        """Тест шифрования без ключа."""
        encryption = TextEncryption()
        text = "test text"
        
        # Без ключа должен возвращать исходный текст
        encrypted = encryption.encrypt(text)
        assert encrypted == text
        
        decrypted = encryption.decrypt(text)
        assert decrypted == text
    
    @patch('app.backend.src.core.encryption.get_settings')
    def test_encryption_with_key(self, mock_settings):
        """Тест шифрования с ключом."""
        mock_settings.return_value.encryption_key = "test_key_123456789012345678901234567890"
        
        encryption = TextEncryption()
        text = "test text"
        
        encrypted = encryption.encrypt(text)
        assert encrypted != text
        assert len(encrypted) > len(text)
        
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == text
    
    def test_is_encrypted(self):
        """Тест проверки зашифрованности."""
        encryption = TextEncryption()
        
        # Короткий текст не считается зашифрованным
        assert not encryption.is_encrypted("short")
        
        # Длинный base64 текст считается зашифрованным
        long_base64 = "gAAAAAB" + "A" * 100
        assert encryption.is_encrypted(long_base64)


class TestMetricsEndpoint:
    """Тесты endpoint метрик."""
    
    def test_metrics_endpoint(self):
        """Тест endpoint /metrics."""
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
    
    def test_healthcheck_with_logging(self):
        """Тест healthcheck с логированием."""
        app = create_app()
        client = TestClient(app)
        
        with patch('app.backend.src.core.logging.get_logger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            
            response = client.get("/healthz")
            assert response.status_code == 200
            
            # Проверяем, что логгер был вызван
            mock_log.info.assert_called_once()
            call_args = mock_log.info.call_args
            assert call_args[0][0] == "healthcheck_requested"
            assert call_args[1]['action'] == "healthcheck"
