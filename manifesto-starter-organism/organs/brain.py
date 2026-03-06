"""Brain — Adaptive Intelligence.

Hybrid reasoning engine:
  1. LLM-powered analysis via Ollama/NVIDIA/OpenAI (primary)
  2. Rule-based heuristics (fallback when LLM unavailable)

Analyzes organism state and produces autonomous decisions.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger("organism.brain")

# ── LLM Config ────────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT_S = int(os.getenv("LLM_TIMEOUT_S", "60"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
LLM_COOLDOWN_S = float(os.getenv("LLM_COOLDOWN_S", "5"))
LLM_SESSION_BUDGET = int(os.getenv("LLM_SESSION_TOKEN_BUDGET", "500000"))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class LLMProvider(str, Enum):
    AUTO = "auto"
    OLLAMA = "ollama"
    NVIDIA = "nvidia"
    OPENAI = "openai"


@dataclass
class Decision:
    """A single autonomous decision."""
    action: str
    target: str = ""
    reason: str = ""
    confidence: float = 0.0
    source: str = "rules"


BRAIN_SYSTEM_PROMPT = """You are the autonomous brain of a living software organism.
Analyze the organism's current state and decide what actions to take.

Actions: spawn, scan, consolidate, adjust, explore, ignore.

RULES:
1. Only suggest actions with confidence >= 0.6
2. Never suggest more than 3 actions per cycle
3. Be specific — include target names and reasons
4. If errors are accumulating, prioritize error analysis
5. If memory is growing fast, suggest consolidation

Respond ONLY with valid JSON:
```json
{
  "decisions": [
    {"action": "...", "target": "...", "reason": "...", "confidence": 0.0}
  ],
  "reasoning": "brief chain of thought"
}
```"""


class Brain:
    """The organism's adaptive intelligence — hybrid LLM + rule-based."""

    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        self.decisions_made: int = 0
        self.llm_calls: int = 0
        self.llm_failures: int = 0

        # LLM state
        self._provider = LLMProvider(LLM_PROVIDER)
        self._model = LLM_MODEL
        self._session_tokens: int = 0
        self._last_call_at: float = 0.0

        if self._provider == LLMProvider.AUTO:
            self._provider = self._auto_detect_provider()
        if not self._model:
            self._model = self._default_model()

        logger.info("🧠 Brain initialized — LLM: %s/%s", self._provider.value, self._model)

    # ── LLM Provider Detection ────────────────────────────

    @staticmethod
    def _auto_detect_provider() -> LLMProvider:
        if os.getenv("NVIDIA_API_KEY"):
            return LLMProvider.NVIDIA
        try:
            resp = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
            if resp.status_code == 200:
                return LLMProvider.OLLAMA
        except Exception:
            pass
        if os.getenv("OPENAI_API_KEY"):
            return LLMProvider.OPENAI
        return LLMProvider.OLLAMA

    def _default_model(self) -> str:
        return {
            LLMProvider.NVIDIA: "meta/llama-3.3-70b-instruct",
            LLMProvider.OLLAMA: "qwen3:8b",
            LLMProvider.OPENAI: "gpt-4o-mini",
        }.get(self._provider, "llama3")

    # ── LLM Generation ────────────────────────────────────

    async def _llm_generate(
        self, prompt: str, system: str = "", temperature: float = 0.7,
    ) -> str | None:
        """Generate a completion from the configured LLM provider."""
        # Cooldown gate
        elapsed = time.time() - self._last_call_at
        if elapsed < LLM_COOLDOWN_S and self._last_call_at > 0:
            return None

        # Budget gate
        if self._session_tokens >= LLM_SESSION_BUDGET:
            logger.warning("🧠 LLM budget exhausted (%d/%d)", self._session_tokens, LLM_SESSION_BUDGET)
            return None

        self._last_call_at = time.time()

        try:
            if self._provider == LLMProvider.OLLAMA:
                content = await self._ollama(prompt, system, temperature)
            elif self._provider == LLMProvider.NVIDIA:
                content = await self._openai_compat(
                    NVIDIA_BASE_URL, os.getenv("NVIDIA_API_KEY", ""),
                    prompt, system, temperature,
                )
            elif self._provider == LLMProvider.OPENAI:
                content = await self._openai_compat(
                    "https://api.openai.com/v1", os.getenv("OPENAI_API_KEY", ""),
                    prompt, system, temperature,
                )
            else:
                return None

            self.llm_calls += 1
            return content

        except Exception as e:
            self.llm_failures += 1
            logger.warning("🧠 LLM call failed: %s", e)
            return None

    async def _ollama(
        self, prompt: str, system: str, temperature: float,
    ) -> str:
        payload: dict = {
            "model": self._model, "prompt": prompt, "stream": False,
            "options": {"temperature": temperature, "num_predict": LLM_MAX_TOKENS},
        }
        if system:
            payload["system"] = system

        def _sync():
            with httpx.Client(timeout=LLM_TIMEOUT_S) as c:
                r = c.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
                r.raise_for_status()
                return r.json()

        data = await asyncio.to_thread(_sync)
        self._session_tokens += data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        return data.get("response", "").strip()

    async def _openai_compat(
        self, base_url: str, api_key: str,
        prompt: str, system: str, temperature: float,
    ) -> str:
        if not api_key:
            raise ValueError(f"API key not set for {base_url}")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_S) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                json={"model": self._model, "messages": messages,
                      "temperature": temperature, "max_tokens": LLM_MAX_TOKENS},
                headers={"Authorization": f"Bearer {api_key}",
                         "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        usage = data.get("usage", {})
        self._session_tokens += usage.get("total_tokens", 0)
        return data["choices"][0]["message"]["content"].strip()

    # ── Analysis ──────────────────────────────────────────

    async def analyze_llm(
        self,
        vitals: dict,
        recent_memories: list[str],
        health_summary: dict,
    ) -> list[Decision]:
        """LLM-powered brain analysis. Falls back to rules on failure."""
        memories_block = "\n".join(f"  - {m}" for m in recent_memories[:10]) or "  (none)"
        degraded = health_summary.get("degraded", [])

        prompt = f"""## Organism State

**Vitals:**
- Uptime: {vitals.get('uptime_seconds', 0):.0f}s
- Heartbeats: {vitals.get('heartbeat_count', 0)}
- Errors: {vitals.get('errors', 0)}
- Decisions made: {vitals.get('decisions_made', 0)}

**Health:**
- Quarantined: {health_summary.get('quarantined_count', 0)}
- Degraded: {', '.join(degraded) if degraded else 'none'}

**Recent Memories:**
{memories_block}

What should the organism do next?"""

        content = await self._llm_generate(prompt, system=BRAIN_SYSTEM_PROMPT)
        if not content:
            return self.analyze_rules(vitals, health_summary)

        return self._parse_llm_response(content)

    def _parse_llm_response(self, content: str) -> list[Decision]:
        """Parse LLM JSON response into Decision objects."""
        try:
            # Strip markdown fences if present
            cleaned = content
            if "```" in cleaned:
                parts = cleaned.split("```")
                for part in parts:
                    stripped = part.strip()
                    if stripped.startswith("json"):
                        stripped = stripped[4:].strip()
                    if stripped.startswith("{"):
                        cleaned = stripped
                        break

            data = json.loads(cleaned)
            decisions = []
            for d in data.get("decisions", []):
                dec = Decision(
                    action=d.get("action", "ignore"),
                    target=d.get("target", ""),
                    reason=d.get("reason", ""),
                    confidence=float(d.get("confidence", 0.0)),
                    source="llm",
                )
                if dec.confidence >= self.CONFIDENCE_THRESHOLD:
                    decisions.append(dec)
            self.decisions_made += len(decisions)
            return decisions[:3]

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("🧠 Failed to parse LLM response: %s", e)
            return []

    # ── Rule-Based Fallback ───────────────────────────────

    def analyze_rules(
        self, vitals: dict, health_summary: dict,
    ) -> list[Decision]:
        """Rule-based heuristic analysis (fallback)."""
        decisions: list[Decision] = []

        # Rule 1: Error accumulation → investigate
        errors = vitals.get("errors", 0)
        heartbeats = vitals.get("heartbeat_count", 1)
        error_rate = errors / max(heartbeats, 1)
        if error_rate > 0.1:
            decisions.append(Decision(
                action="scan", target="error_logs",
                reason=f"Error rate {error_rate:.1%} exceeds threshold",
                confidence=0.8, source="rules",
            ))

        # Rule 2: Quarantined components → alert
        quarantined = health_summary.get("quarantined_count", 0)
        if quarantined > 0:
            decisions.append(Decision(
                action="scan", target="quarantined_components",
                reason=f"{quarantined} components quarantined",
                confidence=0.7, source="rules",
            ))

        # Rule 3: Long uptime without consolidation → consolidate
        uptime = vitals.get("uptime_seconds", 0)
        consolidated = vitals.get("memories_consolidated", 0)
        if uptime > 3600 and consolidated == 0:
            decisions.append(Decision(
                action="consolidate", target="cortex",
                reason="No consolidation in over 1 hour",
                confidence=0.7, source="rules",
            ))

        if not decisions:
            decisions.append(Decision(
                action="ignore", target="",
                reason="All systems nominal", confidence=0.9,
                source="rules",
            ))

        self.decisions_made += len(decisions)
        return decisions[:3]

    def should_act(self, decision: Decision) -> bool:
        return decision.confidence >= self.CONFIDENCE_THRESHOLD

    # ── Stats ─────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "provider": self._provider.value,
            "model": self._model,
            "decisions_made": self.decisions_made,
            "llm_calls": self.llm_calls,
            "llm_failures": self.llm_failures,
            "session_tokens": self._session_tokens,
            "session_budget": LLM_SESSION_BUDGET,
            "confidence_threshold": self.CONFIDENCE_THRESHOLD,
        }
