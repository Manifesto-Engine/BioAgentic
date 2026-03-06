"""Sovereign Script Lexer — Tokenizer.

Converts source text into a stream of typed tokens.
Supports: pipeline, let, if, else, fn, return, for, in,
          true, false, strings, numbers, identifiers, operators, |>
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Keywords
    PIPELINE = auto()
    LET = auto()
    IF = auto()
    ELSE = auto()
    FN = auto()
    RETURN = auto()
    FOR = auto()
    IN = auto()
    TRUE = auto()
    FALSE = auto()
    WHILE = auto()

    # Literals
    STRING = auto()
    NUMBER = auto()
    IDENTIFIER = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    PIPE = auto()          # |>

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()
    NEWLINE = auto()

    # Special
    EOF = auto()


KEYWORDS = {
    "pipeline": TokenType.PIPELINE,
    "let": TokenType.LET,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "while": TokenType.WHILE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


def tokenize(source: str) -> list[Token]:
    """Tokenize Sovereign Script source into a list of tokens."""
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1
    length = len(source)

    while i < length:
        ch = source[i]

        # Whitespace (not newline)
        if ch in (" ", "\t", "\r"):
            i += 1
            col += 1
            continue

        # Newline
        if ch == "\n":
            tokens.append(Token(TokenType.NEWLINE, "\\n", line, col))
            i += 1
            line += 1
            col = 1
            continue

        # Comments
        if ch == "/" and i + 1 < length and source[i + 1] == "/":
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Strings
        if ch in ('"', "'"):
            start = i
            quote = ch
            i += 1
            col += 1
            string_val = []
            while i < length and source[i] != quote:
                if source[i] == "\\" and i + 1 < length:
                    next_ch = source[i + 1]
                    escape_map = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
                    string_val.append(escape_map.get(next_ch, next_ch))
                    i += 2
                    col += 2
                else:
                    if source[i] == "\n":
                        line += 1
                        col = 1
                    string_val.append(source[i])
                    i += 1
                    col += 1
            if i < length:
                i += 1  # closing quote
                col += 1
            tokens.append(Token(TokenType.STRING, "".join(string_val), line, col))
            continue

        # Numbers
        if ch.isdigit() or (ch == "." and i + 1 < length and source[i + 1].isdigit()):
            start = i
            has_dot = False
            while i < length and (source[i].isdigit() or (source[i] == "." and not has_dot)):
                if source[i] == ".":
                    has_dot = True
                i += 1
                col += 1
            tokens.append(Token(TokenType.NUMBER, source[start:i], line, col))
            continue

        # Identifiers / Keywords
        if ch.isalpha() or ch == "_":
            start = i
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
                col += 1
            word = source[start:i]
            tt = KEYWORDS.get(word, TokenType.IDENTIFIER)
            tokens.append(Token(tt, word, line, col))
            continue

        # Two-character operators
        if i + 1 < length:
            two = source[i:i + 2]
            TWO_CHAR = {
                "|>": TokenType.PIPE,
                "==": TokenType.EQ,
                "!=": TokenType.NEQ,
                "<=": TokenType.LTE,
                ">=": TokenType.GTE,
            }
            if two in TWO_CHAR:
                tokens.append(Token(TWO_CHAR[two], two, line, col))
                i += 2
                col += 2
                continue

        # Single-character operators/delimiters
        SINGLE = {
            "+": TokenType.PLUS, "-": TokenType.MINUS,
            "*": TokenType.STAR, "/": TokenType.SLASH,
            "%": TokenType.PERCENT, "=": TokenType.ASSIGN,
            "<": TokenType.LT, ">": TokenType.GT,
            "(": TokenType.LPAREN, ")": TokenType.RPAREN,
            "{": TokenType.LBRACE, "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET, "]": TokenType.RBRACKET,
            ",": TokenType.COMMA, ".": TokenType.DOT,
            ":": TokenType.COLON,
        }
        if ch in SINGLE:
            tokens.append(Token(SINGLE[ch], ch, line, col))
            i += 1
            col += 1
            continue

        # Unknown character — skip
        i += 1
        col += 1

    tokens.append(Token(TokenType.EOF, "", line, col))
    return tokens
