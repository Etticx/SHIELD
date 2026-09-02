# =============================================================================
# SHIELD — Backend configuration
# Reads from .env (or environment variables set by the host/container).
# =============================================================================

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),  # avoids false warning on model_path field
    )

    model_path: str = "../model/xgb_shield_model.joblib"
    cors_origins: str = "http://localhost:3000"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    groq_api_key: str | None = None  # Set GROQ_API_KEY in .env to enable AI advisory
    database_url: str | None = None  # Set DATABASE_URL in .env to enable audit persistence

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


# Singleton — import this everywhere instead of re-instantiating
settings = Settings()
