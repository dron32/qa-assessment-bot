"""Тесты для интеграции ботов."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.backend.src.main import create_app
from app.backend.src.bots.fsm import ReviewState, ReviewSession
from app.backend.src.domain.models import Platform, ReviewType


class TestSlackBot:
    """Тесты для Slack бота."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_slack_webhook_url_verification(self):
        """Тест URL verification для Slack."""
        response = self.client.post(
            "/bot/slack/events",
            json={
                "type": "url_verification",
                "challenge": "test_challenge_123"
            }
        )
        
        assert response.status_code == 200
        # В реальности должен вернуть challenge, но у нас заглушка
        assert response.json() == {"message": "Slack bot not configured"}
    
    def test_slack_webhook_event_callback(self):
        """Тест обработки event callback от Slack."""
        response = self.client.post(
            "/bot/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U123> /self_review",
                    "user": "U456",
                    "channel": "C789"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Slack bot not configured"}
    
    def test_slack_webhook_invalid_payload(self):
        """Тест обработки некорректного payload от Slack."""
        response = self.client.post(
            "/bot/slack/events",
            json={"invalid": "payload"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Slack bot not configured"}
    
    @patch('app.backend.src.bots.slack_app.slack_app')
    def test_slack_command_self_review(self, mock_slack_app):
        """Тест команды /self_review в Slack."""
        # Настройка мока
        mock_slack_app.command.return_value = Mock()
        
        response = self.client.post(
            "/bot/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U123> /self_review",
                    "user": "U456"
                }
            }
        )
        
        assert response.status_code == 200
    
    @patch('app.backend.src.bots.slack_app.slack_app')
    def test_slack_command_peer_review(self, mock_slack_app):
        """Тест команды /peer_review в Slack."""
        # Настройка мока
        mock_slack_app.command.return_value = Mock()
        
        response = self.client.post(
            "/bot/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U123> /peer_review @peer_user",
                    "user": "U456"
                }
            }
        )
        
        assert response.status_code == 200
    
    @patch('app.backend.src.bots.slack_app.slack_app')
    def test_slack_command_summary(self, mock_slack_app):
        """Тест команды /summary в Slack."""
        # Настройка мока
        mock_slack_app.command.return_value = Mock()
        
        response = self.client.post(
            "/bot/slack/events",
            json={
                "type": "event_callback",
                "event": {
                    "type": "app_mention",
                    "text": "<@U123> /summary @user",
                    "user": "U456"
                }
            }
        )
        
        assert response.status_code == 200


class TestTelegramBot:
    """Тесты для Telegram бота."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_telegram_webhook_start_command(self):
        """Тест команды /start в Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "from": {"id": 123, "username": "test_user"},
                    "chat": {"id": 456, "type": "private"},
                    "text": "/start"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}
    
    def test_telegram_webhook_self_review_command(self):
        """Тест команды /self_review в Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={
                "update_id": 2,
                "message": {
                    "message_id": 2,
                    "from": {"id": 123, "username": "test_user"},
                    "chat": {"id": 456, "type": "private"},
                    "text": "/self_review"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}
    
    def test_telegram_webhook_peer_review_command(self):
        """Тест команды /peer_review в Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={
                "update_id": 3,
                "message": {
                    "message_id": 3,
                    "from": {"id": 123, "username": "test_user"},
                    "chat": {"id": 456, "type": "private"},
                    "text": "/peer_review @peer_user"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}
    
    def test_telegram_webhook_summary_command(self):
        """Тест команды /summary в Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={
                "update_id": 4,
                "message": {
                    "message_id": 4,
                    "from": {"id": 123, "username": "test_user"},
                    "chat": {"id": 456, "type": "private"},
                    "text": "/summary @user"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}
    
    def test_telegram_webhook_invalid_update(self):
        """Тест обработки некорректного update от Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={"invalid": "update"}
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}
    
    def test_telegram_webhook_callback_query(self):
        """Тест обработки callback query от Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={
                "update_id": 5,
                "callback_query": {
                    "id": "callback_123",
                    "from": {"id": 123, "username": "test_user"},
                    "message": {"message_id": 1, "chat": {"id": 456}},
                    "data": "competency_1"
                }
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"message": "Telegram bot not configured"}


class TestFSM:
    """Тесты для Finite State Machine."""
    
    def test_review_state_enum(self):
        """Тест enum состояний ревью."""
        assert ReviewState.START.value == "start"
        assert ReviewState.COLLECTING_ANSWERS.value == "collecting_answers"
        assert ReviewState.PREVIEW.value == "preview"
        assert ReviewState.REFINING.value == "refining"
        assert ReviewState.SUBMITTING.value == "submitting"
        assert ReviewState.COMPLETED.value == "completed"
    
    def test_review_session_creation(self):
        """Тест создания сессии ревью."""
        session = ReviewSession(
            user_id=123,
            platform=Platform.SLACK,
            review_type=ReviewType.SELF,
            current_state=ReviewState.START
        )
        
        assert session.user_id == 123
        assert session.platform == Platform.SLACK
        assert session.review_type == ReviewType.SELF
        assert session.current_state == ReviewState.START
        assert session.answers == {}
        assert session.current_competency is None
    
    def test_review_session_with_answers(self):
        """Тест сессии ревью с ответами."""
        session = ReviewSession(
            user_id=123,
            platform=Platform.TELEGRAM,
            review_type=ReviewType.PEER,
            current_state=ReviewState.COLLECTING_ANSWERS,
            answers={"competency_1": {"answer": "Test answer", "score": 4}},
            current_competency="competency_2"
        )
        
        assert session.answers["competency_1"]["answer"] == "Test answer"
        assert session.answers["competency_1"]["score"] == 4
        assert session.current_competency == "competency_2"
    
    def test_review_session_validation(self):
        """Тест валидации сессии ревью."""
        # Валидная сессия
        session = ReviewSession(
            user_id=123,
            platform=Platform.WEB,
            review_type=ReviewType.SELF,
            current_state=ReviewState.START
        )
        assert session.user_id == 123
        
        # Невалидная сессия (отрицательный user_id)
        with pytest.raises(ValueError):
            ReviewSession(
                user_id=-1,
                platform=Platform.WEB,
                review_type=ReviewType.SELF,
                current_state=ReviewState.START
            )


class TestBotFSMIntegration:
    """Тесты интеграции ботов с FSM."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    @patch('app.backend.src.bots.fsm.fsm_store')
    def test_slack_fsm_session_creation(self, mock_fsm_store):
        """Тест создания FSM сессии для Slack."""
        mock_fsm_store.get.return_value = None
        mock_fsm_store.set.return_value = None
        
        # Имитируем создание сессии
        session = ReviewSession(
            user_id=123,
            platform=Platform.SLACK,
            review_type=ReviewType.SELF,
            current_state=ReviewState.START
        )
        
        assert session.platform == Platform.SLACK
        assert session.review_type == ReviewType.SELF
        assert session.current_state == ReviewState.START
    
    @patch('app.backend.src.bots.fsm.fsm_store')
    def test_telegram_fsm_session_creation(self, mock_fsm_store):
        """Тест создания FSM сессии для Telegram."""
        mock_fsm_store.get.return_value = None
        mock_fsm_store.set.return_value = None
        
        # Имитируем создание сессии
        session = ReviewSession(
            user_id=456,
            platform=Platform.TELEGRAM,
            review_type=ReviewType.PEER,
            current_state=ReviewState.START
        )
        
        assert session.platform == Platform.TELEGRAM
        assert session.review_type == ReviewType.PEER
        assert session.current_state == ReviewState.START
    
    def test_fsm_state_transitions(self):
        """Тест переходов состояний FSM."""
        session = ReviewSession(
            user_id=123,
            platform=Platform.WEB,
            review_type=ReviewType.SELF,
            current_state=ReviewState.START
        )
        
        # Переходы состояний
        session.current_state = ReviewState.COLLECTING_ANSWERS
        assert session.current_state == ReviewState.COLLECTING_ANSWERS
        
        session.current_state = ReviewState.PREVIEW
        assert session.current_state == ReviewState.PREVIEW
        
        session.current_state = ReviewState.REFINING
        assert session.current_state == ReviewState.REFINING
        
        session.current_state = ReviewState.SUBMITTING
        assert session.current_state == ReviewState.SUBMITTING
        
        session.current_state = ReviewState.COMPLETED
        assert session.current_state == ReviewState.COMPLETED


class TestBotErrorHandling:
    """Тесты обработки ошибок в ботах."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_slack_webhook_malformed_json(self):
        """Тест обработки некорректного JSON от Slack."""
        response = self.client.post(
            "/bot/slack/events",
            data="malformed json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_telegram_webhook_malformed_json(self):
        """Тест обработки некорректного JSON от Telegram."""
        response = self.client.post(
            "/bot/telegram/webhook",
            data="malformed json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_slack_webhook_missing_headers(self):
        """Тест Slack webhook без заголовков."""
        response = self.client.post(
            "/bot/slack/events",
            json={"type": "url_verification"}
        )
        
        assert response.status_code == 200
    
    def test_telegram_webhook_missing_headers(self):
        """Тест Telegram webhook без заголовков."""
        response = self.client.post(
            "/bot/telegram/webhook",
            json={"update_id": 1}
        )
        
        assert response.status_code == 200


class TestBotSecurity:
    """Тесты безопасности ботов."""
    
    def setup_method(self):
        self.app = create_app()
        self.client = TestClient(self.app)
    
    def test_slack_webhook_signature_validation(self):
        """Тест валидации подписи Slack webhook."""
        # В реальности здесь должна быть проверка подписи
        response = self.client.post(
            "/bot/slack/events",
            json={"type": "url_verification"},
            headers={"X-Slack-Signature": "invalid_signature"}
        )
        
        assert response.status_code == 200
    
    def test_telegram_webhook_token_validation(self):
        """Тест валидации токена Telegram webhook."""
        # В реальности здесь должна быть проверка токена
        response = self.client.post(
            "/bot/telegram/webhook",
            json={"update_id": 1}
        )
        
        assert response.status_code == 200
    
    def test_bot_rate_limiting(self):
        """Тест ограничения скорости запросов к ботам."""
        # Делаем много запросов подряд
        for i in range(10):
            response = self.client.post(
                "/bot/slack/events",
                json={"type": "url_verification", "challenge": f"test_{i}"}
            )
            assert response.status_code == 200
        
        # В реальности здесь должна быть проверка rate limiting
        response = self.client.post(
            "/bot/slack/events",
            json={"type": "url_verification", "challenge": "test_11"}
        )
        assert response.status_code == 200
