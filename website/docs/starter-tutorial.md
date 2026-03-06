---
sidebar_position: 3
title: Starter Tutorial
---

# Starter Organism Tutorial

The `manifesto-starter-organism/` directory contains a **standalone, self-contained organism** with its own `main.py`, organ package, and interaction endpoint. This is different from the root-level organism — it's designed as a ready-to-fork template.

## Architecture

```
manifesto-starter-organism/
  main.py              ← FastAPI app with /pulse and /status
  organs/
    __init__.py         ← Package exports all 4 organs
    heartbeat.py        ← 234 LOC — pulse lifecycle + watchdog
    brain.py            ← 343 LOC — hybrid LLM + rules
    cortex.py           ← 374 LOC — SQLite memory + 3 types
    immune.py           ← 145 LOC — sanitization + rate limiting
```

## The `/pulse` Endpoint

The primary interaction loop. Every request goes through a **4-step pipeline**:

```
POST /pulse
{
  "prompt": "scan the perimeter",
  "context_id": "session_001"
}
```

### Step 1: Immune Check

The immune system sanitizes the input against 6 dangerous patterns:

```python
# Blocked patterns (regex)
__class__, __bases__, __subclasses__, __import__, __builtins__
eval(), exec(), compile(), __import__()
os.system(), os.popen(), subprocess
rm -rf, chmod 777, curl | bash
```

If the input matches any pattern, the request is rejected with `400`.

### Step 2: Rate Limiting

Per-session rate limiting (default: 60 requests/minute). Sliding window tracked in memory.

### Step 3: Cortex Retrieval

The cortex searches for relevant memories matching the prompt:

```python
memories = cortex.recall(request.prompt, limit=5)
```

Memories found are passed as context to the brain.

### Step 4: Brain Processing

The brain analyzes the organism's state and produces decisions:

```python
# Primary: LLM-powered analysis
decisions = await brain.analyze_llm(
    vitals=organism.vitals.to_dict(),
    recent_memories=memory_context,
    health_summary=immune.summary(),
)

# Fallback: rule-based heuristics
decisions = brain.analyze_rules(
    vitals=organism.vitals.to_dict(),
    health_summary=immune.summary(),
)
```

The interaction is then stored in the cortex as an episodic memory.

### Response

```json
{
  "status": "alive",
  "response": "scan→perimeter (threat assessment needed)",
  "context_id": "session_001",
  "pulse_count": 42
}
```

## The `/status` Endpoint

Returns full organism diagnostics:

```bash
curl http://localhost:8000/status
```

```json
{
  "vitals": {
    "alive": true,
    "heartbeat_count": 142,
    "uptime_seconds": 1420,
    "errors": 0
  },
  "brain": {
    "provider": "ollama",
    "model": "llama3.2",
    "decisions_made": 23,
    "llm_calls": 15
  },
  "immune": {
    "total_components": 3,
    "quarantined": [],
    "degraded": []
  },
  "cortex": {
    "total_memories": 87,
    "db_size_mb": 0.4
  }
}
```

## Watchdog Escalation

The heartbeat has a 3-tier watchdog for consecutive pulse failures:

| Consecutive Failures | Action |
|---|---|
| **5** | Pause for 60 seconds, then retry |
| **10** | Disable autonomous mode (brain stops spawning) |
| **20** | Terminate the process entirely |

This prevents a broken organ from consuming infinite resources.

## Running It

```bash
cd manifesto-starter-organism
pip install -r requirements.txt
uvicorn main:app --reload
```

:::caution
The starter organism uses FastAPI's deprecated `@app.on_event` lifecycle hooks. The root-level organism uses the modern `lifespan` context manager. Both work — the starter prioritizes simplicity.
:::

---

**Next:** [Organs →](/docs/organs)
