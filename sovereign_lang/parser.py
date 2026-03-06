"""Sovereign Script Parser — Recursive Descent.

Parses a token stream into an AST. Supports:
  pipeline, let, if/else, fn, return, for, while,
  function calls, binary ops, pipe |>, arrays, booleans.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from sovereign_lang.lexer import Token, TokenType


# ── AST Nodes ────────────────────────────────────────────

@dataclass
class Pipeline:
    name: str
    body: list

@dataclass
class Let:
    name: str
    value: object

@dataclass
class If:
    condition: object
    then_body: list
    else_body: list | None = None

@dataclass
class Fn:
    name: str
    params: list[str]
    body: list

@dataclass
class Return:
    value: object

@dataclass
class For:
    var: str
    iterable: object
    body: list

@dataclass
class While:
    condition: object
    body: list

@dataclass
class Call:
    name: str
    args: list

@dataclass
class MethodCall:
    object: object
    method: str
    args: list

@dataclass
class BinOp:
    op: str
    left: object
    right: object

@dataclass
class UnaryOp:
    op: str
    operand: object

@dataclass
class Pipe:
    left: object
    right: object

@dataclass
class String:
    value: str

@dataclass
class Number:
    value: float

@dataclass
class Bool:
    value: bool

@dataclass
class Identifier:
    name: str

@dataclass
class Array:
    elements: list

@dataclass
class Index:
    object: object
    index: object

@dataclass
class Assign:
    name: str
    value: object


# ── Parser ───────────────────────────────────────────────

class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, "", 0, 0)

    def peek(self) -> Token:
        return self.current()

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, tt: TokenType) -> Token:
        tok = self.current()
        if tok.type != tt:
            raise ParseError(
                f"Expected {tt.name}, got {tok.type.name} ({tok.value!r}) "
                f"at line {tok.line}"
            )
        return self.advance()

    def skip_newlines(self):
        while self.current().type == TokenType.NEWLINE:
            self.advance()

    def parse(self) -> list:
        """Parse top-level statements (pipelines and functions)."""
        nodes = []
        self.skip_newlines()
        while self.current().type != TokenType.EOF:
            nodes.append(self.parse_top_level())
            self.skip_newlines()
        return nodes

    def parse_top_level(self):
        tok = self.current()
        if tok.type == TokenType.PIPELINE:
            return self.parse_pipeline()
        if tok.type == TokenType.FN:
            return self.parse_fn()
        raise ParseError(
            f"Expected 'pipeline' or 'fn' at top level, got {tok.value!r} "
            f"at line {tok.line}"
        )

    def parse_pipeline(self) -> Pipeline:
        self.expect(TokenType.PIPELINE)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        return Pipeline(name=name, body=body)

    def parse_fn(self) -> Fn:
        self.expect(TokenType.FN)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LPAREN)
        params = self.parse_params()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        return Fn(name=name, params=params, body=body)

    def parse_params(self) -> list[str]:
        params = []
        if self.current().type == TokenType.RPAREN:
            return params
        params.append(self.expect(TokenType.IDENTIFIER).value)
        while self.current().type == TokenType.COMMA:
            self.advance()
            params.append(self.expect(TokenType.IDENTIFIER).value)
        return params

    def parse_block(self) -> list:
        stmts = []
        self.skip_newlines()
        while self.current().type not in (TokenType.RBRACE, TokenType.EOF):
            stmts.append(self.parse_statement())
            self.skip_newlines()
        return stmts

    def parse_statement(self):
        tok = self.current()

        if tok.type == TokenType.LET:
            return self.parse_let()
        if tok.type == TokenType.IF:
            return self.parse_if()
        if tok.type == TokenType.FN:
            return self.parse_fn()
        if tok.type == TokenType.RETURN:
            return self.parse_return()
        if tok.type == TokenType.FOR:
            return self.parse_for()
        if tok.type == TokenType.WHILE:
            return self.parse_while()

        # Expression statement (function call, assignment, etc.)
        expr = self.parse_expression()

        # Check for assignment: identifier = expr
        if (isinstance(expr, Identifier)
                and self.current().type == TokenType.ASSIGN):
            self.advance()
            value = self.parse_expression()
            return Assign(name=expr.name, value=value)

        return expr

    def parse_let(self) -> Let:
        self.expect(TokenType.LET)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ASSIGN)
        value = self.parse_expression()
        return Let(name=name, value=value)

    def parse_if(self) -> If:
        self.expect(TokenType.IF)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE)
        then_body = self.parse_block()
        self.expect(TokenType.RBRACE)

        else_body = None
        self.skip_newlines()
        if self.current().type == TokenType.ELSE:
            self.advance()
            if self.current().type == TokenType.IF:
                else_body = [self.parse_if()]
            else:
                self.expect(TokenType.LBRACE)
                else_body = self.parse_block()
                self.expect(TokenType.RBRACE)

        return If(condition=condition, then_body=then_body, else_body=else_body)

    def parse_return(self) -> Return:
        self.expect(TokenType.RETURN)
        value = self.parse_expression()
        return Return(value=value)

    def parse_for(self) -> For:
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.IN)
        iterable = self.parse_expression()
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        return For(var=var, iterable=iterable, body=body)

    def parse_while(self) -> While:
        self.expect(TokenType.WHILE)
        condition = self.parse_expression()
        self.expect(TokenType.LBRACE)
        body = self.parse_block()
        self.expect(TokenType.RBRACE)
        return While(condition=condition, body=body)

    # ── Expression Parsing (precedence climbing) ──────────

    def parse_expression(self):
        return self.parse_pipe()

    def parse_pipe(self):
        left = self.parse_or()
        while self.current().type == TokenType.PIPE:
            self.advance()
            right = self.parse_or()
            left = Pipe(left=left, right=right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.current().type == TokenType.OR:
            self.advance()
            right = self.parse_and()
            left = BinOp(op="or", left=left, right=right)
        return left

    def parse_and(self):
        left = self.parse_comparison()
        while self.current().type == TokenType.AND:
            self.advance()
            right = self.parse_comparison()
            left = BinOp(op="and", left=left, right=right)
        return left

    def parse_comparison(self):
        left = self.parse_addition()
        COMP_OPS = {
            TokenType.EQ: "==", TokenType.NEQ: "!=",
            TokenType.LT: "<", TokenType.GT: ">",
            TokenType.LTE: "<=", TokenType.GTE: ">=",
        }
        while self.current().type in COMP_OPS:
            op = COMP_OPS[self.advance().type]
            right = self.parse_addition()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_addition(self):
        left = self.parse_multiplication()
        while self.current().type in (TokenType.PLUS, TokenType.MINUS):
            op = "+" if self.advance().type == TokenType.PLUS else "-"
            right = self.parse_multiplication()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_multiplication(self):
        left = self.parse_unary()
        while self.current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            tok = self.advance()
            op = {TokenType.STAR: "*", TokenType.SLASH: "/", TokenType.PERCENT: "%"}[tok.type]
            right = self.parse_unary()
            left = BinOp(op=op, left=left, right=right)
        return left

    def parse_unary(self):
        if self.current().type == TokenType.NOT:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op="not", operand=operand)
        if self.current().type == TokenType.MINUS:
            self.advance()
            operand = self.parse_unary()
            return UnaryOp(op="-", operand=operand)
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.current().type == TokenType.LPAREN:
                # Function call
                if isinstance(node, Identifier):
                    self.advance()
                    args = self.parse_args()
                    self.expect(TokenType.RPAREN)
                    node = Call(name=node.name, args=args)
                else:
                    break
            elif self.current().type == TokenType.DOT:
                # Method call
                self.advance()
                method = self.expect(TokenType.IDENTIFIER).value
                if self.current().type == TokenType.LPAREN:
                    self.advance()
                    args = self.parse_args()
                    self.expect(TokenType.RPAREN)
                    node = MethodCall(object=node, method=method, args=args)
                else:
                    node = MethodCall(object=node, method=method, args=[])
            elif self.current().type == TokenType.LBRACKET:
                # Index access
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                node = Index(object=node, index=index)
            else:
                break
        return node

    def parse_primary(self):
        tok = self.current()

        if tok.type == TokenType.NUMBER:
            self.advance()
            val = float(tok.value) if "." in tok.value else int(tok.value)
            return Number(value=val)

        if tok.type == TokenType.STRING:
            self.advance()
            return String(value=tok.value)

        if tok.type == TokenType.TRUE:
            self.advance()
            return Bool(value=True)

        if tok.type == TokenType.FALSE:
            self.advance()
            return Bool(value=False)

        if tok.type == TokenType.IDENTIFIER:
            self.advance()
            return Identifier(name=tok.value)

        if tok.type == TokenType.LBRACKET:
            return self.parse_array()

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        raise ParseError(
            f"Unexpected token {tok.type.name} ({tok.value!r}) at line {tok.line}"
        )

    def parse_array(self) -> Array:
        self.expect(TokenType.LBRACKET)
        elements = []
        self.skip_newlines()
        if self.current().type != TokenType.RBRACKET:
            elements.append(self.parse_expression())
            while self.current().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
                if self.current().type == TokenType.RBRACKET:
                    break
                elements.append(self.parse_expression())
        self.skip_newlines()
        self.expect(TokenType.RBRACKET)
        return Array(elements=elements)

    def parse_args(self) -> list:
        args = []
        self.skip_newlines()
        if self.current().type == TokenType.RPAREN:
            return args
        args.append(self.parse_expression())
        while self.current().type == TokenType.COMMA:
            self.advance()
            self.skip_newlines()
            args.append(self.parse_expression())
        return args


def parse(tokens: list[Token]) -> list:
    """Parse a token list into an AST."""
    return Parser(tokens).parse()
