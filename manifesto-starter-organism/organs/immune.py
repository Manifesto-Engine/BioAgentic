"""Immune System — Input Sanitization + Health Monitoring.

Tracks per-component health metrics and auto-quarantines
failures. Sanitizes untrusted input before it reaches organs.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field

logger = logging.getLogger("organism.immune")

QUARANTINE_THRESHOLD = 3
HEALTH_DECAY = 0.85
HEALTH_RECOVER = 1.02

# Dangerous patterns that should never pass through
_DANGEROUS_PATTERNS = [
    re.compile(r"__(?:class|bases|subclasses|import|builtins)__"),
    re.compile(r"\b(?:eval|exec|compile|__import__)\s*\("),
    re.compile(r"\bos\.(?:system|popen|exec|remove|unlink)\b"),
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsys\.exit\b"),
    re.compile(r"(?:rm\s+-rf|chmod\s+777|curl.*\|\s*(?:sh|bash))"),
]


@dataclass
class HealthRecord:
    """Health record for a single component."""
    name: str
    score: float = 100.0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    quarantined: bool = False
    quarantined_at: float = 0.0
    last_check: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": round(self.score, 1),
            "successes": self.successes,
            "failures": self.failures,
            "quarantined": self.quarantined,
        }


class Immune:
    """Monitors component health and sanitizes input."""

    def __init__(self):
        self._health: dict[str, HealthRecord] = {}
        self._rate_counters: dict[str, list[float]] = {}

    # ── Health Tracking ───────────────────────────────────

    def get_health(self, name: str) -> HealthRecord:
        if name not in self._health:
            self._health[name] = HealthRecord(name=name)
        return self._health[name]

    def record_success(self, name: str) -> None:
        h = self.get_health(name)
        h.successes += 1
        h.consecutive_failures = 0
        h.score = min(100.0, h.score * HEALTH_RECOVER)
        h.last_check = time.time()

    def record_failure(self, name: str, error: str = "") -> None:
        h = self.get_health(name)
        h.failures += 1
        h.consecutive_failures += 1
        h.score = max(0.0, h.score * HEALTH_DECAY)
        h.last_check = time.time()

        if h.consecutive_failures >= QUARANTINE_THRESHOLD and not h.quarantined:
            h.quarantined = True
            h.quarantined_at = time.time()
            logger.warning(
                "🛡️ QUARANTINED %s — %d consecutive failures: %s",
                name, h.consecutive_failures, error[:200],
            )

    def is_quarantined(self, name: str) -> bool:
        return self.get_health(name).quarantined

    def release(self, name: str) -> None:
        """Release a component from quarantine."""
        h = self.get_health(name)
        h.quarantined = False
        h.consecutive_failures = 0
        h.score = 50.0
        logger.info("🛡️ Released %s from quarantine", name)

    def get_quarantined(self) -> list[str]:
        return [n for n, h in self._health.items() if h.quarantined]

    # ── Input Sanitization ────────────────────────────────

    def sanitize(self, text: str) -> tuple[bool, str]:
        """Check text for dangerous patterns.

        Returns (is_safe, reason). If unsafe, reason explains why.
        """
        for pattern in _DANGEROUS_PATTERNS:
            match = pattern.search(text)
            if match:
                reason = f"Blocked dangerous pattern: {match.group()!r}"
                logger.warning("🛡️ %s", reason)
                return False, reason
        return True, ""

    # ── Rate Limiting ─────────────────────────────────────

    def check_rate(self, key: str, max_per_minute: int = 60) -> bool:
        """Returns True if under rate limit, False if exceeded."""
        now = time.time()
        window = self._rate_counters.setdefault(key, [])
        # Purge old entries
        self._rate_counters[key] = [t for t in window if now - t < 60]
        if len(self._rate_counters[key]) >= max_per_minute:
            return False
        self._rate_counters[key].append(now)
        return True

    # ── Summary ───────────────────────────────────────────

    def summary(self) -> dict:
        """Overall immune system health summary."""
        records = list(self._health.values())
        quarantined = [h.name for h in records if h.quarantined]
        degraded = [h.name for h in records if h.score < 50 and not h.quarantined]
        return {
            "total_components": len(records),
            "quarantined": quarantined,
            "quarantined_count": len(quarantined),
            "degraded": degraded,
            "degraded_count": len(degraded),
            "components": {h.name: h.to_dict() for h in records},
        }
