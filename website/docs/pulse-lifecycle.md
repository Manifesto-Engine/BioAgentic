---
sidebar_position: 5
title: Pulse Lifecycle
---

# The Pulse Lifecycle

Every 10 seconds, the organism executes a complete lifecycle pulse. This page documents the full runtime behavior implemented in `organism.py` (393 LOC).

## The 5 Phases

```
┌──────────┐    ┌──────────┐    ┌───────────┐    ┌─────────────┐    ┌──────────┐
│ Reflexes │ →  │  Events  │ →  │Metabolism │ →  │Self-Awareness│ →  │  Brain   │
│ @every   │    │  @on     │    │decay+merge│    │  vital log   │    │ think()  │
└──────────┘    └──────────┘    └───────────┘    └─────────────┘    └──────────┘
  every pulse    every pulse    every 10th       every 30th         every 5th
```

### Phase 1: Reflexes

The organism scans all registered reflexes and fires any whose schedule has elapsed.

**Schedule-based (`@every`):**
```python
# If enough time has passed since last fire, execute
if now - reflex.last_fired >= reflex.interval_seconds:
    self._fire_reflex(reflex)
```

**Interval parsing:**
| Input | Seconds |
|---|---|
| `30s` | 30 |
| `1m` | 60 |
| `5m` | 300 |
| `1h` | 3600 |

**Auto-scanning:** On birth, the organism scans all `.sov` files in `pipelines/` for `@every` and `@on` comment directives and registers them automatically.

### Phase 2: Events

Events emitted by pipelines or the API are queued and processed each pulse.

```python
def emit_event(self, event_name: str, data: dict | None = None):
    self._event_queue.append({"event": event_name, "data": data or {}})
    self.vitals.events_emitted += 1
```

Matching `@on` reflexes are fired when their event name matches:

```python
for reflex in self._reflexes:
    if reflex.trigger_type == "on" and reflex.trigger_value == event["event"]:
        self._fire_reflex(reflex)
```

### Phase 3: Metabolism (Every 10th Pulse)

Memory maintenance — the organism's equivalent of sleep:

1. **Consolidation** — compress old episodic memories into semantic knowledge
2. **Decay** — apply Ebbinghaus forgetting curve to unaccessed memories

```python
consolidated = self.cortex.consolidate(max_age_hours=72)
decayed = self.cortex.decay(factor=0.98)
```

Memories below `0.05` importance after decay are deleted permanently.

### Phase 4: Self-Awareness (Every 30th Pulse)

The organism writes its own vital signs to the cortex:

```python
self._remember(
    f"Vital signs: pulse={self.vitals.heartbeat_count}, "
    f"pipelines={self.vitals.pipelines_executed}, "
    f"errors={self.vitals.errors}",
    tags=["self_awareness", "vitals"],
    importance=0.3,
)
```

This creates a temporal record of the organism's health over time, queryable by the brain or external tools.

### Phase 5: Brain (Every 5th Pulse)

The brain analyzes the organism's state and makes autonomous decisions:

```python
decisions = self.brain.analyze(
    vitals=self.vitals.to_dict(),
    recent_memories=[...],
    health_summary=self.immune.health_summary(),
)
```

Decisions are action objects (e.g., `spawn`, `scan`, `consolidate`, `quarantine`). The organism executes them immediately — spawning new pipelines, adjusting parameters, or quarantining unhealthy components.

## Vital Signs

The `VitalSigns` dataclass tracks the organism's full state:

```python
@dataclass
class VitalSigns:
    alive: bool = False
    heartbeat_count: int = 0
    born_at: float = 0.0
    last_pulse: float = 0.0
    pipelines_executed: int = 0
    memories_consolidated: int = 0
    memories_decayed: int = 0
    reflexes_fired: int = 0
    decisions_made: int = 0
    quarantined: int = 0
    events_emitted: int = 0
    errors: int = 0
    uptime_seconds: float = 0.0
```

## Reflex Registration

### Via API

```bash
curl -X POST http://localhost:8000/engine/reflex \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name":"scanner","trigger_type":"every","trigger_value":"5m"}'
```

### Via Comment Directive

```
// @every("30s")
pipeline heartbeat_logger {
  cx_remember("Still alive", ["heartbeat"], 0.2)
}
```

### Via Event Trigger

```
// @on("pipeline_failed")
pipeline failure_handler {
  print("A pipeline failed!")
}
```

## Pipeline Execution

When a pipeline is executed (via reflex or API), the organism:

1. Loads the `.sov` source from `pipelines/`
2. Compiles it through `sovereign_lang` (lexer → parser → codegen)
3. Runs sandbox analysis (3-layer security check)
4. Executes the generated Python in a restricted environment
5. Records health outcome via the immune system
6. Processes any events emitted by the pipeline

---

**Next:** [Sovereign Script →](/docs/sovereign-script)
