from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from fastapi import APIRouter, Request

from .fsm import ReviewSession, ReviewState, fsm_store
from ..llm.client import LlmClient

logger = logging.getLogger(__name__)

# FastAPI router для вебхуков
router = APIRouter(prefix="/bot/slack")

# Slack Bolt app - инициализация только при наличии токенов
def create_slack_app():
    token = os.getenv("SLACK_BOT_TOKEN")
    secret = os.getenv("SLACK_SIGNING_SECRET")
    if token and secret and token != "xoxb-dummy":
        return App(token=token, signing_secret=secret)
    return None

# Создаём app только если есть токены
slack_app = create_slack_app()

# Заглушки для команд если нет токенов
if slack_app is None:
    class DummyApp:
        def command(self, cmd):
            def decorator(func):
                return func
            return decorator
        
        def event(self, event):
            def decorator(func):
                return func
            return decorator
    
    slack_app = DummyApp()


@slack_app.command("/self_review")
def handle_self_review(ack, respond, command):
    ack()
    user_id = command["user_id"]
    
    # Создаём сессию
    session = ReviewSession(
        user_id=user_id,
        platform="slack",
        review_type="self"
    )
    session.state = ReviewState.SELECTING_CYCLE
    fsm_store.save_session(session)
    
    # Быстрый ответ ≤5с
    respond("🚀 Начинаем самооценку! Выберите цикл оценки или введите 'текущий' для активного.")


@slack_app.command("/peer_review")
def handle_peer_review(ack, respond, command):
    ack()
    user_id = command["user_id"]
    text = command.get("text", "").strip()
    
    if not text or not text.startswith("<@"):
        respond("❌ Укажите пользователя: `/peer_review @username`")
        return
    
    # Извлекаем user_id из @username
    subject_id = text.replace("<@", "").replace(">", "")
    
    session = ReviewSession(
        user_id=user_id,
        platform="slack",
        review_type="peer",
        subject_id=subject_id
    )
    session.state = ReviewState.SELECTING_CYCLE
    fsm_store.save_session(session)
    
    respond(f"👥 Начинаем оценку коллеги <@{subject_id}>! Выберите цикл оценки.")


@slack_app.command("/summary")
def handle_summary(ack, respond, command):
    ack()
    user_id = command["user_id"]
    text = command.get("text", "").strip()
    
    if not text or not text.startswith("<@"):
        respond("❌ Укажите пользователя: `/summary @username`")
        return
    
    subject_id = text.replace("<@", "").replace(">", "")
    
    # Быстрый ответ + фоновая обработка
    respond(f"📊 Генерирую сводку для <@{subject_id}>...")
    
    # Здесь бы вызвали Celery task для фоновой генерации
    # и отправили бы результат через Slack API
    try:
        llm = LlmClient()
        result = llm.generate_summary(
            user_context=f"slack_user:{subject_id}",
            trace_id=f"slack-sum-{user_id}-{subject_id}"
        )
        
        # Отправляем детальный результат
        summary_text = f"""
*Сильные стороны:*
{chr(10).join(f"• {s}" for s in result.strengths)}

*Зоны роста:*
{chr(10).join(f"• {s}" for s in result.areas_for_growth)}

*Следующие шаги:*
{chr(10).join(f"• {s}" for s in result.next_steps)}
"""
        respond(summary_text)
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        respond("❌ Ошибка генерации сводки. Попробуйте позже.")


@slack_app.event("app_mention")
def handle_mention(event, say):
    """Обработка @mentions для продолжения диалога"""
    user_id = event["user"]
    text = event.get("text", "").lower()
    
    session = fsm_store.get_session(user_id, "slack")
    if not session:
        say("👋 Привет! Используйте команды `/self_review`, `/peer_review @user` или `/summary @user`")
        return
    
    if session.state == ReviewState.SELECTING_CYCLE:
        if "текущий" in text or "current" in text:
            session.cycle_id = 1  # Заглушка
            session.state = ReviewState.ANSWERING_COMPETENCIES
            fsm_store.save_session(session)
            say("✅ Выбран текущий цикл. Начинаем с первой компетенции: *Аналитическое мышление*")
        else:
            say("❓ Введите 'текущий' для активного цикла оценки")
    
    elif session.state == ReviewState.ANSWERING_COMPETENCIES:
        # Сохраняем ответ
        competency = "analytical_thinking"  # Заглушка
        session.answers[competency] = text
        fsm_store.save_session(session)
        
        if len(session.answers) >= 3:  # Заглушка: 3 компетенции
            session.state = ReviewState.PREVIEW
            fsm_store.save_session(session)
            say("📝 Все ответы собраны! Введите 'предпросмотр' для просмотра или 'рефакторинг' для улучшения.")
        else:
            say("✅ Ответ сохранён. Следующая компетенция: *Качество баг-репортов*")
    
    elif session.state == ReviewState.PREVIEW:
        if "рефакторинг" in text or "refine" in text:
            session.state = ReviewState.REFINING
            fsm_store.save_session(session)
            
            # LLM рефакторинг
            try:
                llm = LlmClient()
                all_text = " ".join(session.answers.values())
                result = llm.refine_text(text=all_text, trace_id=f"slack-refine-{user_id}")
                
                say(f"✨ Улучшенная версия:\n{result.refined}\n\nПодсказки:\n" + 
                    "\n".join(f"• {hint}" for hint in result.improvement_hints))
                
                session.state = ReviewState.SUBMITTED
                fsm_store.save_session(session)
                say("🎉 Оценка завершена и сохранена!")
                
            except Exception as e:
                logger.error(f"Refinement failed: {e}")
                say("❌ Ошибка рефакторинга. Оценка сохранена как есть.")
                session.state = ReviewState.SUBMITTED
                fsm_store.save_session(session)
        
        elif "отправить" in text or "submit" in text:
            session.state = ReviewState.SUBMITTED
            fsm_store.save_session(session)
            say("🎉 Оценка отправлена!")
        
        else:
            # Показываем предпросмотр
            preview = "\n".join(f"*{k}:* {v}" for k, v in session.answers.items())
            say(f"📋 Предпросмотр:\n{preview}\n\nВведите 'рефакторинг' или 'отправить'")


# FastAPI интеграция
handler = SlackRequestHandler(slack_app) if hasattr(slack_app, 'client') else None


@router.post("/events")
async def slack_events(request: Request):
    if handler:
        return await handler.handle(request)
    return {"ok": True, "message": "Slack bot not configured"}
