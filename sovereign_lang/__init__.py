"""Sovereign Script — Minimal Compiler.

Exports parse() and generate() for the pipeline engine.
"""
from sovereign_lang.lexer import tokenize
from sovereign_lang.parser import parse as _parse
from sovereign_lang.codegen import generate as _generate

__version__ = "1.0.0"


def parse(source: str):
    """Tokenize and parse Sovereign Script source into an AST."""
    tokens = tokenize(source)
    return _parse(tokens)


def generate(ast) -> str:
    """Generate Python code from a Sovereign Script AST."""
    return _generate(ast)
