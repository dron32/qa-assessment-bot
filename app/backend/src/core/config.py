from functools import lru_cache
import os


class Settings:
    def __init__(self) -> None:
        self.env: str = os.getenv("ENV", "dev")
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.database_url: str = os.getenv(
            "DB_DSN",
            "postgresql+asyncpg://postgres:postgres@db:5432/qa_assessment",
        )
        self.redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # OpenAI настройки
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_summary_model: str = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4o")
        
        # Bot токены
        self.slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret: str = os.getenv("SLACK_SIGNING_SECRET", "")
        self.telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        
        # Sentry
        self.sentry_dsn: str = os.getenv("SENTRY_DSN", "")
        
        # Шифрование
        self.encryption_key: str = os.getenv("ENCRYPTION_KEY", "")
        
        # Prometheus
        self.prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "9090"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()




