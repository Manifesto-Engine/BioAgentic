"""LLM Client — Optional provider-agnostic interface for organism reasoning.

Backends (priority order):
  1. Ollama   — local, zero-cost, sovereign
  2. NVIDIA   — free-tier cloud fallback
  3. OpenAI   — paid cloud, last resort

If no provider is available, the Brain falls back to rule-based heuristics.
"""
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("organism.llm")

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_TIMEOUT_S = int(os.environ.get("LLM_TIMEOUT_S", "30"))
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "1024"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


@dataclass
class LLMResponse:
    content: str = ""
    success: bool = False
    error: str = ""
    provider: str = ""
    model: str = ""
    latency_ms: float = 0.0


class LLMClient:
    """Provider-agnostic LLM client with automatic fallback."""

    def __init__(
        self,
        provider: str = LLM_PROVIDER,
        model: str = LLM_MODEL,
        timeout_s: int = LLM_TIMEOUT_S,
        max_tokens: int = LLM_MAX_TOKENS,
    ):
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.provider = self._resolve_provider(provider)
        self.model = model or self._default_model()
        self.total_calls = 0

    @property
    def is_available(self) -> bool:
        """Check if the resolved provider is reachable."""
        if self.provider == "ollama":
            try:
                import httpx
                r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
                return r.status_code == 200
            except Exception:
                return False
        if self.provider == "nvidia":
            return bool(NVIDIA_API_KEY)
        if self.provider == "openai":
            return bool(OPENAI_API_KEY)
        return False

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion. Blocks (sync). Returns LLMResponse."""
        start = time.monotonic()
        try:
            if self.provider == "ollama":
                resp = self._ollama(prompt, system, temperature)
            elif self.provider == "nvidia":
                resp = self._nvidia(prompt, system, temperature)
            elif self.provider == "openai":
                resp = self._openai(prompt, system, temperature)
            else:
                return LLMResponse(error="No LLM provider available")

            resp.latency_ms = (time.monotonic() - start) * 1000
            resp.provider = self.provider
            resp.model = self.model
            self.total_calls += 1
            return resp
        except Exception as e:
            return LLMResponse(
                error=str(e),
                provider=self.provider,
                model=self.model,
                latency_ms=(time.monotonic() - start) * 1000,
            )

    def _ollama(self, prompt: str, system: str, temperature: float) -> LLMResponse:
        import httpx
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": self.max_tokens},
        }
        r = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        return LLMResponse(content=data.get("response", ""), success=True)

    def _nvidia(self, prompt: str, system: str, temperature: float) -> LLMResponse:
        import httpx
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        r = httpx.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return LLMResponse(content=content, success=True)

    def _openai(self, prompt: str, system: str, temperature: float) -> LLMResponse:
        import httpx
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        r = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": self.max_tokens,
            },
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return LLMResponse(content=content, success=True)

    def _resolve_provider(self, provider: str) -> str:
        if provider != "auto":
            return provider
        # Auto-detect: try Ollama first, then NVIDIA, then OpenAI
        try:
            import httpx
            r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if r.status_code == 200:
                return "ollama"
        except Exception:
            pass
        if NVIDIA_API_KEY:
            return "nvidia"
        if OPENAI_API_KEY:
            return "openai"
        return "none"

    def _default_model(self) -> str:
        defaults = {
            "ollama": "llama3.2",
            "nvidia": "meta/llama-3.3-70b-instruct",
            "openai": "gpt-4o-mini",
        }
        return defaults.get(self.provider, "")

    def stats(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "total_calls": self.total_calls,
            "available": self.is_available,
        }
