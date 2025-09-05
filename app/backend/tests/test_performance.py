"""Тесты производительности и кэширования."""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from app.backend.src.core.cache import CacheManager, TemplateCache, EmbeddingsCache, LLMResponseCache
from app.backend.src.llm.profiles import LlmProfileManager, get_fast_profile, get_smart_profile
from app.backend.src.llm.fallback import FallbackManager, FallbackResult, FallbackStrategy


class TestCachePerformance:
    """Тесты производительности кэша."""
    
    @pytest.mark.asyncio
    async def test_cache_set_performance(self):
        """Тест производительности записи в кэш."""
        cache = CacheManager()
        await cache.connect()
        
        start_time = time.time()
        
        # Выполняем 100 операций записи
        for i in range(100):
            await cache.set(f"test_key_{i}", {"data": f"value_{i}"}, ttl=60)
        
        duration = (time.time() - start_time) * 1000
        avg_time = duration / 100
        
        # Проверяем, что среднее время < 1ms
        assert avg_time < 1.0, f"Average cache set time {avg_time:.2f}ms is too slow"
        
        await cache.disconnect()
    
    @pytest.mark.asyncio
    async def test_cache_get_performance(self):
        """Тест производительности чтения из кэша."""
        cache = CacheManager()
        await cache.connect()
        
        # Подготавливаем данные
        await cache.set("test_key", {"data": "test_value"}, ttl=60)
        
        start_time = time.time()
        
        # Выполняем 100 операций чтения
        for _ in range(100):
            result = await cache.get("test_key")
            assert result is not None
        
        duration = (time.time() - start_time) * 1000
        avg_time = duration / 100
        
        # Проверяем, что среднее время < 0.5ms
        assert avg_time < 0.5, f"Average cache get time {avg_time:.2f}ms is too slow"
        
        await cache.disconnect()
    
    @pytest.mark.asyncio
    async def test_template_cache_performance(self):
        """Тест производительности кэша шаблонов."""
        # Мокаем Redis для изоляции теста
        with patch('app.backend.src.core.cache.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value={"template": "test"})
            mock_cache.set = AsyncMock(return_value=True)
            
            start_time = time.time()
            
            # Выполняем 50 операций
            for i in range(50):
                await TemplateCache.get_template(f"competency_{i}")
            
            duration = (time.time() - start_time) * 1000
            avg_time = duration / 50
            
            # Проверяем производительность
            assert avg_time < 1.0, f"Average template cache time {avg_time:.2f}ms is too slow"
    
    @pytest.mark.asyncio
    async def test_embeddings_cache_performance(self):
        """Тест производительности кэша эмбеддингов."""
        with patch('app.backend.src.core.cache.cache_manager') as mock_cache:
            mock_cache.get = AsyncMock(return_value=[0.1, 0.2, 0.3])
            mock_cache.set = AsyncMock(return_value=True)
            
            start_time = time.time()
            
            # Выполняем 30 операций
            for i in range(30):
                await EmbeddingsCache.get_embeddings(f"text_{i}")
            
            duration = (time.time() - start_time) * 1000
            avg_time = duration / 30
            
            # Проверяем производительность
            assert avg_time < 1.0, f"Average embeddings cache time {avg_time:.2f}ms is too slow"


class TestLLMProfiles:
    """Тесты профилей LLM."""
    
    def test_fast_profile_configuration(self):
        """Тест конфигурации быстрого профиля."""
        profile = get_fast_profile()
        
        assert profile.model == "gpt-4o-mini"
        assert profile.temperature == 0.3
        assert profile.max_tokens == 500
        assert profile.timeout_seconds == 2.0
        assert profile.use_cache is True
        assert profile.fallback_enabled is True
        assert profile.fallback_timeout == 2.0
    
    def test_smart_profile_configuration(self):
        """Тест конфигурации умного профиля."""
        profile = get_smart_profile()
        
        assert profile.model == "gpt-4o"
        assert profile.temperature == 0.7
        assert profile.max_tokens == 2000
        assert profile.timeout_seconds == 10.0
        assert profile.use_cache is True
        assert profile.fallback_enabled is True
        assert profile.fallback_timeout == 5.0
    
    def test_profile_manager(self):
        """Тест менеджера профилей."""
        manager = LlmProfileManager()
        
        # Проверяем, что все профили доступны
        assert manager.get_fast_profile() is not None
        assert manager.get_smart_profile() is not None
        assert manager.get_balanced_profile() is not None
        
        # Проверяем список профилей
        profiles = manager.list_profiles()
        assert "fast" in profiles
        assert "smart" in profiles
        assert "balanced" in profiles


class TestFallbackMechanisms:
    """Тесты механизмов фолбэка."""
    
    @pytest.mark.asyncio
    async def test_quick_fallback_performance(self):
        """Тест производительности быстрого фолбэка."""
        fallback_manager = FallbackManager()
        
        async def slow_operation():
            await asyncio.sleep(2.5)  # Превышаем таймаут
            return {"result": "slow"}
        
        async def quick_operation():
            await asyncio.sleep(0.1)
            return {"result": "quick"}
        
        start_time = time.time()
        
        result = await fallback_manager.execute_with_fallback(
            main_operation=slow_operation,
            fallback_timeout=2.0,
            quick_response_generator=quick_operation
        )
        
        duration = (time.time() - start_time) * 1000
        
        # Проверяем, что фолбэк сработал быстро
        assert duration < 3000, f"Fallback took {duration:.2f}ms, should be < 3000ms"
        assert result.success is True
        assert result.strategy == FallbackStrategy.QUICK_RESPONSE
        assert result.is_quick_response is True
    
    @pytest.mark.asyncio
    async def test_cached_fallback(self):
        """Тест кэшированного фолбэка."""
        fallback_manager = FallbackManager()
        
        async def failing_operation():
            raise Exception("Simulated failure")
        
        # Мокаем кэш
        with patch.object(fallback_manager, '_get_cached_response') as mock_cache:
            mock_cache.return_value = {"result": "cached"}
            
            result = await fallback_manager.execute_with_fallback(
                main_operation=failing_operation,
                cache_key="test_key"
            )
            
            assert result.success is True
            assert result.strategy == FallbackStrategy.CACHED_RESPONSE
            assert result.response == {"result": "cached"}
    
    @pytest.mark.asyncio
    async def test_template_fallback(self):
        """Тест шаблонного фолбэка."""
        fallback_manager = FallbackManager()
        
        async def failing_operation():
            raise Exception("Simulated failure")
        
        template_response = {"error": "Service unavailable"}
        
        result = await fallback_manager.execute_with_fallback(
            main_operation=failing_operation,
            template_response=template_response
        )
        
        assert result.success is True
        assert result.strategy == FallbackStrategy.TEMPLATE_RESPONSE
        assert result.response == template_response
    
    @pytest.mark.asyncio
    async def test_error_fallback(self):
        """Тест фолбэка с ошибкой."""
        fallback_manager = FallbackManager()
        
        async def failing_operation():
            raise Exception("Simulated failure")
        
        result = await fallback_manager.execute_with_fallback(
            main_operation=failing_operation
        )
        
        assert result.success is False
        assert result.strategy == FallbackStrategy.ERROR_RESPONSE
        assert "error" in result.response


class TestConcurrentPerformance:
    """Тесты конкурентной производительности."""
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self):
        """Тест конкурентных операций с кэшем."""
        cache = CacheManager()
        await cache.connect()
        
        async def cache_operation(i):
            await cache.set(f"concurrent_key_{i}", {"data": f"value_{i}"}, ttl=60)
            return await cache.get(f"concurrent_key_{i}")
        
        start_time = time.time()
        
        # Запускаем 20 конкурентных операций
        tasks = [cache_operation(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        duration = (time.time() - start_time) * 1000
        
        # Проверяем, что все операции выполнились
        assert len(results) == 20
        assert all(result is not None for result in results)
        
        # Проверяем, что конкурентность не сильно замедлила операции
        assert duration < 1000, f"Concurrent operations took {duration:.2f}ms, should be < 1000ms"
        
        await cache.disconnect()
    
    @pytest.mark.asyncio
    async def test_concurrent_fallback_operations(self):
        """Тест конкурентных операций фолбэка."""
        fallback_manager = FallbackManager()
        
        async def fallback_operation(i):
            async def main_op():
                await asyncio.sleep(1.0)
                return {"result": f"main_{i}"}
            
            async def quick_op():
                await asyncio.sleep(0.1)
                return {"result": f"quick_{i}"}
            
            return await fallback_manager.execute_with_fallback(
                main_operation=main_op,
                fallback_timeout=0.5,
                quick_response_generator=quick_op
            )
        
        start_time = time.time()
        
        # Запускаем 10 конкурентных операций фолбэка
        tasks = [fallback_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        duration = (time.time() - start_time) * 1000
        
        # Проверяем, что все операции выполнились
        assert len(results) == 10
        assert all(result.success for result in results)
        assert all(result.strategy == FallbackStrategy.QUICK_RESPONSE for result in results)
        
        # Проверяем производительность
        assert duration < 2000, f"Concurrent fallback operations took {duration:.2f}ms, should be < 2000ms"


class TestPerformanceMetrics:
    """Тесты метрик производительности."""
    
    def test_p95_calculation(self):
        """Тест расчета P95 метрик."""
        # Симулируем данные времени выполнения
        times = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
        times.sort()
        
        p95_index = int(len(times) * 0.95)
        p95_value = times[p95_index]
        
        assert p95_value == 20  # 95-й процентиль из 20 значений (индекс 19 = значение 20)
    
    @pytest.mark.asyncio
    async def test_performance_benchmark_structure(self):
        """Тест структуры бенчмарка производительности."""
        from app.backend.src.benchmarks.performance import PerformanceBenchmark
        
        benchmark = PerformanceBenchmark()
        
        # Проверяем, что бенчмарк может быть создан
        assert benchmark is not None
        assert benchmark.results == []
        
        # Проверяем метод генерации отчета
        report = benchmark.generate_report()
        assert "error" in report  # Должна быть ошибка, так как нет результатов
