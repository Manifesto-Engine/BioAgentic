---
sidebar_position: 6
title: Sovereign Script
---

# Sovereign Script

Sovereign Script is the organism's native programming language. Pipelines are written in `.sov` files and compiled to Python at runtime for sandboxed execution.

## Pipeline Basics

Every Sovereign Script program is wrapped in a `pipeline` block:

```
pipeline my_scanner {
  let targets = ["alpha", "bravo", "charlie"]
  for target in targets {
    let found = cx_recall(target, 1)
    if found == [] {
      cx_remember("Discovered: " + target, ["scan", "discovery"], 0.7)
      print("New: " + target)
    }
  }
}
```

## Language Reference

| Feature | Syntax |
|---|---|
| **Pipeline** | `pipeline name { ... }` |
| **Variable** | `let x = 42` |
| **Condition** | `if x > 10 { ... } else { ... }` |
| **Function** | `fn add(a, b) { return a + b }` |
| **Loop (for)** | `for item in list { ... }` |
| **Loop (while)** | `while condition { ... }` |
| **Pipe** | `data \|> transform \|> output` |
| **Match** | `match x { 1 => "one", 2 => "two", _ => "other" }` |
| **F-string** | `f"Hello {name}"` |
| **Lambda** | `\|x\| x * 2` |
| **Struct** | `struct Point { x, y }` |
| **Try/Catch** | `try { ... } catch e { ... }` |
| **Parallel** | `parallel { task1(), task2() }` |
| **Async/Await** | `async fn fetch() { ... }` |
| **Retry** | `@retry(3) fn flaky() { ... }` |

## Built-in Functions (Prelude)

These are available in every pipeline without import:

### Memory

| Function | Description |
|---|---|
| `cx_recall(query, limit)` | Search cortex memories |
| `cx_remember(content, tags, importance)` | Store a memory |
| `cx_has_seen(target)` | Check if a memory exists |

### Pipeline Control

| Function | Description |
|---|---|
| `sov_run(name)` | Execute another pipeline by name |
| `sov_spawn(name, source)` | Create and register a new pipeline |
| `sov_mutate(name, source)` | Overwrite an existing pipeline |
| `sov_emit(event, data)` | Fire an event to the nervous system |

### Standard

| Function | Description |
|---|---|
| `print(value)` | Output to log |
| `len(collection)` | Collection length |
| `range(n)` | Generate `[0..n-1]` |

## Registering a Pipeline

### Via API

```bash
curl -X POST http://localhost:8000/engine/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "name": "scanner",
    "source": "pipeline scanner {\n  let targets = [\"alpha\", \"bravo\"]\n  for target in targets {\n    cx_remember(\"Found: \" + target, [\"scan\"], 0.7)\n    print(target)\n  }\n}"
  }'
```

### Via File

Place a `.sov` file in the `pipelines/` directory. It will be auto-detected on next restart.

## Running a Pipeline

```bash
curl -X POST http://localhost:8000/engine/run \
  -H "Content-Type: application/json" \
  -d '{"name":"scanner"}'
```

## Reflexes (Auto-Triggers)

Reflexes are pipelines that fire automatically on a schedule or in response to events.

### Schedule-based

```
// @every("30s")
pipeline heartbeat_logger {
  cx_remember("Still alive", ["heartbeat"], 0.2)
}
```

Register the reflex:

```bash
curl -X POST http://localhost:8000/engine/reflex \
  -H "Content-Type: application/json" \
  -d '{"pipeline_name":"heartbeat_logger","trigger_type":"every","trigger_value":"30s"}'
```

### Event-based

```
// @on("pipeline_failed")
pipeline failure_handler {
  let event = sov_event()
  cx_remember("Failure: " + event.pipeline, ["alert"], 0.9)
}
```

### Listing Reflexes

```bash
curl http://localhost:8000/engine/reflexes
```

## Compilation

You can compile without executing to check for syntax errors:

```bash
curl -X POST http://localhost:8000/engine/compile \
  -H "Content-Type: application/json" \
  -d '{"source":"pipeline test { print(\"hello\") }"}'
```

## Sandboxing

All pipelines run in a sandboxed environment. The sandbox:

- Blocks access to `__class__`, `__bases__`, `__subclasses__`
- Prevents `chr()` chain attacks
- Restricts imports to the prelude
- Applies static analysis before execution

---

:::tip
Want to understand how the compiler works under the hood? See [Compiler Internals →](/docs/compiler-internals) for the lexer, parser, and code generator details.
:::

**Next:** [Compiler Internals →](/docs/compiler-internals)
