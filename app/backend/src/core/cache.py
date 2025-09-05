"""Система кэширования с Redis."""

import json
import hashlib
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Менеджер кэша с Redis."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._settings = get_settings()
        
    async def connect(self) -> None:
        """Подключение к Redis."""
        try:
            self._redis = redis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Проверяем подключение
            await self._redis.ping()
            logger.info("redis_connected", action="cache_init")
            
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e), action="cache_init")
            self._redis = None
    
    async def disconnect(self) -> None:
        """Отключение от Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("redis_disconnected", action="cache_cleanup")
    
    def _generate_key(self, prefix: str, *args: Any) -> str:
        """Генерация ключа кэша."""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        
        # Если ключ слишком длинный, хэшируем его
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        
        return key_string
    
    async def get(self, key: str) -> Optional[Any]:
        """Получение значения из кэша."""
        if not self._redis:
            return None
            
        try:
            value = await self._redis.get(key)
            if value:
                logger.debug("cache_hit", key=key, action="cache_get")
                return json.loads(value)
            else:
                logger.debug("cache_miss", key=key, action="cache_get")
                return None
                
        except Exception as e:
            logger.error("cache_get_failed", key=key, error=str(e), action="cache_get")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """Сохранение значения в кэш."""
        if not self._redis:
            return False
            
        try:
            serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            
            kwargs = {}
            if ttl:
                kwargs["ex"] = ttl
            if nx:
                kwargs["nx"] = True
                
            result = await self._redis.set(key, serialized_value, **kwargs)
            
            if result:
                logger.debug("cache_set", key=key, ttl=ttl, action="cache_set")
            else:
                logger.debug("cache_set_failed", key=key, action="cache_set")
                
            return bool(result)
            
        except Exception as e:
            logger.error("cache_set_failed", key=key, error=str(e), action="cache_set")
            return False
    
    async def delete(self, key: str) -> bool:
        """Удаление значения из кэша."""
        if not self._redis:
            return False
            
        try:
            result = await self._redis.delete(key)
            logger.debug("cache_delete", key=key, action="cache_delete")
            return bool(result)
            
        except Exception as e:
            logger.error("cache_delete_failed", key=key, error=str(e), action="cache_delete")
            return False
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа."""
        if not self._redis:
            return False
            
        try:
            result = await self._redis.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error("cache_exists_failed", key=key, error=str(e), action="cache_exists")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Получение множества значений."""
        if not self._redis or not keys:
            return {}
            
        try:
            values = await self._redis.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value:
                    result[key] = json.loads(value)
                    
            logger.debug("cache_mget", keys_count=len(keys), hits=len(result), action="cache_get_many")
            return result
            
        except Exception as e:
            logger.error("cache_mget_failed", keys_count=len(keys), error=str(e), action="cache_get_many")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Сохранение множества значений."""
        if not self._redis or not mapping:
            return False
            
        try:
            pipe = self._redis.pipeline()
            
            for key, value in mapping.items():
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
                if ttl:
                    pipe.setex(key, ttl, serialized_value)
                else:
                    pipe.set(key, serialized_value)
                    
            await pipe.execute()
            logger.debug("cache_mset", keys_count=len(mapping), ttl=ttl, action="cache_set_many")
            return True
            
        except Exception as e:
            logger.error("cache_mset_failed", keys_count=len(mapping), error=str(e), action="cache_set_many")
            return False


# Глобальный экземпляр кэш-менеджера
cache_manager = CacheManager()


class TemplateCache:
    """Кэш для шаблонов ответов."""
    
    CACHE_PREFIX = "template"
    DEFAULT_TTL = 3600  # 1 час
    
    @classmethod
    async def get_template(cls, competency_key: str) -> Optional[Dict[str, Any]]:
        """Получение шаблона из кэша."""
        key = cache_manager._generate_key(cls.CACHE_PREFIX, competency_key)
        return await cache_manager.get(key)
    
    @classmethod
    async def set_template(cls, competency_key: str, template: Dict[str, Any]) -> bool:
        """Сохранение шаблона в кэш."""
        key = cache_manager._generate_key(cls.CACHE_PREFIX, competency_key)
        return await cache_manager.set(key, template, ttl=cls.DEFAULT_TTL)
    
    @classmethod
    async def invalidate_template(cls, competency_key: str) -> bool:
        """Инвалидация шаблона."""
        key = cache_manager._generate_key(cls.CACHE_PREFIX, competency_key)
        return await cache_manager.delete(key)


class EmbeddingsCache:
    """Кэш для эмбеддингов."""
    
    CACHE_PREFIX = "embeddings"
    DEFAULT_TTL = 86400  # 24 часа
    
    @classmethod
    def _text_hash(cls, text: str) -> str:
        """Хэш текста для ключа кэша."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    @classmethod
    async def get_embeddings(cls, text: str, model: str = "text-embedding-3-small") -> Optional[List[float]]:
        """Получение эмбеддингов из кэша."""
        text_hash = cls._text_hash(text)
        key = cache_manager._generate_key(cls.CACHE_PREFIX, model, text_hash)
        return await cache_manager.get(key)
    
    @classmethod
    async def set_embeddings(
        cls, 
        text: str, 
        embeddings: List[float], 
        model: str = "text-embedding-3-small"
    ) -> bool:
        """Сохранение эмбеддингов в кэш."""
        text_hash = cls._text_hash(text)
        key = cache_manager._generate_key(cls.CACHE_PREFIX, model, text_hash)
        return await cache_manager.set(key, embeddings, ttl=cls.DEFAULT_TTL)
    
    @classmethod
    async def get_many_embeddings(
        cls, 
        texts: List[str], 
        model: str = "text-embedding-3-small"
    ) -> Dict[str, List[float]]:
        """Получение множества эмбеддингов."""
        keys = []
        text_to_key = {}
        
        for text in texts:
            text_hash = cls._text_hash(text)
            key = cache_manager._generate_key(cls.CACHE_PREFIX, model, text_hash)
            keys.append(key)
            text_to_key[key] = text
            
        cached_data = await cache_manager.get_many(keys)
        
        # Преобразуем ключи обратно в тексты
        result = {}
        for key, embeddings in cached_data.items():
            text = text_to_key[key]
            result[text] = embeddings
            
        return result


class LLMResponseCache:
    """Кэш для ответов LLM."""
    
    CACHE_PREFIX = "llm_response"
    DEFAULT_TTL = 1800  # 30 минут
    
    @classmethod
    def _request_hash(cls, prompt: str, model: str, temperature: float) -> str:
        """Хэш запроса для ключа кэша."""
        content = f"{prompt}:{model}:{temperature}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    @classmethod
    async def get_response(
        cls, 
        prompt: str, 
        model: str, 
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """Получение ответа LLM из кэша."""
        request_hash = cls._request_hash(prompt, model, temperature)
        key = cache_manager._generate_key(cls.CACHE_PREFIX, model, request_hash)
        return await cache_manager.get(key)
    
    @classmethod
    async def set_response(
        cls, 
        prompt: str, 
        response: Dict[str, Any], 
        model: str, 
        temperature: float = 0.7
    ) -> bool:
        """Сохранение ответа LLM в кэш."""
        request_hash = cls._request_hash(prompt, model, temperature)
        key = cache_manager._generate_key(cls.CACHE_PREFIX, model, request_hash)
        return await cache_manager.set(key, response, ttl=cls.DEFAULT_TTL)


async def warmup_cache():
    """Подогрев кэша при старте приложения."""
    logger.info("cache_warmup_started", action="cache_warmup")
    
    try:
        # Подключаемся к Redis
        await cache_manager.connect()
        
        # Подогреваем шаблоны (заглушка - в реальном приложении загружали бы из БД)
        templates_data = [
            {
                "competency_key": "analytical_thinking",
                "title": "Шаблон для аналитического мышления",
                "content": "Опишите конкретный случай анализа проблемы..."
            },
            {
                "competency_key": "bug_reports", 
                "title": "Шаблон для баг-репортов",
                "content": "Опишите пример качественного баг-репорта..."
            }
        ]
        
        for template in templates_data:
            await TemplateCache.set_template(
                template["competency_key"], 
                template
            )
        
        # Подогреваем популярные эмбеддинги (заглушка)
        popular_texts = [
            "аналитическое мышление",
            "написание баг-репортов", 
            "планирование тестирования",
            "автоматизация тестов"
        ]
        
        # В реальном приложении здесь бы генерировали эмбеддинги через LLM
        dummy_embeddings = [[0.1, 0.2, 0.3] for _ in popular_texts]
        
        for text, embeddings in zip(popular_texts, dummy_embeddings):
            await EmbeddingsCache.set_embeddings(text, embeddings)
        
        logger.info("cache_warmup_completed", 
                   templates_count=len(templates_data),
                   embeddings_count=len(popular_texts),
                   action="cache_warmup")
        
    except Exception as e:
        logger.error("cache_warmup_failed", error=str(e), action="cache_warmup")


async def get_cache_stats() -> Dict[str, Any]:
    """Получение статистики кэша."""
    if not cache_manager._redis:
        return {"status": "disconnected"}
    
    try:
        info = await cache_manager._redis.info()
        
        return {
            "status": "connected",
            "used_memory": info.get("used_memory_human", "0B"),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) / 
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            ) * 100
        }
        
    except Exception as e:
        logger.error("cache_stats_failed", error=str(e), action="cache_stats")
        return {"status": "error", "error": str(e)}
