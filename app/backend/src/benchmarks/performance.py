"""Микробенчмарки для измерения производительности."""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.backend.src.core.logging import get_logger
from app.backend.src.core.cache import cache_manager, warmup_cache
from app.backend.src.llm.profiles import get_fast_profile, get_smart_profile, get_balanced_profile
from app.backend.src.llm.fallback import fallback_manager

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Результат бенчмарка."""
    operation: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    success_rate: float
    errors: List[str]


class PerformanceBenchmark:
    """Класс для проведения бенчмарков производительности."""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    async def run_benchmark(
        self,
        operation_name: str,
        operation: callable,
        iterations: int = 100,
        warmup_iterations: int = 10
    ) -> BenchmarkResult:
        """Запуск бенчмарка для операции."""
        logger.info("benchmark_started",
                   operation=operation_name,
                   iterations=iterations,
                   action="benchmark")
        
        # Прогрев
        for _ in range(warmup_iterations):
            try:
                await operation()
            except Exception:
                pass
        
        # Основные измерения
        times = []
        errors = []
        start_time = time.time()
        
        for i in range(iterations):
            try:
                iter_start = time.time()
                await operation()
                iter_time = (time.time() - iter_start) * 1000
                times.append(iter_time)
                
            except Exception as e:
                errors.append(str(e))
                logger.debug("benchmark_iteration_failed",
                            operation=operation_name,
                            iteration=i,
                            error=str(e),
                            action="benchmark")
        
        total_time = (time.time() - start_time) * 1000
        
        # Статистика
        if times:
            times.sort()
            result = BenchmarkResult(
                operation=operation_name,
                iterations=iterations,
                total_time_ms=total_time,
                avg_time_ms=statistics.mean(times),
                min_time_ms=min(times),
                max_time_ms=max(times),
                p50_time_ms=times[int(len(times) * 0.5)],
                p95_time_ms=times[int(len(times) * 0.95)],
                p99_time_ms=times[int(len(times) * 0.99)],
                success_rate=(len(times) / iterations) * 100,
                errors=errors
            )
        else:
            result = BenchmarkResult(
                operation=operation_name,
                iterations=iterations,
                total_time_ms=total_time,
                avg_time_ms=0,
                min_time_ms=0,
                max_time_ms=0,
                p50_time_ms=0,
                p95_time_ms=0,
                p99_time_ms=0,
                success_rate=0,
                errors=errors
            )
        
        self.results.append(result)
        
        logger.info("benchmark_completed",
                   operation=operation_name,
                   p95_ms=round(result.p95_time_ms, 2),
                   success_rate=round(result.success_rate, 1),
                   action="benchmark")
        
        return result
    
    async def benchmark_cache_operations(self) -> List[BenchmarkResult]:
        """Бенчмарк операций кэша."""
        results = []
        
        # Подключаемся к кэшу
        await cache_manager.connect()
        
        # Тест записи в кэш
        async def cache_set_operation():
            await cache_manager.set(f"benchmark_key_{int(time.time() * 1000)}", {"test": "data"}, ttl=60)
        
        result = await self.run_benchmark("cache_set", cache_set_operation, iterations=1000)
        results.append(result)
        
        # Тест чтения из кэша
        test_key = "benchmark_read_key"
        await cache_manager.set(test_key, {"test": "data"}, ttl=60)
        
        async def cache_get_operation():
            await cache_manager.get(test_key)
        
        result = await self.run_benchmark("cache_get", cache_get_operation, iterations=1000)
        results.append(result)
        
        # Тест множественного чтения
        keys = [f"benchmark_mget_{i}" for i in range(10)]
        await cache_manager.set_many({key: {"test": f"data_{i}"} for i, key in enumerate(keys)}, ttl=60)
        
        async def cache_mget_operation():
            await cache_manager.get_many(keys)
        
        result = await self.run_benchmark("cache_mget", cache_mget_operation, iterations=500)
        results.append(result)
        
        return results
    
    async def benchmark_llm_profiles(self) -> List[BenchmarkResult]:
        """Бенчмарк профилей LLM."""
        results = []
        
        # Мокаем LLM клиент для тестирования
        class MockLlmClient:
            async def generate_competency_analysis(self, user_response: str, competency: str, profile):
                # Симулируем время выполнения в зависимости от профиля
                if profile.model == "gpt-4o-mini":
                    await asyncio.sleep(0.1)  # Быстрый профиль
                else:
                    await asyncio.sleep(0.5)  # Умный профиль
                
                return {
                    "analysis": f"Analysis of {competency}",
                    "score": 4,
                    "recommendations": ["Test recommendation"]
                }
        
        mock_client = MockLlmClient()
        
        # Тест быстрого профиля
        fast_profile = get_fast_profile()
        async def fast_operation():
            return await mock_client.generate_competency_analysis(
                "Test response", "analytical_thinking", fast_profile
            )
        
        result = await self.run_benchmark("llm_fast_profile", fast_operation, iterations=100)
        results.append(result)
        
        # Тест умного профиля
        smart_profile = get_smart_profile()
        async def smart_operation():
            return await mock_client.generate_competency_analysis(
                "Test response", "analytical_thinking", smart_profile
            )
        
        result = await self.run_benchmark("llm_smart_profile", smart_operation, iterations=50)
        results.append(result)
        
        return results
    
    async def benchmark_fallback_mechanisms(self) -> List[BenchmarkResult]:
        """Бенчмарк механизмов фолбэка."""
        results = []
        
        # Тест быстрого фолбэка
        async def quick_fallback_operation():
            async def main_op():
                await asyncio.sleep(2.5)  # Превышаем таймаут
                return {"result": "main"}
            
            async def quick_op():
                await asyncio.sleep(0.1)
                return {"result": "quick"}
            
            return await fallback_manager.execute_with_fallback(
                main_operation=main_op,
                fallback_timeout=2.0,
                quick_response_generator=quick_op
            )
        
        result = await self.run_benchmark("fallback_quick", quick_fallback_operation, iterations=50)
        results.append(result)
        
        # Тест кэшированного фолбэка
        async def cached_fallback_operation():
            async def main_op():
                await asyncio.sleep(2.5)  # Превышаем таймаут
                return {"result": "main"}
            
            return await fallback_manager.execute_with_fallback(
                main_operation=main_op,
                fallback_timeout=2.0,
                cache_key="test_cache_key"
            )
        
        result = await self.run_benchmark("fallback_cached", cached_fallback_operation, iterations=50)
        results.append(result)
        
        return results
    
    async def benchmark_concurrent_operations(self) -> List[BenchmarkResult]:
        """Бенчмарк конкурентных операций."""
        results = []
        
        # Тест конкурентного доступа к кэшу
        async def concurrent_cache_operation():
            tasks = []
            for i in range(10):
                task = cache_manager.set(f"concurrent_key_{i}", {"data": f"value_{i}"}, ttl=60)
                tasks.append(task)
            
            await asyncio.gather(*tasks)
        
        result = await self.run_benchmark("concurrent_cache", concurrent_cache_operation, iterations=20)
        results.append(result)
        
        # Тест конкурентных LLM операций
        async def concurrent_llm_operation():
            async def mock_llm_call():
                await asyncio.sleep(0.1)
                return {"result": "mock"}
            
            tasks = [mock_llm_call() for _ in range(5)]
            await asyncio.gather(*tasks)
        
        result = await self.run_benchmark("concurrent_llm", concurrent_llm_operation, iterations=20)
        results.append(result)
        
        return results
    
    async def run_all_benchmarks(self) -> Dict[str, List[BenchmarkResult]]:
        """Запуск всех бенчмарков."""
        logger.info("all_benchmarks_started", action="benchmark")
        
        # Подогреваем кэш
        await warmup_cache()
        
        all_results = {}
        
        # Кэш операции
        all_results["cache"] = await self.benchmark_cache_operations()
        
        # LLM профили
        all_results["llm"] = await self.benchmark_llm_profiles()
        
        # Фолбэк механизмы
        all_results["fallback"] = await self.benchmark_fallback_mechanisms()
        
        # Конкурентные операции
        all_results["concurrent"] = await self.benchmark_concurrent_operations()
        
        logger.info("all_benchmarks_completed", action="benchmark")
        
        return all_results
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерация отчета по бенчмаркам."""
        if not self.results:
            return {"error": "No benchmark results available"}
        
        report = {
            "summary": {
                "total_benchmarks": len(self.results),
                "total_operations": sum(r.iterations for r in self.results),
                "avg_success_rate": statistics.mean([r.success_rate for r in self.results])
            },
            "results": []
        }
        
        for result in self.results:
            report["results"].append({
                "operation": result.operation,
                "iterations": result.iterations,
                "avg_time_ms": round(result.avg_time_ms, 2),
                "p95_time_ms": round(result.p95_time_ms, 2),
                "p99_time_ms": round(result.p99_time_ms, 2),
                "success_rate": round(result.success_rate, 1),
                "errors_count": len(result.errors)
            })
        
        return report


async def run_performance_benchmark() -> Dict[str, Any]:
    """Запуск бенчмарка производительности."""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_all_benchmarks()
    report = benchmark.generate_report()
    
    return {
        "benchmark_results": results,
        "report": report,
        "p95_summary": {
            "cache_set": next((r.p95_time_ms for r in results["cache"] if r.operation == "cache_set"), 0),
            "cache_get": next((r.p95_time_ms for r in results["cache"] if r.operation == "cache_get"), 0),
            "llm_fast": next((r.p95_time_ms for r in results["llm"] if r.operation == "llm_fast_profile"), 0),
            "llm_smart": next((r.p95_time_ms for r in results["llm"] if r.operation == "llm_smart_profile"), 0),
            "fallback_quick": next((r.p95_time_ms for r in results["fallback"] if r.operation == "fallback_quick"), 0)
        }
    }


if __name__ == "__main__":
    async def main():
        results = await run_performance_benchmark()
        print("Benchmark Results:")
        print(f"Cache Set P95: {results['p95_summary']['cache_set']:.2f}ms")
        print(f"Cache Get P95: {results['p95_summary']['cache_get']:.2f}ms")
        print(f"LLM Fast P95: {results['p95_summary']['llm_fast']:.2f}ms")
        print(f"LLM Smart P95: {results['p95_summary']['llm_smart']:.2f}ms")
        print(f"Fallback Quick P95: {results['p95_summary']['fallback_quick']:.2f}ms")
    
    asyncio.run(main())
