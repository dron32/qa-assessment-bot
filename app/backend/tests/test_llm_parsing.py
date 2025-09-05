"""Тесты для LLM парсинга."""

import pytest
import json
from unittest.mock import Mock, patch
from pydantic import ValidationError

from app.backend.src.llm.client import LlmClient, FAST_PROFILE, SUMMARY_PROFILE
from app.backend.src.llm.schemas import (
    TemplateResponse, RefineResponse, ConflictsResponse, SummaryResponse
)


class TestLLMParsing:
    """Тесты для парсинга LLM ответов."""
    
    def setup_method(self):
        self.client = LlmClient()
    
    def test_parse_template_response_valid(self):
        """Тест парсинга валидного ответа шаблона."""
        valid_response = {
            "outline": "План ответа по аналитическому мышлению",
            "example": "Пример: При тестировании API я сначала анализирую требования...",
            "bullet_points": [
                "Опишите конкретный пример",
                "Объясните ваш подход",
                "Укажите результат"
            ]
        }
        
        response = TemplateResponse.model_validate(valid_response)
        
        assert response.outline == "План ответа по аналитическому мышлению"
        assert "API" in response.example
        assert len(response.bullet_points) == 3
        assert "пример" in response.bullet_points[0]
    
    def test_parse_template_response_invalid(self):
        """Тест парсинга невалидного ответа шаблона."""
        invalid_response = {
            "outline": "План ответа",
            # Отсутствует example
            "bullet_points": []
        }
        
        with pytest.raises(ValidationError):
            TemplateResponse.model_validate(invalid_response)
    
    def test_parse_refine_response_valid(self):
        """Тест парсинга валидного ответа рефакторинга."""
        valid_response = {
            "refined": "Сжатая версия текста с улучшениями",
            "improvement_hints": [
                "Добавить конкретные примеры",
                "Убрать общие фразы"
            ]
        }
        
        response = RefineResponse.model_validate(valid_response)
        
        assert response.refined == "Сжатая версия текста с улучшениями"
        assert len(response.improvement_hints) == 2
        assert "примеры" in response.improvement_hints[0]
    
    def test_parse_refine_response_invalid(self):
        """Тест парсинга невалидного ответа рефакторинга."""
        invalid_response = {
            # Отсутствует refined
            "improvement_hints": []
        }
        
        with pytest.raises(ValidationError):
            RefineResponse.model_validate(invalid_response)
    
    def test_parse_conflicts_response_valid(self):
        """Тест парсинга валидного ответа конфликтов."""
        valid_response = {
            "duplicates": [
                {
                    "self_item": "Хорошо анализирую проблемы",
                    "peer_item": "Отлично анализирует проблемы",
                    "similarity": 0.9
                }
            ],
            "contradictions": [
                {
                    "self_item": "Оценка 5",
                    "peer_item": "Оценка 2",
                    "competency": "analytical_thinking"
                }
            ]
        }
        
        response = ConflictsResponse.model_validate(valid_response)
        
        assert len(response.duplicates) == 1
        assert len(response.contradictions) == 1
        assert response.duplicates[0].similarity == 0.9
        assert response.contradictions[0].competency == "analytical_thinking"
    
    def test_parse_conflicts_response_empty(self):
        """Тест парсинга пустого ответа конфликтов."""
        empty_response = {
            "duplicates": [],
            "contradictions": []
        }
        
        response = ConflictsResponse.model_validate(empty_response)
        
        assert len(response.duplicates) == 0
        assert len(response.contradictions) == 0
    
    def test_parse_summary_response_valid(self):
        """Тест парсинга валидного ответа сводки."""
        valid_response = {
            "strengths": [
                "Отличные аналитические навыки",
                "Качественные баг-репорты",
                "Хорошая коммуникация"
            ],
            "areas_for_growth": [
                "Автоматизация тестирования",
                "Performance тестирование"
            ],
            "next_steps": [
                "Изучить Selenium",
                "Практиковать нагрузочное тестирование"
            ]
        }
        
        response = SummaryResponse.model_validate(valid_response)
        
        assert len(response.strengths) == 3
        assert len(response.areas_for_growth) == 2
        assert len(response.next_steps) == 2
        assert "аналитические" in response.strengths[0]
        assert "автоматизация" in response.areas_for_growth[0]
    
    def test_parse_summary_response_invalid(self):
        """Тест парсинга невалидного ответа сводки."""
        invalid_response = {
            "strengths": [],
            # Отсутствует areas_for_growth
            "next_steps": []
        }
        
        with pytest.raises(ValidationError):
            SummaryResponse.model_validate(invalid_response)


class TestLLMClientIntegration:
    """Тесты интеграции LLM клиента."""
    
    def setup_method(self):
        self.client = LlmClient()
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_generate_template_with_mock(self, mock_openai):
        """Тест генерации шаблона с моком OpenAI."""
        # Настройка мока
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "outline": "План ответа",
            "example": "Пример ответа",
            "bullet_points": ["Пункт 1", "Пункт 2"]
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 100
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем
        result = client.generate_template(
            competency="analytical_thinking",
            context="QA тестирование",
            trace_id="test-trace"
        )
        
        assert isinstance(result, TemplateResponse)
        assert result.outline == "План ответа"
        assert result.example == "Пример ответа"
        assert len(result.bullet_points) == 2
        
        # Проверяем, что OpenAI был вызван
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == FAST_PROFILE.model
        assert call_args[1]['max_tokens'] == FAST_PROFILE.max_tokens
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_refine_text_with_mock(self, mock_openai):
        """Тест рефакторинга текста с моком OpenAI."""
        # Настройка мока
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "refined": "Улучшенный текст",
            "improvement_hints": ["Подсказка 1", "Подсказка 2"]
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем
        result = client.refine_text(
            text="Исходный текст для рефакторинга",
            trace_id="test-trace"
        )
        
        assert isinstance(result, RefineResponse)
        assert result.refined == "Улучшенный текст"
        assert len(result.improvement_hints) == 2
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_detect_conflicts_with_mock(self, mock_openai):
        """Тест обнаружения конфликтов с моком OpenAI."""
        # Настройка мока
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "duplicates": [
                {
                    "self_item": "Хорошо анализирую",
                    "peer_item": "Отлично анализирует",
                    "similarity": 0.8
                }
            ],
            "contradictions": [
                {
                    "self_item": "Оценка 5",
                    "peer_item": "Оценка 2",
                    "competency": "analytical_thinking"
                }
            ]
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 75
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем
        result = client.detect_conflicts(
            self_items=["Хорошо анализирую проблемы"],
            peer_items=["Отлично анализирует проблемы"],
            trace_id="test-trace"
        )
        
        assert isinstance(result, ConflictsResponse)
        assert len(result.duplicates) == 1
        assert len(result.contradictions) == 1
        assert result.duplicates[0].similarity == 0.8
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_generate_summary_with_mock(self, mock_openai):
        """Тест генерации сводки с моком OpenAI."""
        # Настройка мока
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "strengths": ["Сила 1", "Сила 2"],
            "areas_for_growth": ["Рост 1", "Рост 2"],
            "next_steps": ["Шаг 1", "Шаг 2"]
        })
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 150
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем
        result = client.generate_summary(
            user_context="Контекст пользователя",
            trace_id="test-trace"
        )
        
        assert isinstance(result, SummaryResponse)
        assert len(result.strengths) == 2
        assert len(result.areas_for_growth) == 2
        assert len(result.next_steps) == 2
        
        # Проверяем, что использовался SUMMARY_PROFILE
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == SUMMARY_PROFILE.model
        assert call_args[1]['max_tokens'] == SUMMARY_PROFILE.max_tokens
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_llm_timeout_fallback(self, mock_openai):
        """Тест fallback при таймауте LLM."""
        # Настройка мока для таймаута
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Timeout")
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем fallback
        result = client.generate_template(
            competency="test",
            context="test",
            trace_id="test-trace"
        )
        
        # Должен вернуться fallback ответ
        assert isinstance(result, TemplateResponse)
        assert result.outline == "Краткий план"
        assert result.example == "Краткий пример"
        assert len(result.bullet_points) == 3
    
    @patch('app.backend.src.llm.client.OpenAI')
    def test_llm_invalid_json_fallback(self, mock_openai):
        """Тест fallback при невалидном JSON."""
        # Настройка мока для невалидного JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Невалидный JSON"
        mock_response.usage = Mock()
        mock_response.usage.completion_tokens = 50
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Создаем новый клиент с моком
        client = LlmClient()
        client._client = mock_client
        
        # Тестируем fallback
        result = client.refine_text(
            text="test",
            trace_id="test-trace"
        )
        
        # Должен вернуться fallback ответ
        assert isinstance(result, RefineResponse)
        assert result.refined == "Сжатая версия текста"
        assert len(result.improvement_hints) == 2


class TestLLMProfiles:
    """Тесты для профилей LLM."""
    
    def test_fast_profile_configuration(self):
        """Тест конфигурации быстрого профиля."""
        assert FAST_PROFILE.model == "gpt-4o-mini"
        assert FAST_PROFILE.max_tokens == 500
        assert FAST_PROFILE.temperature == 0.2
        assert FAST_PROFILE.timeout_seconds == 5
    
    def test_summary_profile_configuration(self):
        """Тест конфигурации профиля для сводок."""
        assert SUMMARY_PROFILE.model == "gpt-4o"
        assert SUMMARY_PROFILE.max_tokens == 700
        assert SUMMARY_PROFILE.temperature == 0.4
        assert SUMMARY_PROFILE.timeout_seconds == 15
    
    def test_profile_immutability(self):
        """Тест неизменяемости профилей."""
        # Попытка изменить профиль должна вызвать ошибку
        with pytest.raises(AttributeError):
            FAST_PROFILE.model = "gpt-3.5-turbo"
        
        with pytest.raises(AttributeError):
            SUMMARY_PROFILE.max_tokens = 1000
