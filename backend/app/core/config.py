"""Application configuration, read once from the environment.

Kept apart from `settings.py` (engine constants) so importing the engine never
requires database or OAuth secrets.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    ENV: str = "development"
    DATABASE_URL: str | None = None
    APP_ORIGIN: str = "http://localhost:3000"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    BREVO_API_KEY: str | None = None
    BREVO_SENDER: str | None = None

    @property
    def cookie_secure(self) -> bool:
        """Secure cookies need https; local development and e2e run over http."""
        return self.ENV == "production"

    @property
    def google_enabled(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
