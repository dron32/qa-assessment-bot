from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Generator, Iterable, Optional

import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

try:
    # OpenAI SDK v1+
    from openai import OpenAI
    from openai import APIError as OpenAIError
except Exception:  # pragma: no cover - optional import guard for environments without SDK
    OpenAI = object  # type: ignore
    class OpenAIError(Exception):
        ...

from ..core.logging import get_logger
from ..core.metrics import LLMMetrics
from ..core.cache import LLMResponseCache, EmbeddingsCache
from .profiles import LlmProfile as NewLlmProfile
from .prompts import PROMPT_TEMPLATE, PROMPT_REFINE, PROMPT_CONFLICTS, PROMPT_SUMMARY
from .schemas import (
    TemplateResponse,
    RefineResponse,
    ConflictsResponse,
    SummaryResponse,
)


logger = get_logger(__name__)


@dataclass(frozen=True)
class LlmProfile:
    model: str
    max_tokens: int
    temperature: float
    timeout_seconds: int


FAST_PROFILE = LlmProfile(model=os.getenv("LLM_FAST_MODEL", "gpt-4o-mini"), max_tokens=500, temperature=0.2, timeout_seconds=5)
SUMMARY_PROFILE = LlmProfile(model=os.getenv("LLM_SUMMARY_MODEL", "gpt-4o"), max_tokens=700, temperature=0.4, timeout_seconds=15)


class LlmClient:
    def __init__(self, *, api_key: Optional[str] = None) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            logger.warning("openai_api_key_not_set", action="llm_init")
        self._client = OpenAI(api_key=key)  # type: ignore[call-arg]

    def _build_messages(self, system_prompt: str, user_payload: dict) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
        retry=retry_if_exception_type((OpenAIError, TimeoutError)),
    )
    def _complete_json(self, *, profile: LlmProfile, system_prompt: str, user_payload: dict, trace_id: str, operation: str) -> str:
        start_time = time.time()
        tokens_in = len(json.dumps(user_payload, ensure_ascii=False))
        
        try:
            resp = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=profile.model,
                messages=self._build_messages(system_prompt, user_payload),
                temperature=profile.temperature,
                max_tokens=profile.max_tokens,
                timeout=profile.timeout_seconds,
            )
            
            duration = time.time() - start_time
            tokens_out = getattr(resp.usage, 'completion_tokens', 0) if hasattr(resp, 'usage') else 0
            
            # Записываем метрики
            LLMMetrics.record_request(
                model=profile.model,
                operation=operation,
                status="success",
                duration=duration,
                tokens_in=tokens_in,
                tokens_out=tokens_out
            )
            
            # Логируем успех
            logger.info("llm_request_success", 
                       trace_id=trace_id, 
                       model=profile.model,
                       operation=operation,
                       tokens_in=tokens_in,
                       tokens_out=tokens_out,
                       latency_ms=round(duration * 1000, 2))
            
        except Exception as exc:
            duration = time.time() - start_time
            
            # Записываем метрики ошибки
            LLMMetrics.record_request(
                model=profile.model,
                operation=operation,
                status="error",
                duration=duration,
                tokens_in=tokens_in
            )
            
            # Логируем ошибку
            logger.error("llm_request_failed", 
                        trace_id=trace_id, 
                        model=profile.model,
                        operation=operation,
                        error=str(exc),
                        latency_ms=round(duration * 1000, 2))
            
            # Отправляем в Sentry с тегами
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("llm_model", profile.model)
                scope.set_tag("llm_operation", operation)
                scope.set_tag("trace_id", trace_id)
                scope.set_context("llm_request", {
                    "model": profile.model,
                    "operation": operation,
                    "tokens_in": tokens_in,
                    "duration": duration
                })
                sentry_sdk.capture_exception(exc)
            
            raise

        content = (resp.choices[0].message.content or "").strip()  # type: ignore[attr-defined]
        return content

    def _graceful_fallback(self, *, kind: str) -> str:
        short = {
            "template": {"outline": "Краткий план", "example": "Краткий пример", "bullet_points": ["Пункт 1", "Пункт 2", "Пункт 3"]},
            "refine": {"refined": "Сжатая версия текста", "improvement_hints": ["Уточнить примеры", "Избегать общих фраз"]},
            "conflicts": {"duplicates": [], "contradictions": []},
            "summary": {"strengths": ["Сила 1", "Сила 2", "Сила 3"], "areas_for_growth": ["Рост 1", "Рост 2", "Рост 3"], "next_steps": ["Шаг 1", "Шаг 2", "Шаг 3"]},
        }[kind]
        return json.dumps(short, ensure_ascii=False)

    def generate_template(self, *, competency: str, context: str, trace_id: str) -> TemplateResponse:
        payload = {"competency": competency, "context": context}
        try:
            raw = self._complete_json(profile=FAST_PROFILE, system_prompt=PROMPT_TEMPLATE, user_payload=payload, trace_id=trace_id, operation="template")
        except Exception:
            raw = self._graceful_fallback(kind="template")
        return TemplateResponse.model_validate_json(raw)

    def refine_text(self, *, text: str, trace_id: str) -> RefineResponse:
        payload = {"text": text}
        try:
            raw = self._complete_json(profile=FAST_PROFILE, system_prompt=PROMPT_REFINE, user_payload=payload, trace_id=trace_id, operation="refine")
        except Exception:
            raw = self._graceful_fallback(kind="refine")
        return RefineResponse.model_validate(raw)

    def detect_conflicts(self, *, self_items: list[str], peer_items: list[str], trace_id: str) -> ConflictsResponse:
        payload = {"self_items": self_items, "peer_items": peer_items}
        try:
            raw = self._complete_json(profile=FAST_PROFILE, system_prompt=PROMPT_CONFLICTS, user_payload=payload, trace_id=trace_id, operation="conflicts")
        except Exception:
            raw = self._graceful_fallback(kind="conflicts")
        return ConflictsResponse.model_validate_json(raw)

    def generate_summary(self, *, user_context: str, trace_id: str) -> SummaryResponse:
        payload = {"context": user_context}
        try:
            raw = self._complete_json(profile=SUMMARY_PROFILE, system_prompt=PROMPT_SUMMARY, user_payload=payload, trace_id=trace_id, operation="summary")
        except Exception:
            raw = self._graceful_fallback(kind="summary")
        return SummaryResponse.model_validate_json(raw)

    def stream_chat(self, *, system_prompt: str, user_text: str, trace_id: str, profile: LlmProfile = FAST_PROFILE) -> Generator[str, None, None]:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ]
        try:
            stream = self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=profile.model,
                messages=messages,
                temperature=profile.temperature,
                max_tokens=profile.max_tokens,
                stream=True,
                timeout=profile.timeout_seconds,
            )
            for chunk in stream:  # type: ignore[union-attr]
                delta = chunk.choices[0].delta.content  # type: ignore[attr-defined]
                if delta:
                    yield delta
        except Exception as exc:
            logger.warning("llm_stream_failed", extra={"trace_id": trace_id, "error": str(exc)})
            return

    async def generate_embeddings(self, text: str, model: str = 'text-embedding-3-small') -> List[float]:
        """Генерация эмбеддингов для текста с кэшированием."""
        trace_id = str(uuid.uuid4())
        
        # Проверяем кэш
        cached_embeddings = await EmbeddingsCache.get_embeddings(text, model)
        if cached_embeddings:
            logger.info("embeddings_cache_hit", 
                       trace_id=trace_id,
                       model=model,
                       action="embeddings_cache")
            return cached_embeddings
        
        try:
            response = await self._client.embeddings.create(
                model=model,
                input=text,
                timeout=30
            )
            
            embeddings = response.data[0].embedding
            
            # Сохраняем в кэш
            await EmbeddingsCache.set_embeddings(text, embeddings, model)
            
            logger.info("llm_embeddings_success", 
                       trace_id=trace_id, 
                       model=model,
                       action="embeddings_generation")
            return embeddings
            
        except Exception as exc:
            logger.error("llm_embeddings_failed", 
                        trace_id=trace_id, 
                        error=str(exc),
                        action="embeddings_generation")
            raise


