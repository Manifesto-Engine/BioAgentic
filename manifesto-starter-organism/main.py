"""Manifesto Starter Organism — FastAPI Entry Point.

A minimal, closed-loop organism server. No federation, no SovCloud.
Four core organs boot on startup and a single /pulse endpoint
drives the interaction loop.

Start:
    uvicorn main:app --reload
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from organs.heartbeat import Heartbeat

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-18s │ %(message)s",
    datefmt="%H:%M:%S",
)

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title="Manifesto Starter Organism",
    version="0.1.0",
    description="Minimal living agent — 4 organs, 1 endpoint, zero config.",
)

# Heartbeat owns all organs (cortex, brain, immune)
organism = Heartbeat(name="starter", tick_interval=10.0)


# ── Request / Response Models ─────────────────────────────
class PulseRequest(BaseModel):
    prompt: str
    context_id: str = "default_session"


class PulseResponse(BaseModel):
    status: str
    response: str
    context_id: str
    pulse_count: int


# ── Lifecycle Events ──────────────────────────────────────
@app.on_event("startup")
async def awaken_organism():
    """Fires when uvicorn boots. Initializes the organism's lifecycle."""
    print("Initializing Manifesto Engine Starter Organism...")
    await organism.birth()
    print("Organism is breathing. Cortex online.")


@app.on_event("shutdown")
async def sleep_organism():
    """Graceful shutdown. Saves state and stops the heartbeat."""
    print("Initiating sleep cycle...")
    await organism.death()
    print("Organism is dormant.")


# ── Primary Interaction Endpoint ──────────────────────────
@app.post("/pulse", response_model=PulseResponse)
async def trigger_pulse(request: PulseRequest):
    """The primary interaction loop.

    1. Immune check — sanitize input
    2. Cortex retrieval — fetch memory context
    3. Brain processing — produce a response
    4. Cortex update — store the interaction
    """
    immune = organism.immune
    cortex = organism.cortex
    brain = organism.brain

    # 1. Immune check
    is_safe, reason = immune.sanitize(request.prompt)
    if not is_safe:
        immune.record_failure("pulse_input", reason)
        raise HTTPException(status_code=400, detail=f"Immune system rejected input: {reason}")
    immune.record_success("pulse_input")

    # 2. Rate limit
    if not immune.check_rate(f"pulse:{request.context_id}"):
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    # 3. Cortex retrieval — pull relevant memories
    memories = cortex.recall(request.prompt, limit=5)
    memory_context = [m.content for m in memories] if memories else []

    # 4. Brain processing
    try:
        decisions = await brain.analyze_llm(
            vitals=organism.vitals.to_dict(),
            recent_memories=memory_context,
            health_summary=immune.summary(),
        )
        brain_response = "; ".join(
            f"{d.action}→{d.target} ({d.reason})" for d in decisions
        ) if decisions else "No autonomous decisions — organism stable."
    except Exception:
        # Fallback to rule-based
        rule_decisions = brain.analyze_rules(
            vitals=organism.vitals.to_dict(),
            health_summary=immune.summary(),
        )
        brain_response = "; ".join(
            f"{d.action}→{d.target} ({d.reason})" for d in rule_decisions
        ) if rule_decisions else "Rule-based: all systems nominal."

    # 5. Cortex update — store the interaction
    from organs.cortex import MemoryType
    cortex.remember(
        f"[{request.context_id}] prompt={request.prompt!r} → {brain_response[:200]}",
        memory_type=MemoryType.EPISODIC,
        tags=["interaction", request.context_id],
        importance=0.5,
        source="pulse_endpoint",
    )

    return PulseResponse(
        status="alive",
        response=brain_response,
        context_id=request.context_id,
        pulse_count=organism.vitals.heartbeat_count,
    )


# ── Status Endpoint ───────────────────────────────────────
@app.get("/status")
async def get_status():
    """Full organism status — vitals, brain, immune, cortex."""
    return organism.status()
