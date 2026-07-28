"""Application configuration loaded from environment variables.

All sensitive values (API keys, tokens) are read from the environment at
startup and never hard-coded.  Users bring their own keys (BYOK).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Settings:
    """Central settings object for the Autonomous DevOps backend."""

    # ---- Server ----
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # ---- LLM ----
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    cheap_model: str = os.getenv("LLM_CHEAP_MODEL", "gpt-4o-mini")
    capable_model: str = os.getenv("LLM_CAPABLE_MODEL", "gpt-4o")

    # ---- GitHub ----
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    github_webhook_secret: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    # ---- Langfuse (Observability) ----
    langfuse_public_key: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    langfuse_host: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    # ---- Docker Sandbox ----
    docker_enabled: bool = os.getenv("DOCKER_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    sandbox_timeout: int = int(os.getenv("SANDBOX_TIMEOUT", "120"))
    sandbox_cpu_quota: int = int(os.getenv("SANDBOX_CPU_QUOTA", "50000"))
    sandbox_memory_mb: int = int(os.getenv("SANDBOX_MEMORY_MB", "512"))

    # ---- Redis (optional for state persistence) ----
    redis_url: str = os.getenv("REDIS_URL", "")

    # ---- CORS ----
    cors_origins: list[str] = field(default_factory=lambda: [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ])

    # ---- Secrets / User BYOK ----
    # User API keys are NOT stored here. They are passed via frontend
    # in request headers and stored ephemerally in-memory per session.

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def is_ready(self) -> tuple[bool, list[str]]:
        """Check if critical settings are configured.

        Returns (is_ready, list_of_missing_keys).
        """
        missing: list[str] = []
        if not self.llm_api_key:
            missing.append("LLM_API_KEY")
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        return (len(missing) == 0, missing)


# Singleton
settings = Settings()
