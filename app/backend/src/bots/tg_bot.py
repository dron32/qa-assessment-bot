from __future__ import annotations

import logging
import os
from typing import Any, Dict

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fastapi import APIRouter, Request, HTTPException

from .fsm import ReviewSession, ReviewState, fsm_store
from ..llm.client import LlmClient

logger = logging.getLogger(__name__)

# FastAPI router для вебхуков
router = APIRouter(prefix="/telegram")

# Глобальная переменная для приложения (в продакшене - DI)
tg_app: Application | None = None


async def start_self_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    session = ReviewSession(
        user_id=user_id,
        platform="telegram",
        review_type="self"
    )
    session.state = ReviewState.SELECTING_CYCLE
    fsm_store.save_session(session)
    
    await update.message.reply_text("🚀 Начинаем самооценку! Выберите цикл оценки или введите 'текущий' для активного.")


async def start_peer_review(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("❌ Укажите username: `/peer_review @username`")
        return
    
    username = context.args[0].replace("@", "")
    
    session = ReviewSession(
        user_id=user_id,
        platform="telegram",
        review_type="peer",
        subject_id=username
    )
    session.state = ReviewState.SELECTING_CYCLE
    fsm_store.save_session(session)
    
    await update.message.reply_text(f"👥 Начинаем оценку коллеги @{username}! Выберите цикл оценки.")


async def generate_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.effective_user.id)
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("❌ Укажите username: `/summary @username`")
        return
    
    username = context.args[0].replace("@", "")
    
    # Быстрый ответ
    await update.message.reply_text(f"📊 Генерирую сводку для @{username}...")
    
    try:
        llm = LlmClient()
        result = llm.generate_summary(
            user_context=f"tg_user:{username}",
            trace_id=f"tg-sum-{user_id}-{username}"
        )
        
        summary_text = f"""
*Сильные стороны:*
{chr(10).join(f"• {s}" for s in result.strengths)}

*Зоны роста:*
{chr(10).join(f"• {s}" for s in result.areas_for_growth)}

*Следующие шаги:*
{chr(10).join(f"• {s}" for s in result.next_steps)}
"""
        await update.message.reply_text(summary_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        await update.message.reply_text("❌ Ошибка генерации сводки. Попробуйте позже.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка текстовых сообщений для FSM"""
    user_id = str(update.effective_user.id)
    text = update.message.text.lower()
    
    session = fsm_store.get_session(user_id, "telegram")
    if not session:
        await update.message.reply_text("👋 Привет! Используйте команды /self_review, /peer_review @user или /summary @user")
        return
    
    if session.state == ReviewState.SELECTING_CYCLE:
        if "текущий" in text or "current" in text:
            session.cycle_id = 1  # Заглушка
            session.state = ReviewState.ANSWERING_COMPETENCIES
            fsm_store.save_session(session)
            await update.message.reply_text("✅ Выбран текущий цикл. Начинаем с первой компетенции: *Аналитическое мышление*", parse_mode="Markdown")
        else:
            await update.message.reply_text("❓ Введите 'текущий' для активного цикла оценки")
    
    elif session.state == ReviewState.ANSWERING_COMPETENCIES:
        # Сохраняем ответ
        competency = "analytical_thinking"  # Заглушка
        session.answers[competency] = text
        fsm_store.save_session(session)
        
        if len(session.answers) >= 3:  # Заглушка: 3 компетенции
            session.state = ReviewState.PREVIEW
            fsm_store.save_session(session)
            await update.message.reply_text("📝 Все ответы собраны! Введите 'предпросмотр' для просмотра или 'рефакторинг' для улучшения.")
        else:
            await update.message.reply_text("✅ Ответ сохранён. Следующая компетенция: *Качество баг-репортов*", parse_mode="Markdown")
    
    elif session.state == ReviewState.PREVIEW:
        if "рефакторинг" in text or "refine" in text:
            session.state = ReviewState.REFINING
            fsm_store.save_session(session)
            
            # LLM рефакторинг
            try:
                llm = LlmClient()
                all_text = " ".join(session.answers.values())
                result = llm.refine_text(text=all_text, trace_id=f"tg-refine-{user_id}")
                
                await update.message.reply_text(
                    f"✨ Улучшенная версия:\n{result.refined}\n\nПодсказки:\n" + 
                    "\n".join(f"• {hint}" for hint in result.improvement_hints)
                )
                
                session.state = ReviewState.SUBMITTED
                fsm_store.save_session(session)
                await update.message.reply_text("🎉 Оценка завершена и сохранена!")
                
            except Exception as e:
                logger.error(f"Refinement failed: {e}")
                await update.message.reply_text("❌ Ошибка рефакторинга. Оценка сохранена как есть.")
                session.state = ReviewState.SUBMITTED
                fsm_store.save_session(session)
        
        elif "отправить" in text or "submit" in text:
            session.state = ReviewState.SUBMITTED
            fsm_store.save_session(session)
            await update.message.reply_text("🎉 Оценка отправлена!")
        
        else:
            # Показываем предпросмотр
            preview = "\n".join(f"*{k}:* {v}" for k, v in session.answers.items())
            await update.message.reply_text(f"📋 Предпросмотр:\n{preview}\n\nВведите 'рефакторинг' или 'отправить'", parse_mode="Markdown")


def create_telegram_app() -> Application | None:
    """Создание Telegram приложения"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token and token != "dummy-token":
        app = Application.builder().token(token).build()
        
        # Команды
        app.add_handler(CommandHandler("self_review", start_self_review))
        app.add_handler(CommandHandler("peer_review", start_peer_review))
        app.add_handler(CommandHandler("summary", generate_summary))
        
        # Обработка текстовых сообщений
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        return app
    return None


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Вебхук для Telegram"""
    global tg_app
    
    if not tg_app:
        tg_app = create_telegram_app()
    
    if not tg_app:
        return {"ok": True, "message": "Telegram bot not configured"}
    
    try:
        body = await request.json()
        update = Update.de_json(body, tg_app.bot)
        
        if update:
            await tg_app.process_update(update)
        
        return {"ok": True}
    
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
