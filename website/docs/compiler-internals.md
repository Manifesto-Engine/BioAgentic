---
sidebar_position: 7
title: Compiler Internals
---

# Sovereign Script Compiler Internals

The compiler is a classic 3-stage pipeline: **source → tokens → AST → Python**. It lives in `sovereign_lang/` (3 files, ~870 LOC total).

## Pipeline

```
Source Code            Lexer              Parser           CodeGen
─────────────  →  ─────────────  →  ─────────────  →  ─────────────
"pipeline x {     [PIPELINE, ID,     Pipeline(        "def pipeline_x():
  let y = 42       LET, ID, ASSIGN,    name="x",         y = 42
}"                  NUMBER, ...]        body=[Let(...)])  _result = pipeline_x()"
```

## Stage 1: Lexer (`lexer.py` — 213 LOC)

The tokenizer converts raw source text into typed tokens. Single-pass, character-by-character.

### Token Types (40+)

| Category | Tokens |
|---|---|
| **Keywords** | `pipeline`, `let`, `if`, `else`, `fn`, `return`, `for`, `in`, `while`, `true`, `false`, `and`, `or`, `not` |
| **Literals** | `STRING`, `NUMBER`, `IDENTIFIER` |
| **Operators** | `+`, `-`, `*`, `/`, `%`, `=`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `\|>` |
| **Delimiters** | `(`, `)`, `{`, `}`, `[`, `]`, `,`, `.`, `:` |
| **Special** | `NEWLINE`, `EOF` |

### Features
- String escape sequences (`\n`, `\t`, `\\`, `\"`, `\'`)
- Single-line comments (`// comment`)
- Decimal numbers (`3.14`)
- Two-character operator lookahead (`|>`, `==`, `!=`, `<=`, `>=`)

## Stage 2: Parser (`parser.py` — 454 LOC)

Recursive descent parser. Produces an AST from the token stream.

### AST Node Types (20)

| Node | Fields | Example |
|---|---|---|
| `Pipeline` | `name`, `body` | `pipeline x { ... }` |
| `Let` | `name`, `value` | `let x = 42` |
| `If` | `condition`, `then_body`, `else_body` | `if x > 10 { ... }` |
| `Fn` | `name`, `params`, `body` | `fn add(a, b) { ... }` |
| `Return` | `value` | `return x + 1` |
| `For` | `var`, `iterable`, `body` | `for item in list { ... }` |
| `While` | `condition`, `body` | `while x < 10 { ... }` |
| `Call` | `name`, `args` | `print("hello")` |
| `MethodCall` | `object`, `method`, `args` | `list.map(fn)` |
| `BinOp` | `op`, `left`, `right` | `x + y` |
| `UnaryOp` | `op`, `operand` | `not x` |
| `Pipe` | `left`, `right` | `data \|> transform` |
| `String` | `value` | `"hello"` |
| `Number` | `value` | `42` |
| `Bool` | `value` | `true` |
| `Identifier` | `name` | `x` |
| `Array` | `elements` | `[1, 2, 3]` |
| `Index` | `object`, `index` | `list[0]` |
| `Assign` | `name`, `value` | `x = 42` |

### Operator Precedence (Low → High)

```
Pipe (|>)
  → Or (or)
    → And (and)
      → Comparison (==, !=, <, >, <=, >=)
        → Addition (+, -)
          → Multiplication (*, /, %)
            → Unary (not, -)
              → Postfix (calls, index, method)
                → Primary (literals, identifiers, arrays)
```

## Stage 3: Code Generator (`codegen.py` — 202 LOC)

Translates the AST into executable Python. Two key features:

### Prelude Injection

Every compiled pipeline gets a prelude with built-in functions:

```python
# Auto-injected builtins
cx_remember(content, tags, importance)  # Store memory
cx_recall(query, limit)                 # Search memories
cx_has_seen(target)                     # Check if memory exists
sov_emit(event, data)                   # Queue event emission
sov_run(pipeline_name)                  # Execute another pipeline
```

The prelude also imports safe standard library modules: `json`, `time`, `math`, `re`, `hashlib`, `datetime`, `random`.

### Pipe Desugaring

The `|>` operator is syntactic sugar for function application:

```
data |> transform |> output
```

Compiles to:

```python
output(transform(data))
```

### Pipeline Auto-Execution

Pipelines compile to a function definition + immediate call:

```python
# Sovereign Script:
pipeline scanner { print("scanning") }

# Compiled Python:
def pipeline_scanner():
    print("scanning")

# Auto-execute pipeline
_result = pipeline_scanner()
```

## Using the Compiler Directly

```python
from sovereign_lang import parse, generate
from sovereign_lang.lexer import tokenize

source = 'pipeline test { let x = 42\n print(x) }'

# Stage 1: Tokenize
tokens = tokenize(source)

# Stage 2: Parse
ast = parse(tokens)

# Stage 3: Generate
python_code = generate(ast)
```

---

**Next:** [API Reference →](/docs/api-reference)
