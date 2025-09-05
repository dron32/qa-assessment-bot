"""Профили LLM для разных сценариев использования."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

from ..core.logging import get_logger

logger = get_logger(__name__)


class LlmProfileType(Enum):
    """Типы профилей LLM."""
    FAST = "fast"      # Быстрые ответы
    SMART = "smart"    # Умные ответы
    BALANCED = "balanced"  # Сбалансированные


@dataclass
class LlmProfile:
    """Профиль LLM с настройками."""
    name: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    description: str
    use_cache: bool = True
    fallback_enabled: bool = True
    fallback_timeout: float = 3.0


class LlmProfileManager:
    """Менеджер профилей LLM."""
    
    def __init__(self):
        self._profiles: Dict[str, LlmProfile] = {}
        self._initialize_profiles()
    
    def _initialize_profiles(self):
        """Инициализация профилей."""
        
        # Быстрый профиль - для быстрых ответов
        self._profiles[LlmProfileType.FAST.value] = LlmProfile(
            name="Fast Response",
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=500,
            timeout_seconds=2.0,
            description="Быстрые ответы с короткими подсказками и низкими лимитами токенов",
            use_cache=True,
            fallback_enabled=True,
            fallback_timeout=2.0
        )
        
        # Умный профиль - для детальных ответов
        self._profiles[LlmProfileType.SMART.value] = LlmProfile(
            name="Smart Analysis",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=2000,
            timeout_seconds=10.0,
            description="Детальный анализ с развернутыми ответами и сводками",
            use_cache=True,
            fallback_enabled=True,
            fallback_timeout=5.0
        )
        
        # Сбалансированный профиль - по умолчанию
        self._profiles[LlmProfileType.BALANCED.value] = LlmProfile(
            name="Balanced",
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=1000,
            timeout_seconds=5.0,
            description="Сбалансированный профиль для большинства задач",
            use_cache=True,
            fallback_enabled=True,
            fallback_timeout=3.0
        )
        
        logger.info("llm_profiles_initialized", 
                   profiles_count=len(self._profiles),
                   action="llm_profiles_init")
    
    def get_profile(self, profile_type: str) -> Optional[LlmProfile]:
        """Получение профиля по типу."""
        profile = self._profiles.get(profile_type)
        if profile:
            logger.debug("llm_profile_retrieved", 
                        profile_type=profile_type,
                        model=profile.model,
                        action="llm_profile_get")
        else:
            logger.warning("llm_profile_not_found", 
                          profile_type=profile_type,
                          action="llm_profile_get")
        return profile
    
    def get_fast_profile(self) -> LlmProfile:
        """Получение быстрого профиля."""
        return self.get_profile(LlmProfileType.FAST.value)
    
    def get_smart_profile(self) -> LlmProfile:
        """Получение умного профиля."""
        return self.get_profile(LlmProfileType.SMART.value)
    
    def get_balanced_profile(self) -> LlmProfile:
        """Получение сбалансированного профиля."""
        return self.get_profile(LlmProfileType.BALANCED.value)
    
    def list_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Список всех профилей."""
        return {
            profile_type: {
                "name": profile.name,
                "model": profile.model,
                "temperature": profile.temperature,
                "max_tokens": profile.max_tokens,
                "timeout_seconds": profile.timeout_seconds,
                "description": profile.description,
                "use_cache": profile.use_cache,
                "fallback_enabled": profile.fallback_enabled,
                "fallback_timeout": profile.fallback_timeout
            }
            for profile_type, profile in self._profiles.items()
        }
    
    def create_custom_profile(
        self,
        name: str,
        model: str,
        temperature: float = 0.5,
        max_tokens: int = 1000,
        timeout_seconds: float = 5.0,
        description: str = "",
        use_cache: bool = True,
        fallback_enabled: bool = True,
        fallback_timeout: float = 3.0
    ) -> LlmProfile:
        """Создание кастомного профиля."""
        profile = LlmProfile(
            name=name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            description=description,
            use_cache=use_cache,
            fallback_enabled=fallback_enabled,
            fallback_timeout=fallback_timeout
        )
        
        logger.info("custom_llm_profile_created",
                   name=name,
                   model=model,
                   action="llm_profile_create")
        
        return profile


# Глобальный экземпляр менеджера профилей
profile_manager = LlmProfileManager()


def get_profile(profile_type: str) -> Optional[LlmProfile]:
    """Получение профиля LLM."""
    return profile_manager.get_profile(profile_type)


def get_fast_profile() -> LlmProfile:
    """Получение быстрого профиля."""
    return profile_manager.get_fast_profile()


def get_smart_profile() -> LlmProfile:
    """Получение умного профиля."""
    return profile_manager.get_smart_profile()


def get_balanced_profile() -> LlmProfile:
    """Получение сбалансированного профиля."""
    return profile_manager.get_balanced_profile()


# Предустановленные промпты для разных профилей
FAST_PROMPTS = {
    "competency_analysis": """
Проанализируй ответ пользователя по компетенции "{competency}" и дай краткую оценку (1-2 предложения).

Ответ пользователя: {user_response}

Оцени:
- Качество ответа (1-5)
- Ключевые сильные стороны
- Области для улучшения
""",
    
    "quick_feedback": """
Дай краткую обратную связь по ответу (максимум 100 слов):

Ответ: {user_response}
Компетенция: {competency}

Фокус на:
- Что сделано хорошо
- Что можно улучшить
- Конкретный совет
""",
    
    "conflict_detection": """
Есть ли конфликт между самооценкой и оценкой коллег? (да/нет + краткое объяснение)

Самооценка: {self_review}
Оценка коллег: {peer_review}
"""
}

SMART_PROMPTS = {
    "detailed_analysis": """
Проведи детальный анализ ответа пользователя по компетенции "{competency}".

Ответ пользователя: {user_response}

Проанализируй:
1. **Структурированность ответа** (есть ли четкая структура, логика изложения)
2. **Конкретность примеров** (насколько детальны и релевантны примеры)
3. **Глубина понимания** (показывает ли ответ глубокое понимание темы)
4. **Практическая применимость** (можно ли применить описанные подходы)
5. **Оригинальность мышления** (есть ли нестандартные решения)

Дай оценку по каждому критерию (1-5) и общую оценку.
Предложи конкретные рекомендации для развития.
""",
    
    "comprehensive_summary": """
Создай комплексную сводку по результатам оценки пользователя.

Данные:
- Самооценка: {self_review}
- Оценки коллег: {peer_reviews}
- Компетенции: {competencies}

Структура сводки:
1. **Общая картина** - ключевые сильные стороны и области роста
2. **Детальный анализ по компетенциям** - сравнение самооценки и внешних оценок
3. **Выявленные паттерны** - повторяющиеся темы и тенденции
4. **Конфликты и расхождения** - где есть разногласия и почему
5. **Рекомендации по развитию** - конкретный план действий
6. **Следующие шаги** - что делать дальше

Сводка должна быть детальной, но структурированной и понятной.
""",
    
    "conflict_resolution": """
Проанализируй конфликт между самооценкой и оценкой коллег.

Самооценка: {self_review}
Оценка коллег: {peer_review}
Компетенция: {competency}

Анализ должен включать:
1. **Природа конфликта** - в чем именно расхождение
2. **Возможные причины** - почему могло возникнуть расхождение
3. **Влияние на развитие** - как это влияет на профессиональный рост
4. **Рекомендации по разрешению** - конкретные шаги для устранения конфликта
5. **Предотвращение в будущем** - как избежать подобных ситуаций
"""
}

BALANCED_PROMPTS = {
    "standard_analysis": """
Проанализируй ответ пользователя по компетенции "{competency}".

Ответ: {user_response}

Дай оценку (1-5) и краткий анализ:
- Сильные стороны
- Области для улучшения  
- Конкретные рекомендации
""",
    
    "standard_summary": """
Создай сводку по результатам оценки.

Данные:
- Самооценка: {self_review}
- Оценки коллег: {peer_reviews}

Включи:
- Ключевые выводы
- Сравнение самооценки и внешних оценок
- Рекомендации по развитию
"""
}


def get_prompt(profile_type: str, prompt_type: str) -> Optional[str]:
    """Получение промпта для профиля."""
    prompts_map = {
        LlmProfileType.FAST.value: FAST_PROMPTS,
        LlmProfileType.SMART.value: SMART_PROMPTS,
        LlmProfileType.BALANCED.value: BALANCED_PROMPTS
    }
    
    prompts = prompts_map.get(profile_type)
    if prompts:
        return prompts.get(prompt_type)
    
    return None


def format_prompt(prompt: str, **kwargs) -> str:
    """Форматирование промпта с параметрами."""
    try:
        return prompt.format(**kwargs)
    except KeyError as e:
        logger.error("prompt_formatting_failed", 
                    missing_key=str(e),
                    action="prompt_format")
        return prompt
