"""Pluggable LLM client supporting OpenAI-compatible providers (Groq, OpenRouter, Together)
and Anthropic. Enabled via env vars. Gracefully no-ops when no provider is configured.

Env config:
    LLM_PROVIDER: anthropic | openai | groq | openrouter | together | none (default: auto-detect)
    LLM_MODEL: model name
    ANTHROPIC_API_KEY
    OPENAI_API_KEY / OPENAI_BASE_URL
    GROQ_API_KEY
    OPENROUTER_API_KEY
"""
import json
import os
from typing import Any, Optional

import httpx
from loguru import logger


ANTHROPIC_DEFAULT = "claude-haiku-4-5-20251001"
GROQ_DEFAULT = "llama-3.3-70b-versatile"
OPENROUTER_DEFAULT = "meta-llama/llama-3.3-70b-instruct"
OPENAI_DEFAULT = "gpt-4o-mini"


def _detect_provider() -> tuple[str, str, str, str]:
    """Return (provider, base_url, api_key, model). Empty api_key means disabled."""
    override = (os.getenv("LLM_PROVIDER") or "").lower().strip()
    model_override = os.getenv("LLM_MODEL")

    def pick(provider: str, base: str, key_env: str, default_model: str):
        key = os.getenv(key_env, "")
        return provider, base, key, (model_override or default_model)

    if override == "anthropic":
        return pick("anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", ANTHROPIC_DEFAULT)
    if override == "groq":
        return pick("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", GROQ_DEFAULT)
    if override == "openrouter":
        return pick("openrouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", OPENROUTER_DEFAULT)
    if override == "openai":
        return pick("openai", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), "OPENAI_API_KEY", OPENAI_DEFAULT)
    if override == "together":
        return pick("openai", "https://api.together.xyz/v1", "TOGETHER_API_KEY", "meta-llama/Llama-3.3-70B-Instruct-Turbo")

    # Auto-detect in preference order
    if os.getenv("ANTHROPIC_API_KEY"):
        return pick("anthropic", "https://api.anthropic.com", "ANTHROPIC_API_KEY", ANTHROPIC_DEFAULT)
    if os.getenv("GROQ_API_KEY"):
        return pick("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", GROQ_DEFAULT)
    if os.getenv("OPENROUTER_API_KEY"):
        return pick("openrouter", "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", OPENROUTER_DEFAULT)
    if os.getenv("OPENAI_API_KEY"):
        return pick("openai", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"), "OPENAI_API_KEY", OPENAI_DEFAULT)
    return "none", "", "", ""


class LLMClient:
    def __init__(self):
        self.provider, self.base_url, self.api_key, self.model = _detect_provider()
        self.enabled = bool(self.api_key)
        if self.enabled:
            logger.info(f"LLM enabled: provider={self.provider} model={self.model}")
        else:
            logger.info("LLM disabled (no API key set); features will fall back")

    async def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 512,
        temperature: float = 0.3,
        timeout: float = 8.0,
    ) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if self.provider == "anthropic":
                    r = await client.post(
                        f"{self.base_url}/v1/messages",
                        headers={
                            "x-api-key": self.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "system": system,
                            "messages": [{"role": "user", "content": user}],
                        },
                    )
                    r.raise_for_status()
                    data = r.json()
                    return data["content"][0]["text"]
                else:  # OpenAI-compatible (groq, openrouter, openai, together)
                    r = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": user},
                            ],
                        },
                    )
                    r.raise_for_status()
                    data = r.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"LLM call failed ({self.provider}): {e}")
            return None

    async def complete_json(self, system: str, user: str, **kwargs) -> Optional[dict]:
        text = await self.complete(system + "\n\nRespond with valid JSON only.", user, **kwargs)
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1].lstrip("json").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    return None
            return None


_client: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
