---
sidebar_position: 12
title: Contributing
---

# Contributing

## Architecture Overview

```
File                  LOC    Purpose
──────────────────    ───    ────────────────────────────
main.py               63    FastAPI entry point (birth/death)
organism.py           393    Living runtime (heartbeat + pulse)
cortex.py             ~400   Persistent memory (SQLite)
cortex_api.py          60    REST API for cortex
brain.py              ~150   Reasoning engine
immune.py             ~130   Health monitoring
pipeline_engine.py    330    Pipeline CRUD + execution
sandbox.py            113    3-layer execution safety
llm_client.py         197    Provider-agnostic LLM interface
sovereign_lang/
  lexer.py            213    Tokenizer
  parser.py           454    Recursive descent parser
  codegen.py          202    AST → Python code generator
tests/
  test_starter.py     324    35+ test cases
```

## Adding a New Organ

Every organ follows a simple contract:

### 1. Create the Module

```python
# organs/perception.py
"""Perception — Codebase Awareness."""
from __future__ import annotations
import logging

logger = logging.getLogger("organism.perception")


class Perception:
    """Detects file changes and emits events."""

    def __init__(self):
        self.scans = 0
        self.changes_detected = 0

    async def pulse(self, vitals: dict) -> None:
        """Called every Nth heartbeat by the organism."""
        self.scans += 1
        # Scan for changes...

    def stats(self) -> dict:
        return {
            "scans": self.scans,
            "changes_detected": self.changes_detected,
        }
```

### 2. Register in Organism

```python
# organism.py — in __init__
from perception import Perception
self.perception = Perception()

# In _pulse() — add to appropriate phase
if self.vitals.heartbeat_count % 5 == 0:
    await self.perception.pulse(self.vitals.to_dict())
```

### 3. Write Tests

```python
class TestPerception:
    def test_scan_increments(self):
        p = Perception()
        asyncio.run(p.pulse({}))
        assert p.scans == 1
```

## Adding a Sovereign Script Feature

Adding a new language feature touches all three compiler stages:

### 1. Lexer — Add Token Type

```python
# lexer.py
class TokenType(Enum):
    MATCH = auto()     # New keyword

KEYWORDS = {
    "match": TokenType.MATCH,
    # ...
}
```

### 2. Parser — Add AST Node + Parse Rule

```python
# parser.py
@dataclass
class Match:
    subject: object
    arms: list  # [(pattern, body), ...]

class Parser:
    def parse_statement(self):
        if self.current().type == TokenType.MATCH:
            return self.parse_match()
        # ...

    def parse_match(self):
        self.expect(TokenType.MATCH)
        subject = self.parse_expression()
        self.expect(TokenType.LBRACE)
        arms = []
        # Parse match arms...
        self.expect(TokenType.RBRACE)
        return Match(subject=subject, arms=arms)
```

### 3. Codegen — Add Emission Rule

```python
# codegen.py
def emit_node(self, node):
    if isinstance(node, Match):
        self.emit_match(node)
    # ...

def emit_match(self, node: Match):
    subject_expr = self.expr(node.subject)
    self.emit(f"_match_val = {subject_expr}")
    for i, (pattern, body) in enumerate(node.arms):
        keyword = "if" if i == 0 else "elif"
        self.emit(f"{keyword} _match_val == {self.expr(pattern)}:")
        self.indent += 1
        for stmt in body:
            self.emit_node(stmt)
        self.indent -= 1
```

## Extending the Sandbox

### Adding a Forbidden Pattern

```python
# sandbox.py
FORBIDDEN_PATTERNS = [
    # ...existing...
    "pickle.loads",  # New forbidden pattern
]
```

### Adding an Allowed Module

```python
ALLOWED_MODULES = frozenset({
    # ...existing...
    "itertools",  # New safe module
})
```

## Test-First Workflow

1. Write the test first
2. Run `python -m pytest tests/ -v` — see it fail
3. Implement the feature
4. Run tests again — see it pass
5. Run the full suite to check for regressions

## Code Standards

- **Python 3.11+** — use modern features (`match`, type hints, `dataclass`)
- **Functions < 40 LOC** — break up anything larger
- **No magic numbers** — use named constants
- **Docstrings on public methods** — one line minimum
- **No debug prints** — use `logging.getLogger()`
