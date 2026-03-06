"""Sovereign Pipeline Engine — .sov execution for the Organism.

Pipeline Registry: Store, load, list, execute .sov programs.
Reflex Management: Register auto-triggered pipelines.
Event System: Emit events that trigger @on reflexes.
"""
from __future__ import annotations

import json
import time
import re
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from sovereign_lang import parse, generate
from sandbox import sandbox_code

logger = logging.getLogger("organism.engine")
router = APIRouter(prefix="/engine", tags=["engine"])

PIPELINE_DIR = Path(__file__).parent / "pipelines"
PIPELINE_DIR.mkdir(exist_ok=True)

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")

# The organism instance is wired at startup
_organism = None


def set_organism(org):
    global _organism
    _organism = org


def _validate_name(name: str):
    if not _SAFE_NAME_RE.match(name):
        raise HTTPException(400, f"Invalid pipeline name: {name!r}")


# ── Models ───────────────────────────────────────────────

class PipelineSubmit(BaseModel):
    name: str
    source: str
    description: str = ""


class PipelineRun(BaseModel):
    name: str
    timeout: int = 30


class ReflexRegister(BaseModel):
    pipeline_name: str
    trigger_type: str = "every"
    trigger_value: str = "60s"


class EventEmit(BaseModel):
    event: str
    data: dict = {}


# ── Pipeline CRUD ────────────────────────────────────────

@router.post("/pipeline")
def register_pipeline(req: PipelineSubmit):
    """Register a new .sov pipeline."""
    _validate_name(req.name)

    # Validate: parse + compile + sandbox scan
    try:
        ast = parse(req.source)
        python_code = generate(ast)
        _, violations = sandbox_code(python_code)
        if violations:
            raise HTTPException(400, f"Sandbox violations: {violations}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Compilation error: {e}")

    # Save source
    path = PIPELINE_DIR / f"{req.name}.sov"
    path.write_text(req.source)

    # Save metadata
    meta = {
        "name": req.name,
        "description": req.description,
        "created_at": time.time(),
        "functions": len([n for n in ast if hasattr(n, "params")]),
        "pipelines": len([n for n in ast if hasattr(n, "body") and not hasattr(n, "params")]),
    }
    meta_path = PIPELINE_DIR / f"{req.name}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))

    logger.info("Pipeline registered: %s", req.name)
    return {"status": "registered", **meta}


@router.get("/pipelines")
def list_pipelines():
    """List all registered .sov pipelines."""
    pipelines = []
    for path in sorted(PIPELINE_DIR.glob("*.sov")):
        meta_path = PIPELINE_DIR / f"{path.stem}.meta.json"
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except Exception:
                pass
        pipelines.append({
            "name": path.stem,
            "description": meta.get("description", ""),
            "created_at": meta.get("created_at", 0),
        })
    return pipelines


@router.get("/pipeline/{name}")
def get_pipeline(name: str):
    """Get a pipeline's source and metadata."""
    _validate_name(name)
    path = PIPELINE_DIR / f"{name}.sov"
    if not path.exists():
        raise HTTPException(404, f"Pipeline not found: {name}")
    return {
        "name": name,
        "source": path.read_text(),
    }


@router.delete("/pipeline/{name}")
def delete_pipeline(name: str):
    """Remove a pipeline from the registry."""
    _validate_name(name)
    path = PIPELINE_DIR / f"{name}.sov"
    meta_path = PIPELINE_DIR / f"{name}.meta.json"
    if not path.exists():
        raise HTTPException(404, f"Pipeline not found: {name}")
    path.unlink()
    meta_path.unlink(missing_ok=True)
    return {"status": "deleted", "name": name}


# ── Execution ────────────────────────────────────────────

@router.post("/run")
def run_pipeline(req: PipelineRun):
    """Compile and execute a registered .sov pipeline."""
    _validate_name(req.name)

    if _organism.immune.is_quarantined(req.name):
        raise HTTPException(
            423, f"Pipeline {req.name!r} is quarantined — too many failures"
        )

    path = PIPELINE_DIR / f"{req.name}.sov"
    if not path.exists():
        raise HTTPException(404, f"Pipeline not found: {req.name}")

    source = path.read_text()
    try:
        ast = parse(source)
        python_code = generate(ast)
        sandboxed, violations = sandbox_code(python_code)
        if violations:
            raise RuntimeError(f"Sandbox violations: {violations}")
    except Exception as e:
        _organism.immune.record_failure(req.name, str(e))
        raise HTTPException(400, f"Compilation error: {e}")

    # Execute
    import io
    from contextlib import redirect_stdout

    output_buffer = io.StringIO()
    namespace = {"_CORTEX": _organism.cortex, "_EMIT_QUEUE": []}

    try:
        with redirect_stdout(output_buffer):
            exec(sandboxed, namespace)
        _organism.immune.record_success(req.name)
        _organism.vitals.pipelines_executed += 1
    except Exception as e:
        _organism.immune.record_failure(req.name, str(e))
        raise HTTPException(500, f"Execution error: {e}")

    output = output_buffer.getvalue()

    # Process emitted events
    import asyncio
    for evt in namespace.get("_EMIT_QUEUE", []):
        try:
            loop = asyncio.get_event_loop()
            loop.create_task(_organism.emit_event(evt["event"], evt.get("data")))
        except Exception:
            pass

    return {
        "name": req.name,
        "output": output,
        "result": str(namespace.get("_result", "")),
        "events_emitted": len(namespace.get("_EMIT_QUEUE", [])),
    }


@router.post("/compile")
def compile_pipeline(req: PipelineRun):
    """Compile a pipeline to Python without executing."""
    _validate_name(req.name)
    path = PIPELINE_DIR / f"{req.name}.sov"
    if not path.exists():
        raise HTTPException(404, f"Pipeline not found: {req.name}")

    source = path.read_text()
    try:
        ast = parse(source)
        python_code = generate(ast)
        _, violations = sandbox_code(python_code)
    except Exception as e:
        raise HTTPException(400, f"Compilation error: {e}")

    return {
        "name": req.name,
        "python": python_code,
        "violations": violations,
    }


# ── Engine Status ────────────────────────────────────────

@router.get("/status")
def engine_status():
    """Engine health and capabilities."""
    return {
        "alive": _organism.vitals.alive if _organism else False,
        "version": "1.0.0",
        "organs": ["heartbeat", "brain", "immune", "cortex"],
        "pipelines_registered": len(list(PIPELINE_DIR.glob("*.sov"))),
        "reflexes_active": len(_organism.reflexes) if _organism else 0,
    }


@router.get("/pulse")
def engine_pulse():
    """Read the organism's vital signs."""
    if not _organism:
        raise HTTPException(503, "Organism not born yet")
    return _organism.vitals.to_dict()


# ── Reflexes ─────────────────────────────────────────────

@router.post("/reflex")
def register_reflex(req: ReflexRegister):
    """Register a new reflex (auto-triggered pipeline)."""
    _validate_name(req.pipeline_name)
    path = PIPELINE_DIR / f"{req.pipeline_name}.sov"
    if not path.exists():
        raise HTTPException(404, f"Pipeline not found: {req.pipeline_name}")
    if req.trigger_type not in ("every", "on"):
        raise HTTPException(400, "trigger_type must be 'every' or 'on'")

    _organism.register_reflex(req.pipeline_name, req.trigger_type, req.trigger_value)
    return {
        "status": "registered",
        "pipeline": req.pipeline_name,
        "trigger": f"@{req.trigger_type}({req.trigger_value!r})",
    }


@router.get("/reflexes")
def list_reflexes():
    """List all active reflexes."""
    if not _organism:
        return []
    return [
        {
            "pipeline": r.pipeline_name,
            "trigger_type": r.trigger_type,
            "trigger_value": r.trigger_value,
            "fire_count": r.fire_count,
            "last_fired": r.last_fired,
        }
        for r in _organism.reflexes
    ]


# ── Events ───────────────────────────────────────────────

@router.post("/emit")
async def emit_event(req: EventEmit):
    """Emit an event that may trigger @on reflexes."""
    if not _organism:
        raise HTTPException(503, "Organism not born yet")
    await _organism.emit_event(req.event, req.data)
    return {"status": "emitted", "event": req.event}


@router.get("/events")
def list_events():
    """Recent event log."""
    if not _organism:
        return []
    return _organism._event_log[-20:]


# ── Health ───────────────────────────────────────────────

@router.get("/health")
def pipeline_health():
    """Per-pipeline health scores and quarantine status."""
    if not _organism:
        return {}
    return _organism.immune.summary()


@router.get("/brain")
def brain_status():
    """Brain state and recent decisions."""
    if not _organism:
        return {}
    return _organism.brain.stats()
