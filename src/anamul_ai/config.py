"""Day 7: settings and secrets, read from the .env file.

Secrets like API keys never go in the code or on GitHub. They live in .env on my
computer, which git ignores, and this class reads them when the app starts.
.env.example shows which settings exist, without the real values.
"""

from functools import cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # Like a Pydantic model, but it fills its fields from .env and the environment
    # Matches ANTHROPIC_API_KEY in .env (the names ignore upper and lower case).
    # SecretStr hides the value if it's ever printed or logged: it shows ********** instead.
    anthropic_api_key: SecretStr
    # Day 8: the model that writes the answers. To switch, add CLAUDE_MODEL=... to .env.
    claude_model: str = "claude-opus-5-5"

    model_config = SettingsConfigDict(env_file=".env")


@cache  # Runs once, then hands back the same Settings every time, like a memoized function in JavaScript
def get_settings() -> Settings:
    return Settings()
