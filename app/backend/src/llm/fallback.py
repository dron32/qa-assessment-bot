"""Система фолбэка для LLM ответов."""

import asyncio
import time
from typing import Any, Dict, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum

from ..core.logging import get_logger
from ..core.metrics import LLMMetrics
from .profiles import get_fast_profile, get_smart_profile, LlmProfile

logger = get_logger(__name__)


class FallbackStrategy(Enum):
    """Стратегии фолбэка."""
    QUICK_RESPONSE = "quick_response"      # Быстрый ответ + дополнение
    CACHED_RESPONSE = "cached_response"    # Ответ из кэша
    TEMPLATE_RESPONSE = "template_response"  # Шаблонный ответ
    ERROR_RESPONSE = "error_response"      # Сообщение об ошибке


@dataclass
class FallbackResult:
    """Результат фолбэка."""
    success: bool
    response: Any
    strategy: FallbackStrategy
    latency_ms: float
    is_quick_response: bool = False
    background_task_id: Optional[str] = None


class FallbackManager:
    """Менеджер фолбэка для LLM."""
    
    def __init__(self):
        self._background_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_with_fallback(
        self,
        main_operation: Callable[[], Awaitable[Any]],
        fallback_timeout: float = 3.0,
        quick_response_generator: Optional[Callable[[], Awaitable[Any]]] = None,
        cache_key: Optional[str] = None,
        template_response: Optional[Any] = None
    ) -> FallbackResult:
        """
        Выполнение операции с фолбэком.
        
        Args:
            main_operation: Основная операция
            fallback_timeout: Таймаут для фолбэка
            quick_response_generator: Генератор быстрого ответа
            cache_key: Ключ для поиска в кэше
            template_response: Шаблонный ответ
        """
        start_time = time.time()
        
        try:
            # Пытаемся выполнить основную операцию с таймаутом
            result = await asyncio.wait_for(main_operation(), timeout=fallback_timeout)
            
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info("llm_operation_success",
                       latency_ms=round(latency_ms, 2),
                       action="llm_fallback")
            
            return FallbackResult(
                success=True,
                response=result,
                strategy=FallbackStrategy.QUICK_RESPONSE,
                latency_ms=latency_ms
            )
            
        except asyncio.TimeoutError:
            latency_ms = (time.time() - start_time) * 1000
            
            logger.warning("llm_operation_timeout",
                          timeout=fallback_timeout,
                          latency_ms=round(latency_ms, 2),
                          action="llm_fallback")
            
            # Пытаемся получить быстрый ответ
            if quick_response_generator:
                return await self._handle_quick_response(
                    quick_response_generator, 
                    main_operation,
                    latency_ms
                )
            
            # Пытаемся получить ответ из кэша
            if cache_key:
                cached_result = await self._get_cached_response(cache_key)
                if cached_result:
                    return FallbackResult(
                        success=True,
                        response=cached_result,
                        strategy=FallbackStrategy.CACHED_RESPONSE,
                        latency_ms=latency_ms
                    )
            
            # Возвращаем шаблонный ответ
            if template_response:
                return FallbackResult(
                    success=True,
                    response=template_response,
                    strategy=FallbackStrategy.TEMPLATE_RESPONSE,
                    latency_ms=latency_ms
                )
            
            # Последний резерв - сообщение об ошибке
            return FallbackResult(
                success=False,
                response={"error": "Operation timeout", "message": "Попробуйте позже"},
                strategy=FallbackStrategy.ERROR_RESPONSE,
                latency_ms=latency_ms
            )
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            logger.error("llm_operation_failed",
                        error=str(e),
                        latency_ms=round(latency_ms, 2),
                        action="llm_fallback")
            
            # Пытаемся получить ответ из кэша при ошибке
            if cache_key:
                cached_result = await self._get_cached_response(cache_key)
                if cached_result:
                    return FallbackResult(
                        success=True,
                        response=cached_result,
                        strategy=FallbackStrategy.CACHED_RESPONSE,
                        latency_ms=latency_ms
                    )
            
            return FallbackResult(
                success=False,
                response={"error": str(e), "message": "Произошла ошибка"},
                strategy=FallbackStrategy.ERROR_RESPONSE,
                latency_ms=latency_ms
            )
    
    async def _handle_quick_response(
        self,
        quick_generator: Callable[[], Awaitable[Any]],
        main_operation: Callable[[], Awaitable[Any]],
        latency_ms: float
    ) -> FallbackResult:
        """Обработка быстрого ответа с фоновой задачей."""
        try:
            # Генерируем быстрый ответ
            quick_result = await quick_generator()
            
            # Запускаем фоновую задачу для полного ответа
            task_id = f"fallback_{int(time.time() * 1000)}"
            background_task = asyncio.create_task(
                self._background_operation(main_operation, task_id)
            )
            self._background_tasks[task_id] = background_task
            
            logger.info("quick_response_generated",
                       task_id=task_id,
                       latency_ms=round(latency_ms, 2),
                       action="llm_fallback")
            
            return FallbackResult(
                success=True,
                response=quick_result,
                strategy=FallbackStrategy.QUICK_RESPONSE,
                latency_ms=latency_ms,
                is_quick_response=True,
                background_task_id=task_id
            )
            
        except Exception as e:
            logger.error("quick_response_failed",
                        error=str(e),
                        action="llm_fallback")
            
            return FallbackResult(
                success=False,
                response={"error": str(e), "message": "Не удалось сгенерировать быстрый ответ"},
                strategy=FallbackStrategy.ERROR_RESPONSE,
                latency_ms=latency_ms
            )
    
    async def _background_operation(
        self,
        operation: Callable[[], Awaitable[Any]],
        task_id: str
    ) -> None:
        """Выполнение операции в фоне."""
        try:
            result = await operation()
            
            logger.info("background_operation_completed",
                       task_id=task_id,
                       action="llm_fallback")
            
            # Здесь можно было бы отправить результат через WebSocket
            # или сохранить в кэш для последующего получения
            
        except Exception as e:
            logger.error("background_operation_failed",
                        task_id=task_id,
                        error=str(e),
                        action="llm_fallback")
        
        finally:
            # Удаляем задачу из списка
            self._background_tasks.pop(task_id, None)
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Получение ответа из кэша."""
        try:
            from ..core.cache import LLMResponseCache
            
            # Пытаемся получить из кэша (упрощенная версия)
            # В реальном приложении здесь был бы вызов кэша
            logger.debug("attempting_cache_lookup",
                        cache_key=cache_key,
                        action="llm_fallback")
            
            return None  # Заглушка
            
        except Exception as e:
            logger.error("cache_lookup_failed",
                        cache_key=cache_key,
                        error=str(e),
                        action="llm_fallback")
            return None
    
    async def get_background_task_result(self, task_id: str) -> Optional[Any]:
        """Получение результата фоновой задачи."""
        task = self._background_tasks.get(task_id)
        if task and task.done():
            try:
                result = await task
                return result
            except Exception as e:
                logger.error("background_task_result_failed",
                            task_id=task_id,
                            error=str(e),
                            action="llm_fallback")
                return None
        
        return None
    
    def get_active_tasks(self) -> Dict[str, str]:
        """Получение списка активных фоновых задач."""
        return {
            task_id: "running" if not task.done() else "completed"
            for task_id, task in self._background_tasks.items()
        }


# Глобальный экземпляр менеджера фолбэка
fallback_manager = FallbackManager()


class LlmWithFallback:
    """LLM клиент с поддержкой фолбэка."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.fallback_manager = fallback_manager
    
    async def generate_with_fallback(
        self,
        prompt: str,
        profile_type: str = "balanced",
        fallback_timeout: float = 3.0
    ) -> FallbackResult:
        """Генерация с фолбэком."""
        
        # Получаем профиль
        from .profiles import get_profile
        profile = get_profile(profile_type)
        if not profile:
            profile = get_profile("balanced")
        
        # Основная операция
        async def main_operation():
            return await self.llm_client.generate_competency_analysis(
                user_response=prompt,
                competency="test",
                profile=profile
            )
        
        # Быстрая операция
        async def quick_operation():
            fast_profile = get_fast_profile()
            return await self.llm_client.generate_competency_analysis(
                user_response=prompt,
                competency="test", 
                profile=fast_profile
            )
        
        # Шаблонный ответ
        template_response = {
            "analysis": "Анализ временно недоступен. Попробуйте позже.",
            "score": 3,
            "recommendations": ["Попробуйте переформулировать ответ", "Обратитесь к менеджеру"]
        }
        
        return await self.fallback_manager.execute_with_fallback(
            main_operation=main_operation,
            fallback_timeout=fallback_timeout,
            quick_response_generator=quick_operation,
            template_response=template_response
        )
    
    async def generate_summary_with_fallback(
        self,
        user_id: int,
        cycle_id: Optional[int] = None,
        fallback_timeout: float = 5.0
    ) -> FallbackResult:
        """Генерация сводки с фолбэком."""
        
        # Основная операция
        async def main_operation():
            smart_profile = get_smart_profile()
            return await self.llm_client.generate_summary(
                user_id=user_id,
                cycle_id=cycle_id,
                profile=smart_profile
            )
        
        # Быстрая операция
        async def quick_operation():
            fast_profile = get_fast_profile()
            return await self.llm_client.generate_summary(
                user_id=user_id,
                cycle_id=cycle_id,
                profile=fast_profile
            )
        
        # Шаблонный ответ
        template_response = {
            "summary": "Сводка временно недоступна. Попробуйте позже.",
            "key_points": ["Анализ в процессе", "Результаты будут доступны позже"],
            "recommendations": ["Обратитесь к менеджеру", "Попробуйте позже"]
        }
        
        return await self.fallback_manager.execute_with_fallback(
            main_operation=main_operation,
            fallback_timeout=fallback_timeout,
            quick_response_generator=quick_operation,
            template_response=template_response
        )


def create_llm_with_fallback(llm_client) -> LlmWithFallback:
    """Создание LLM клиента с фолбэком."""
    return LlmWithFallback(llm_client)
