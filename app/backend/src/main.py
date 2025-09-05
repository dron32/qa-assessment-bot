import os
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

from .core.logging import configure_json_logging, get_logger
from .core.config import get_settings
from .core.metrics import MetricsMiddleware, get_metrics, update_system_metrics
from .core.cache import cache_manager, warmup_cache, get_cache_stats
from .api.routes import router as api_router
from .bots.slack_app import router as slack_router
from .bots.tg_bot import router as telegram_router

logger = get_logger(__name__)


def setup_sentry():
    """Настройка Sentry для мониторинга ошибок."""
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enabling_instrumentations=False),
                CeleryIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=settings.env,
            release="qa-assessment@0.1.0",
        )
        logger.info("sentry_initialized", action="sentry_setup")
    else:
        logger.warning("sentry_dsn_not_set", action="sentry_setup")


def create_app() -> FastAPI:
    """Создание FastAPI приложения с observability."""
    configure_json_logging()
    setup_sentry()
    
    app = FastAPI(
        title="QA Assessment API",
        version="0.1.0",
        description="API для самооценки и взаимной оценки QA команды"
    )
    
    # Подогрев кэша при старте
    @app.on_event("startup")
    async def startup_event():
        logger.info("app_startup_started", action="app_startup")
        
        # Подогреваем кэш
        try:
            await warmup_cache()
            logger.info("cache_warmup_completed", action="app_startup")
        except Exception as e:
            logger.error("cache_warmup_failed", error=str(e), action="app_startup")
        
        logger.info("app_startup_completed", action="app_startup")
    
    # Очистка при завершении
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("app_shutdown_started", action="app_shutdown")
        
        # Отключаемся от кэша
        try:
            await cache_manager.disconnect()
            logger.info("cache_disconnected", action="app_shutdown")
        except Exception as e:
            logger.error("cache_disconnect_failed", error=str(e), action="app_shutdown")
        
        logger.info("app_shutdown_completed", action="app_shutdown")
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене ограничить
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Prometheus metrics middleware
    app.add_middleware(MetricsMiddleware)

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        """Health check endpoint."""
        logger.info("healthcheck_requested", action="healthcheck")
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        update_system_metrics()
        return get_metrics()
    
    @app.get("/cache/stats")
    async def cache_stats():
        """Статистика кэша."""
        stats = await get_cache_stats()
        return stats

    # Включаем роутеры
    app.include_router(api_router, prefix="/api")
    app.include_router(slack_router, prefix="/bot")
    app.include_router(telegram_router, prefix="/bot")
    
    logger.info("app_created", action="app_init", version="0.1.0")
    return app


app = create_app()




