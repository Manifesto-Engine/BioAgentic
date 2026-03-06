---
sidebar_position: 2
title: Quickstart
---

# Quickstart — 5 Minutes to a Living Organism

## Prerequisites

- Python 3.11+
- pip

## Boot It

```bash
git clone https://github.com/Manifesto-Engine/BioAgentic.git
cd BioAgentic
pip install -r requirements.txt
uvicorn main:app --port 8000
```

You'll see the heartbeat pulsing in your terminal every 10 seconds.

## Verify It's Alive

Open a second terminal:

```bash
# Health check
curl http://localhost:8000/

# Engine status + capabilities
curl http://localhost:8000/engine/status

# Vital signs (heartbeat count, uptime, pipeline stats)
curl http://localhost:8000/engine/pulse
```

## Talk to Its Memory

```bash
# Store a memory
curl -X POST http://localhost:8000/cortex/remember \
  -H "Content-Type: application/json" \
  -d '{"content":"My first custom memory","tags":["test"],"importance":0.8}'

# Search memories
curl "http://localhost:8000/cortex/recall?query=first"

# Recent memories
curl http://localhost:8000/cortex/recent
```

## Run a Pipeline

The starter comes with a `hello_world` pipeline:

```bash
curl -X POST http://localhost:8000/engine/run \
  -H "Content-Type: application/json" \
  -d '{"name":"hello_world"}'
```

## Interactive API Docs

FastAPI auto-generates interactive documentation:

**[http://localhost:8000/docs](http://localhost:8000/docs)**

Every endpoint is testable directly from the browser.

## What Just Happened

When you ran `uvicorn main:app`, the organism:

1. **Was born** — `organism.birth()` initialized all four organs
2. **Started pulsing** — the heartbeat loop fires every 10 seconds
3. **Began remembering** — every pulse writes vital signs to the cortex
4. **Armed its immune system** — pipeline health tracking is active

It will continue living until you kill the server. On restart, it recovers its memories from the cortex.

---

**Next:** [Organs →](/docs/organs)
