---
sidebar_position: 9
title: LLM Providers
---

# LLM Provider System

The organism's brain can operate in two modes: **rule-based** (zero dependencies) or **LLM-augmented** (deeper reasoning). The `LLMClient` class provides a provider-agnostic interface with automatic fallback.

## Provider Priority

Auto-detection tries providers in this order:

```
1. Ollama    — local, free, sovereign (recommended)
2. NVIDIA NIM — free-tier cloud
3. OpenAI    — paid cloud, last resort
4. None      — rule-based fallback
```

```python
def _resolve_provider(self, provider: str) -> str:
    if provider != "auto":
        return provider
    # Try Ollama first
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            return "ollama"
    except Exception:
        pass
    if NVIDIA_API_KEY:
        return "nvidia"
    if OPENAI_API_KEY:
        return "openai"
    return "none"
```

## Configuration

All settings via environment variables:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `auto` | `auto`, `ollama`, `nvidia`, `openai` |
| `LLM_MODEL` | *(auto)* | Override default model |
| `LLM_TIMEOUT_S` | `30` | Request timeout in seconds |
| `LLM_MAX_TOKENS` | `1024` | Max tokens per response |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `NVIDIA_API_KEY` | *(empty)* | NVIDIA NIM API key |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key |

## Default Models

| Provider | Default Model |
|---|---|
| Ollama | `llama3.2` |
| NVIDIA NIM | `meta/llama-3.3-70b-instruct` |
| OpenAI | `gpt-4o-mini` |

## Setup

```bash
cp .env.template .env
```

### Option 1: Ollama (Recommended)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2

# .env
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
```

### Option 2: NVIDIA NIM

```bash
# .env
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key-here
```

### Option 3: OpenAI

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
```

## LLMResponse

Every call returns a structured response:

```python
@dataclass
class LLMResponse:
    content: str = ""       # The generated text
    success: bool = False   # Whether the call succeeded
    error: str = ""         # Error message if failed
    provider: str = ""      # Which provider was used
    model: str = ""         # Which model was used
    latency_ms: float = 0.0 # Round-trip time
```

## Brain System Prompt

When the LLM is active, the brain sends this system prompt:

```
You are the autonomous brain of a living software organism.
Analyze the organism's current state and decide what actions to take.

Actions: spawn, scan, consolidate, adjust, explore, ignore.

RULES:
1. If errors > 5, suggest a scan
2. If a pipeline is quarantined, investigate
3. If uptime > 1 hour with no activity, explore
4. Don't make more than 3 decisions per analysis
5. If memory is growing fast, suggest consolidation

Respond ONLY with valid JSON:
{
  "decisions": [
    {"action": "...", "target": "...", "reason": "...", "confidence": 0.0}
  ],
  "reasoning": "brief chain of thought"
}
```

Decisions with confidence below `0.6` are discarded.

## Availability Check

```python
@property
def is_available(self) -> bool:
    if self.provider == "ollama":
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    if self.provider == "nvidia":
        return bool(NVIDIA_API_KEY)
    if self.provider == "openai":
        return bool(OPENAI_API_KEY)
    return False
```

## Stats

```bash
curl http://localhost:8000/engine/brain
```

```json
{
  "provider": "ollama",
  "model": "llama3.2",
  "total_calls": 15,
  "available": true,
  "decisions_made": 23
}
```

---

**Next:** [Security →](/docs/security)
