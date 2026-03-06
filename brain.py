"""Adaptive Intelligence — The Organism's Brain.

Hybrid reasoning engine:
  1. Rule-based heuristic analysis (always available)
  2. LLM-powered analysis (optional — via llm_client)

Analyzes cortex state and makes autonomous decisions:
  - What pipelines to spawn or mutate
  - When to consolidate memory
  - How to adjust behavior based on patterns
"""
from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("organism.brain")


@dataclass
class Decision:
    action: str
    target: str = ""
    reason: str = ""
    confidence: float = 0.0
    payload: dict = field(default_factory=dict)
    source: str = "rules"


class Brain:
    """The organism's adaptive intelligence — hybrid LLM + rule-based."""

    CONFIDENCE_THRESHOLD = 0.5

    def __init__(self):
        self.decisions_made: int = 0
        self.last_analysis: float = 0.0
        self._recent_decisions: list[str] = []
        self._cortex = None
        self._llm = None

        # Try to load LLM client (optional)
        try:
            from llm_client import LLMClient
            self._llm = LLMClient()
            if not self._llm.is_available:
                logger.info("Brain: LLM not reachable — rule-based mode")
                self._llm = None
            else:
                logger.info("Brain: LLM available (%s/%s)",
                            self._llm.provider, self._llm.model)
        except Exception:
            logger.info("Brain: No LLM configured — rule-based mode")

    def set_cortex(self, cortex):
        """Wire the cortex for memory-informed reasoning."""
        self._cortex = cortex

    def analyze(
        self,
        vitals: dict | None = None,
        pipeline_health: dict | None = None,
    ) -> list[Decision]:
        """Rule-based heuristic analysis.

        Scans patterns and produces decisions. Always available,
        no external dependencies.
        """
        decisions: list[Decision] = []
        vitals = vitals or {}
        pipeline_health = pipeline_health or {}

        # Rule 1: Consolidate if many unconsolidated episodic memories
        if self._cortex:
            try:
                episodes = self._cortex.recall_by_tags(["organism"], limit=50)
                if len(episodes) > 30:
                    decisions.append(Decision(
                        action="consolidate",
                        target="cortex",
                        reason=f"{len(episodes)} episodic memories — time to consolidate",
                        confidence=0.7,
                    ))
            except Exception:
                pass

        # Rule 2: Alert on high error rate
        errors = vitals.get("errors", 0)
        heartbeats = vitals.get("heartbeat_count", 1)
        if heartbeats > 10 and errors / heartbeats > 0.3:
            decisions.append(Decision(
                action="alert",
                target="health",
                reason=f"High error rate: {errors}/{heartbeats} pulses",
                confidence=0.9,
            ))

        # Rule 3: Suggest scan if no recent activity
        pipelines_executed = vitals.get("pipelines_executed", 0)
        if heartbeats > 50 and pipelines_executed == 0:
            decisions.append(Decision(
                action="scan",
                target="pipelines",
                reason="No pipelines executed — organism idle",
                confidence=0.5,
            ))

        # Rule 4: Quarantine recovery check
        quarantined = vitals.get("quarantined", 0)
        if quarantined > 0:
            decisions.append(Decision(
                action="scan",
                target="quarantine",
                reason=f"{quarantined} pipelines quarantined — review needed",
                confidence=0.6,
            ))

        self.decisions_made += len(decisions)
        self.last_analysis = time.time()
        for d in decisions:
            self._recent_decisions.append(f"{d.action}:{d.target}")
            if len(self._recent_decisions) > 20:
                self._recent_decisions.pop(0)

        return decisions

    def should_act(self, decision: Decision) -> bool:
        """Decide whether to act on a decision based on confidence."""
        return decision.confidence >= self.CONFIDENCE_THRESHOLD

    def stats(self) -> dict:
        """Brain statistics."""
        return {
            "decisions_made": self.decisions_made,
            "last_analysis": self.last_analysis,
            "recent_decisions": self._recent_decisions[-10:],
            "llm_available": self._llm is not None,
            "mode": "hybrid" if self._llm else "rule-based",
        }
