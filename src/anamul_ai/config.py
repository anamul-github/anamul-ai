"""Settings and secrets, read from .env, which is never committed. .env.example lists the names."""

from functools import cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: SecretStr  # SecretStr keeps keys out of prints and logs
    claude_model: str = "claude-opus-5-5"  # Switch models with CLAUDE_MODEL in .env
    voyage_api_key: SecretStr

    model_config = SettingsConfigDict(env_file=".env")


@cache  # Read .env once and reuse it
def get_settings() -> Settings:
    return Settings()
