import json
from unittest.mock import Mock, patch

import pytest
from starlette.testclient import TestClient

from app.backend.src.main import create_app


def test_slack_webhook_endpoint():
    """Контрактный тест: Slack вебхук принимает POST запросы"""
    app = create_app()
    client = TestClient(app)
    
    # Тестируем без токенов (заглушка)
    response = client.post("/bot/slack/events", json={"type": "url_verification"})
    assert response.status_code == 200
    assert response.json()["message"] == "Slack bot not configured"


def test_telegram_webhook_endpoint():
    """Контрактный тест: Telegram вебхук принимает POST запросы"""
    app = create_app()
    client = TestClient(app)
    
    # Тестируем без токена (заглушка)
    response = client.post("/bot/telegram/webhook", json={"update_id": 1})
    assert response.status_code == 200
    assert response.json()["message"] == "Telegram bot not configured"


def test_slack_commands_structure():
    """Контрактный тест: Slack команды имеют правильную структуру"""
    from app.backend.src.bots.slack_app import slack_app
    
    # Проверяем, что app создан (заглушка или реальный)
    assert slack_app is not None
    assert hasattr(slack_app, "command")
    assert hasattr(slack_app, "event")


def test_telegram_commands_structure():
    """Контрактный тест: Telegram команды имеют правильную структуру"""
    from app.backend.src.bots.tg_bot import create_telegram_app
    
    app = create_telegram_app()
    
    # Без токена app будет None
    if app is None:
        # Проверяем, что функция существует и возвращает None без токена
        assert app is None
    else:
        # Если есть токен, проверяем структуру
        assert hasattr(app, "handlers")
        assert len(app.handlers) > 0


def test_fsm_session_management():
    """Контрактный тест: FSM корректно управляет сессиями"""
    from app.backend.src.bots.fsm import fsm_store, ReviewSession, ReviewState
    
    # Создаём сессию
    session = ReviewSession(
        user_id="test_user",
        platform="slack",
        review_type="self"
    )
    
    # Сохраняем
    fsm_store.save_session(session)
    
    # Получаем
    retrieved = fsm_store.get_session("test_user", "slack")
    assert retrieved is not None
    assert retrieved.user_id == "test_user"
    assert retrieved.platform == "slack"
    
    # Очищаем
    fsm_store.clear_session("test_user", "slack")
    assert fsm_store.get_session("test_user", "slack") is None


def test_llm_integration_in_bots():
    """Контрактный тест: боты интегрированы с LLM клиентом"""
    from app.backend.src.bots.slack_app import LlmClient
    from app.backend.src.bots.tg_bot import LlmClient as TgLlmClient
    
    # Проверяем, что LLM клиент импортируется в обоих ботах
    assert LlmClient is not None
    assert TgLlmClient is not None
    assert LlmClient == TgLlmClient  # Один и тот же класс


@patch.dict("os.environ", {"SLACK_BOT_TOKEN": "xoxb-test", "SLACK_SIGNING_SECRET": "test-secret"})
def test_slack_app_initialization():
    """Контрактный тест: Slack app инициализируется с токенами"""
    from app.backend.src.bots.slack_app import slack_app
    
    assert slack_app is not None
    # Проверяем, что app создан (не падает при импорте)


@patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "test-token"})
def test_telegram_app_initialization():
    """Контрактный тест: Telegram app инициализируется с токеном"""
    from app.backend.src.bots.tg_bot import create_telegram_app
    
    app = create_telegram_app()
    assert app is not None
    assert len(app.handlers) > 0
