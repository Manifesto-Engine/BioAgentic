"""Sovereign Organism — The Living Runtime.

Not a compiler. Not a script runner. A living process.

It has:
  - HEARTBEAT — continuous pulse loop
  - REFLEXES  — @every("30s") and @on("event") auto-triggers
  - METABOLISM — cortex consolidation + memory decay
  - SELF-AWARENESS — logs its own state to the cortex
  - BRAIN — rule-based + optional LLM reasoning

Usage:
    The organism starts as a background asyncio task when the
    FastAPI server boots. It pulses every tick_interval seconds,
    checking for scheduled pipelines, consolidating memory, and
    maintaining its own vital signs.
"""
from __future__ import annotations

import asyncio
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

from cortex import Cortex, MemoryType
from brain import Brain
from immune import ImmuneSystem
from sovereign_lang import parse, generate

logger = logging.getLogger("organism")


# ── Vital Signs ───────────────────────────────────────────

@dataclass
class VitalSigns:
    """The organism's current state."""
    alive: bool = False
    heartbeat_count: int = 0
    born_at: float = 0.0
    last_pulse: float = 0.0
    pipelines_executed: int = 0
    memories_consolidated: int = 0
    memories_decayed: int = 0
    reflexes_fired: int = 0
    decisions_made: int = 0
    quarantined: int = 0
    events_emitted: int = 0
    errors: int = 0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["uptime_seconds"] = round(time.time() - self.born_at, 1) if self.born_at else 0
        d["born_at_iso"] = (
            datetime.fromtimestamp(self.born_at).isoformat() if self.born_at else None
        )
        return d


# ── Reflex Registry ──────────────────────────────────────

@dataclass
class Reflex:
    """A scheduled or event-triggered pipeline."""
    pipeline_name: str
    trigger_type: str           # "every" or "on"
    trigger_value: str          # "30s", "1m", "5m" or event name
    interval_seconds: float = 0
    last_fired: float = 0.0
    fire_count: int = 0


def _parse_interval(value: str) -> float:
    """Parse human-readable interval: 30s, 1m, 5m, 1h."""
    value = value.strip().lower()
    if value.endswith("s"):
        return float(value[:-1])
    if value.endswith("m"):
        return float(value[:-1]) * 60
    if value.endswith("h"):
        return float(value[:-1]) * 3600
    return float(value)


# ── The Organism ─────────────────────────────────────────

class Organism:
    """The living runtime."""

    WATCHDOG_PAUSE_THRESHOLD = 5
    WATCHDOG_KILL_THRESHOLD = 15

    def __init__(self, tick_interval: float = 10.0):
        self.tick_interval = tick_interval
        self.vitals = VitalSigns()
        self.reflexes: list[Reflex] = []
        self._task: asyncio.Task | None = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._pipeline_dir = Path(__file__).parent / "pipelines"
        self._event_log: list[dict] = []

        # ── Eager organs ──
        self.cortex = Cortex()
        self.brain = Brain()
        self.immune = ImmuneSystem()

        # Wire brain to cortex
        self.brain.set_cortex(self.cortex)

    # ── Lifecycle ─────────────────────────────────────

    async def birth(self):
        """Bring the organism to life."""
        self.vitals.alive = True
        self.vitals.born_at = time.time()
        self._log("BIRTH", "Organism is alive")

        # Load reflexes from registered pipelines
        self._scan_for_reflexes()

        # Record birth in cortex
        self._remember(
            "Organism born. Sovereign Script runtime active.",
            tags=["organism", "birth", "identity"],
            importance=1.0,
        )

        # Start the heartbeat
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("🫀 Organism born — heartbeat started (%.1fs tick)", self.tick_interval)

    async def death(self):
        """Graceful shutdown."""
        self.vitals.alive = False
        if self._task:
            self._task.cancel()

        elapsed = round(time.time() - self.vitals.born_at, 1)
        self._remember(
            f"Organism died after {elapsed}s, "
            f"{self.vitals.heartbeat_count} heartbeats, "
            f"{self.vitals.pipelines_executed} pipelines executed",
            tags=["organism", "death", "identity"],
            importance=0.9,
        )
        self.cortex.close()
        logger.info("💀 Organism died — %d heartbeats", self.vitals.heartbeat_count)

    # ── Heartbeat ─────────────────────────────────────

    async def _heartbeat_loop(self):
        """The core pulse. Runs continuously with basic watchdog."""
        consecutive_failures = 0
        while self.vitals.alive:
            try:
                await self._pulse()
                consecutive_failures = 0
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.vitals.errors += 1
                consecutive_failures += 1
                logger.error("Pulse error (%d): %s", consecutive_failures, e)

                if consecutive_failures >= self.WATCHDOG_KILL_THRESHOLD:
                    logger.critical(
                        "[WATCHDOG] %d consecutive failures — stopping heartbeat",
                        consecutive_failures,
                    )
                    break

                if consecutive_failures >= self.WATCHDOG_PAUSE_THRESHOLD:
                    logger.warning(
                        "[WATCHDOG] %d consecutive failures — pausing 60s",
                        consecutive_failures,
                    )
                    await asyncio.sleep(60)

            await asyncio.sleep(self.tick_interval)

    async def _pulse(self):
        """A single heartbeat — the organism's life cycle."""
        self.vitals.heartbeat_count += 1
        self.vitals.last_pulse = time.time()
        count = self.vitals.heartbeat_count

        # Phase 1: Check reflexes (scheduled pipelines)
        await self._check_reflexes()

        # Phase 2: Process event queue
        await self._process_events()

        # Phase 3: Metabolism (every 10th pulse)
        if count % 10 == 0:
            self._metabolize()

        # Phase 4: Self-awareness (every 30th pulse)
        if count % 30 == 0:
            self._self_report()

        # Phase 5: Brain analysis (every 5th pulse)
        if count % 5 == 0:
            self._think()

        # Phase 6: Idle logging
        if count % 100 == 0:
            logger.info(
                "💓 Pulse #%d — %d pipelines, %d memories, %d errors",
                count, self.vitals.pipelines_executed,
                self.cortex.count(), self.vitals.errors,
            )

    # ── Reflexes ──────────────────────────────────────

    def register_reflex(
        self, pipeline_name: str, trigger_type: str, trigger_value: str,
    ):
        """Register a new reflex (auto-triggered pipeline)."""
        reflex = Reflex(
            pipeline_name=pipeline_name,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
        )
        if trigger_type == "every":
            reflex.interval_seconds = _parse_interval(trigger_value)
        self.reflexes.append(reflex)
        logger.info("Reflex registered: %s @%s(%s)", pipeline_name, trigger_type, trigger_value)

    async def _check_reflexes(self):
        """Fire any reflexes whose time has come."""
        now = time.time()
        for reflex in self.reflexes:
            if reflex.trigger_type != "every":
                continue
            if now - reflex.last_fired >= reflex.interval_seconds:
                await self._fire_reflex(reflex)

    async def _fire_reflex(self, reflex: Reflex):
        """Execute a reflex pipeline."""
        if self.immune.is_quarantined(reflex.pipeline_name):
            return
        if not self.immune.check_reflex_rate(reflex.pipeline_name):
            return

        try:
            output = self._execute_pipeline(reflex.pipeline_name)
            reflex.last_fired = time.time()
            reflex.fire_count += 1
            self.vitals.reflexes_fired += 1
            self.immune.record_success(reflex.pipeline_name)
        except Exception as e:
            self.immune.record_failure(reflex.pipeline_name, str(e))

    # ── Events ────────────────────────────────────────

    async def emit_event(self, event_name: str, data: dict | None = None):
        """Emit an event that may trigger @on reflexes."""
        self.vitals.events_emitted += 1
        event = {"event": event_name, "data": data or {}, "time": time.time()}
        self._event_log.append(event)
        if len(self._event_log) > 100:
            self._event_log = self._event_log[-100:]
        await self._event_queue.put(event)

    async def _process_events(self):
        """Process pending events and fire matching @on reflexes."""
        while not self._event_queue.empty():
            event = await self._event_queue.get()
            for reflex in self.reflexes:
                if reflex.trigger_type == "on" and reflex.trigger_value == event["event"]:
                    await self._fire_reflex(reflex)

    # ── Metabolism ────────────────────────────────────

    def _metabolize(self):
        """Cortex maintenance — consolidate and decay."""
        try:
            consolidated = self.cortex.consolidate()
            self.vitals.memories_consolidated += len(consolidated)
            if consolidated:
                self._log("METABOLISM", f"Consolidated {len(consolidated)} memories")
        except Exception as e:
            logger.debug("Consolidation skipped: %s", e)

        try:
            decayed = self.cortex.decay()
            self.vitals.memories_decayed += decayed
        except Exception as e:
            logger.debug("Decay skipped: %s", e)

    # ── Self-Awareness ────────────────────────────────

    def _self_report(self):
        """The organism reflects on its own state."""
        self._remember(
            f"Vital signs: pulse #{self.vitals.heartbeat_count}, "
            f"{self.vitals.pipelines_executed} pipelines executed, "
            f"{self.vitals.errors} errors, "
            f"{self.cortex.count()} memories stored",
            tags=["organism", "self_report"],
            importance=0.3,
        )

    # ── Brain ─────────────────────────────────────────

    def _think(self):
        """Brain analysis — rule-based + optional LLM reasoning."""
        try:
            decisions = self.brain.analyze(
                vitals=self.vitals.to_dict(),
                pipeline_health=self.immune.summary(),
            )
            for decision in decisions:
                if self.brain.should_act(decision):
                    self.vitals.decisions_made += 1
                    self._log("BRAIN", f"{decision.action}: {decision.reason}")

                    if decision.action == "consolidate":
                        self._metabolize()
        except Exception as e:
            logger.debug("Brain analysis skipped: %s", e)

    # ── Pipeline Execution ────────────────────────────

    def _execute_pipeline(self, name: str) -> str:
        """Compile and execute a .sov pipeline by name."""
        from sandbox import sandbox_code

        path = self._pipeline_dir / f"{name}.sov"
        if not path.exists():
            raise FileNotFoundError(f"Pipeline not found: {name}")

        source = path.read_text()
        ast = parse(source)
        python_code = generate(ast)

        sandboxed, violations = sandbox_code(python_code)
        if violations:
            raise RuntimeError(f"Sandbox violations: {violations}")

        # Execute in isolated namespace
        namespace = {"_CORTEX": self.cortex, "_EMIT_QUEUE": []}
        exec(sandboxed, namespace)

        self.vitals.pipelines_executed += 1

        # Process emitted events
        for evt in namespace.get("_EMIT_QUEUE", []):
            asyncio.ensure_future(
                self.emit_event(evt["event"], evt.get("data"))
            )

        return namespace.get("_result", "")

    def _scan_for_reflexes(self):
        """Scan pipeline files for @every/@on directives in comments."""
        if not self._pipeline_dir.exists():
            return
        for path in self._pipeline_dir.glob("*.sov"):
            try:
                first_line = path.read_text().splitlines()[0] if path.stat().st_size > 0 else ""
                if first_line.startswith("// @every("):
                    interval = first_line.split("(")[1].split(")")[0].strip('"\'')
                    self.register_reflex(path.stem, "every", interval)
                elif first_line.startswith("// @on("):
                    event = first_line.split("(")[1].split(")")[0].strip('"\'')
                    self.register_reflex(path.stem, "on", event)
            except Exception:
                pass

    # ── Helpers ───────────────────────────────────────

    def _remember(self, content: str, tags: list[str] | None = None, importance: float = 0.5):
        """Convenience: write to cortex."""
        try:
            self.cortex.remember(
                content=content,
                memory_type=MemoryType.EPISODIC,
                tags=tags,
                importance=importance,
                source="organism",
            )
        except Exception as e:
            logger.debug("Cortex write failed: %s", e)

    def _log(self, phase: str, message: str):
        """Structured log output."""
        logger.info("[%10s] %s", phase, message)
