"""Immune System — Pipeline Health Monitoring & Quarantine.

Tracks per-pipeline health metrics:
  - Success/failure counts + health score (0-100)
  - Auto-quarantine after 3 consecutive failures
  - Reflex rate limiting (max 5 fires/min)
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("organism.immune")

HEALTH_DECAY = 0.85
HEALTH_RECOVER = 1.02
MAX_REFLEX_RATE = 5
QUARANTINE_THRESHOLD = 3


@dataclass
class PipelineHealth:
    """Health record for a single pipeline."""
    name: str
    score: float = 100.0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    quarantined: bool = False
    quarantined_at: float = 0.0
    last_run: float = 0.0
    total_runs: int = 0

    @property
    def success_rate(self) -> float:
        total = self.successes + self.failures
        return self.successes / total if total > 0 else 1.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": round(self.score, 1),
            "successes": self.successes,
            "failures": self.failures,
            "consecutive_failures": self.consecutive_failures,
            "quarantined": self.quarantined,
            "success_rate": round(self.success_rate, 3),
            "total_runs": self.total_runs,
        }


class ImmuneSystem:
    """Monitors pipeline health and quarantines failures."""

    def __init__(self):
        self._health: dict[str, PipelineHealth] = {}
        self._reflex_timestamps: dict[str, list[float]] = {}

    def get_health(self, name: str) -> PipelineHealth:
        if name not in self._health:
            self._health[name] = PipelineHealth(name=name)
        return self._health[name]

    def record_success(self, name: str):
        """Record a successful pipeline execution."""
        h = self.get_health(name)
        h.successes += 1
        h.total_runs += 1
        h.consecutive_failures = 0
        h.last_run = time.time()
        h.score = min(100.0, h.score * HEALTH_RECOVER)

        if h.quarantined:
            h.quarantined = False
            h.quarantined_at = 0.0
            logger.info("Pipeline %s released from quarantine", name)

    def record_failure(self, name: str, error: str = ""):
        """Record a failed pipeline execution."""
        h = self.get_health(name)
        h.failures += 1
        h.total_runs += 1
        h.consecutive_failures += 1
        h.last_run = time.time()
        h.score = max(0.0, h.score * HEALTH_DECAY)

        if h.consecutive_failures >= QUARANTINE_THRESHOLD and not h.quarantined:
            h.quarantined = True
            h.quarantined_at = time.time()
            logger.warning(
                "Pipeline %s quarantined after %d consecutive failures: %s",
                name, h.consecutive_failures, error[:100],
            )

    def is_quarantined(self, name: str) -> bool:
        """Check if a pipeline is quarantined."""
        h = self._health.get(name)
        return h.quarantined if h else False

    def get_quarantined(self) -> list[str]:
        """Get all quarantined pipeline names."""
        return [n for n, h in self._health.items() if h.quarantined]

    def check_reflex_rate(self, pipeline_name: str) -> bool:
        """Returns True if the reflex is within rate limits."""
        now = time.time()
        timestamps = self._reflex_timestamps.setdefault(pipeline_name, [])

        # Prune timestamps older than 60 seconds
        cutoff = now - 60
        self._reflex_timestamps[pipeline_name] = [
            t for t in timestamps if t > cutoff
        ]
        timestamps = self._reflex_timestamps[pipeline_name]

        if len(timestamps) >= MAX_REFLEX_RATE:
            return False

        timestamps.append(now)
        return True

    def summary(self) -> dict:
        """Summary of all pipeline health states."""
        return {
            "total_tracked": len(self._health),
            "quarantined": len(self.get_quarantined()),
            "pipelines": {
                name: h.to_dict() for name, h in self._health.items()
            },
        }
