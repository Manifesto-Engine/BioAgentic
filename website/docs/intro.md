---
sidebar_position: 1
title: Introduction
slug: /intro
---

# What Is BioAgentic?

BioAgentic is a **living AI agent runtime** — not a chatbot, not a script runner. It boots as a server process, pulses through a biological lifecycle every 10 seconds, and maintains persistent memory between sessions.

It has **four core organs**:

| Organ | Role |
|---|---|
| 🫀 **Heartbeat** | Continuous pulse loop with watchdog recovery |
| 🧠 **Brain** | Rule-based reasoning (LLM optional) |
| 🛡️ **Immune** | Pipeline health tracking + auto-quarantine |
| 🧠 **Cortex** | Persistent memory with Ebbinghaus decay |

## The Pulse Lifecycle

Every 10 seconds, the organism pulses through five phases:

1. **Reflexes** — fire scheduled pipelines
2. **Events** — process the event queue
3. **Metabolism** — consolidate and decay memories
4. **Self-Awareness** — log vital signs to cortex
5. **Brain** — analyze state and make autonomous decisions

## Not a Framework

This is not a library you import. It's a process you boot. When you run `uvicorn main:app --port 8000`, you're not starting a web server that happens to run some AI code — you're giving birth to an organism that happens to expose a REST API.

The organism **thinks**, **remembers**, **heals itself**, and **evolves** — with or without an LLM backing its brain.

## What's in the Starter Kit

The starter kit gives you the minimum viable organism: four organs, a pipeline engine, and the Sovereign Script compiler. Everything needed to:

- Boot a living agent in under 5 minutes
- Store and recall memories across sessions
- Write and execute pipelines in Sovereign Script
- Set up reflexes (auto-triggered pipelines on schedule)
- Monitor health via REST API

The full BioAgentic platform extends this to **20+ organs** — dreams, genetics, evolution, federation, perception, and more. The starter kit is the foundation.

---

**Next:** [Quickstart →](/docs/quickstart)
