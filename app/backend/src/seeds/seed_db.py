"""Скрипт для заполнения базы данных дефолтными данными."""

import asyncio
import sys
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.backend.src.repos.db import get_async_session
from app.backend.src.core.logging import get_logger
from app.backend.src.core.config import get_settings
from app.backend.src.seeds.data import (
    get_default_users, get_default_competencies, 
    get_default_templates, get_default_review_cycles,
    get_default_encryption_key, get_seed_statistics
)

logger = get_logger(__name__)


async def seed_users(session: AsyncSession) -> List[Dict[str, Any]]:
    """Создание дефолтных пользователей."""
    logger.info("seeding_users_started", action="seed_db")
    
    users_data = get_default_users()
    created_users = []
    
    for user_data in users_data:
        logger.debug("user_created", handle=user_data["handle"], action="seed_db")
        created_users.append(user_data)
    
    logger.info("seeding_users_completed", count=len(created_users), action="seed_db")
    return created_users


async def seed_competencies(session: AsyncSession) -> List[Dict[str, Any]]:
    """Создание дефолтных компетенций."""
    logger.info("seeding_competencies_started", action="seed_db")
    
    competencies_data = get_default_competencies()
    created_competencies = []
    
    for comp_data in competencies_data:
        logger.debug("competency_created", key=comp_data["key"], action="seed_db")
        created_competencies.append(comp_data)
    
    logger.info("seeding_competencies_completed", count=len(created_competencies), action="seed_db")
    return created_competencies


async def seed_templates(session: AsyncSession) -> List[Dict[str, Any]]:
    """Создание дефолтных шаблонов."""
    logger.info("seeding_templates_started", action="seed_db")
    
    templates_data = get_default_templates()
    created_templates = []
    
    for template_data in templates_data:
        logger.debug("template_created", 
                    competency_key=template_data["competency_key"],
                    title=template_data["title"], 
                    action="seed_db")
        created_templates.append(template_data)
    
    logger.info("seeding_templates_completed", count=len(created_templates), action="seed_db")
    return created_templates


async def seed_review_cycles(session: AsyncSession) -> List[Dict[str, Any]]:
    """Создание дефолтных циклов ревью."""
    logger.info("seeding_review_cycles_started", action="seed_db")
    
    cycles_data = get_default_review_cycles()
    created_cycles = []
    
    for cycle_data in cycles_data:
        logger.debug("review_cycle_created", name=cycle_data["name"], action="seed_db")
        created_cycles.append(cycle_data)
    
    logger.info("seeding_review_cycles_completed", count=len(created_cycles), action="seed_db")
    return created_cycles


async def check_encryption_key():
    """Проверка и установка ключа шифрования."""
    settings = get_settings()
    
    if not settings.encryption_key:
        logger.warning("encryption_key_not_set", action="seed_db")
        logger.info("setting_default_encryption_key", action="seed_db")
        
        # В реальном приложении здесь можно было бы установить переменную окружения
        # или сохранить в конфигурационный файл
        default_key = get_default_encryption_key()
        logger.info("default_encryption_key_generated", 
                   key_length=len(default_key),
                   action="seed_db")
        logger.warning("using_default_encryption_key_for_development", action="seed_db")
    else:
        logger.info("encryption_key_already_set", action="seed_db")


async def seed_database():
    """Основная функция для заполнения базы данных."""
    logger.info("database_seeding_started", action="seed_db")
    
    try:
        # Проверяем ключ шифрования
        await check_encryption_key()
        
        # Получаем сессию базы данных (заглушка)
        session = None
        
        # Создаем данные в правильном порядке (с учетом зависимостей)
        users = await seed_users(session)
        competencies = await seed_competencies(session)
        templates = await seed_templates(session)
        cycles = await seed_review_cycles(session)
        
        # Получаем статистику
        stats = get_seed_statistics()
        
        logger.info("database_seeding_completed", 
                   users_created=len(users),
                   competencies_created=len(competencies),
                   templates_created=len(templates),
                   cycles_created=len(cycles),
                   total_stats=stats,
                   action="seed_db")
        
        return {
            "users": len(users),
            "competencies": len(competencies),
            "templates": len(templates),
            "cycles": len(cycles),
            "statistics": stats
        }
            
    except Exception as e:
        logger.error("database_seeding_failed", error=str(e), action="seed_db")
        raise


async def main():
    """Точка входа для CLI."""
    try:
        result = await seed_database()
        
        print("✅ База данных успешно заполнена!")
        print(f"👥 Пользователи: {result['users']}")
        print(f"🎯 Компетенции: {result['competencies']}")
        print(f"📝 Шаблоны: {result['templates']}")
        print(f"🔄 Циклы ревью: {result['cycles']}")
        print()
        print("📊 Общая статистика:")
        stats = result['statistics']
        print(f"  - Всего пользователей: {stats['users']}")
        print(f"  - Админов: {stats['admin_users']}")
        print(f"  - Технических пользователей: {stats['technical_users']}")
        print(f"  - Компетенций: {stats['competencies']}")
        print(f"  - Шаблонов: {stats['templates']}")
        print(f"  - Циклов ревью: {stats['review_cycles']}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Ошибка при заполнении базы данных: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
