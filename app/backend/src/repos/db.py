from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import get_settings


def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().database_url, future=True, echo=False)


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), expire_on_commit=False, autoflush=False, autocommit=False)


def get_async_session():
    """Контекстный менеджер для получения сессии базы данных."""
    session_maker = get_session_maker()
    return session_maker()




