---
sidebar_position: 8
title: API Reference
---

# API Reference

All endpoints are served by the FastAPI application on the configured port (default `8000`).

Interactive docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Root

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns organism name, version, alive status |

## Engine

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/engine/status` | Engine health + capabilities list |
| `GET` | `/engine/pulse` | Organism vital signs (heartbeat count, uptime, errors) |
| `POST` | `/engine/pipeline` | Register a new pipeline |
| `GET` | `/engine/pipelines` | List all registered pipelines |
| `POST` | `/engine/run` | Compile and execute a pipeline by name |
| `POST` | `/engine/compile` | Compile pipeline source without executing |
| `POST` | `/engine/reflex` | Register an auto-triggered reflex |
| `GET` | `/engine/reflexes` | List all active reflexes |
| `POST` | `/engine/emit` | Fire an event to the nervous system |
| `GET` | `/engine/events` | Recent event log |
| `GET` | `/engine/health` | Per-pipeline health scores |
| `GET` | `/engine/brain` | Brain state + recent decisions |

## Cortex (Memory)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/cortex/remember` | Store a memory |
| `GET` | `/cortex/recall` | Search memories by query |
| `GET` | `/cortex/recent` | Retrieve recent memories |
| `GET` | `/cortex/stats` | Cortex statistics (total memories, avg importance, etc.) |

## Request / Response Examples

### Register a Pipeline

```bash
curl -X POST http://localhost:8000/engine/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "name": "scanner",
    "source": "pipeline scanner { print(\"scanning\") }"
  }'
```

**Response:**
```json
{
  "status": "registered",
  "name": "scanner"
}
```

### Run a Pipeline

```bash
curl -X POST http://localhost:8000/engine/run \
  -H "Content-Type: application/json" \
  -d '{"name": "scanner"}'
```

**Response:**
```json
{
  "status": "success",
  "pipeline": "scanner",
  "output": ["scanning"],
  "execution_time_ms": 12
}
```

### Store a Memory

```bash
curl -X POST http://localhost:8000/cortex/remember \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Discovered anomalous traffic pattern",
    "tags": ["security", "anomaly"],
    "importance": 0.9
  }'
```

**Response:**
```json
{
  "status": "remembered",
  "id": "mem_a7f3c2"
}
```

### Search Memories

```bash
curl "http://localhost:8000/cortex/recall?query=anomaly&limit=5"
```

**Response:**
```json
{
  "results": [
    {
      "content": "Discovered anomalous traffic pattern",
      "tags": ["security", "anomaly"],
      "importance": 0.9,
      "relevance": 0.92,
      "created_at": "2026-03-06T08:30:00"
    }
  ]
}
```

### Fire an Event

```bash
curl -X POST http://localhost:8000/engine/emit \
  -H "Content-Type: application/json" \
  -d '{"event": "scan_complete", "data": {"targets_found": 3}}'
```

---

**Next:** [Advanced →](/docs/advanced)
