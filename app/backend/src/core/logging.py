import json
import logging
import re
import sys
import time
import uuid
from typing import Any, Dict, Optional

from .config import get_settings


class PIIMasker:
    """Маскирование PII данных в логах."""
    
    # Паттерны для поиска PII
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'(\+7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b')
    PASSPORT_PATTERN = re.compile(r'\b\d{4}\s?\d{6}\b')
    
    @classmethod
    def mask_pii(cls, text: str) -> str:
        """Маскирует PII данные в тексте."""
        if not isinstance(text, str):
            return text
            
        # Маскируем email
        text = cls.EMAIL_PATTERN.sub('[EMAIL_MASKED]', text)
        # Маскируем телефоны
        text = cls.PHONE_PATTERN.sub('[PHONE_MASKED]', text)
        # Маскируем кредитные карты
        text = cls.CREDIT_CARD_PATTERN.sub('[CARD_MASKED]', text)
        # Маскируем паспорта
        text = cls.PASSPORT_PATTERN.sub('[PASSPORT_MASKED]', text)
        
        return text
    
    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивно маскирует PII в словаре."""
        if not isinstance(data, dict):
            return data
            
        masked = {}
        for key, value in data.items():
            if isinstance(value, str):
                masked[key] = cls.mask_pii(value)
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [cls.mask_dict(item) if isinstance(item, dict) else cls.mask_pii(item) if isinstance(item, str) else item for item in value]
            else:
                masked[key] = value
        return masked


class ObservabilityFormatter(logging.Formatter):
    """Расширенный JSON форматтер с метриками и PII маскированием."""
    
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        base: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        
        # Добавляем trace_id если есть
        if hasattr(record, 'trace_id'):
            base["trace_id"] = record.trace_id
        
        # Добавляем user_id если есть
        if hasattr(record, 'user_id'):
            base["user_id"] = record.user_id
            
        # Добавляем platform если есть
        if hasattr(record, 'platform'):
            base["platform"] = record.platform
            
        # Добавляем action если есть
        if hasattr(record, 'action'):
            base["action"] = record.action
            
        # Добавляем latency_ms если есть
        if hasattr(record, 'latency_ms'):
            base["latency_ms"] = record.latency_ms
            
        # Добавляем токены если есть
        if hasattr(record, 'tokens_in'):
            base["tokens_in"] = record.tokens_in
        if hasattr(record, 'tokens_out'):
            base["tokens_out"] = record.tokens_out
            
        # Добавляем exception info
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
            
        # Добавляем extra поля с маскированием PII
        for key, value in getattr(record, "__dict__", {}).items():
            if key.startswith("_") or key in base:
                continue
            if key in ("args", "msg", "exc_info", "exc_text", "stack_info"):
                continue
            try:
                # Маскируем PII в значениях
                if isinstance(value, str):
                    value = PIIMasker.mask_pii(value)
                elif isinstance(value, dict):
                    value = PIIMasker.mask_dict(value)
                    
                json.dumps({key: value})
                base[key] = value
            except Exception:
                base[key] = str(value)
                
        return json.dumps(base, ensure_ascii=False)


class ObservabilityLogger:
    """Логгер с поддержкой observability метрик."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._start_time: Optional[float] = None
        
    def _log_with_metrics(self, level: int, msg: str, **kwargs):
        """Логирование с автоматическими метриками."""
        # Добавляем trace_id если нет
        if 'trace_id' not in kwargs:
            kwargs['trace_id'] = str(uuid.uuid4())
            
        # Добавляем latency если есть start_time
        if self._start_time is not None:
            kwargs['latency_ms'] = round((time.time() - self._start_time) * 1000, 2)
            self._start_time = None
            
        self.logger.log(level, msg, extra=kwargs)
        
    def start_timer(self):
        """Начинает измерение времени для latency метрики."""
        self._start_time = time.time()
        
    def info(self, msg: str, **kwargs):
        self._log_with_metrics(logging.INFO, msg, **kwargs)
        
    def warning(self, msg: str, **kwargs):
        self._log_with_metrics(logging.WARNING, msg, **kwargs)
        
    def error(self, msg: str, **kwargs):
        self._log_with_metrics(logging.ERROR, msg, **kwargs)
        
    def debug(self, msg: str, **kwargs):
        self._log_with_metrics(logging.DEBUG, msg, **kwargs)


def configure_json_logging() -> None:
    """Настройка JSON логирования с observability."""
    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ObservabilityFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


def get_logger(name: str) -> ObservabilityLogger:
    """Получение логгера с observability метриками."""
    return ObservabilityLogger(name)




