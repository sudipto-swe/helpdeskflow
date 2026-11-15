"""Configuration settings for HelpdeskFlow API."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8100
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./helpdeskflow.db"

    # LLM Settings
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "default"
    LLM_CACHE_DIR: str = ".cache/llm_cache"
    LLM_REQUEST_TIMEOUT_SECONDS: int = 30

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Guardrails and Policy
    MAX_TOOL_CALLS_PER_TICKET: int = 5
    MAX_TOKENS_PER_TICKET: int = 4096
    CONFIDENCE_THRESHOLD_APPROVAL: float = 0.75

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
