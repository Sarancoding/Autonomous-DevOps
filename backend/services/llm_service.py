"""LLM service abstraction with model routing and structured output parsing."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, AsyncIterator, Optional

import httpx

logger = logging.getLogger(__name__)

# Default model routing: cheap model for analysis, capable model for fixes
_CHEAP_MODEL = os.getenv("LLM_CHEAP_MODEL", "gpt-4o-mini")
_CAPABLE_MODEL = os.getenv("LLM_CAPABLE_MODEL", "gpt-4o")
_API_BASE = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")


class LLMService:
    """Thin LLM client with model routing and structured output support.

    Supports OpenAI-compatible APIs (OpenAI, OpenRouter, Azure, etc.).
    """

    def __init__(self, api_key: str = "", api_base: str = "") -> None:
        self._api_key = api_key or os.getenv("LLM_API_KEY", "")
        self._api_base = (api_base or _API_BASE).rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(headers=self._headers, timeout=60.0)

    async def __aenter__(self) -> "LLMService":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Main public interface
    # ------------------------------------------------------------------

    async def analyze(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Use the *cheap* model for analysis tasks."""
        return await self._chat_completion(
            model=_CHEAP_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
        )

    async def generate_fix(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Use the *capable* model for fix generation."""
        return await self._chat_completion(
            model=_CAPABLE_MODEL,
            prompt=prompt,
            system_prompt=system_prompt or self._fix_system_prompt(),
        )

    async def structured_output(
        self,
        prompt: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Request a structured JSON response conforming to *schema*."""
        system_prompt = (
            "You are a precise JSON generator. Respond ONLY with a valid JSON "
            f"object that conforms to this schema: {json.dumps(schema)}\n"
            "Do not include markdown fences or any other text."
        )
        raw = await self._chat_completion(
            model=model or _CHEAP_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON; attempting repair...")
            repaired = _extract_json(raw)
            return json.loads(repaired) if repaired else {}

    # ------------------------------------------------------------------
    # Low-level completion
    # ------------------------------------------------------------------

    async def _chat_completion(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Send a chat completion request and return the content string."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
        }
        if response_format:
            body["response_format"] = response_format

        response = await self._client.post(
            f"{self._api_base}/chat/completions",
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    # ------------------------------------------------------------------
    # Streaming (for live agent logs on the frontend)
    # ------------------------------------------------------------------

    async def stream_chat(
        self,
        prompt: str,
        model: str | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream tokens from the LLM, yielding each chunk as a string."""
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with self._client.stream(
            "POST",
            f"{self._api_base}/chat/completions",
            json={
                "model": model or _CAPABLE_MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4096,
                "stream": True,
            },
        ) as stream:
            async for line in stream.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    # ------------------------------------------------------------------
    # Default system prompts
    # ------------------------------------------------------------------

    @staticmethod
    def _fix_system_prompt() -> str:
        return (
            "You are an expert software engineer. Your task is to fix bugs in code.\n"
            "You produce concise, correct diffs. Always include a confidence score.\n"
            "Be conservative — do not change code beyond what is necessary to fix the issue."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> str | None:
    """Try to extract a JSON object from free-form text."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None
