"""Test Suite — Sovereign Organism Starter Kit.

Covers all four organs, the pipeline engine, sandbox, and Sovereign Script compiler.
"""
from __future__ import annotations

import os
import sys
import time
import pytest
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Cortex Tests ─────────────────────────────────────────

class TestCortex:
    """Persistent memory engine tests."""

    def setup_method(self):
        from cortex import Cortex
        self.db_path = Path("/tmp/test_cortex.db")
        self.db_path.unlink(missing_ok=True)
        self.cortex = Cortex(db_path=self.db_path)

    def teardown_method(self):
        self.cortex.close()
        self.db_path.unlink(missing_ok=True)
        for suffix in ("-shm", "-wal"):
            p = Path(str(self.db_path) + suffix)
            p.unlink(missing_ok=True)

    def test_remember_and_recall(self):
        from cortex import MemoryType
        mem = self.cortex.remember(
            "Test memory content",
            memory_type=MemoryType.EPISODIC,
            tags=["test", "unit"],
            importance=0.8,
        )
        assert mem.id
        assert mem.content == "Test memory content"

        results = self.cortex.recall("Test memory")
        assert len(results) >= 1
        assert results[0].content == "Test memory content"

    def test_recall_by_tags(self):
        from cortex import MemoryType
        self.cortex.remember("Alpha", tags=["alpha"])
        self.cortex.remember("Beta", tags=["beta"])

        results = self.cortex.recall_by_tags(["alpha"])
        assert len(results) == 1
        assert results[0].content == "Alpha"

    def test_count(self):
        from cortex import MemoryType
        assert self.cortex.count() == 0
        self.cortex.remember("One", tags=["test"])
        self.cortex.remember("Two", tags=["test"])
        assert self.cortex.count() == 2

    def test_stats(self):
        stats = self.cortex.stats()
        assert "total_memories" in stats
        assert "db_size_mb" in stats
        assert stats["total_memories"] == 0

    def test_decay(self):
        from cortex import MemoryType
        self.cortex.remember("Decaying", importance=0.5, tags=["test"])
        decayed = self.cortex.decay(decay_rate=0.5)
        assert decayed >= 1

    def test_identity_tags_immune_to_decay(self):
        from cortex import MemoryType
        self.cortex.remember("Permanent", importance=0.5, tags=["identity"])
        # Very aggressive decay
        self.cortex.decay(decay_rate=0.001)
        results = self.cortex.recall("Permanent")
        assert len(results) >= 1


# ── Immune System Tests ──────────────────────────────────

class TestImmune:
    """Pipeline health monitoring tests."""

    def test_track_success(self):
        from immune import ImmuneSystem
        immune = ImmuneSystem()
        immune.record_success("test_pipeline")
        h = immune.get_health("test_pipeline")
        assert h.successes == 1
        assert h.failures == 0
        assert not h.quarantined

    def test_quarantine_after_failures(self):
        from immune import ImmuneSystem
        immune = ImmuneSystem()
        for _ in range(3):
            immune.record_failure("bad_pipeline", "error")
        assert immune.is_quarantined("bad_pipeline")

    def test_release_from_quarantine(self):
        from immune import ImmuneSystem
        immune = ImmuneSystem()
        for _ in range(3):
            immune.record_failure("bad_pipeline", "error")
        assert immune.is_quarantined("bad_pipeline")
        immune.record_success("bad_pipeline")
        assert not immune.is_quarantined("bad_pipeline")

    def test_reflex_rate_limiting(self):
        from immune import ImmuneSystem
        immune = ImmuneSystem()
        for _ in range(5):
            assert immune.check_reflex_rate("fast_pipeline")
        assert not immune.check_reflex_rate("fast_pipeline")

    def test_summary(self):
        from immune import ImmuneSystem
        immune = ImmuneSystem()
        immune.record_success("a")
        immune.record_failure("b", "err")
        s = immune.summary()
        assert s["total_tracked"] == 2


# ── Brain Tests ──────────────────────────────────────────

class TestBrain:
    """Reasoning engine tests."""

    def test_rule_based_analysis(self):
        from brain import Brain
        brain = Brain()
        decisions = brain.analyze(vitals={
            "errors": 8,
            "heartbeat_count": 20,
            "pipelines_executed": 0,
            "quarantined": 1,
        })
        assert len(decisions) >= 1
        actions = [d.action for d in decisions]
        # Should trigger alert (8/20 = 0.4 > 0.3) and/or quarantine scan
        assert "alert" in actions or "scan" in actions

    def test_confidence_threshold(self):
        from brain import Brain, Decision
        brain = Brain()
        low = Decision(action="test", confidence=0.2)
        high = Decision(action="test", confidence=0.8)
        assert not brain.should_act(low)
        assert brain.should_act(high)

    def test_stats(self):
        from brain import Brain
        brain = Brain()
        s = brain.stats()
        assert "decisions_made" in s
        assert "mode" in s


# ── Sandbox Tests ────────────────────────────────────────

class TestSandbox:
    """Pipeline execution safety tests."""

    def test_blocks_eval(self):
        from sandbox import scan_code
        violations = scan_code("import os\nos.system('ls')")
        assert len(violations) > 0

    def test_blocks_os(self):
        from sandbox import scan_code
        violations = scan_code("import os\nos.system('rm -rf /')")
        assert len(violations) > 0

    def test_allows_safe_code(self):
        from sandbox import scan_code
        violations = scan_code("import json\nresult = json.dumps({'a': 1})")
        assert len(violations) == 0

    def test_sandbox_code_injection(self):
        from sandbox import sandbox_code
        safe = "import json\nresult = json.dumps({'a': 1})"
        sandboxed, violations = sandbox_code(safe)
        assert len(violations) == 0
        assert "Sandbox Header" in sandboxed

    def test_blocks_class_escape(self):
        from sandbox import scan_code
        violations = scan_code("x = ''.__class__.__bases__[0].__subclasses__()")
        assert len(violations) > 0


# ── Sovereign Script Tests ───────────────────────────────

class TestSovereignScript:
    """Compiler tests — lexer, parser, codegen."""

    def test_tokenize_pipeline(self):
        from sovereign_lang.lexer import tokenize, TokenType
        tokens = tokenize('pipeline test { let x = 42 }')
        types = [t.type for t in tokens if t.type != TokenType.NEWLINE]
        assert TokenType.PIPELINE in types
        assert TokenType.IDENTIFIER in types
        assert TokenType.NUMBER in types

    def test_parse_pipeline(self):
        from sovereign_lang import parse
        ast = parse('pipeline test { let x = 42 }')
        assert len(ast) == 1
        assert ast[0].name == "test"

    def test_codegen_pipeline(self):
        from sovereign_lang import parse, generate
        ast = parse('pipeline hello { print("hi") }')
        code = generate(ast)
        assert "def pipeline_hello" in code
        assert 'print' in code

    def test_full_roundtrip(self):
        from sovereign_lang import parse, generate
        source = '''pipeline demo {
          let msg = "Hello"
          cx_remember(msg, ["test"])
          print(msg)
        }'''
        ast = parse(source)
        code = generate(ast)
        # Should be executable Python
        namespace = {"_CORTEX": None, "_EMIT_QUEUE": []}
        exec(code, namespace)

    def test_pipe_operator(self):
        from sovereign_lang import parse, generate
        source = 'pipeline p { let x = 42 |> str }'
        ast = parse(source)
        code = generate(ast)
        assert "str(42)" in code

    def test_if_else(self):
        from sovereign_lang import parse, generate
        source = '''pipeline p {
          let x = 10
          if x > 5 {
            print("big")
          } else {
            print("small")
          }
        }'''
        ast = parse(source)
        code = generate(ast)
        assert "if " in code
        assert "else:" in code

    def test_for_loop(self):
        from sovereign_lang import parse, generate
        source = '''pipeline p {
          for item in [1, 2, 3] {
            print(item)
          }
        }'''
        ast = parse(source)
        code = generate(ast)
        assert "for item in" in code

    def test_function_def(self):
        from sovereign_lang import parse, generate
        source = '''pipeline p {
          fn add(a, b) {
            return a + b
          }
          print(add(1, 2))
        }'''
        ast = parse(source)
        code = generate(ast)
        assert "def add(a, b):" in code


# ── Organism Tests ───────────────────────────────────────

class TestOrganism:
    """Living runtime tests."""

    def test_vitals_initial(self):
        from organism import VitalSigns
        v = VitalSigns()
        assert not v.alive
        assert v.heartbeat_count == 0
        assert v.errors == 0

    def test_vitals_to_dict(self):
        from organism import VitalSigns
        v = VitalSigns(alive=True, born_at=time.time())
        d = v.to_dict()
        assert d["alive"] is True
        assert "uptime_seconds" in d
        assert "born_at_iso" in d

    def test_parse_interval(self):
        from organism import _parse_interval
        assert _parse_interval("30s") == 30.0
        assert _parse_interval("2m") == 120.0
        assert _parse_interval("1h") == 3600.0

    def test_organism_creation(self):
        from organism import Organism
        org = Organism(tick_interval=1.0)
        assert not org.vitals.alive
        assert org.cortex is not None
        assert org.brain is not None
        assert org.immune is not None
        org.cortex.close()
        # Clean up test DB
        Path("cortex.db").unlink(missing_ok=True)
        for suffix in ("-shm", "-wal"):
            Path(f"cortex.db{suffix}").unlink(missing_ok=True)
