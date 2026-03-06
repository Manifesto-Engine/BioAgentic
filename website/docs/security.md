---
sidebar_position: 8
title: Security
---

# Security Architecture

Pipeline execution is the organism's most dangerous surface. Every pipeline runs arbitrary code. The security system uses **defense-in-depth** — three independent layers that must all pass before code executes.

## Layer 1: Static Analysis

Before any code runs, the sandbox scans the compiled Python for forbidden patterns:

### Forbidden String Patterns

```python
FORBIDDEN_PATTERNS = [
    "__class__", "__bases__", "__subclasses__", "__mro__",
    "__globals__", "__builtins__", "__code__", "__dict__",
    "os.system", "os.popen", "subprocess",
    "importlib", "ctypes", "socket",
    "__import__", "eval(", "exec(",
]
```

### Escape Attempt Detection (Regex)

Catches creative bypass attempts:

```python
# chr() chain attacks: chr(101) + chr(118) + chr(97) + chr(108)
chr\s*\(\s*\d+\s*\)\s*\+\s*chr\s*\(\s*\d+\s*\)

# String concatenation tricks: "ev" + "al"
['"][a-z_]{1,6}['"]\s*\+\s*['"][a-z_]{1,6}['"]

# Hex byte injection: b"\x65\x76"
b['\"]\x[0-9a-f]{2}
```

### Prelude Exclusion

The scanner skips the trusted prelude (codegen builtins) — only user-authored code is analyzed:

```python
prelude_end = "# ── End Prelude"
if prelude_end in python_code:
    user_code = python_code[python_code.index(prelude_end):]
```

## Layer 2: Import Whitelist

Only approved modules can be imported at runtime:

```python
ALLOWED_MODULES = frozenset({
    "json", "time", "math", "re", "functools", "collections",
    "hashlib", "datetime", "random",
})
```

Any import of a non-whitelisted module (e.g., `os`, `subprocess`, `socket`) is flagged as a violation.

## Layer 3: Builtin Restriction

At runtime, dangerous Python builtins are removed from the execution environment:

```python
BLOCKED_BUILTINS = frozenset({
    "eval", "exec", "compile", "__import__",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit",
    "open", "input", "memoryview", "bytearray",
})
```

The sandbox header injects a restricted `__builtins__` that strips these functions:

```python
_safe_builtins = {k: v for k, v in builtins.__dict__.items()
                   if k not in _blocked and not k.startswith('_')}
_safe_builtins['__import__'] = lambda *a, **kw: (
    _ for _ in ()).throw(ImportError(f"Import blocked in sandbox: {a[0]}"))
```

## Immune System Sanitization

The immune system runs **before** the sandbox, catching dangerous input at the API boundary:

```python
_DANGEROUS_PATTERNS = [
    r"__(?:class|bases|subclasses|import|builtins)__",
    r"\b(?:eval|exec|compile|__import__)\s*\(",
    r"\bos\.(?:system|popen|exec|remove|unlink)\b",
    r"\bsubprocess\b",
    r"\bsys\.exit\b",
    r"(?:rm\s+-rf|chmod\s+777|curl.*\|\s*(?:sh|bash))",
]
```

## Rate Limiting

Sliding window rate limiter — 60 requests per minute per key:

```python
def check_rate(self, key: str, max_per_minute: int = 60) -> bool:
    now = time.time()
    window = self._rate_counters.setdefault(key, [])
    self._rate_counters[key] = [t for t in window if now - t < 60]
    if len(self._rate_counters[key]) >= max_per_minute:
        return False
    self._rate_counters[key].append(now)
    return True
```

## Quarantine Mechanics

Pipeline health is tracked using a **decay/recover** scoring model:

| Event | Effect |
|---|---|
| Success | Score × `1.02` (capped at 100) |
| Failure | Score × `0.85` |
| 3 consecutive failures | **Auto-quarantine** |

Quarantined pipelines are blocked from execution until manually released:

```bash
# Check quarantine status
curl http://localhost:8000/engine/health
```

:::caution
The starter kit has **no API authentication**. The full engine uses `sovereign_auth.py` with bearer tokens and 5 trust tiers (GENESIS → ORGAN → PIPELINE → API → EXTERNAL).
:::

---

**Next:** [LLM Providers →](/docs/llm-providers)
