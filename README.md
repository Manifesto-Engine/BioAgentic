# Sovereign Organism — Starter Kit

A living AI agent runtime. Four organs. One heartbeat. Clone it, run it, watch it breathe.

```
git clone https://github.com/Manifesto-Engine/BioGentic-Agents.git
cd BioGentic-Agents
pip install -r requirements.txt
uvicorn main:app --port 8000
```

You'll see the heartbeat pulsing in your terminal every 10 seconds.

---

## What You're Running

A **living process** — not a chatbot, not a script runner. It has:

| Organ | Role |
|-------|------|
| 🫀 **Heartbeat** | Continuous pulse loop with watchdog recovery |
| 🧠 **Brain** | Rule-based reasoning (LLM optional) |
| 🛡️ **Immune** | Pipeline health tracking + auto-quarantine |
| 🧠 **Cortex** | Persistent memory (SQLite) with Ebbinghaus decay |

Every 10 seconds, the organism pulses through its lifecycle:
1. **Reflexes** — fire scheduled pipelines
2. **Events** — process event queue
3. **Metabolism** — consolidate + decay memories
4. **Self-awareness** — log vital signs
5. **Brain** — analyze state + make decisions

---

## Try It

Open a second terminal:

```bash
# Check if it's alive
curl http://localhost:8000/engine/status

# Read vital signs
curl http://localhost:8000/engine/pulse

# Search its memory
curl "http://localhost:8000/cortex/recall?query=birth"

# Run the example pipeline
curl -X POST http://localhost:8000/engine/run \
  -H "Content-Type: application/json" \
  -d '{"name":"hello_world"}'

# Store a custom memory
curl -X POST http://localhost:8000/cortex/remember \
  -H "Content-Type: application/json" \
  -d '{"content":"My first custom memory","tags":["test"],"importance":0.8}'
```

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Write a Pipeline

Pipelines are written in **Sovereign Script** (`.sov` files in `pipelines/`):

```
pipeline scanner {
  let targets = ["alpha", "bravo", "charlie"]
  for target in targets {
    let found = cx_recall(target, 1)
    if found == [] {
      cx_remember("Discovered: " + target, ["scan", "discovery"], 0.7)
      print("New: " + target)
    }
  }
}
```

Register it:
```bash
curl -X POST http://localhost:8000/engine/pipeline \
  -H "Content-Type: application/json" \
  -d '{"name":"scanner","source":"pipeline scanner {\n  let targets = [\"alpha\", \"bravo\"]\n  for target in targets {\n    cx_remember(\"Found: \" + target, [\"scan\"], 0.7)\n    print(target)\n  }\n}"}'
```

### Sovereign Script Cheat Sheet

| Feature | Syntax |
|---------|--------|
| Pipeline | `pipeline name { ... }` |
| Variable | `let x = 42` |
| Condition | `if x > 10 { ... } else { ... }` |
| Function | `fn add(a, b) { return a + b }` |
| Loop | `for item in list { ... }` |
| Pipe | `data \|> transform \|> output` |
| Remember | `cx_remember(content, tags, importance)` |
| Recall | `cx_recall(query, limit)` |
| Event | `sov_emit("event_name", data)` |

### Auto-Triggered Reflexes

Add a comment on line 1 of your `.sov` file:

```
// @every("30s")
pipeline heartbeat_logger {
  cx_remember("Still alive", ["heartbeat"], 0.2)
}
```

Register the reflex via API:
```bash
curl -X POST http://localhost:8000/engine/reflex \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name":"heartbeat_logger","trigger_type":"every","trigger_value":"30s"}'
```

---

## Optional: Enable LLM Brain

Copy `.env.template` to `.env` and configure a provider:

```bash
cp .env.template .env
# Edit .env — set LLM_PROVIDER and API keys
```

The Brain works without an LLM (rule-based heuristics). The LLM adds deeper pattern analysis and autonomous pipeline generation.

Supported providers:
- **Ollama** — local, free, sovereign (recommended)
- **NVIDIA NIM** — free tier cloud
- **OpenAI** — paid cloud fallback

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/engine/status` | Engine health + capabilities |
| GET | `/engine/pulse` | Organism vital signs |
| POST | `/engine/pipeline` | Register a pipeline |
| GET | `/engine/pipelines` | List all pipelines |
| POST | `/engine/run` | Execute a pipeline |
| POST | `/engine/compile` | Compile without executing |
| POST | `/engine/reflex` | Register auto-trigger |
| GET | `/engine/reflexes` | List active reflexes |
| POST | `/engine/emit` | Fire an event |
| GET | `/engine/events` | Recent event log |
| GET | `/engine/health` | Pipeline health scores |
| GET | `/engine/brain` | Brain state + decisions |
| POST | `/cortex/remember` | Store a memory |
| GET | `/cortex/recall` | Search memories |
| GET | `/cortex/recent` | Recent memories |
| GET | `/cortex/stats` | Cortex statistics |

---

## What's Next

This starter gives you the four essential organs. The full Sovereign Organism has 20+:

- 💭 **Dreams** — offline pattern synthesis during idle
- 🧬 **DNA** — pipeline genetics and genome tracking
- 🍳 **Breeder** — evolutionary reproduction of pipelines
- 🌐 **Federation** — peer discovery and cross-organism breeding
- 👀 **Perception** — codebase awareness and file change detection
- 🔍 **Code Index** — anti-hallucination codebase indexing
- 🎯 **Reinforcement** — outcome tracking and reward signals
- 📈 **Growth** — composite maturity scoring
- 🎓 **Skills** — crystallized competencies from repeated success
- 🦴 **Skeleton** — structural invariant enforcement

Each organ is a standalone Python module. Add them one at a time.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

---

## Architecture

```
main.py              ← FastAPI entry point (birth/death lifecycle)
organism.py          ← The living runtime (heartbeat + pulse loop)
cortex.py            ← Persistent memory engine (SQLite)
cortex_api.py        ← REST API for memory access
brain.py             ← Hybrid reasoning (rules + optional LLM)
immune.py            ← Pipeline health monitoring
pipeline_engine.py   ← Pipeline CRUD + sandboxed execution
sandbox.py           ← Static analysis + runtime restriction
llm_client.py        ← Optional LLM client (Ollama/NVIDIA/OpenAI)
sovereign_lang/      ← Sovereign Script compiler
  lexer.py           ← Tokenizer
  parser.py          ← Recursive descent parser → AST
  codegen.py         ← AST → Python code generator
pipelines/           ← Your .sov pipeline files
  hello_world.sov    ← Example pipeline
```

---

> **⚠️ Security:** This starter has no authentication. Add API key auth before exposing to the internet. See the full engine's `sovereign_auth.py` for a production-grade implementation.

---

*Built with the Manifesto Engine. Sovereignty is strong — but community makes it unstoppable.*
