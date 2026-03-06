---
sidebar_position: 11
title: Advanced
---

# Advanced Topics

## Enabling the LLM Brain

The Brain organ works out-of-the-box with rule-based heuristics. Adding an LLM unlocks deeper pattern analysis and autonomous pipeline generation.

### Setup

```bash
cp .env.template .env
```

Edit `.env` with your provider:

```bash
# Option 1: Ollama (local, free, sovereign) — recommended
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Option 2: NVIDIA NIM (free tier cloud)
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here

# Option 3: OpenAI (paid cloud fallback)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

Restart the organism. The brain will automatically detect the LLM and switch from rule-based to hybrid mode.

### What Changes with LLM

| Capability | Rule-based | LLM-backed |
|---|---|---|
| Pipeline quarantine | ✅ | ✅ |
| Vital sign logging | ✅ | ✅ |
| Pattern analysis | ❌ | ✅ |
| Autonomous pipeline generation | ❌ | ✅ |
| Cortex memory synthesis | ❌ | ✅ |
| Natural language reasoning | ❌ | ✅ |

## The Full Organ Catalog (20+)

The starter kit has four organs. The full Sovereign Organism adds:

| Organ | Module | Pulse Frequency | Role |
|---|---|---|---|
| 💭 Dreams | `dreams.py` | Every 20th pulse | Offline pattern synthesis during idle |
| 🧬 DNA | `dna.py` | On birth | Pipeline genetics, genome registry |
| 🧪 Genetics | `genetics.py` | On breed | Gene pool management, tournament selection |
| 🍳 Breeder | `breeder.py` | Every 50th pulse | Evolutionary reproduction of pipelines |
| 🌐 Federation | `federation.py` | Every 30th pulse | Peer discovery, cross-organism breeding |
| 👀 Perception | `perception.py` | Every 5th pulse | Codebase awareness, file change detection |
| 🔍 Code Index | `code_index.py` | On birth | Anti-hallucination — indexes real codebase symbols |
| 🧠 Neural Cortex | `neural_cortex.py` | Every 100th pulse | Embedding backfill for semantic memory search |
| 📊 Working Memory | `working_memory.py` | Every pulse | Short-term salience-gated buffer (capacity 64) |
| 🎯 Reinforcement | `reinforcement.py` | On pipeline exec | Outcome ledger, reward/penalty tracking |
| 📈 Growth | `growth.py` | Every 100th pulse | Composite growth score, trajectory tracking |
| 🎓 Skills | `skills.py` | Every ~36 metab | Skill crystallization from repeated success |
| 🧩 Cognitive Biases | `cognitive_biases.py` | Every pulse | Attention gating, mood-aware salience filtering |
| 🦴 Skeleton | `skeleton.py` | Every pulse | Structural invariant enforcement |
| 🚔 Immune Patrol | `immune_patrol.py` | Every pulse | Active threat hunting, anomaly sweeps |
| 🔗 Cortex Graph | `cortex_graph.py` | Every ~10 metab | Knowledge graph edges, clustering |
| 🌉 Cortex Bridge | `cortex_bridge.py` | Every 3rd pulse | Scans agent artifacts, publishes to shared cortex |
| 🛡️ Bred Filter | `bred_filters.py` | On pipeline exec | Pre/post-compile whitelist for bred pipelines |

Each organ is a standalone Python module. Add them one at a time to your starter organism.

## Architecture

```
main.py              ← FastAPI entry point (birth/death lifecycle)
organism.py          ← The living runtime (heartbeat + pulse loop)
cortex.py            ← Persistent memory engine
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

## Security Warning

:::caution
The starter kit has **no authentication**. Do not expose it to the public internet without adding API key auth. The full engine ships with `sovereign_auth.py` — a production-grade bearer token system with trust tiers.
:::

## Running Tests

```bash
python -m pytest tests/ -v
```
