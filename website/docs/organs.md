---
sidebar_position: 4
title: Organs
---

# The Four Starter Organs

Every BioAgentic organism is built from organs — self-contained modules that handle a specific biological function. The starter kit ships with four, implemented in the `organs/` package.

```python
# organs/__init__.py — what's exported
from .heartbeat import Heartbeat, VitalSigns
from .brain import Brain, Decision
from .immune import Immune, HealthRecord
from .cortex import Cortex, Memory, MemoryType
```

## 🫀 Heartbeat

**File:** `organs/heartbeat.py` (234 LOC)

The heartbeat is the master clock. It owns all other organs and drives the pulse lifecycle.

### Initialization

```python
organism = Heartbeat(name="starter", tick_interval=10.0)
# Creates: organism.cortex, organism.brain, organism.immune
```

### Vital Signs

```python
@dataclass
class VitalSigns:
    alive: bool = False
    heartbeat_count: int = 0
    born_at: float = 0.0
    last_pulse: float = 0.0
    errors: int = 0
    decisions_made: int = 0
    memories_consolidated: int = 0
    memories_decayed: int = 0
    uptime_seconds: float = 0.0
```

### The 4-Phase Pulse Cycle

Each heartbeat executes:

1. **Immune sweep** — check component health
2. **Cortex metabolism** — consolidate and decay memories (every 10th pulse)
3. **Brain analysis** — rule-based + optional LLM reasoning (every 5th pulse)
4. **Self-report** — log vital signs to cortex (every 30th pulse)

### Watchdog Escalation

| Consecutive Failures | Action |
|---|---|
| **5** | Pause for 60 seconds, then retry |
| **10** | Disable autonomous mode |
| **20** | Terminate the process |

## 🧠 Brain

**File:** `organs/brain.py` (343 LOC)

Hybrid reasoning engine with automatic provider detection.

### Decision Dataclass

```python
@dataclass
class Decision:
    action: str           # spawn, scan, consolidate, adjust, explore, ignore
    target: str = ""      # what to act on
    reason: str = ""      # why
    confidence: float = 0.0
    source: str = "rules" # "rules" or "llm"
```

Decisions below `0.6` confidence are discarded (`Brain.CONFIDENCE_THRESHOLD`).

### LLM Provider Detection

```python
class LLMProvider(Enum):
    AUTO = "auto"      # Detect best available
    OLLAMA = "ollama"  # Local, free
    NVIDIA = "nvidia"  # Free-tier cloud
    OPENAI = "openai"  # Paid cloud
```

Auto-detection order: Ollama → NVIDIA → OpenAI → rule-based fallback.

### Rule-Based Heuristics

When no LLM is available, the brain applies these rules:

- **Error threshold** → if `errors > 5`, suggest a system scan
- **Quarantine check** → if components are quarantined, investigate
- **Idle detection** → if high uptime + low activity, suggest exploration
- **Memory growth** → if memories growing fast, suggest consolidation
- **Longevity milestone** → if uptime exceeds thresholds, log achievement

See [LLM Providers →](/docs/llm-providers) for full LLM configuration.

## 🛡️ Immune System

**File:** `organs/immune.py` (145 LOC)

### Health Scoring Math

```python
QUARANTINE_THRESHOLD = 3    # consecutive failures to quarantine
HEALTH_DECAY = 0.85         # multiplier on failure
HEALTH_RECOVER = 1.02       # multiplier on success

# Score starts at 100.0
# Success: score = min(100.0, score * 1.02)
# Failure: score = max(0.0, score * 0.85)
```

### Health Record

```python
@dataclass
class HealthRecord:
    name: str
    score: float = 100.0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    quarantined: bool = False
    quarantined_at: float = 0.0
```

### Input Sanitization

6 regex patterns block dangerous input at the API boundary:

```python
__class__, __bases__, __subclasses__, __import__, __builtins__
eval(), exec(), compile()
os.system(), os.popen(), subprocess
sys.exit()
rm -rf, chmod 777, curl | bash
```

### Rate Limiting

Sliding window — 60 requests/minute per key. See [Security →](/docs/security) for full details.

## 🧠 Cortex (Memory)

**File:** `organs/cortex.py` (374 LOC)

### Three Memory Types

```python
class MemoryType(Enum):
    EPISODIC = "episodic"       # Events, interactions, experiences
    PROCEDURAL = "procedural"   # How-to knowledge, procedures
    SEMANTIC = "semantic"       # Facts, distilled knowledge
```

### Memory Structure

```python
@dataclass
class Memory:
    id: str
    type: MemoryType
    content: str
    tags: list[str]
    importance: float       # 0.0–1.0
    created_at: float       # timestamp
    last_accessed: float    # timestamp
    access_count: int
    source: str             # who created it
    metadata: dict
```

### Consolidation

Like human sleep — compresses old episodic memories into semantic knowledge:

```python
cortex.consolidate(max_age_hours=72)
# Groups old episodic memories by tags
# Creates semantic summaries
# Deletes the original episodes
```

### Ebbinghaus Decay

```python
cortex.decay(factor=0.98)
# importance *= factor * (1 + log(access_count + 1))
# Memories accessed recently decay slower
# Below 0.05 importance → deleted
```

### Identity Tag Immunity

Memories tagged with `identity` are immune to decay — they persist indefinitely. This is used for core memories that define the organism's character.

### Safety Limits

```python
MAX_DB_SIZE_MB = 100    # Raises CortexFullError if exceeded
MAX_MEMORY_COUNT = 500  # Auto-prunes least important when exceeded
```

## Adding More Organs

See [Contributing →](/docs/contributing) for the organ interface contract and step-by-step guide.

---

**Next:** [Pulse Lifecycle →](/docs/pulse-lifecycle)
