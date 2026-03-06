"""Heartbeat — The Organism's Core Pulse Lifecycle.

The heartbeat is the central event loop that drives all organs.
Each pulse executes a phase sequence:
  1. Immune sweep — check component health
  2. Brain think — analyze state, decide actions (every 5th pulse)
  3. Cortex metabolize — consolidate + decay memories (every 10th pulse)
  4. Self-report — log vital signs (every 30th pulse)
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime

from .cortex import Cortex, MemoryType
from .brain import Brain
from .immune import Immune

logger = logging.getLogger("organism")

WATCHDOG_PAUSE_THRESHOLD = 5
WATCHDOG_KILL_THRESHOLD = 10
WATCHDOG_EXIT_THRESHOLD = 20


@dataclass
class VitalSigns:
    """The organism's current state."""
    alive: bool = False
    heartbeat_count: int = 0
    born_at: float = 0.0
    last_pulse: float = 0.0
    errors: int = 0
    decisions_made: int = 0
    memories_consolidated: int = 0
    memories_decayed: int = 0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["uptime_seconds"] = round(time.time() - self.born_at, 1) if self.born_at else 0
        d["born_at_iso"] = (
            datetime.fromtimestamp(self.born_at).isoformat() if self.born_at else None
        )
        d["last_pulse_iso"] = (
            datetime.fromtimestamp(self.last_pulse).isoformat() if self.last_pulse else None
        )
        return d


class Heartbeat:
    """The organism's core lifecycle engine."""

    def __init__(self, name: str = "organism", tick_interval: float = 10.0):
        self.name = name
        self.tick_interval = tick_interval
        self.vitals = VitalSigns()
        self.autonomous_enabled = True
        self._task: asyncio.Task | None = None

        # The four organs
        self.cortex = Cortex()
        self.brain = Brain()
        self.immune = Immune()

    # ── Lifecycle ─────────────────────────────────────────

    async def birth(self) -> None:
        """Bring the organism to life."""
        self.vitals.alive = True
        self.vitals.born_at = time.time()

        self.cortex.remember(
            f"Organism '{self.name}' born.",
            memory_type=MemoryType.EPISODIC,
            tags=["organism", "birth"],
            importance=1.0,
        )

        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("🫀 Organism '%s' born — heartbeat started (tick=%ss)", self.name, self.tick_interval)

    async def death(self) -> None:
        """Graceful shutdown."""
        self.vitals.alive = False
        if self._task:
            self._task.cancel()

        elapsed = round(time.time() - self.vitals.born_at, 1)
        self.cortex.remember(
            f"Organism '{self.name}' died after {elapsed}s, "
            f"{self.vitals.heartbeat_count} heartbeats.",
            memory_type=MemoryType.EPISODIC,
            tags=["organism", "death"],
            importance=0.9,
        )
        self.cortex.close()
        logger.info("💀 Organism '%s' died after %ss", self.name, elapsed)

    # ── Heartbeat Loop ────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """The core pulse. Runs continuously with escalating watchdog.

        Escalation thresholds:
          5 consecutive failures  → 60s pause, then retry
          10 consecutive failures → disable autonomous mode
          20 consecutive failures → terminate process
        """
        restart_count = 0
        while self.vitals.alive:
            try:
                await self._pulse()
                restart_count = 0
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.vitals.errors += 1
                restart_count += 1
                logger.error("Pulse error (%d): %s", restart_count, e)

                if restart_count >= WATCHDOG_EXIT_THRESHOLD:
                    logger.critical(
                        "[WATCHDOG] %d consecutive failures — TERMINATING",
                        restart_count,
                    )
                    import os
                    os._exit(1)

                elif restart_count >= WATCHDOG_KILL_THRESHOLD:
                    if self.autonomous_enabled:
                        self.autonomous_enabled = False
                        logger.critical(
                            "[WATCHDOG] %d consecutive failures — AUTONOMY DISABLED",
                            restart_count,
                        )

                elif restart_count >= WATCHDOG_PAUSE_THRESHOLD:
                    logger.critical(
                        "[WATCHDOG] %d consecutive failures — pausing 60s",
                        restart_count,
                    )
                    await asyncio.sleep(60)

            await asyncio.sleep(self.tick_interval)

    async def _pulse(self) -> None:
        """A single heartbeat — the 4-phase cycle."""
        self.vitals.heartbeat_count += 1
        self.vitals.last_pulse = time.time()
        count = self.vitals.heartbeat_count

        # Phase 1: Immune sweep (every pulse)
        try:
            self.immune.record_success("heartbeat")
        except Exception as e:
            self.immune.record_failure("heartbeat", str(e))

        # Phase 2: Brain analysis (every 5th pulse)
        if count % 5 == 0 and self.autonomous_enabled:
            try:
                recent = self.cortex.recall_recent(hours=1, limit=10)
                recent_texts = [m.content[:100] for m in recent]

                decisions = await self.brain.analyze_llm(
                    vitals=self.vitals.to_dict(),
                    recent_memories=recent_texts,
                    health_summary=self.immune.summary(),
                )
                self.vitals.decisions_made += len(decisions)

                for dec in decisions:
                    if self.brain.should_act(dec):
                        logger.info(
                            "🧠 Decision: %s → %s (%.0f%%) — %s",
                            dec.action, dec.target,
                            dec.confidence * 100, dec.reason,
                        )
                self.immune.record_success("brain")
            except Exception as e:
                self.immune.record_failure("brain", str(e))
                logger.debug("Brain analysis skipped: %s", e)

        # Phase 3: Metabolism (every 10th pulse)
        if count % 10 == 0:
            try:
                # Consolidation
                consolidated = self.cortex.consolidate()
                self.vitals.memories_consolidated += len(consolidated)

                # Decay
                decayed = self.cortex.decay()
                self.vitals.memories_decayed += decayed

                self.immune.record_success("metabolism")
            except Exception as e:
                self.immune.record_failure("metabolism", str(e))
                logger.debug("Metabolism skipped: %s", e)

        # Phase 4: Self-report (every 30th pulse)
        if count % 30 == 0:
            try:
                vitals_dict = self.vitals.to_dict()
                self.cortex.remember(
                    f"Self-report: heartbeat={count}, "
                    f"errors={self.vitals.errors}, "
                    f"decisions={self.vitals.decisions_made}",
                    memory_type=MemoryType.EPISODIC,
                    tags=["organism", "self_report"],
                    importance=0.3,
                )
                logger.info(
                    "📊 Pulse #%d — errors=%d decisions=%d memories=%s",
                    count, self.vitals.errors, self.vitals.decisions_made,
                    self.cortex.stats()["total_memories"],
                )
            except Exception as e:
                logger.debug("Self-report skipped: %s", e)

    # ── Status ────────────────────────────────────────────

    def status(self) -> dict:
        """Full organism status."""
        return {
            "name": self.name,
            "vitals": self.vitals.to_dict(),
            "brain": self.brain.stats(),
            "immune": self.immune.summary(),
            "cortex": self.cortex.stats(),
        }
