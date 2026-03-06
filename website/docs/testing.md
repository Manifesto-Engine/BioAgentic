---
sidebar_position: 10
title: Testing
---

# Test Suite

The test suite covers all five major components: cortex, immune system, brain, sandbox, and the Sovereign Script compiler. 35+ test cases in `tests/test_starter.py` (324 LOC).

## Running Tests

```bash
python -m pytest tests/ -v
```

## Test Coverage

### TestCortex — 7 Tests

The persistent memory engine:

| Test | What It Verifies |
|---|---|
| `test_remember_and_recall` | Store memory → recall by keyword → correct content and tags |
| `test_recall_by_tags` | Tag-based memory retrieval works correctly |
| `test_count` | Internal memory count tracking |
| `test_stats` | Memory statistics (total, db size, types) |
| `test_decay` | Ebbinghaus decay reduces importance over iterations |
| `test_identity_tags_immune_to_decay` | Memories tagged `identity` survive decay |

Each test creates a temporary SQLite DB that is deleted after the test.

### TestImmune — 5 Tests

Pipeline health monitoring and input sanitization:

| Test | What It Verifies |
|---|---|
| `test_track_success` | Success recording increases score |
| `test_quarantine_after_failures` | 3 consecutive failures trigger quarantine |
| `test_release_from_quarantine` | Quarantined component can be released |
| `test_reflex_rate_limiting` | Rate limiter blocks after threshold |
| `test_summary` | Health summary returns correct structure |

### TestBrain — 3 Tests

The reasoning engine:

| Test | What It Verifies |
|---|---|
| `test_rule_based_analysis` | Rules fire correctly for given vitals |
| `test_confidence_threshold` | Decisions below 0.6 confidence are rejected |
| `test_stats` | Brain statistics track calls and decisions |

### TestSandbox — 5 Tests

Pipeline execution safety:

| Test | What It Verifies |
|---|---|
| `test_blocks_eval` | `eval()` is caught by static analysis |
| `test_blocks_os` | `os.system()` is caught |
| `test_allows_safe_code` | Legitimate code passes all checks |
| `test_sandbox_code_injection` | Sandbox header is correctly injected |
| `test_blocks_class_escape` | `__class__.__bases__` escape vector blocked |

### TestSovereignScript — 8 Tests

The full compiler pipeline:

| Test | What It Verifies |
|---|---|
| `test_tokenize_pipeline` | Lexer produces correct token types |
| `test_parse_pipeline` | Parser generates correct AST structure |
| `test_codegen_pipeline` | Code generator outputs valid Python |
| `test_full_roundtrip` | Source → compile → execute produces expected output |
| `test_pipe_operator` | `\|>` desugars to nested function calls |
| `test_if_else` | Conditional compilation works |
| `test_for_loop` | For loop compilation works |
| `test_function_def` | Function definition + call roundtrip |

## Writing New Tests

Follow the existing pattern:

```python
class TestNewOrgan:
    """Your new organ tests."""

    def setup_method(self):
        """Create fresh instances for each test."""
        self.organ = NewOrgan()

    def teardown_method(self):
        """Clean up any resources."""
        self.organ.close()

    def test_basic_functionality(self):
        result = self.organ.do_something()
        assert result is not None
        assert result.status == "success"
```

## Test Fixtures

- **Cortex tests** use a temp file path (`/tmp/test_cortex_*.db`) and delete it on teardown
- **Brain tests** run with `LLM_PROVIDER=none` to test rule-based mode only
- **Sandbox tests** use inline code strings — no file I/O needed

---

**Next:** [Advanced →](/docs/advanced)
