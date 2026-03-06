"""Sovereign Script Sandbox — Pipeline Execution Safety.

Defense-in-depth:
  Layer 1: STATIC ANALYSIS — scan compiled code for forbidden patterns
  Layer 2: IMPORT WHITELIST — only approved modules can be imported
  Layer 3: BUILTIN RESTRICTION — dangerous builtins removed at runtime
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger("organism.sandbox")

ALLOWED_MODULES = frozenset({
    "json", "time", "math", "re", "functools", "collections",
    "hashlib", "datetime", "random",
})

BLOCKED_BUILTINS = frozenset({
    "eval", "exec", "compile", "__import__", "globals", "locals",
    "vars", "dir", "getattr", "setattr", "delattr", "breakpoint",
    "exit", "quit", "open", "input", "memoryview", "bytearray",
})

FORBIDDEN_PATTERNS = [
    "__class__", "__bases__", "__subclasses__", "__mro__",
    "__globals__", "__builtins__", "__code__", "__dict__",
    "os.system", "os.popen", "subprocess",
    "importlib", "ctypes", "socket",
    "__import__", "eval(", "exec(",
]

ESCAPE_REGEXES = [
    re.compile(r"chr\s*\(\s*\d+\s*\)\s*\+\s*chr\s*\(\s*\d+\s*\)"),
    re.compile(r"""['"][a-z_]{1,6}['"]\s*\+\s*['"][a-z_]{1,6}['"]"""),
    re.compile(r"b['\"]\\x[0-9a-f]{2}"),
]


def generate_sandbox_header() -> str:
    """Generate Python code that restricts the execution environment."""
    blocked = ", ".join(f'"{b}"' for b in sorted(BLOCKED_BUILTINS))
    return f"""
# ── Sandbox Header ──────────────────────────────────
import builtins as _builtins
_blocked = {{{blocked}}}
_safe_builtins = {{k: v for k, v in _builtins.__dict__.items()
                   if k not in _blocked and not k.startswith('_')}}
_safe_builtins['__import__'] = lambda *a, **kw: (_ for _ in ()).throw(
    ImportError(f"Import blocked in sandbox: {{a[0]}}"))
_safe_builtins['print'] = print
# ── End Sandbox ─────────────────────────────────────
"""


def scan_code(python_code: str) -> list[str]:
    """Static analysis: scan compiled Python for forbidden patterns.

    Returns list of violations found. Empty = safe.
    Skips the codegen prelude zone (before '# ── End Prelude').
    """
    violations: list[str] = []

    # Strip the trusted prelude — only scan user code
    prelude_end = "# ── End Prelude"
    if prelude_end in python_code:
        user_code = python_code[python_code.index(prelude_end):]
    else:
        user_code = python_code

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in user_code:
            violations.append(f"Forbidden pattern: {pattern}")

    for regex in ESCAPE_REGEXES:
        if regex.search(user_code):
            violations.append(f"Escape attempt detected: {regex.pattern[:40]}")

    for line in user_code.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            module = stripped.split()[1].split(".")[0]
            if module not in ALLOWED_MODULES and module != "builtins":
                violations.append(f"Blocked import: {module}")

    return violations


def sandbox_code(python_code: str) -> tuple[str, list[str]]:
    """Apply sandbox to compiled Python code.

    Returns (sandboxed_code, violations).
    If violations is non-empty, the code should NOT be executed.
    """
    violations = scan_code(python_code)
    if violations:
        return python_code, violations

    header = generate_sandbox_header()
    lines = python_code.splitlines()

    # Find first non-comment, non-docstring line to inject header after
    insert_at = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith('"""'):
            insert_at = i
            break

    sandboxed = "\n".join(lines[:insert_at]) + "\n" + header + "\n" + "\n".join(lines[insert_at:])
    return sandboxed, []
